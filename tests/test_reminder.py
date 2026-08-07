"""提醒功能测试：字段、迁移、调度、弹窗。"""
from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.core import storage
from app.core.reminder import ReminderScheduler
from app.ui.reminder_popup import ReminderPopup
from app.ui.task_dialog import TaskDialog
from app.ui.time_picker import TimeButton, TimePickerDialog


class ReminderTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._old_dir = storage.DATA_DIR
        self._old_file = storage.DATA_FILE
        storage.DATA_DIR = Path(self.tmp.name)
        storage.DATA_FILE = storage.DATA_DIR / "plan.json"
        self.app = QApplication.instance() or QApplication([])

    def tearDown(self):
        storage.DATA_DIR = self._old_dir
        storage.DATA_FILE = self._old_file
        self.tmp.cleanup()

    def test_new_task_reminder_fields(self):
        task = storage.new_task(
            "喝水", "2026-08-07", reminder_mode="daily", reminder_time="08:00"
        )
        self.assertEqual(task["reminder_mode"], "daily")
        self.assertTrue(task["is_daily"])
        self.assertEqual(task["reminder_time"], "08:00")
        plain = storage.new_task("开会", "2026-08-07")
        self.assertEqual(plain["reminder_mode"], "none")
        self.assertFalse(plain["is_daily"])
        self.assertIsNone(plain["reminder_time"])

    def test_migration_is_daily_to_reminder_mode(self):
        data = storage.empty_data()
        data["tasks"].append(
            {"id": "x", "text": "旧任务", "date": "2026-08-07", "is_daily": True}
        )
        storage.save_data(data)
        loaded = storage.load_data()
        self.assertEqual(loaded["tasks"][0]["reminder_mode"], "daily")
        self.assertIsNone(loaded["tasks"][0]["reminder_time"])
        self.assertTrue(loaded["tasks"][0]["is_daily"])
        self.assertEqual(loaded["tasks"][0]["reminder_weekdays"], list(range(7)))

    def test_scheduler_daily_once_and_dedupe(self):
        data = storage.empty_data()
        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        daily = storage.new_task(
            "每天喝水", today, reminder_mode="daily", reminder_time="09:00"
        )
        once = storage.new_task(
            "今天开会", today, reminder_mode="once", reminder_time="09:00"
        )
        other_day = storage.new_task(
            "明天开会", tomorrow, reminder_mode="once", reminder_time="09:00"
        )
        data["tasks"].extend([daily, once, other_day])
        storage.save_data(data)

        sched = ReminderScheduler()
        sched.set_data(data)
        fired = []
        sched.reminderReady.connect(fired.append)

        sched.check(now_hhmm="09:00", today=today)
        self.assertEqual(len(fired), 2)  # 每天任务 + 今天的一次性任务
        fired.clear()
        sched.check(now_hhmm="09:00", today=today)
        self.assertEqual(fired, [])  # 已提醒过，不重复

        sched.check(now_hhmm="09:00", today=tomorrow)
        self.assertEqual(len(fired), 2)  # 每天任务 + 明天的一次性任务
        ids = {t["id"] for t in fired}
        self.assertIn(daily["id"], ids)
        self.assertIn(other_day["id"], ids)

    def test_cleanup_prunes_reminded(self):
        data = storage.empty_data()
        old_date = (date.today() - timedelta(days=20)).isoformat()
        data["reminded"] = {old_date: {"t1": "09:00"}}
        storage.save_data(data)
        loaded = storage.load_data()
        storage.run_cleanup(loaded)
        self.assertNotIn(old_date, loaded["reminded"])

    def test_scheduler_weekday_restriction(self):
        data = storage.empty_data()
        saturday = "2026-08-08"
        monday = "2026-08-10"
        daily = storage.new_task(
            "工作日喝水",
            "2026-08-01",
            reminder_mode="daily",
            reminder_time="09:00",
            reminder_weekdays=[0, 1, 2, 3, 4],
        )
        sat_once = storage.new_task(
            "周六开会",
            saturday,
            reminder_mode="once",
            reminder_time="09:00",
            reminder_weekdays=[0, 1, 2, 3, 4],
        )
        data["tasks"].extend([daily, sat_once])
        sched = ReminderScheduler()
        sched.set_data(data)
        fired = []
        sched.reminderReady.connect(fired.append)

        sched.check(now_hhmm="09:00", today=saturday)
        self.assertEqual(fired, [])  # 周六：工作日提醒与周六的一次性任务都不触发
        fired.clear()
        sched.check(now_hhmm="09:00", today=monday)
        self.assertEqual(len(fired), 1)
        self.assertEqual(fired[0]["id"], daily["id"])

    def test_task_dialog_reminder_values(self):
        dialog = TaskDialog(
            None,
            {
                "text": "x",
                "color": "#E05252",
                "reminder_mode": "once",
                "reminder_time": "07:30",
                "is_daily": False,
            },
        )
        text, start, end, is_daily, mode, remind_time, weekdays = dialog.values()
        self.assertEqual(mode, "once")
        self.assertEqual(remind_time, "07:30")
        self.assertFalse(is_daily)
        self.assertEqual(text, "x")
        self.assertEqual(weekdays, list(range(7)))

    def test_time_picker(self):
        btn = TimeButton("09:30")
        self.assertEqual(btn.time(), "09:30")
        btn.set_time("23:59")
        self.assertEqual(btn.time(), "23:59")

        dialog = TimePickerDialog(None, "07:05")
        dialog.hour_list.setCurrentRow(12)
        dialog.minute_list.setCurrentRow(45)
        self.assertEqual(dialog.selected_time(), "12:45")
        dialog.close()

    def test_popup_constructs_and_closes(self):
        task = storage.new_task(
            "测试提醒",
            date.today().isoformat(),
            reminder_mode="daily",
            reminder_time="09:00",
            color="#E05252",
        )
        popup = ReminderPopup(task)
        closed = []
        popup.closed.connect(lambda: closed.append(True))
        popup.show()
        popup.slide_in()
        popup.close()
        self.assertEqual(closed, [True])


if __name__ == "__main__":
    unittest.main()
