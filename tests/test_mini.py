"""迷你窗口模式与设置项测试。"""
from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QLabel

from app.core import storage
from app.ui.main_window import AnimatedTextLabel, BigCheckBox, MainWindow
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
        self.assertEqual(len(values), 11)
        self.assertFalse(values[6])  # 总在最前默认关闭
        self.assertEqual(values[7], "mini")  # 最小化默认迷你模式
        self.assertEqual(values[8], "tray")  # 关闭默认托盘
        self.assertEqual(values[9], 80)  # 迷你不透明度默认 80%
        self.assertIn("终于完成任务了耶", values[10])

    def test_mini_two_columns_and_readonly(self):
        data = storage.empty_data()
        today = date.today().isoformat()
        for i in range(4):
            data["tasks"].append(
                storage.new_task(f"任务{i}", today, "09:00", "10:00")
            )
        storage.save_data(data)

        window = MainWindow()
        window._play_check_sound = lambda: None
        window._enter_mini_mode()

        self.assertEqual(window._mini_tasks_grid.columnCount(), 2)
        self.assertIn("rgba(", window.centralWidget().styleSheet())
        # 迷你窗口只读，不提供勾选框
        self.assertEqual(window.findChildren(BigCheckBox), [])
        # 迷你窗口不显示在任务栏（Qt.Tool），退出后恢复
        self.assertTrue((window.windowFlags() & Qt.Tool) == Qt.Tool)
        # 迷你窗口不置顶（降低存在感）
        self.assertFalse(window.windowFlags() & Qt.WindowStaysOnTopHint)
        # 点击不激活、不跳到最前
        self.assertTrue(window.windowFlags() & Qt.WindowDoesNotAcceptFocus)

        window._exit_mini_mode()
        self.assertFalse((window.windowFlags() & Qt.Tool) == Qt.Tool)
        self.assertFalse(window.windowFlags() & Qt.WindowStaysOnTopHint)
        self.assertFalse(window.windowFlags() & Qt.WindowDoesNotAcceptFocus)

    def test_mini_pin_toggle(self):
        window = MainWindow()
        window._enter_mini_mode()
        self.assertFalse(window.data["settings"].get("mini_pinned", False))
        # 迷你窗口不置顶（降低存在感）
        self.assertFalse(window.windowFlags() & Qt.WindowStaysOnTopHint)
        self.assertTrue(window.windowFlags() & Qt.WindowDoesNotAcceptFocus)
        self.assertTrue((window.windowFlags() & Qt.Tool) == Qt.Tool)

        window._toggle_mini_pin()
        self.assertTrue(window.data["settings"]["mini_pinned"])
        self.assertIn("QPushButton", window.mini_pin_btn.styleSheet())
        # 固定只锁定拖动，与置顶无关
        self.assertFalse(window.windowFlags() & Qt.WindowStaysOnTopHint)
        # 固定后按下鼠标不应开始拖动
        event = QMouseEvent(
            QEvent.MouseButtonPress,
            QPointF(20, 20),
            QPointF(120, 120),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier,
        )
        window.mousePressEvent(event)
        self.assertIsNone(window._drag_offset)

        window._toggle_mini_pin()
        self.assertFalse(window.data["settings"]["mini_pinned"])
        window._exit_mini_mode()

    def test_confirm_complete_flow(self):
        data = storage.empty_data()
        today = date.today().isoformat()
        task = storage.new_task("确认测试", today)
        data["tasks"].append(task)
        storage.save_data(data)

        window = MainWindow()
        window._play_check_sound = lambda: None
        window._show_completion_message = lambda: None
        label = AnimatedTextLabel("确认测试", "#1F3A4D")
        check = BigCheckBox()

        # 用户选择“我再想想”：不标记完成
        window._confirm_complete = lambda: False
        window._on_toggle_done(task, today, True, label, check)
        self.assertFalse(storage.is_done(window.data, task["id"], today))
        self.assertFalse(check.isChecked())

        # 用户选择“确定”：标记完成
        window._confirm_complete = lambda: True
        window._on_toggle_done(task, today, True, label, check)
        self.assertTrue(storage.is_done(window.data, task["id"], today))


if __name__ == "__main__":
    unittest.main()
