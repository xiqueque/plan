"""日历跳转对话框：点击日期后快速选择任意一天。"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCalendarWidget,
    QDialog,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)


class CalendarDialog(QDialog):
    def __init__(self, parent=None, current: date | None = None):
        super().__init__(parent)
        self.setWindowTitle("选择日期")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setFirstDayOfWeek(Qt.Monday)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        if current is not None:
            self.calendar.setSelectedDate(QDate(current.year, current.month, current.day))
        self.calendar.activated.connect(self.accept)
        layout.addWidget(self.calendar)

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

    def _go_today(self) -> None:
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.calendar.setCurrentPage(today.year(), today.month())

    def selected_date(self) -> date:
        qd = self.calendar.selectedDate()
        return date(qd.year(), qd.month(), qd.day())
