"""Defense Lab — the guardrail that stops each attack, its code, and live proof."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..async_bridge import AsyncLoop, run_job
from ..catalog import CASES_BY_ID, judge
from ..catalog_attacks import AttackMeta, grouped
from ..ops import arena_run
from ..state import LabState
from ..theme import BLUE_TEAM, MONO, PALETTE, RED_TEAM, rgba
from .arena import _TeamColumn
from .common import (
    Badge,
    BusyBar,
    Card,
    button,
    clear_layout,
    filter_grouped_list,
    flash,
    make_scroll,
    muted,
    page_header,
    search_box,
    title_label,
)
from .highlight import PythonHighlighter

_LIST_QSS = f"""
QListWidget {{ background: {PALETTE['surface_2']}; border: 1px solid {PALETTE['border']};
    border-radius: 12px; padding: 6px; }}
QListWidget::item {{ border-radius: 9px; margin: 2px 0; }}
QListWidget::item:selected {{ background: {PALETTE['surface_hi']}; }}
QListWidget::item:hover {{ background: {PALETTE['surface']}; }}
"""


class DefenseLabPage(QWidget):
    def __init__(self, loop: AsyncLoop, lab: LabState, parent=None) -> None:
        super().__init__(parent)
        self._loop = loop
        self._lab = lab
        self._meta: AttackMeta | None = None
        self._job = None
        self._highlighter = None

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 22)
        root.setSpacing(16)
        root.addWidget(
            page_header("Defense Lab", "See the guardrail that stops each attack — and prove it")
        )
        root.addWidget(self._build_arm_banner())

        split = QSplitter(Qt.Horizontal)
        split.setHandleWidth(14)
        split.addWidget(self._build_list())
        split.addWidget(make_scroll(self._build_detail_host()))
        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 5)
        split.setSizes([330, 620])
        root.addWidget(split, 1)

        self._lab.changed.connect(self._sync_armed)
        self._select_first()

    # -- arm banner (shared lab state) ------------------------------------ #
    def _build_arm_banner(self) -> Card:
        card = Card()
        card.setStyleSheet(
            "QFrame#Card {"
            f"  border: 1px solid {rgba(PALETTE['blue'], 0.34)}; border-radius: 14px;"
            "   background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 rgba(59,130,246,0.12), stop:1 rgba(59,130,246,0.03)); }}"
        )
        row = QHBoxLayout()
        row.setSpacing(12)
        info = QLabel("🛡")
        info.setStyleSheet(f"font-size: 20px; color: {PALETTE['blue']};")
        row.addWidget(info)
        tbox = QVBoxLayout()
        tbox.setSpacing(2)
        t = QLabel("Verify a defense by replaying the attack")
        t.setStyleSheet(f"font-weight: 800; color: {PALETTE['text']};")
        tbox.addWidget(t)
        tbox.addWidget(muted(
            "Verifying launches the vulnerable server AND its hardened twin to show the same "
            "payload exploited, then blocked. Arming is shared with the Attack Lab.",
            faint=True,
        ))
        row.addLayout(tbox, 1)
        self._arm = QCheckBox("Arm the lab")
        self._arm.setChecked(self._lab.armed)
        self._arm.setStyleSheet(
            f"QCheckBox {{ color: {PALETTE['blue']}; font-weight: 700; }}"
            f"QCheckBox::indicator:checked {{ background: {PALETTE['blue']}; border-color: {PALETTE['blue']}; }}"
        )
        self._arm.toggled.connect(self._lab.set_armed)
        row.addWidget(self._arm, alignment=Qt.AlignVCenter)
        card.body.addLayout(row)
        return card

    def _sync_armed(self, armed: bool) -> None:
        if self._arm.isChecked() != armed:
            self._arm.setChecked(armed)
        if hasattr(self, "_verify_btn") and self._verify_btn is not None:
            self._verify_btn.setEnabled(armed)
            self._verify_btn.setToolTip("" if armed else "Arm the lab above to verify")

    # -- list ------------------------------------------------------------- #
    def _build_list(self) -> QWidget:
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.addWidget(title_label("Defenses"))
        lay.addWidget(search_box("Filter defenses…", lambda t: filter_grouped_list(self._list, t)))
        self._list = QListWidget()
        self._list.setStyleSheet(_LIST_QSS)
        self._list.itemSelectionChanged.connect(self._on_select)
        for family, items in grouped():
            header = QListWidgetItem(family.upper())
            header.setFlags(Qt.NoItemFlags)
            header.setForeground(QColor(PALETTE["text_faint"]))
            self._list.addItem(header)
            for meta in items:
                item = QListWidgetItem(self._list)
                item.setData(Qt.UserRole, meta)
                roww = _defense_row(meta)
                item.setSizeHint(roww.sizeHint())
                self._list.addItem(item)
                self._list.setItemWidget(item, roww)
        lay.addWidget(self._list)
        return wrap

    def _select_first(self) -> None:
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.UserRole) is not None:
                self._list.setCurrentRow(i)
                return

    # -- detail ----------------------------------------------------------- #
    def _build_detail_host(self) -> QWidget:
        self._detail_host = QWidget()
        self._detail = QVBoxLayout(self._detail_host)
        self._detail.setContentsMargins(0, 0, 0, 0)
        self._detail.setSpacing(14)
        self._detail.addWidget(muted("Select a defense to read the guardrail and prove it."))
        self._detail.addStretch(1)
        return self._detail_host

    def _on_select(self) -> None:
        items = self._list.selectedItems()
        if not items:
            return
        meta = items[0].data(Qt.UserRole)
        if meta is None:
            return
        self._meta = meta
        self._verify_btn = None
        self._build_detail(meta)

    def _build_detail(self, meta: AttackMeta) -> None:
        clear_layout(self._detail)
        case = CASES_BY_ID.get(meta.arena_case_id) if meta.arena_case_id else None

        head = QHBoxLayout()
        head.addWidget(Badge(f"#{meta.num}", PALETTE["blue"]))
        title = QLabel(meta.title)
        title.setStyleSheet(f"font-size: 19px; font-weight: 800; color: {PALETTE['text']};")
        head.addWidget(title)
        head.addStretch(1)
        self._detail.addLayout(head)

        # mechanism
        mech = Card("How the fix works")
        mech.body.addWidget(muted(case.explain if case else meta.threat))
        if case:
            grow = QHBoxLayout()
            gl = QLabel()
            from ..icons import icon

            gl.setPixmap(icon("lock", PALETTE["blue"], 15).pixmap(15, 15))
            grow.addWidget(gl)
            grow.addWidget(muted(case.guardrail, faint=True), 1)
            mech.body.addLayout(grow)
        self._detail.addWidget(mech)

        # guardrail source
        if meta.guardrail_source and meta.guardrail_source.exists():
            src_card = Card(f"Guardrail · purplemcp/guardrails/{meta.guardrail_source.name}")
            view = QPlainTextEdit()
            view.setReadOnly(True)
            view.setPlainText(meta.guardrail_source.read_text(encoding="utf-8"))
            view.setStyleSheet(
                f"QPlainTextEdit {{ font-family: {MONO}; font-size: 11.5px; color: {PALETTE['text']};"
                f" background: {PALETTE['bg']}; border: 1px solid {PALETTE['border']}; border-radius: 8px; }}"
            )
            view.setMinimumHeight(300)
            self._highlighter = PythonHighlighter(view.document())
            src_card.body.addWidget(view)
            self._detail.addWidget(src_card)

        # verify
        verify_card = Card("Verify")
        if case:
            run_row = QHBoxLayout()
            self._verify_btn = button("Verify defense", "blue", "play", icon_color=PALETTE["blue"])
            self._verify_btn.setEnabled(self._lab.armed)
            if not self._lab.armed:
                self._verify_btn.setToolTip("Arm the lab above to verify")
            self._verify_btn.clicked.connect(self._verify)
            run_row.addWidget(self._verify_btn)
            self._verify_status = muted("", faint=True)
            run_row.addWidget(self._verify_status)
            run_row.addStretch(1)
            verify_card.body.addLayout(run_row)
            self._busy = BusyBar()
            verify_card.body.addWidget(self._busy)

            cols = QHBoxLayout()
            cols.setSpacing(14)
            self._red = _TeamColumn("Vulnerable server", RED_TEAM, "skull")
            self._blue = _TeamColumn("Hardened twin", BLUE_TEAM, "lock")
            cols.addWidget(self._red, 1)
            cols.addWidget(self._blue, 1)
            verify_card.body.addLayout(cols)
        else:
            verify_card.body.addWidget(muted(
                "This one is best seen as a live exploit — open it in the Attack Lab. The guardrail "
                "above is the fix.", faint=True,
            ))
        self._detail.addWidget(verify_card)
        self._detail.addStretch(1)

    # -- verify ----------------------------------------------------------- #
    def _verify(self) -> None:
        if self._meta is None or not self._meta.arena_case_id or not self._lab.armed:
            return
        case = CASES_BY_ID[self._meta.arena_case_id]
        self._verify_btn.setEnabled(False)
        self._busy.start()
        self._red.reset()
        self._blue.reset()
        flash(self._verify_status, "replaying attack on both servers…", PALETTE["text_dim"], ms=60000)
        self._job = run_job(self._loop, arena_run(case), parent=self)
        self._job.succeeded.connect(lambda r, c=case: self._on_verified(c, r))
        self._job.failed.connect(self._on_failed)

    def _on_verified(self, case, result) -> None:
        self._busy.stop()
        self._verify_btn.setEnabled(self._lab.armed)
        v = judge(result.vuln_attack, case, hardened=False)
        h = judge(result.hard_attack, case, hardened=True)
        self._red.fill(result.vuln_benign, result.vuln_attack, v, case)
        self._blue.fill(result.hard_benign, result.hard_attack, h, case)
        if v.kind == "bad" and h.kind == "good":
            flash(self._verify_status, "✓ exploited on the left, blocked on the right", PALETTE["green"])
        else:
            flash(self._verify_status, "done — read the verdicts", PALETTE["text_dim"])

    def _on_failed(self, msg: str) -> None:
        self._busy.stop()
        self._verify_btn.setEnabled(self._lab.armed)
        flash(self._verify_status, msg, PALETTE["red"], ms=6000)


def _defense_row(meta: AttackMeta) -> QWidget:
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(9, 8, 9, 8)
    lay.setSpacing(10)
    num = QLabel(meta.num)
    num.setFixedSize(28, 28)
    num.setAlignment(Qt.AlignCenter)
    num.setStyleSheet(
        f"background: {PALETTE['surface_hi']}; color: {PALETTE['blue']};"
        f" border-radius: 8px; font-weight: 800; font-family: {MONO};"
    )
    lay.addWidget(num)
    tbox = QVBoxLayout()
    tbox.setSpacing(1)
    t = QLabel(meta.title)
    t.setStyleSheet(f"font-weight: 700; color: {PALETTE['text']};")
    tbox.addWidget(t)
    guard = QLabel(meta.guardrail or "—")
    guard.setObjectName("Faint")
    guard.setStyleSheet(f"font-family: {MONO}; color: {PALETTE['text_faint']}; font-size: 11px;")
    tbox.addWidget(guard)
    lay.addLayout(tbox, 1)
    return row
