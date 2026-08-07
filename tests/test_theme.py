"""主题系统测试：默认主题、图片配色提取、主题切换。"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PySide6.QtGui import QColor, QImage

from app.core import theme


def make_image(path: Path, colors) -> None:
    img = QImage(64, 64, QImage.Format_RGB32)
    for y in range(64):
        for x in range(64):
            c = colors[(x + y) % len(colors)]
            img.setPixelColor(x, y, QColor(*c))
    img.save(str(path), "PNG")


class ThemeTestCase(unittest.TestCase):
    def test_default_theme(self):
        t = theme.DEFAULT_THEME
        self.assertEqual(t.id, theme.DEFAULT_THEME_ID)
        self.assertTrue(t.bg.startswith("#"))
        self.assertEqual(len(t.bg), 7)

    def test_extract_theme(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "sample.png"
            make_image(
                p,
                [(230, 246, 252), (127, 184, 212), (173, 216, 230), (31, 58, 77)],
            )
            t = theme.extract_theme(p)
            self.assertEqual(t.id, p.stem)
            self.assertEqual(t.name, "")
            for color in (t.bg, t.border, t.button, t.text, t.hint, t.card):
                self.assertRegex(color, r"^#[0-9A-F]{6}$")

    def test_load_and_get_theme(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            for i in range(2):
                make_image(folder / f"c{i}.png", [(i * 40, 120, 200), (20, 40, 90)])
            themes = theme.load_themes(folder)
            self.assertEqual(len(themes), 2)
            names = [t.name for t in themes.values()]
            self.assertTrue(all(len(n) == 4 for n in names))
            self.assertEqual(len(set(names)), len(names))
            theme_id = next(iter(themes))
            t = theme.get_theme({"theme": theme_id}, themes)
            self.assertEqual(t.id, theme_id)
            fallback = theme.get_theme({"theme": "不存在"}, themes)
            self.assertEqual(fallback.id, theme.DEFAULT_THEME_ID)

    def test_build_main_qss_uses_theme_colors(self):
        from app.ui.style import build_main_qss

        qss = build_main_qss(theme.DEFAULT_THEME)
        self.assertIn(theme.DEFAULT_THEME.bg, qss)
        self.assertIn(theme.DEFAULT_THEME.border, qss)



if __name__ == "__main__":
    unittest.main()
