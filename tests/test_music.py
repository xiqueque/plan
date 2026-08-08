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

    def test_notes_save(self):
        data = storage.empty_data()
        storage.save_data(data)
        window = MainWindow()
        dialog = NotesDialog(window)
        self.assertIn(window.theme.border, dialog.styleSheet())
        dialog.edit.setPlainText("记得买牛奶")
        dialog._save()
        self.assertEqual(window.data["notes"], "记得买牛奶")
        loaded = storage.load_data()
        self.assertEqual(loaded["notes"], "记得买牛奶")
        dialog.close()


if __name__ == "__main__":
    unittest.main()
