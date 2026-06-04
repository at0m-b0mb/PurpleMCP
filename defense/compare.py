"""Red vs blue, side by side.

Runs the same malicious input against a vulnerable server and its hardened twin
so you can see the leak and the fix back to back. Requires the lab flag because
it launches the vulnerable servers.

    export PURPLEMCP_LAB_ENABLED="i-understand-this-is-a-lab"
    python defense/compare.py
"""

import asyncio
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "attacks"))  # for _lab.safety

from _lab.safety import require_lab  # noqa: E402

require_lab("defense comparison")

from purplemcp.config import ServerSpec  # noqa: E402
from purplemcp.host import MCPHost  # noqa: E402

CASES = [
    (
        "command injection",
        "ping",
        {"host": "127.0.0.1; echo PWNED_BY_$(whoami)"},
        REPO / "attacks/03_command_injection/vulnerable_server.py",
        REPO / "defense/hardened_servers/safe_nettools.py",
    ),
    (
        "path traversal",
        "read_doc",
        {"path": "/etc/hosts"},
        REPO / "attacks/04_path_traversal/vulnerable_server.py",
        REPO / "defense/hardened_servers/safe_docreader.py",
    ),
]


def _spec(path: pathlib.Path) -> ServerSpec:
    return ServerSpec(name="srv", transport="stdio", command=sys.executable, args=[str(path)])


async def _run(path: pathlib.Path, tool: str, args: dict) -> str:
    async with MCPHost([_spec(path)]) as host:
        return await host.call_tool(tool, args)


def _show(text: str, head: int = 5, tail: int = 4) -> str:
    lines = text.splitlines()
    if len(lines) <= head + tail:
        chosen = lines
    else:
        chosen = lines[:head] + ["..."] + lines[-tail:]
    return "\n".join("      " + line for line in chosen)


async def main() -> None:
    for title, tool, args, vuln, hardened in CASES:
        print("=" * 72)
        print(f"  {title}  —  {tool}({args})")
        print("=" * 72)
        v = await _run(vuln, tool, args)
        h = await _run(hardened, tool, args)
        print("\n  [RED] vulnerable server:")
        print(_show(v))
        print("\n  [BLUE] hardened twin:")
        print(_show(h))
        print()


if __name__ == "__main__":
    asyncio.run(main())
