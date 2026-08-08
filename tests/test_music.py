"""音乐播放器与便签测试。"""
from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.core import storage
from app.ui.main_window import MainWindow
from app.ui.music_dialog import MusicPlayerDialog
from app.ui.notes_dialog import NotesDialog


class MusicTestCase(unittest.TestCase):
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

    def test_default_music_exists(self):
        music = storage.default_music()
        self.assertIsNotNone(music)
        self.assertTrue(music.exists())

    def test_music_dialog_playlist(self):
        data = storage.empty_data()
        data["tasks"].append(storage.new_task("t", date.today().isoformat()))
        storage.save_data(data)
        window = MainWindow()
        dialog = MusicPlayerDialog(window)
        self.assertGreaterEqual(dialog.playlist.count(), 1)
        self.assertIn(window.theme.border, dialog.styleSheet())  # 配色跟随主题
        dialog._on_volume(35)
        self.assertEqual(window.data["settings"]["music_volume"], 35)
        dialog.close()

    def test_notes_immediate_save(self):
        data = storage.empty_data()
        storage.save_data(data)
        window = MainWindow()
        dialog = NotesDialog(window)
        self.assertIn(window.theme.border, dialog.styleSheet())
        dialog.edit.setPlainText("记得买牛奶")
        self.assertEqual(window.data["notes"], "记得买牛奶")  # 即改即存
        loaded = storage.load_data()
        self.assertEqual(loaded["notes"], "记得买牛奶")
        dialog.close()

    def test_music_modes_and_priority(self):
        data = storage.empty_data()
        data["settings"]["music_playlist"] = [
            r"C:\a\song1.mp3",
            r"C:\a\song2.mp3",
            r"C:\a\song3.mp3",
        ]
        storage.save_data(data)
        window = MainWindow()
        dialog = MusicPlayerDialog(window)
        self.assertEqual(dialog.playlist.count(), 3)

        # 单曲循环
        dialog.mode_combo.setCurrentIndex(dialog.mode_combo.findData("single"))
        dialog._on_mode_changed()
        self.assertEqual(dialog._pick_next(0), 0)

        # 随机播放
        dialog.mode_combo.setCurrentIndex(dialog.mode_combo.findData("random"))
        dialog._on_mode_changed()
        for _ in range(30):
            self.assertIn(dialog._pick_next(1), (0, 1, 2))

        # 自定义优先级：song2(1) → song1(2) → song3(3)
        dialog._set_priority(r"C:\a\song2.mp3", 1)
        dialog._set_priority(r"C:\a\song1.mp3", 2)
        dialog._set_priority(r"C:\a\song3.mp3", 3)
        dialog.mode_combo.setCurrentIndex(dialog.mode_combo.findData("priority"))
        dialog._on_mode_changed()
        self.assertEqual(dialog._pick_next(1), 0)  # song2 之后是 song1
        self.assertEqual(dialog._pick_next(2), 1)  # song3 之后回到 song2
        dialog.close()


if __name__ == "__main__":
    unittest.main()
