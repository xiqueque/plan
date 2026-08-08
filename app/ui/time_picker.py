"""时间快速选择：弹出式选择器 + 大号时间按钮。"""
from __future__ import annotations

import time as _time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

DIALOG_QSS = """
QWidget { font-family:"幼圆","Microsoft YaHei"; font-size:14px; color:#1F3A4D; }
QDialog { background:#EAF6FC; }
QLabel#timeDisplay { font-size:28px; font-weight:bold; color:#1F3A4D; }
QListWidget { background:white; border:1px solid #7FB8D4; border-radius:8px; font-size:16px; }
QListWidget::item { padding:4px 2px; }
QListWidget::item:selected { background:#ADD8E6; color:#1F3A4D; }
QListWidget QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 3px;
}
QListWidget QScrollBar::handle:vertical {
    background: #B9DCEC;
    border-radius: 5px;
    min-height: 24px;
}
QListWidget QScrollBar::handle:vertical:hover { background: #7FB8D4; }
QListWidget QScrollBar::add-line:vertical,
QListWidget QScrollBar::sub-line:vertical { height: 0; }
QListWidget QScrollBar::add-page:vertical,
QListWidget QScrollBar::sub-page:vertical { background: transparent; }
QPushButton { background:#ADD8E6; border:1px solid #7FB8D4; border-radius:8px; padding:7px 16px; }
QPushButton:hover { background:#9CCFE0; }
"""

BUTTON_QSS = """
QPushButton {
    background: white;
    border: 1px solid #7FB8D4;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 16px;
    font-weight: 600;
}
QPushButton:hover { border-color: #3B7DBF; background: #F0F9FD; }
QPushButton:disabled { background: #E5EEF4; color: #9AA5AC; }
"""


def parse_hhmm(value: str) -> tuple[int, int]:
    """把 'HH:MM' 解析为 (时, 分)，异常时返回 (8, 0)。"""
    try:
        hh, mm = value.strip().split(":")
        return max(0, min(23, int(hh))), max(0, min(59, int(mm)))
    except Exception:
        return 8, 0


class TimePickerDialog(QDialog):
    """弹出式时间选择：左侧小时列表 + 右侧分钟列表。"""

    def __init__(self, parent=None, initial: str = "08:00"):
        super().__init__(parent)
        self.setWindowTitle("选择时间")
        self.setStyleSheet(DIALOG_QSS)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.display = QLabel(initial)
        self.display.setObjectName("timeDisplay")
        self.display.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.display)

        cols = QHBoxLayout()
        self.hour_list = QListWidget()
        self.minute_list = QListWidget()
        for lst in (self.hour_list, self.minute_list):
            lst.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
            lst.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for h in range(24):
            self.hour_list.addItem(QListWidgetItem(f"{h:02d}"))
        for m in range(60):
            self.minute_list.addItem(QListWidgetItem(f"{m:02d}"))
        self.hour_list.setFixedWidth(110)
        self.minute_list.setFixedWidth(110)
        cols.addWidget(self.hour_list)
        cols.addWidget(self.minute_list)
        layout.addLayout(cols)

        self.hour_list.currentRowChanged.connect(self._refresh)
        self.minute_list.currentRowChanged.connect(self._refresh)
        self.hour_list.itemDoubleClicked.connect(lambda _: self.accept())
        self.minute_list.itemDoubleClicked.connect(lambda _: self.accept())

        hh, mm = parse_hhmm(initial)
        self.hour_list.setCurrentRow(hh)
        self.minute_list.setCurrentRow(mm)
        self.hour_list.scrollToItem(self.hour_list.item(hh))
        self.minute_list.scrollToItem(self.minute_list.item(mm))

        buttons = QHBoxLayout()
        now_btn = QPushButton("现在")
        now_btn.clicked.connect(self._set_now)
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(now_btn)
        buttons.addStretch(1)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _refresh(self) -> None:
        hh = self.hour_list.currentRow()
        mm = self.minute_list.currentRow()
        if hh >= 0 and mm >= 0:
            self.display.setText(f"{hh:02d}:{mm:02d}")

    def _set_now(self) -> None:
        hh, mm = parse_hhmm(_time.strftime("%H:%M"))
        self.hour_list.setCurrentRow(hh)
        self.minute_list.setCurrentRow(mm)

    def selected_time(self) -> str:
        hh = max(0, self.hour_list.currentRow())
        mm = max(0, self.minute_list.currentRow())
        return f"{hh:02d}:{mm:02d}"


class TimeButton(QPushButton):
    """大号时间按钮：点击弹出时间选择器，无需手动打字。"""

    timeChanged = Signal(str)
    timePicked = Signal(str)

    def __init__(self, time_str: str = "08:00", parent=None):
        super().__init__(parent)
        self.setStyleSheet(BUTTON_QSS)
        self.setCursor(Qt.PointingHandCursor)
        self._time = "08:00"
        self.set_time(time_str)
        self.clicked.connect(self._pick)

    def set_time(self, time_str: str) -> None:
        hh, mm = parse_hhmm(time_str)
        new_time = f"{hh:02d}:{mm:02d}"
        if new_time != self._time:
            self._time = new_time
            self.setText(self._time)
            self.timeChanged.emit(self._time)

    def time(self) -> str:
        return self._time

    def _pick(self) -> None:
        dialog = TimePickerDialog(self, self._time)
        if dialog.exec() == TimePickerDialog.Accepted:
            self.set_time(dialog.selected_time())
            self.timePicked.emit(self._time)
