"""图片功能测试：导入、清理、对话框附图、缩略图、图片区。"""
from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from app.core import storage
from app.ui.thumb import ThumbButton
from app.ui.task_dialog import TaskDialog


def make_png(path: Path) -> None:
    img = QImage(32, 32, QImage.Format_ARGB32)
    img.fill(QColor("#E05252"))
    img.save(str(path), "PNG")


class ImageTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self._old_dir = storage.DATA_DIR
        self._old_file = storage.DATA_FILE
        self._old_images = storage.IMAGES_DIR
        storage.DATA_DIR = self.tmp_path
        storage.DATA_FILE = storage.DATA_DIR / "plan.json"
        storage.IMAGES_DIR = storage.DATA_DIR / "images"
        self.app = QApplication.instance() or QApplication([])

    def tearDown(self):
        storage.DATA_DIR = self._old_dir
        storage.DATA_FILE = self._old_file
        storage.IMAGES_DIR = self._old_images
        self.tmp.cleanup()

    def test_import_path_delete(self):
        src = self.tmp_path / "src.png"
        make_png(src)
        name = storage.import_image(str(src))
        self.assertTrue(name)
        self.assertTrue(storage.image_path(name).exists())
        storage.delete_image_file(name)
        self.assertFalse(storage.image_path(name).exists())

    def test_cleanup_removes_unreferenced_images(self):
        src = self.tmp_path / "a.png"
        make_png(src)
        name = storage.import_image(str(src))
        data = storage.empty_data()
        data["day_images"]["2026-01-01"] = [name]  # 过期日期
        storage.save_data(data)
        loaded = storage.load_data()
        storage.run_cleanup(loaded)
        self.assertNotIn("2026-01-01", loaded["day_images"])
        self.assertFalse(storage.image_path(name).exists())

    def test_referenced_images_kept(self):
        src = self.tmp_path / "b.png"
        make_png(src)
        name = storage.import_image(str(src))
        data = storage.empty_data()
        data["tasks"].append(
            storage.new_task("带图任务", date.today().isoformat(), images=[name])
        )
        storage.run_cleanup(data)
        self.assertTrue(storage.image_path(name).exists())

    def test_task_dialog_images_cleanup_on_reject(self):
        src = self.tmp_path / "c.png"
        make_png(src)
        name = storage.import_image(str(src))
        dialog = TaskDialog(None, {"text": "x", "color": "#E05252"})
        dialog._add_image_name(name, created=True)
        self.assertEqual(dialog.images(), [name])
        dialog.reject()
        self.assertFalse(storage.image_path(name).exists())

    def test_thumb_button_constructs(self):
        src = self.tmp_path / "d.png"
        make_png(src)
        name = storage.import_image(str(src))
        thumb = ThumbButton(storage.image_path(name))
        thumb.show()
        self.assertEqual(thumb.width(), 100)
        thumb.close()

    def test_main_window_image_strip(self):
        from app.ui.main_window import MainWindow

        src = self.tmp_path / "e.png"
        make_png(src)
        name = storage.import_image(str(src))
        data = storage.empty_data()
        data["day_images"][date.today().isoformat()] = [name]
        storage.save_data(data)

        window = MainWindow()
        thumbs = window.findChildren(ThumbButton)
        self.assertEqual(len(thumbs), 1)

        window._delete_day_image(name)
        self.assertEqual(
            window.data["day_images"].get(date.today().isoformat()), []
        )
        self.assertFalse(storage.image_path(name).exists())


if __name__ == "__main__":
    unittest.main()
