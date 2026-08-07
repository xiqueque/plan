"""图片功能测试：导入、清理、对话框附图、缩略图、图片区。"""
from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
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
        data["image_daily"] = {name: True}
        storage.save_data(data)
        loaded = storage.load_data()
        storage.run_cleanup(loaded)
        self.assertNotIn("2026-01-01", loaded["day_images"])
        self.assertFalse(storage.image_path(name).exists())
        self.assertNotIn(name, loaded["image_daily"])

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
        self.assertEqual(thumb.width(), 106)
        thumb.close()

    def test_main_window_image_strip(self):
        from app.ui.main_window import MainWindow

        today = date.today().isoformat()
        names = []
        for i in range(2):
            src = self.tmp_path / f"e{i}.png"
            make_png(src)
            names.append(storage.import_image(str(src)))
        data = storage.empty_data()
        data["day_images"][today] = names
        storage.save_data(data)

        window = MainWindow()
        thumbs = window.findChildren(ThumbButton)
        self.assertEqual(len(thumbs), 2)

        # 软件内重命名
        window._rename_day_image(names[0], "课程表")
        self.assertEqual(window.data["image_names"][names[0]], "课程表")

        # 删除一张 -> 剩一张
        window._delete_day_image(names[0])
        self.assertEqual(window.data["day_images"][today], [names[1]])
        self.assertFalse(storage.image_path(names[0]).exists())

        # 只剩一张时也可以删除
        window._delete_day_image(names[1])
        self.assertEqual(window.data["day_images"][today], [])
        self.assertFalse(storage.image_path(names[1]).exists())

    def test_daily_marked_and_task_images_appear_every_day(self):
        from app.ui.main_window import MainWindow

        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        src1 = self.tmp_path / "m1.png"
        make_png(src1)
        name1 = storage.import_image(str(src1))
        src2 = self.tmp_path / "m2.png"
        make_png(src2)
        name2 = storage.import_image(str(src2))

        data = storage.empty_data()
        data["day_images"][today] = [name1]
        data["tasks"].append(
            storage.new_task("每天任务", today, is_daily=True, images=[name2])
        )
        storage.save_data(data)

        window = MainWindow()
        window._toggle_daily_image(name1)  # 标记为每日图片
        window.show()
        self.app.processEvents()

        entries = window._day_image_entries(tomorrow)
        sources = dict(entries)
        self.assertIn(name1, sources)  # 每日标记的图片
        self.assertEqual(sources[name1], "daily")
        self.assertIn(name2, sources)  # 每天任务附带的图片
        self.assertEqual(sources[name2], "task")

        # 标记后的缩略图带有星标
        thumbs = window.findChildren(ThumbButton)
        marked_thumb = next(t for t in thumbs if t._marked)
        self.assertTrue(marked_thumb._marked)


if __name__ == "__main__":
    unittest.main()
