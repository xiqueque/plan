"""提醒调度：周期检查任务提醒时间，到点触发。"""
from __future__ import annotations

import time
from datetime import date

from PySide6.QtCore import QObject, QTimer, Signal

from .storage import is_reminded, mark_reminded

CHECK_INTERVAL_MS = 20000


class ReminderScheduler(QObject):
    """到点提醒调度器。"""

    reminderReady = Signal(dict)  # 需要提醒的任务

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}
        self._timer = QTimer(self)
        self._timer.setInterval(CHECK_INTERVAL_MS)
        self._timer.timeout.connect(self.check)
        self._timer.start()

    def set_data(self, data: dict) -> None:
        self.data = data

    def check(self, now_hhmm: str | None = None, today: str | None = None) -> None:
        """检查当前是否有任务到点；可注入时间便于测试。"""
        if now_hhmm is None:
            now_hhmm = time.strftime("%H:%M")
        if today is None:
            today = date.today().isoformat()

        for task in self.data.get("tasks", []):
            mode = task.get("reminder_mode", "none")
            rt = task.get("reminder_time")
            if mode == "none" or not rt:
                continue
            if mode == "once" and task.get("date") != today:
                continue
            if rt != now_hhmm:
                continue
            if is_reminded(self.data, task["id"], today):
                continue
            mark_reminded(self.data, task["id"], today, rt)
            self.reminderReady.emit(task)
