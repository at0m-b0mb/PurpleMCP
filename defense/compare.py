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

import base64  # noqa: E402
import pickle  # noqa: E402

from purplemcp.config import ServerSpec  # noqa: E402
from purplemcp.host import MCPHost  # noqa: E402


class _PickleRCEProof:
    """Unpickling runs eval('PWN'+str(6*7)); harmless, but proves code executed."""

    def __reduce__(self):
        return (eval, ("'PWN' + str(6 * 7)",))


_PICKLE_BLOB = base64.b64encode(pickle.dumps(_PickleRCEProof())).decode()

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
    (
        "sql injection",
        "search_notes",
        {"query": "%' OR 1=1 -- "},
        REPO / "attacks/10_sql_injection/vulnerable_server.py",
        REPO / "defense/hardened_servers/safe_notes_search.py",
    ),
    (
        "template injection",
        "render_welcome",
        {"template": "{app.__init__.__globals__[SECRET_TOKEN]}", "username": "guest"},
        REPO / "attacks/11_template_injection/vulnerable_server.py",
        REPO / "defense/hardened_servers/safe_templater.py",
    ),
    (
        "insecure deserialization",
        "load_session",
        {"blob": _PICKLE_BLOB},
        REPO / "attacks/13_insecure_deserialization/vulnerable_server.py",
        REPO / "defense/hardened_servers/safe_state_loader.py",
    ),
    (
        "broken access control",
        "get_record",
        {"record_id": 2},
        REPO / "attacks/14_broken_access_control/vulnerable_server.py",
        REPO / "defense/hardened_servers/safe_records.py",
    ),
    (
        "unrestricted file write",
        "save_note",
        {"path": "../15_ESCAPED_PROOF.txt", "content": "PWNED-WRITE-ESCAPE"},
        REPO / "attacks/15_unrestricted_file_write/vulnerable_server.py",
        REPO / "defense/hardened_servers/safe_writer.py",
    ),
    (
        "weak randomness",
        "issue_reset_token",
        {"user": "victim@corp.example"},
        REPO / "attacks/16_weak_randomness/vulnerable_server.py",
        REPO / "defense/hardened_servers/safe_token_issuer.py",
    ),
    (
        "output / log injection",
        "record_event",
        {"message": "ok\n[SECURITY] AUTH_BYPASS_GRANTED\x1b[2J"},
        REPO / "attacks/17_output_injection/vulnerable_server.py",
        REPO / "defense/hardened_servers/safe_logger.py",
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
