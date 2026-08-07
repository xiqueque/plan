"""日历跳转对话框：选择日期并显示当天的计划。"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCalendarWidget,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..core import storage

CALENDAR_QSS = """
QDialog {
    background: #EAF6FC;
    font-family: "幼圆", "Microsoft YaHei";
    font-size: 14px;
    color: #1F3A4D;
}
QPushButton {
    background: #ADD8E6;
    border: 1px solid #7FB8D4;
    border-radius: 6px;
    padding: 5px 12px;
}
QPushButton:hover { background: #9CCFE0; }
QLabel#dayTitle { font-size: 16px; font-weight: bold; color: #3B7DBF; }
QLabel#emptyLabel { color: #6B8CA3; padding: 12px; }
"""


class CalendarDialog(QDialog):
    def __init__(self, parent=None, current: date | None = None, data: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("选择日期")
        self.setMinimumWidth(430)
        self.setStyleSheet(CALENDAR_QSS)
        self.data = data or {}

        layout = QVBoxLayout(self)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setFirstDayOfWeek(Qt.Monday)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        if current is not None:
            self.calendar.setSelectedDate(QDate(current.year, current.month, current.day))
        self.calendar.activated.connect(self.accept)
        layout.addWidget(self.calendar)

        self.day_title = QLabel()
        self.day_title.setObjectName("dayTitle")
        layout.addWidget(self.day_title)

        self.tasks_scroll = QScrollArea()
        self.tasks_scroll.setWidgetResizable(True)
        self.tasks_scroll.setFixedHeight(190)
        self.tasks_container = QWidget()
        self.tasks_vbox = QVBoxLayout(self.tasks_container)
        self.tasks_vbox.setContentsMargins(4, 2, 4, 2)
        self.tasks_vbox.setSpacing(4)
        self.tasks_scroll.setWidget(self.tasks_container)
        layout.addWidget(self.tasks_scroll, 1)

        bottom = QHBoxLayout()
        today_btn = QPushButton("今天")
        today_btn.clicked.connect(self._go_today)
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        bottom.addWidget(today_btn)
        bottom.addStretch(1)
        bottom.addWidget(ok_btn)
        bottom.addWidget(cancel_btn)
        layout.addLayout(bottom)

        self.calendar.selectionChanged.connect(self._update_day_tasks)
        self._update_day_tasks()

    def _go_today(self) -> None:
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.calendar.setCurrentPage(today.year(), today.month())

    def selected_date(self) -> date:
        qd = self.calendar.selectedDate()
        return date(qd.year(), qd.month(), qd.day())

    def _selected_iso(self) -> str:
        qd = self.calendar.selectedDate()
        return f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"

    def _update_day_tasks(self) -> None:
        while self.tasks_vbox.count():
            item = self.tasks_vbox.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()

        qd = self.calendar.selectedDate()
        date_str = self._selected_iso()
        self.day_title.setText(f"{qd.month()}月{qd.day()}日 计划")
        tasks = storage.tasks_for_date(self.data, date_str)
        if not tasks:
            empty = QLabel("这一天没有计划")
            empty.setObjectName("emptyLabel")
            empty.setAlignment(Qt.AlignCenter)
            self.tasks_vbox.addWidget(empty)
            return
        for task in tasks:
            done = storage.is_done(self.data, task["id"], date_str)
            color = "#9AA5AC" if done else (task.get("color") or "#1F3A4D")
            deco = " text-decoration: line-through;" if done else ""
            text = task.get("text", "")
            extra = ""
            if task.get("time_start"):
                extra = task["time_start"]
                if task.get("time_end"):
                    extra += f" – {task['time_end']}"
            if extra:
                text += f"（{extra}）"
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet(f"font-size:14px; color:{color};{deco}")
            self.tasks_vbox.addWidget(label)
        self.tasks_vbox.addStretch(1)
