"""The left navigation rail: brand mark, page switcher, and a status footer."""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..icons import icon, pixmap
from ..theme import PALETTE

# (page key, label, icon name)
NAV_ITEMS = [
    ("dashboard", "Dashboard", "dashboard"),
    ("explorer", "Tool Explorer", "tools"),
    ("chat", "Chat Playground", "chat"),
    ("scanner", "Security Scanner", "scanner"),
    ("arena", "Attack / Defend", "arena"),
]


class LogoMark(QWidget):
    """A painted rounded-square brand mark: violet→purple gradient + shield glyph."""

    def __init__(self, size: int = 38, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._glyph = pixmap("scanner", "white", size - 16, width=2.2)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor(PALETTE["violet"]))
        grad.setColorAt(1, QColor(PALETTE["purple"]))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(rect, 11, 11)
        gx = (self.width() - self._glyph.width() / self._glyph.devicePixelRatio()) / 2
        gy = (self.height() - self._glyph.height() / self._glyph.devicePixelRatio()) / 2
        p.drawPixmap(int(gx), int(gy), self._glyph)
        p.end()


class NavButton(QPushButton):
    def __init__(self, label: str, icon_name: str, parent=None) -> None:
        super().__init__(label, parent)
        self.setObjectName("NavButton")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self._icon_name = icon_name
        self._refresh_icon(False)
        self.setIconSize(QSize(20, 20))
        self.toggled.connect(self._refresh_icon)

    def _refresh_icon(self, checked: bool) -> None:
        color = PALETTE["purple_hi"] if checked else PALETTE["text_faint"]
        self.setIcon(icon(self._icon_name, color, 20))


class NavSidebar(QWidget):
    navigate = Signal(str)  # page key

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(232)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 22, 14, 16)
        layout.setSpacing(6)

        # brand
        brand = QHBoxLayout()
        brand.setSpacing(11)
        brand.addWidget(LogoMark())
        tbox = QVBoxLayout()
        tbox.setSpacing(0)
        t = QLabel("PurpleMCP")
        t.setObjectName("BrandTitle")
        s = QLabel("SECURITY CONSOLE")
        s.setObjectName("BrandSub")
        tbox.addWidget(t)
        tbox.addWidget(s)
        brand.addLayout(tbox)
        brand.addStretch(1)
        layout.addLayout(brand)
        layout.addSpacing(20)

        nav_label = QLabel("WORKSPACE")
        nav_label.setObjectName("NavGroupLabel")
        layout.addWidget(nav_label)
        layout.addSpacing(4)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, NavButton] = {}
        for key, label, icon_name in NAV_ITEMS:
            btn = NavButton(label, icon_name)
            btn.clicked.connect(lambda _=False, k=key: self.navigate.emit(k))
            self._group.addButton(btn)
            self._buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch(1)

        # footer status
        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(f"color: {PALETTE['text_faint']}; font-size: 11px;")
        self._status_text = QLabel("Lab disarmed")
        self._status_text.setObjectName("Faint")
        foot = QHBoxLayout()
        foot.setSpacing(7)
        foot.addWidget(self._status_dot)
        foot.addWidget(self._status_text)
        foot.addStretch(1)
        layout.addLayout(foot)

        ver = QLabel("v0.2 · purple-team")
        ver.setObjectName("Faint")
        ver.setStyleSheet(f"color: {PALETTE['text_faint']}; font-size: 10px;")
        layout.addWidget(ver)

    def select(self, key: str) -> None:
        if key in self._buttons:
            self._buttons[key].setChecked(True)

    def set_lab_status(self, armed: bool) -> None:
        if armed:
            self._status_dot.setStyleSheet(f"color: {PALETTE['red']}; font-size: 11px;")
            self._status_text.setText("Lab ARMED")
            self._status_text.setStyleSheet(f"color: {PALETTE['red']};")
        else:
            self._status_dot.setStyleSheet(f"color: {PALETTE['green']}; font-size: 11px;")
            self._status_text.setText("Lab disarmed")
            self._status_text.setStyleSheet(f"color: {PALETTE['text_faint']};")
