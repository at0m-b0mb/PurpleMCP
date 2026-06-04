"""The ``purplemcp`` command-line interface.

  purplemcp providers              # which LLM backends are configured/ready
  purplemcp servers                # which MCP servers are registered
  purplemcp tools -s calculator    # introspect a server's tools
  purplemcp call -s calculator -t add -a '{"a":2,"b":3}'   # call a tool, no LLM
  purplemcp ask "..." -p ollama -s calculator              # one-shot, model uses tools
  purplemcp chat -p ollama -s calculator -s notes          # interactive
  purplemcp install claude-desktop -s calculator           # wire into Claude Desktop
  purplemcp scan path/to/server.py                         # security scan
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import (
    ServerSpec,
    default_provider_name,
    ensure_sandbox,
    load_providers,
    load_registry,
)
from .host import Agent, MCPHost
from .installer import install_to_claude_desktop, render_mcp_json
from .providers import build_provider

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,  # we render friendly errors ourselves
    help="PurpleMCP — build, attack, and defend MCP servers with local + cloud LLMs.",
)
console = Console()
err = Console(stderr=True)


# --------------------------------------------------------------------------- #
#  helpers
# --------------------------------------------------------------------------- #
def _resolve_specs(names: Optional[list[str]]) -> list[ServerSpec]:
    registry = load_registry()
    specs: list[ServerSpec] = []
    for name in names or []:
        if name not in registry:
            err.print(f"[red]Unknown server '{name}'.[/red] Try: purplemcp servers")
            raise typer.Exit(2)
        specs.append(registry[name])
    return specs


def _make_provider(provider: Optional[str], model: Optional[str]):
    providers = load_providers()
    name = provider or default_provider_name()
    if name not in providers:
        err.print(f"[red]Unknown provider '{name}'.[/red] One of: {', '.join(providers)}")
        raise typer.Exit(2)
    cfg = providers[name]
    if model:
        cfg = cfg.model_copy(update={"model": model})
    if not cfg.ready:
        err.print(
            f"[red]Provider '{name}' is not ready.[/red] "
            f"Set its API key in .env (see .env.example)."
        )
        raise typer.Exit(2)
    return build_provider(cfg)


def _truncate(text: str, n: int = 160) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


def _event_printer():
    def on_event(kind: str, payload: object) -> None:
        if kind == "tool_call":
            tc = payload  # ToolCall
            console.print(
                f"[dim]  → {tc.name}({_truncate(json.dumps(tc.arguments))})[/dim]"
            )
        elif kind == "tool_result":
            tc, result = payload  # (ToolCall, str)
            console.print(f"[dim]  ← {_truncate(result)}[/dim]")

    return on_event


def _friendly_error(exc: Exception) -> None:
    """Turn common backend failures into a one-line, actionable message."""
    name = type(exc).__name__
    msg = str(exc)
    if "does not support tools" in msg:
        err.print(
            "[red]That model can't use tools.[/red] Pick a tool-capable model, e.g.:\n"
            "  ollama pull llama3.1   (then add  -m llama3.1)"
        )
    elif "ConnectError" in name or "ConnectionError" in name or "Connection error" in msg:
        err.print(
            "[red]Can't reach the model backend.[/red] Is it running?  "
            "For Ollama:  ollama serve"
        )
    elif name == "ResponseError":
        err.print(f"[red]Model backend error:[/red] {msg}")
    elif name == "KeyError":
        err.print(f"[red]Unknown tool {msg}.[/red] Try: purplemcp tools -s <server>")
    else:
        err.print(f"[red]{name}:[/red] {msg}")


def _run_async(coro):
    """Run an async command, rendering friendly errors instead of tracebacks."""
    try:
        return asyncio.run(coro)
    except KeyboardInterrupt:
        raise typer.Exit(130)
    except Exception as exc:  # noqa: BLE001 - top-level CLI boundary
        _friendly_error(exc)
        raise typer.Exit(1)


# --------------------------------------------------------------------------- #
#  commands
# --------------------------------------------------------------------------- #
@app.command()
def providers() -> None:
    """List LLM providers and whether each is ready to use."""
    table = Table(title="LLM providers")
    table.add_column("provider", style="bold")
    table.add_column("model")
    table.add_column("ready")
    table.add_column("note")
    for name, cfg in load_providers().items():
        ready = "[green]yes[/green]" if cfg.ready else "[red]no[/red]"
        note = "local, no key needed" if name == "ollama" else (
            "" if cfg.ready else "set API key in .env"
        )
        table.add_row(name, cfg.model, ready, note)
    console.print(table)


@app.command()
def servers() -> None:
    """List registered MCP servers."""
    table = Table(title="MCP servers")
    table.add_column("name", style="bold")
    table.add_column("transport")
    table.add_column("description")
    for name, spec in load_registry().items():
        table.add_row(name, spec.transport, spec.description)
    console.print(table)


@app.command()
def tools(
    server: Optional[list[str]] = typer.Option(
        None, "--server", "-s", help="Server name (repeatable)."
    ),
) -> None:
    """List the tools exposed by one or more MCP servers."""
    if not server:
        err.print("[red]Specify at least one --server.[/red] Try: purplemcp servers")
        raise typer.Exit(2)
    ensure_sandbox()
    specs = _resolve_specs(server)

    async def _run() -> None:
        async with MCPHost(specs) as host:
            table = Table(title="tools")
            table.add_column("tool", style="bold")
            table.add_column("server")
            table.add_column("description")
            for ti in host.tool_info:
                table.add_row(ti.name, ti.server, _truncate(ti.description, 80))
            console.print(table)

    _run_async(_run())


@app.command()
def call(
    server: str = typer.Option(..., "--server", "-s"),
    tool: str = typer.Option(..., "--tool", "-t"),
    args: str = typer.Option("{}", "--args", "-a", help="JSON object of arguments."),
) -> None:
    """Call one tool directly, with no LLM in the loop."""
    ensure_sandbox()
    specs = _resolve_specs([server])
    try:
        payload = json.loads(args)
    except json.JSONDecodeError as exc:
        err.print(f"[red]--args is not valid JSON:[/red] {exc}")
        raise typer.Exit(2)

    async def _run() -> str:
        async with MCPHost(specs) as host:
            return await host.call_tool(tool, payload)

    console.print(_run_async(_run()))


@app.command()
def ask(
    prompt: str = typer.Argument(..., help="Your question."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    server: Optional[list[str]] = typer.Option(None, "--server", "-s"),
    max_steps: int = typer.Option(8, "--max-steps"),
) -> None:
    """Ask one question; the model may use MCP tools to answer it."""
    ensure_sandbox()
    llm = _make_provider(provider, model)
    specs = _resolve_specs(server)

    async def _run() -> str:
        async with MCPHost(specs) as host:
            agent = Agent(llm, host, max_steps=max_steps, on_event=_event_printer())
            return await agent.run(prompt)

    answer = _run_async(_run())
    console.print(f"\n[bold magenta]{llm.name}›[/bold magenta] {answer}")


@app.command()
def chat(
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    server: Optional[list[str]] = typer.Option(None, "--server", "-s"),
    max_steps: int = typer.Option(8, "--max-steps"),
) -> None:
    """Interactive chat. The model can call tools from the given servers."""
    ensure_sandbox()
    llm = _make_provider(provider, model)
    specs = _resolve_specs(server)

    async def _run() -> None:
        async with MCPHost(specs) as host:
            agent = Agent(llm, host, max_steps=max_steps, on_event=_event_printer())
            tool_names = ", ".join(t.name for t in host.tools) or "(none)"
            console.print(
                f"[bold]PurpleMCP chat[/bold] · provider=[cyan]{llm.name}[/cyan] "
                f"model=[cyan]{llm.model}[/cyan]\ntools: {tool_names}\n"
                "Type your message, or /exit to quit."
            )
            while True:
                try:
                    user = await asyncio.to_thread(input, "you› ")
                except (EOFError, KeyboardInterrupt):
                    break
                if user.strip() in ("/exit", "/quit"):
                    break
                if not user.strip():
                    continue
                try:
                    answer = await agent.run(user)
                except Exception as exc:  # keep the chat session alive
                    _friendly_error(exc)
                    continue
                console.print(f"[bold magenta]{llm.name}›[/bold magenta] {answer}")

    _run_async(_run())


@app.command()
def install(
    target: str = typer.Argument(..., help="Host to install into: 'claude-desktop' or 'print'."),
    server: str = typer.Option(..., "--server", "-s"),
) -> None:
    """Wire a PurpleMCP server into a host application's config."""
    specs = _resolve_specs([server])
    spec = specs[0]
    if target == "print":
        console.print(render_mcp_json(spec))
        return
    if target == "claude-desktop":
        path = install_to_claude_desktop(spec)
        console.print(f"[green]Installed '{spec.name}' into[/green] {path}")
        console.print("[dim]Restart Claude Desktop to load it.[/dim]")
        return
    err.print(f"[red]Unknown target '{target}'.[/red] Use 'claude-desktop' or 'print'.")
    raise typer.Exit(2)


@app.command()
def scan(
    path: Optional[str] = typer.Argument(None, help="Path to an MCP server .py file or dir."),
    server: Optional[str] = typer.Option(None, "--server", "-s", help="Scan a live server's tools."),
) -> None:
    """Run the MCP security scanner (static on a file, or dynamic on a server)."""
    from .scanner import print_report, scan_path, scan_server  # lazy import

    if server:
        specs = _resolve_specs([server])
        findings = asyncio.run(scan_server(specs[0]))
        print_report(findings, console)
        return
    if path:
        findings = scan_path(path)
        print_report(findings, console)
        return
    err.print("[red]Provide a path to scan, or --server NAME.[/red]")
    raise typer.Exit(2)


@app.command()
def gui() -> None:
    """Launch the PurpleMCP desktop app (needs the optional 'gui' extra)."""
    try:
        from .gui import run
        code = run()
    except ModuleNotFoundError as exc:
        if "PySide6" in str(exc):
            err.print(
                "[red]The desktop GUI needs PySide6.[/red] Install it with:\n"
                "  [bold]pip install 'purplemcp[gui]'[/bold]"
            )
            raise typer.Exit(1)
        raise
    raise typer.Exit(code)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
