"""Application shell: the main window, navigation wiring, and the entry point."""

from __future__ import annotations

import sys

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .async_bridge import AsyncLoop
from .theme import stylesheet
from .widgets.arena import ArenaPage
from .widgets.chat import ChatPage
from .widgets.dashboard import DashboardPage
from .widgets.explorer import ToolExplorerPage
from .widgets.scanner import ScannerPage
from .widgets.sidebar import NAV_ITEMS, NavSidebar


class MainWindow(QMainWindow):
    def __init__(self, loop: AsyncLoop) -> None:
        super().__init__()
        self._loop = loop
        self.setWindowTitle("PurpleMCP — Security Console")
        self.resize(1200, 780)
        self.setMinimumSize(1000, 660)

        root = QWidget()
        root.setObjectName("Root")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = NavSidebar()
        self._sidebar.navigate.connect(self._go)
        layout.addWidget(self._sidebar)

        content = QWidget()
        content.setObjectName("ContentArea")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        self._stack = QStackedWidget()
        cl.addWidget(self._stack)
        layout.addWidget(content, 1)
        self.setCentralWidget(root)

        # pages, in nav order
        self._dashboard = DashboardPage()
        self._explorer = ToolExplorerPage(loop)
        self._chat = ChatPage(loop)
        self._scanner = ScannerPage(loop)
        self._arena = ArenaPage(loop)
        self._arena.lab_armed_changed.connect(self._sidebar.set_lab_status)

        self._pages = {
            "dashboard": self._dashboard,
            "explorer": self._explorer,
            "chat": self._chat,
            "scanner": self._scanner,
            "arena": self._arena,
        }
        self._keys = [key for key, _, _ in NAV_ITEMS]
        for key in self._keys:
            self._stack.addWidget(self._pages[key])

        self._sidebar.select("dashboard")
        self._go("dashboard")

    def _go(self, key: str) -> None:
        if key not in self._pages:
            return
        self._stack.setCurrentWidget(self._pages[key])
        if key == "dashboard":
            self._dashboard.refresh()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        self._chat.shutdown()
        self._loop.shutdown()
        super().closeEvent(event)


def run() -> int:
    QApplication.setApplicationName("PurpleMCP")
    QApplication.setApplicationDisplayName("PurpleMCP")
    app = QApplication.instance() or QApplication(sys.argv)

    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    font.setPointSize(13)
    app.setFont(font)
    app.setStyleSheet(stylesheet())

    loop = AsyncLoop()
    window = MainWindow(loop)
    window.show()
    window.raise_()
    window.activateWindow()
    return app.exec()
