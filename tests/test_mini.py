"""迷你窗口模式与设置项测试。"""
from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.core import storage
from app.ui.main_window import MainWindow
from app.ui.settings_dialog import SettingsDialog


class MiniModeTestCase(unittest.TestCase):
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

    def test_mini_mode_roundtrip(self):
        data = storage.empty_data()
        data["tasks"].append(storage.new_task("迷你测试", date.today().isoformat()))
        storage.save_data(data)

        window = MainWindow()
        window.show()
        self.app.processEvents()
        full_central = window.centralWidget()
        self.assertIsNotNone(full_central)

        window._enter_mini_mode()
        self.assertTrue(window._mini_mode)
        self.assertIsNot(window.centralWidget(), full_central)

        window._exit_mini_mode()
        self.assertFalse(window._mini_mode)
        self.assertIs(window.centralWidget(), full_central)
        self.assertEqual(window.windowOpacity(), 1.0)

    def test_settings_values_tuple(self):
        dialog = SettingsDialog(None)
        values = dialog.values()
        self.assertEqual(len(values), 10)
        self.assertFalse(values[6])  # 总在最前默认关闭
        self.assertEqual(values[7], "mini")  # 最小化默认迷你模式
        self.assertEqual(values[8], "tray")  # 关闭默认托盘
        self.assertEqual(values[9], 80)  # 迷你不透明度默认 80%


if __name__ == "__main__":
    unittest.main()
