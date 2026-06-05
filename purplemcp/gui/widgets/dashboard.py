"""Dashboard — an at-a-glance overview of providers, servers, and the lab."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ...config import REPO_ROOT, load_providers, load_registry
from ..icons import icon
from ..theme import PALETTE, rgba
from .common import (
    Badge,
    Card,
    add_shadow,
    button,
    clear_layout,
    hline,
    make_scroll,
    mono,
    muted,
    page_header,
)


def _count_attack_labs() -> int:
    attacks = REPO_ROOT / "attacks"
    if not attacks.exists():
        return 0
    return sum(
        1 for p in attacks.iterdir() if p.is_dir() and p.name[:2].isdigit()
    )


def _count_hardened_twins() -> int:
    twins = REPO_ROOT / "defense" / "hardened_servers"
    if not twins.exists():
        return 0
    return sum(1 for p in twins.glob("safe_*.py"))


class StatCard(Card):
    def __init__(self, value: str, label: str, icon_name: str, color: str, parent=None) -> None:
        super().__init__(parent=parent)
        self.body.setSpacing(8)
        top = QHBoxLayout()
        chip = QLabel()
        chip.setPixmap(icon(icon_name, color, 20).pixmap(20, 20))
        chip.setFixedSize(38, 38)
        chip.setAlignment(Qt.AlignCenter)
        chip.setStyleSheet(f"background: {rgba(color, 0.13)}; border-radius: 10px;")
        top.addWidget(chip)
        top.addStretch(1)
        self.body.addLayout(top)
        self._value = QLabel(value)
        self._value.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {PALETTE['text']};")
        self.body.addWidget(self._value)
        self.body.addWidget(muted(label, faint=True))

    def set_value(self, value: str) -> None:
        self._value.setText(value)


class HeroCard(Card):
    """The branded 'Build it. Attack it. Defend it.' banner."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setStyleSheet(
            "QFrame#Card {"
            "  border: 1px solid #2a2444;"
            "  border-radius: 16px;"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "    stop:0 rgba(139,92,246,0.20), stop:0.55 rgba(99,102,241,0.06),"
            "    stop:1 rgba(244,63,94,0.10));"
            "}"
        )
        add_shadow(self)
        tag = QLabel("Build it.  Attack it.  Defend it.")
        tag.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {PALETTE['text']};")
        self.body.addWidget(tag)
        self.body.addWidget(
            muted(
                "A purple-team lab for the Model Context Protocol — connect models to MCP "
                "servers, then break and harden them.",
            )
        )
        pillars = QHBoxLayout()
        pillars.setSpacing(10)
        for text, color in (
            ("🏗  Build & Connect", PALETTE["violet"]),
            ("🔴  Attack (lab)", PALETTE["red"]),
            ("🔵  Defend", PALETTE["blue"]),
        ):
            pillars.addWidget(Badge(text, color))
        pillars.addStretch(1)
        self.body.addLayout(pillars)


class DashboardPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(18)

        header_row = QHBoxLayout()
        header_row.addWidget(page_header("Dashboard", "Your PurpleMCP lab at a glance"), 1)
        self._refresh_btn = button("Refresh", "ghost", "refresh")
        self._refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(self._refresh_btn, alignment=Qt.AlignTop)
        root.addLayout(header_row)

        root.addWidget(HeroCard())

        # stat cards
        self._stats = QGridLayout()
        self._stats.setSpacing(14)
        self._providers_stat = StatCard("0 / 0", "Providers ready", "cpu", PALETTE["green"])
        self._servers_stat = StatCard("0", "MCP servers", "server", PALETTE["violet"])
        self._labs_stat = StatCard("0", "Attack labs", "skull", PALETTE["red"])
        self._twins_stat = StatCard(str(_count_hardened_twins()), "Hardened twins", "lock", PALETTE["blue"])
        for col, card in enumerate(
            (self._providers_stat, self._servers_stat, self._labs_stat, self._twins_stat)
        ):
            self._stats.addWidget(card, 0, col)
        root.addLayout(self._stats)

        # detail cards row
        detail = QHBoxLayout()
        detail.setSpacing(16)
        self._providers_card = Card("LLM Providers", "Bring-your-own-key backends")
        self._providers_box = QVBoxLayout()
        self._providers_box.setSpacing(0)
        self._providers_card.body.addLayout(self._providers_box)
        detail.addWidget(self._providers_card, 1)

        self._servers_card = Card("MCP Servers", "Clean example servers, sandboxed")
        self._servers_box = QVBoxLayout()
        self._servers_box.setSpacing(0)
        self._servers_card.body.addLayout(self._servers_box)
        detail.addWidget(self._servers_card, 1)
        root.addLayout(detail)
        root.addStretch(1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scroll(inner))
        self.refresh()

    # -- data ------------------------------------------------------------- #
    def refresh(self) -> None:
        providers = load_providers()
        registry = load_registry()
        ready = sum(1 for c in providers.values() if c.ready)
        self._providers_stat.set_value(f"{ready} / {len(providers)}")
        self._servers_stat.set_value(str(len(registry)))
        self._labs_stat.set_value(str(_count_attack_labs()))

        _clear(self._providers_box)
        for i, (name, cfg) in enumerate(providers.items()):
            if i:
                self._providers_box.addWidget(hline())
            self._providers_box.addWidget(_provider_row(name, cfg))

        _clear(self._servers_box)
        for i, (name, spec) in enumerate(registry.items()):
            if i:
                self._servers_box.addWidget(hline())
            self._servers_box.addWidget(_server_row(name, spec))


def _clear(layout) -> None:
    clear_layout(layout)


def _provider_row(name: str, cfg) -> QWidget:
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 9, 0, 9)
    lay.setSpacing(10)
    nm = QLabel(name)
    nm.setStyleSheet("font-weight: 700;")
    nm.setFixedWidth(92)
    lay.addWidget(nm)
    lay.addWidget(mono(cfg.model, PALETTE["text_dim"]))
    lay.addStretch(1)
    if cfg.ready:
        lay.addWidget(Badge("ready", PALETTE["green"]))
    else:
        lay.addWidget(Badge("no key", PALETTE["text_faint"]))
    return row


def _server_row(name: str, spec) -> QWidget:
    row = QWidget()
    lay = QVBoxLayout(row)
    lay.setContentsMargins(0, 9, 0, 9)
    lay.setSpacing(2)
    top = QHBoxLayout()
    nm = QLabel(name)
    nm.setStyleSheet("font-weight: 700;")
    top.addWidget(nm)
    top.addStretch(1)
    top.addWidget(Badge(spec.transport, PALETTE["indigo"]))
    lay.addLayout(top)
    lay.addWidget(muted(spec.description, faint=True))
    return row
