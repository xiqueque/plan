"""自绘日历控件：大号圆角日期方块，方块内直接显示当天任务名。"""
from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..core import storage

WEEKDAY_HEADERS = ["一", "二", "三", "四", "五", "六", "日"]
WEEKDAY_FULL = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
MAX_TASKS_IN_CELL = 2


class DayCell(QFrame):
    """单个日期方块：大号数字 + 当天任务名（最多两条）。"""

    clicked_day = Signal(object)
    double_clicked_day = Signal(object)

    def __init__(
        self,
        day: date,
        tasks: list,
        today: bool = False,
        selected: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.day = day
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(86)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(8, 5, 8, 5)
        vbox.setSpacing(1)

        num = QLabel(str(day.day))
        num.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        num.setStyleSheet(
            "font-size:18px; font-weight:bold; color:#3B7DBF;"
            if today
            else "font-size:18px; font-weight:bold; color:#1F3A4D;"
        )
        vbox.addWidget(num)

        names = [t.get("text", "") for t in tasks][:MAX_TASKS_IN_CELL]
        for name in names:
            label = QLabel(self._elide(name))
            label.setStyleSheet("font-size:12px; font-weight:600; color:#4A6B82;")
            vbox.addWidget(label)
        if len(tasks) > MAX_TASKS_IN_CELL:
            more = QLabel(f"… 还有 {len(tasks) - MAX_TASKS_IN_CELL} 条")
            more.setStyleSheet("font-size:11px; color:#9AA5AC;")
            vbox.addWidget(more)
        vbox.addStretch(1)

        if selected:
            bg, border = "#E4F3FB", "#3B7DBF"
        else:
            bg = "#FFF7EF" if day.weekday() >= 5 else "#FFFFFF"
            border = "#5FA8CC" if today else "#DDEBF3"
        self.setStyleSheet(
            f"QFrame {{ background:{bg}; border:2px solid {border}; border-radius:12px; }}"
            "QFrame:hover { border-color:#7FB8D4; }"
        )

    @staticmethod
    def _elide(text: str) -> str:
        metrics = QFontMetrics(QLabel().font())
        return metrics.elidedText(text, Qt.ElideRight, 64)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked_day.emit(self.day)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked_day.emit(self.day)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class CalendarGrid(QWidget):
    """月份日历网格：7 列日期方块，可翻月。"""

    dateClicked = Signal(object)
    dateDoubleClicked = Signal(object)

    def __init__(self, data: dict | None = None, parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.today = date.today()
        self.month = self.today.replace(day=1)
        self.selected = self.today

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        nav = QHBoxLayout()
        self.prev_btn = QPushButton("◀")
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size:18px; font-weight:bold;")
        self.next_btn = QPushButton("▶")
        self.today_btn = QPushButton("今天")
        self.prev_btn.clicked.connect(self._prev)
        self.next_btn.clicked.connect(self._next)
        self.today_btn.clicked.connect(self._go_today)
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.title_label, 1)
        nav.addWidget(self.next_btn)
        nav.addWidget(self.today_btn)
        root.addLayout(nav)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(8)
        self.grid.setVerticalSpacing(8)
        for col, name in enumerate(WEEKDAY_HEADERS):
            head = QLabel(name)
            head.setAlignment(Qt.AlignCenter)
            head.setStyleSheet("font-size:14px; font-weight:bold; color:#6B8CA3;")
            self.grid.addWidget(head, 0, col)
        root.addLayout(self.grid, 1)
        self._rebuild()

    def _prev(self) -> None:
        self._change(-1)

    def _next(self) -> None:
        self._change(1)

    def _change(self, delta: int) -> None:
        index = self.month.year * 12 + (self.month.month - 1) + delta
        self.month = date(index // 12, index % 12 + 1, 1)
        self._rebuild()

    def _go_today(self) -> None:
        self.month = self.today.replace(day=1)
        self.selected = self.today
        self._rebuild()

    def selected_date(self) -> date:
        return self.selected

    def _rebuild(self) -> None:
        while self.grid.count() > 7:
            item = self.grid.takeAt(7)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()

        self.title_label.setText(f"{self.month.year}年{self.month.month}月")
        first = self.month
        start = first - timedelta(days=first.weekday())
        for i in range(42):
            day = start + timedelta(days=i)
            row, col = i // 7 + 1, i % 7
            if day.month != self.month.month or day.year != self.month.year:
                blank = QFrame()
                blank.setStyleSheet("QFrame { background:transparent; border:none; }")
                self.grid.addWidget(blank, row, col)
                continue
            tasks = storage.tasks_for_date(self.data, day.isoformat())
            cell = DayCell(
                day,
                tasks,
                today=(day == self.today),
                selected=(day == self.selected),
            )
            cell.clicked_day.connect(self._on_clicked)
            cell.double_clicked_day.connect(self._on_double)
            self.grid.addWidget(cell, row, col)
        for col in range(7):
            self.grid.setColumnStretch(col, 1)
        for row in range(1, 7):
            self.grid.setRowStretch(row, 1)

    def _on_clicked(self, day: date) -> None:
        self.selected = day
        self._rebuild()
        self.dateClicked.emit(day)

    def _on_double(self, day: date) -> None:
        self.selected = day
        self.dateDoubleClicked.emit(day)


class DayDetailDialog(QDialog):
    """某一天的详细计划查看。"""

    def __init__(self, parent=None, data: dict | None = None, day: date | None = None):
        super().__init__(parent)
        self.setWindowTitle("计划详情")
        self.resize(460, 520)
        self.setStyleSheet(
            "QDialog { background:#EAF6FC; font-family:'幼圆','Microsoft YaHei'; "
            "font-size:14px; color:#1F3A4D; }"
            "QPushButton { background:#ADD8E6; border:1px solid #7FB8D4; "
            "border-radius:8px; padding:7px 18px; }"
            "QPushButton:hover { background:#9CCFE0; }"
        )
        self.data = data or {}
        self.day = day or date.today()

        layout = QVBoxLayout(self)
        title = QLabel(
            f"{self.day.month}月{self.day.day}日 {WEEKDAY_FULL[self.day.weekday()]} 计划详情"
        )
        title.setStyleSheet("font-size:18px; font-weight:bold; color:#1F3A4D;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(4, 4, 4, 4)
        vbox.setSpacing(8)
        date_str = self.day.isoformat()
        tasks = storage.tasks_for_date(self.data, date_str)
        if not tasks:
            empty = QLabel("这一天没有计划")
            empty.setStyleSheet("color:#6B8CA3; padding:20px;")
            empty.setAlignment(Qt.AlignCenter)
            vbox.addWidget(empty)
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
            if task.get("reminder_time"):
                extra += (
                    (" · " if extra else "")
                    + "提醒 "
                    + task["reminder_time"]
                    + storage.format_weekdays(task.get("reminder_weekdays"))
                )
            if extra:
                text += f"（{extra}）"
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet(f"font-size:15px; font-weight:600; color:{color};{deco}")
            vbox.addWidget(label)
        vbox.addStretch(1)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)
