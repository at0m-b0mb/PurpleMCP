"""Regenerate the GUI screenshots used in the README/docs.

Renders each page of the desktop app offscreen at a consistent size and saves it
to docs/images/gui/. Reproducible:

    QT_QPA_PLATFORM=offscreen python scripts/gen_screenshots.py

Needs the GUI extra (PySide6). A couple of pages are driven (the scanner runs a
scan; the explorer connects to the calculator) so the shots show real content;
everything else is rendered as-loaded.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "images" / "gui"
SIZE = (1360, 880)

PAGE_SHOTS = {
    "dashboard": "1_dashboard.png",
    "explorer": "2_explorer.png",
    "chat": "3_chat.png",
    "scanner": "4_scanner.png",
    "attacks": "5_attacks.png",
    "defense": "6_defense.png",
    "models": "7_models.png",
    "servers": "8_servers.png",
    "research": "9_research.png",
    "learn": "10_learn.png",
}


def pump(app: QApplication, seconds: float) -> None:
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.01)


def pump_until(app: QApplication, cond, timeout: float = 8.0) -> None:
    end = time.time() + timeout
    while time.time() < end and not cond():
        app.processEvents()
        time.sleep(0.02)
    pump(app, 0.3)


def main() -> int:
    from purplemcp.gui.app import MainWindow
    from purplemcp.gui.async_bridge import AsyncLoop
    from purplemcp.gui.theme import stylesheet

    OUT.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(stylesheet())
    window = MainWindow(AsyncLoop())
    window.resize(*SIZE)
    window.show()
    pump(app, 0.8)

    for key, filename in PAGE_SHOTS.items():
        window._go_and_select(key)
        page = window._pages[key]
        pump(app, 0.5)

        # drive a couple of pages so the screenshots show real content
        try:
            if key == "scanner" and hasattr(page, "_scan_btn"):
                page._scan_btn.click()
                pump_until(app, lambda: page._findings_box.count() > 0, 10)
            elif key == "explorer" and hasattr(page, "_connect_btn"):
                page._connect_btn.click()
                pump_until(app, lambda: page._tool_list.count() > 0, 10)
            else:
                pump(app, 2.0)  # let async-loading pages (e.g. Models) populate
        except Exception as exc:  # noqa: BLE001 - best-effort; still grab
            print(f"  ! {key}: {exc}")

        window.grab().save(str(OUT / filename))
        print(f"  saved {filename}")

    # command palette (a separate popup widget)
    window._open_palette()
    pump(app, 0.4)
    window._palette.grab().save(str(OUT / "11_palette.png"))
    print("  saved 11_palette.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
