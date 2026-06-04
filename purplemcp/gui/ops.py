"""Backend coroutines the GUI pages run through the async bridge.

These are thin wrappers over the same core the CLI uses (``MCPHost``, the
scanner). Keeping them here means the page widgets stay about layout, not about
how MCP sessions are opened and torn down.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from typing import Optional

from ..config import ServerSpec
from ..host import MCPHost
from ..host.client import ToolInfo
from .catalog import LAB_ENV_VAR, LAB_TOKEN, ArenaCase


# --------------------------------------------------------------------------- #
#  tool explorer
# --------------------------------------------------------------------------- #
async def list_tools(spec: ServerSpec) -> list[ToolInfo]:
    async with MCPHost([spec]) as host:
        return list(host.tool_info)


async def call_tool(spec: ServerSpec, tool: str, args: dict) -> str:
    async with MCPHost([spec]) as host:
        return await host.call_tool(tool, args)


# --------------------------------------------------------------------------- #
#  scanner
# --------------------------------------------------------------------------- #
async def scan_path(target: str):
    from ..scanner import scan_path as _scan  # lazy: pulls in ast-only path

    return await asyncio.to_thread(_scan, target)


async def scan_server(spec: ServerSpec):
    from ..scanner import scan_server as _scan

    return await _scan(spec)


# --------------------------------------------------------------------------- #
#  arena
# --------------------------------------------------------------------------- #
@dataclass
class ArenaResult:
    case_id: str
    vuln_benign: Optional[str] = None
    vuln_attack: str = ""
    hard_benign: Optional[str] = None
    hard_attack: str = ""


def _lab_spec(path, name: str) -> ServerSpec:
    """A spec that launches a lab server with the opt-in token set in its env."""
    return ServerSpec(
        name=name,
        transport="stdio",
        command=sys.executable,
        args=[str(path)],
        env={LAB_ENV_VAR: LAB_TOKEN},
    )


async def _try(host: MCPHost, tool: str, args: dict) -> str:
    try:
        return await host.call_tool(tool, args)
    except Exception as exc:  # noqa: BLE001 - shown verbatim in the arena
        return f"ERROR: {type(exc).__name__}: {exc}"


async def _pair(spec: ServerSpec, tool: str, benign, attack) -> tuple[Optional[str], str]:
    async with MCPHost([spec]) as host:
        b = await _try(host, tool, benign) if benign is not None else None
        a = await _try(host, tool, attack)
    return b, a


async def arena_run(case: ArenaCase) -> ArenaResult:
    """Fire the benign + attack payloads at the vulnerable and hardened twins."""
    result = ArenaResult(case_id=case.id)
    result.vuln_benign, result.vuln_attack = await _pair(
        _lab_spec(case.vuln_path, "vulnerable"), case.tool, case.benign_args, case.attack_args
    )
    result.hard_benign, result.hard_attack = await _pair(
        _lab_spec(case.hardened_path, "hardened"), case.tool, case.benign_args, case.attack_args
    )
    return result
