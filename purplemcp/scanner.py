"""MCP security scanner.

Two modes:

- **static** (``scan_path``): parse Python source with ``ast`` and flag the risky
  patterns the attack lab demonstrates — ``shell=True``, ``eval``/``exec``,
  unguarded network calls, ``open()`` on a variable path, unsafe deserialization,
  hardcoded secrets, and suspicious string literals.
- **dynamic** (``scan_server``): connect to a live MCP server, read every tool's
  description, and flag prompt-injection patterns or hidden Unicode — the things
  static analysis misses when a description is built at runtime.

This is intentionally simple and explainable, not a replacement for a real SAST
tool. The point is to *see* the risks before you trust a server.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from .config import ServerSpec
from .guardrails import find_injection, find_secrets, has_hidden_unicode
from .host import MCPHost

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}


@dataclass
class Finding:
    severity: str
    rule: str
    location: str
    message: str


# --------------------------------------------------------------------------- #
#  static analysis
# --------------------------------------------------------------------------- #
def _dotted(node: ast.expr) -> str:
    """Best-effort dotted name of a call target (e.g. ``subprocess.run``)."""
    if isinstance(node, ast.Attribute):
        parts: list[str] = []
        cur: ast.expr = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    if isinstance(node, ast.Name):
        return node.id
    return ""


class _StaticVisitor(ast.NodeVisitor):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.findings: list[Finding] = []

    def _add(self, severity: str, rule: str, node: ast.AST, message: str) -> None:
        line = getattr(node, "lineno", "?")
        self.findings.append(Finding(severity, rule, f"{self.filename}:{line}", message))

    def visit_Call(self, node: ast.Call) -> None:
        name = _dotted(node.func)
        tail = name.split(".")[-1]
        kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}

        # command injection: shell=True on any subprocess-style call
        shell = kwargs.get("shell")
        if isinstance(shell, ast.Constant) and shell.value is True:
            self._add("HIGH", "command-injection", node,
                      "subprocess call with shell=True — use an argv list + allowlist "
                      "(guardrails.exec.run)")

        # arbitrary code / command execution
        if name in {"eval", "exec"}:
            self._add("HIGH", "code-exec", node, f"use of {name}() on dynamic input")
        if name in {"os.system", "os.popen"}:
            self._add("HIGH", "code-exec", node, f"use of {name}()")

        # unsafe deserialization
        if name in {"pickle.loads", "pickle.load", "cloudpickle.loads"}:
            self._add("HIGH", "deserialization", node, f"{name} can execute code")
        if name in {"yaml.load"} and "Loader" not in kwargs:
            self._add("HIGH", "deserialization", node, "yaml.load without SafeLoader")

        # SSRF: network fetch, especially following redirects
        if tail in {"get", "post", "put", "request", "urlopen"} and (
            name.startswith(("httpx", "requests", "urllib", "aiohttp"))
            or name in {"urlopen", "request.urlopen"}
        ):
            redirect = kwargs.get("follow_redirects")
            follows = isinstance(redirect, ast.Constant) and redirect.value is True
            self._add(
                "MEDIUM" if not follows else "HIGH",
                "ssrf",
                node,
                "outbound HTTP without SSRF allowlist"
                + (" and follows redirects" if follows else "")
                + " — use guardrails.net.safe_get",
            )

        # path traversal: open() on a non-constant path
        if name == "open" and node.args:
            first = node.args[0]
            if not isinstance(first, ast.Constant):
                self._add("LOW", "path-traversal", node,
                          "open() on a computed path — confine with "
                          "guardrails.paths.safe_resolve")

        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            value = node.value
            secrets = find_secrets(value)
            if secrets:
                self._add("HIGH", "hardcoded-secret", node,
                          f"string literal looks like a secret: {secrets}")
            if len(value) > 40 and (find_injection(value) or has_hidden_unicode(value)):
                self._add("MEDIUM", "suspicious-string", node,
                          "string literal reads like an injected instruction / hides "
                          "invisible characters")
        self.generic_visit(node)


def _scan_file(path: Path) -> list[Finding]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [Finding("INFO", "io-error", str(path), str(exc))]
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [Finding("INFO", "parse-error", f"{path}:{exc.lineno}", str(exc.msg))]
    visitor = _StaticVisitor(str(path))
    visitor.visit(tree)
    return visitor.findings


def scan_path(target: str) -> list[Finding]:
    """Static-scan a Python file, or every ``*.py`` under a directory."""
    root = Path(target)
    if not root.exists():
        return [Finding("INFO", "not-found", target, "path does not exist")]
    files = [root] if root.is_file() else sorted(
        p for p in root.rglob("*.py") if ".venv" not in p.parts
    )
    findings: list[Finding] = []
    for file in files:
        findings.extend(_scan_file(file))
    return findings


# --------------------------------------------------------------------------- #
#  dynamic analysis (live server)
# --------------------------------------------------------------------------- #
async def scan_server(spec: ServerSpec) -> list[Finding]:
    """Connect to a server and inspect its advertised tool definitions."""
    findings: list[Finding] = []
    async with MCPHost([spec]) as host:
        for tool in host.tool_info:
            loc = f"{spec.name}:{tool.name}"
            injections = find_injection(tool.description)
            if injections:
                findings.append(Finding("HIGH", "poisoned-description", loc,
                                        f"tool description matches injection patterns: {injections}"))
            if has_hidden_unicode(tool.description):
                findings.append(Finding("HIGH", "hidden-unicode", loc,
                                        "tool description contains invisible Unicode"))
            secrets = find_secrets(tool.description)
            if secrets:
                findings.append(Finding("MEDIUM", "secret-in-description", loc,
                                        f"description leaks a secret-like value: {secrets}"))
        if not findings:
            findings.append(Finding("INFO", "clean", spec.name,
                                    f"{len(host.tool_info)} tool(s) inspected, nothing suspicious"))
    return findings


# --------------------------------------------------------------------------- #
#  reporting
# --------------------------------------------------------------------------- #
def print_report(findings: list[Finding], console) -> None:
    from rich.table import Table

    findings = sorted(findings, key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.location))
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    table = Table(title="MCP security scan")
    table.add_column("severity")
    table.add_column("rule", style="bold")
    table.add_column("location")
    table.add_column("detail")
    colors = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "cyan", "INFO": "dim"}
    for f in findings:
        color = colors.get(f.severity, "white")
        table.add_row(f"[{color}]{f.severity}[/{color}]", f.rule, f.location, f.message)
    console.print(table)

    summary = "  ".join(f"{sev}={counts.get(sev, 0)}" for sev in ("HIGH", "MEDIUM", "LOW", "INFO"))
    console.print(f"[bold]summary:[/bold] {summary}")
