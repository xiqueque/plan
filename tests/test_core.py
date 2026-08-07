"""数据层单元测试。"""
from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from app.core import storage


class StorageTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._old_dir = storage.DATA_DIR
        self._old_file = storage.DATA_FILE
        storage.DATA_DIR = Path(self.tmp.name)
        storage.DATA_FILE = storage.DATA_DIR / "plan.json"

    def tearDown(self):
        storage.DATA_DIR = self._old_dir
        storage.DATA_FILE = self._old_file
        self.tmp.cleanup()

    def test_save_and_load_roundtrip(self):
        data = storage.empty_data()
        task = storage.new_task("写作业", storage.today_str(), "09:00", "10:00")
        data["tasks"].append(task)
        storage.save_data(data)
        loaded = storage.load_data()
        self.assertEqual(loaded["tasks"][0]["text"], "写作业")
        self.assertEqual(loaded["tasks"][0]["time_start"], "09:00")

    def test_settings_roundtrip_sound(self):
        data = storage.empty_data()
        data["settings"]["sound_file"] = r"C:\audio\ding.mp3"
        data["settings"]["sound_volume"] = 65
        storage.save_data(data)
        loaded = storage.load_data()
        self.assertEqual(loaded["settings"]["sound_file"], r"C:\audio\ding.mp3")
        self.assertEqual(loaded["settings"]["sound_volume"], 65)

    def test_migrate_check_sound_to_sound_file(self):
        data = storage.empty_data()
        data["settings"]["check_sound"] = r"C:\audio\old.mp3"
        storage.save_data(data)
        loaded = storage.load_data()
        self.assertNotIn("check_sound", loaded["settings"])
        self.assertEqual(loaded["settings"]["sound_file"], r"C:\audio\old.mp3")

    def test_daily_task_appears_every_day(self):
        data = storage.empty_data()
        daily = storage.new_task("喝水", storage.today_str(), is_daily=True)
        once = storage.new_task("开会", storage.today_str())
        data["tasks"].extend([daily, once])
        today = storage.today_str()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        self.assertEqual(
            {t["text"] for t in storage.tasks_for_date(data, today)}, {"喝水", "开会"}
        )
        self.assertEqual(
            {t["text"] for t in storage.tasks_for_date(data, tomorrow)}, {"喝水"}
        )

    def test_done_status_per_day(self):
        data = storage.empty_data()
        task = storage.new_task("背单词", storage.today_str())
        data["tasks"].append(task)
        today = storage.today_str()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        storage.set_done(data, task["id"], today, True)
        self.assertTrue(storage.is_done(data, task["id"], today))
        self.assertFalse(storage.is_done(data, task["id"], tomorrow))

    def test_cleanup_removes_old_tasks_keeps_daily(self):
        data = storage.empty_data()
        data["settings"]["cleanup_days"] = 15
        old = storage.new_task("旧计划", (date.today() - timedelta(days=20)).isoformat())
        recent = storage.new_task("新计划", storage.today_str())
        daily = storage.new_task("每天任务", storage.today_str(), is_daily=True)
        data["tasks"].extend([old, recent, daily])
        old_date = old["date"]
        storage.set_done(data, old["id"], old_date, True)
        removed = storage.run_cleanup(data)
        self.assertEqual(removed, 1)
        texts = {t["text"] for t in data["tasks"]}
        self.assertNotIn("旧计划", texts)
        self.assertIn("新计划", texts)
        self.assertIn("每天任务", texts)
        self.assertNotIn(old_date, data["done"])

    def test_pinned_tasks_sort_first(self):
        data = storage.empty_data()
        normal_early = storage.new_task("早间", storage.today_str(), "08:00")
        pinned = storage.new_task("置顶任务", storage.today_str(), "10:00")
        pinned["pinned"] = True
        pinned["pinned_at"] = 100.0
        data["tasks"].extend([normal_early, pinned])
        tasks = storage.tasks_for_date(data, storage.today_str())
        self.assertEqual(tasks[0]["text"], "置顶任务")
        self.assertEqual(tasks[1]["text"], "早间")

    def test_broken_file_recovers(self):
        storage.DATA_DIR.mkdir(parents=True, exist_ok=True)
        storage.DATA_FILE.write_text("{不是合法json", encoding="utf-8")
        data = storage.load_data()
        self.assertEqual(data["tasks"], [])
        self.assertTrue(storage.DATA_FILE.with_suffix(".broken.json").exists())


if __name__ == "__main__":
    unittest.main()
