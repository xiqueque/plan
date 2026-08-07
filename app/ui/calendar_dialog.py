"""日历跳转对话框：圆角大气卡片样式，选择日期并显示当天计划。"""
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
QDialog { background: transparent; }
QWidget#card {
    background: #F2FAFF;
    border: 2px solid #7FB8D4;
    border-radius: 18px;
}
QWidget {
    font-family: "幼圆", "Microsoft YaHei";
    font-size: 14px;
    color: #1F3A4D;
}
QLabel#dialogTitle { font-size: 20px; font-weight: bold; color: #1F3A4D; }
QLabel#dayTitle { font-size: 17px; font-weight: bold; color: #3B7DBF; }
QLabel#emptyLabel { color: #6B8CA3; padding: 16px; }
QCalendarWidget {
    background: white;
    border: 1px solid #D5E8F2;
    border-radius: 14px;
}
QCalendarWidget QToolButton {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 15px;
    font-weight: bold;
    color: #1F3A4D;
}
QCalendarWidget QToolButton:hover { background: #E4F3FB; }
QCalendarWidget QAbstractItemView {
    selection-background-color: #ADD8E6;
    selection-color: #1F3A4D;
    border: none;
}
QWidget#tasksCard {
    background: white;
    border: 1px solid #D5E8F2;
    border-radius: 14px;
}
QScrollArea { border: none; background: transparent; }
QPushButton {
    background: #ADD8E6;
    border: 1px solid #7FB8D4;
    border-radius: 10px;
    padding: 8px 20px;
    font-size: 14px;
}
QPushButton:hover { background: #9CCFE0; }
QPushButton#closeBtn {
    background: transparent;
    border: none;
    font-size: 16px;
    color: #6B8CA3;
}
QPushButton#closeBtn:hover { color: #1F3A4D; }
"""


class CalendarDialog(QDialog):
    def __init__(self, parent=None, current: date | None = None, data: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("选择日期")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(560, 640)
        self.setMinimumSize(500, 580)
        self.setStyleSheet(CALENDAR_QSS)
        self.data = data or {}
        self._drag_offset = None

        card = QWidget()
        card.setObjectName("card")
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 16, 22, 18)
        layout.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel("选择日期")
        title.setObjectName("dialogTitle")
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setToolTip("关闭")
        close_btn.clicked.connect(self.reject)
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(close_btn)
        layout.addLayout(top)

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

        tasks_card = QWidget()
        tasks_card.setObjectName("tasksCard")
        tasks_layout = QVBoxLayout(tasks_card)
        tasks_layout.setContentsMargins(10, 8, 10, 8)
        self.tasks_scroll = QScrollArea()
        self.tasks_scroll.setWidgetResizable(True)
        self.tasks_container = QWidget()
        self.tasks_vbox = QVBoxLayout(self.tasks_container)
        self.tasks_vbox.setContentsMargins(4, 2, 4, 2)
        self.tasks_vbox.setSpacing(6)
        self.tasks_scroll.setWidget(self.tasks_container)
        tasks_layout.addWidget(self.tasks_scroll)
        layout.addWidget(tasks_card, 1)

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
            label.setStyleSheet(f"font-size:15px; color:{color};{deco}")
            self.tasks_vbox.addWidget(label)
        self.tasks_vbox.addStretch(1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)
