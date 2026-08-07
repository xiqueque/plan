"""月度计划查看测试。"""
from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel

from app.core import storage
from app.ui.month_dialog import MonthPlanDialog


class MonthDialogTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._old_dir = storage.DATA_DIR
        self._old_file = storage.DATA_FILE
        storage.DATA_DIR = Path(self.tmp.name)
        storage.DATA_FILE = Path(self.tmp.name) / "plan.json"
        self.app = QApplication.instance() or QApplication([])

    def tearDown(self):
        storage.DATA_DIR = self._old_dir
        storage.DATA_FILE = self._old_file
        self.tmp.cleanup()

    def test_month_with_tasks(self):
        today = date.today()
        data = storage.empty_data()
        data["tasks"].append(
            storage.new_task("每天喝水", today.isoformat(), is_daily=True)
        )
        data["tasks"].append(
            storage.new_task(
                "月度会议",
                today.isoformat(),
                "10:00",
                "11:00",
                color="#E05252",
            )
        )
        dialog = MonthPlanDialog(None, data, today)
        labels = [lbl.text() for lbl in dialog.findChildren(QLabel)]
        self.assertTrue(any("每天任务" in t for t in labels))
        self.assertTrue(any("月度会议" in t for t in labels))
        self.assertFalse(any("本月暂无计划" in t for t in labels))

    def test_month_empty(self):
        data = storage.empty_data()
        dialog = MonthPlanDialog(None, data, date.today())
        labels = [lbl.text() for lbl in dialog.findChildren(QLabel)]
        self.assertTrue(any("本月暂无计划" in t for t in labels))

    def test_month_navigation(self):
        data = storage.empty_data()
        dialog = MonthPlanDialog(None, data, date.today())
        dialog._change(1)
        self.assertIn("月", dialog.title_label.text())


if __name__ == "__main__":
    unittest.main()
