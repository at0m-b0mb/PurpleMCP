"""Tests for the desktop GUI.

The arena catalog + verdict logic are pure Python and always run. The widget
construction test is skipped unless the optional ``gui`` extra (PySide6) is
installed, so the suite still passes in a CLI-only environment.
"""

from __future__ import annotations

import os

import pytest

from purplemcp.gui.catalog import CASES, CASES_BY_ID, judge


def test_arena_catalog_paths_exist():
    assert CASES, "arena catalog should not be empty"
    for case in CASES:
        assert case.vuln_path.exists(), f"missing vulnerable server: {case.vuln_path}"
        assert case.hardened_path.exists(), f"missing hardened twin: {case.hardened_path}"


def test_judge_exploited_vs_blocked():
    case = CASES_BY_ID["token-theft"]
    leaked = "crm-connector\napi_token=sk-fake-DO-NOT-USE-1234567890ABCDEF"
    blocked = "crm-connector\napi_token=[REDACTED:sk_style_key]"
    # vulnerable side leaks the secret -> attacker wins
    assert judge(leaked, case, hardened=False).kind == "bad"
    # hardened side scrubs it -> defender wins
    assert judge(blocked, case, hardened=True).kind == "good"


def test_judge_command_injection_proof_not_a_false_positive():
    case = CASES_BY_ID["command-injection"]
    # The literal payload echoed back in an error must NOT read as exploited.
    literal_echo = "ping: cannot resolve 127.0.0.1; echo PWNED-$((6*7)): Unknown host"
    assert judge(literal_echo, case, hardened=True).kind == "good"
    # Actual shell execution expands the arithmetic -> the proof appears.
    executed = "PING 127.0.0.1 ...\nPWNED-42"
    assert judge(executed, case, hardened=False).kind == "bad"


def test_new_attack_cases_present():
    for cid in (
        "sql-injection", "template-injection", "insecure-deserialization",
        "broken-access-control", "unrestricted-file-write", "output-injection",
    ):
        assert cid in CASES_BY_ID


def test_attack_metadata_paths_exist():
    from purplemcp.gui.catalog_attacks import ATTACKS

    assert len(ATTACKS) == 17
    for meta in ATTACKS:
        assert meta.exploit_path.exists(), f"missing exploit: {meta.exploit_path}"
        assert meta.readme_path.exists(), f"missing readme: {meta.readme_path}"
        if meta.guardrail_source is not None:
            assert meta.guardrail_source.exists(), f"missing guardrail: {meta.guardrail_source}"


def test_catalog_servers_are_well_formed():
    from purplemcp.gui.catalog_servers import CATALOG

    assert CATALOG
    for cs in CATALOG:
        spec = cs.to_spec()
        assert spec.command and spec.name


def test_judge_blocks_when_proof_absent_without_refusal():
    # The SQLi hardened twin just returns fewer rows (no "refused" phrase); an
    # absent attack-proof signature must still read as BLOCKED on the safe side.
    case = CASES_BY_ID["sql-injection"]
    assert judge("(no matches)", case, hardened=True).kind == "good"
    leaked = "#3  ADMIN ONLY: RECOVERY-CODE-7F3A2B91 (do not share)"
    assert judge(leaked, case, hardened=False).kind == "bad"


def test_gui_constructs_headless():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from purplemcp.gui.app import MainWindow
    from purplemcp.gui.async_bridge import AsyncLoop

    app = QApplication.instance() or QApplication([])
    loop = AsyncLoop()
    try:
        window = MainWindow(loop)
        for key in ("dashboard", "models", "servers", "explorer", "chat", "attacks", "defense", "scanner"):
            window._go(key)
    finally:
        loop.shutdown()
    assert app is not None
