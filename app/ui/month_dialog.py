"""月度计划查看：按月分组显示计划，可前后翻月。"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..core import storage

MONTH_QSS = """
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
QLabel#monthTitle { font-size: 20px; font-weight: bold; }
QLabel#dayHeader { font-size: 15px; font-weight: bold; color: #3B7DBF; padding-top: 8px; }
QLabel#emptyLabel { color: #6B8CA3; font-size: 15px; padding: 30px; }
"""

WEEKDAY_NAMES = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


class MonthPlanDialog(QDialog):
    def __init__(self, parent=None, data: dict | None = None, current: date | None = None):
        super().__init__(parent)
        self.setWindowTitle("月度计划")
        self.resize(660, 560)
        self.setStyleSheet(MONTH_QSS)
        self.data = data or {}
        today = current or date.today()
        self.month = today.replace(day=1)

        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        self.prev_btn = QPushButton("◀ 上一月")
        self.title_label = QLabel()
        self.title_label.setObjectName("monthTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.next_btn = QPushButton("下一月 ▶")
        self.today_btn = QPushButton("本月")
        self.prev_btn.clicked.connect(lambda: self._change(-1))
        self.next_btn.clicked.connect(lambda: self._change(1))
        self.today_btn.clicked.connect(self._go_today)
        header.addWidget(self.prev_btn)
        header.addWidget(self.title_label, 1)
        header.addWidget(self.next_btn)
        header.addWidget(self.today_btn)
        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setContentsMargins(8, 8, 8, 8)
        self.vbox.setSpacing(4)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)
        self._rebuild()

    def _change(self, delta: int) -> None:
        index = self.month.year * 12 + (self.month.month - 1) + delta
        self.month = date(index // 12, index % 12 + 1, 1)
        self._rebuild()

    def _go_today(self) -> None:
        self.month = date.today().replace(day=1)
        self._rebuild()

    def _rebuild(self) -> None:
        self.title_label.setText(f"{self.month.year}年{self.month.month}月")
        while self.vbox.count():
            item = self.vbox.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()

        daily = [t for t in self.data.get("tasks", []) if t.get("is_daily")]
        daily.sort(key=storage.task_sort_key)
        prefix = self.month.strftime("%Y-%m")
        per_day = {}
        for task in self.data.get("tasks", []):
            if not task.get("is_daily") and task.get("date", "").startswith(prefix):
                per_day.setdefault(task["date"], []).append(task)
        for day_list in per_day.values():
            day_list.sort(key=storage.task_sort_key)

        any_task = False
        if daily:
            any_task = True
            head = QLabel("每天任务")
            head.setObjectName("dayHeader")
            self.vbox.addWidget(head)
            for task in daily:
                self.vbox.addWidget(self._task_label(task))

        for day_str in sorted(per_day):
            day = date.fromisoformat(day_str)
            head = QLabel(f"{day.month}月{day.day}日 {WEEKDAY_NAMES[day.weekday()]}")
            head.setObjectName("dayHeader")
            self.vbox.addWidget(head)
            any_task = True
            for task in per_day[day_str]:
                self.vbox.addWidget(self._task_label(task))

        if not any_task:
            empty = QLabel("本月暂无计划")
            empty.setObjectName("emptyLabel")
            empty.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(empty)
        self.vbox.addStretch(1)

    def _task_label(self, task: dict) -> QLabel:
        color = task.get("color") or "#1F3A4D"
        extra = ""
        extra = storage.format_time_period(
            task.get("time_start"), task.get("time_end")
        )
        if task.get("reminder_time"):
            extra += (" · " if extra else "") + "提醒 " + task["reminder_time"]
        text = task.get("text", "")
        if extra:
            text += f"（{extra}）"
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"font-size:15px; color:{color};")
        return label
