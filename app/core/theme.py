"""主题系统：默认淡蓝主题 + 从图片提取配色主题。"""
from __future__ import annotations

import random
import colorsys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

THEME_FOLDER = Path(r"C:\Users\Junhong\Pictures\peise")
SCREENSHOT_FOLDER = Path(r"C:\Users\Junhong\Pictures\Screenshots")
DEFAULT_THEME_ID = "默认淡蓝"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
THEME_NAMES = [
    "碧海晴空",
    "青翠山林",
    "暖阳橙光",
    "桃粉春色",
    "紫霞暮色",
    "金秋麦浪",
    "冰川银雪",
    "莓果甜心",
]


def _hex(rgb) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _from_hex(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _hue(rgb) -> float:
    r, g, b = (v / 255.0 for v in rgb)
    h, _, _ = colorsys.rgb_to_hsv(r, g, b)
    return h


def _luminance(rgb) -> float:
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def _blend(rgb1, rgb2, t: float):
    return tuple(round(a + (b - a) * t) for a, b in zip(rgb1, rgb2))


def _darken(rgb, t: float):
    return _blend(rgb, (0, 0, 0), t)


def _lighten(rgb, t: float):
    return _blend(rgb, (255, 255, 255), t)


def _dist2(a, b) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


@dataclass
class Theme:
    id: str
    name: str
    bg: str
    border: str
    button: str
    button_hover: str
    button_pressed: str
    text: str
    hint: str
    card: str
    done: str = "#9AA5AC"
    checkbox: str = "#7FB8D4"
    danger: str = "#F4C7C3"
    danger_hover: str = "#EFB4AE"
    danger_border: str = "#D9A29C"


DEFAULT_THEME = Theme(
    id=DEFAULT_THEME_ID,
    name="默认淡蓝",
    bg="#EAF6FC",
    border="#7FB8D4",
    button="#ADD8E6",
    button_hover="#9CCFE0",
    button_pressed="#8BC4D8",
    text="#1F3A4D",
    hint="#6B8CA3",
    card="#FFFFFF",
)


def _extract_colors(image_path: Path) -> list:
    """从图片提取 5 个主色（k-means 聚类），按亮度从亮到暗排序。"""
    img = QImage(str(image_path))
    if img.isNull():
        raise ValueError("图片无法读取")
    img = img.convertToFormat(QImage.Format_RGB32)
    if img.width() > 64 or img.height() > 64:
        img = img.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    points = []
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            points.append((c.red(), c.green(), c.blue()))

    rng = random.Random(7)
    k = 5
    centers = rng.sample(points, k)
    for _ in range(15):
        groups = [[] for _ in range(k)]
        for p in points:
            idx = min(range(k), key=lambda i: _dist2(p, centers[i]))
            groups[idx].append(p)
        new_centers = []
        for i, group in enumerate(groups):
            if group:
                n = len(group)
                new_centers.append(
                    tuple(sum(p[j] for p in group) // n for j in range(3))
                )
            else:
                new_centers.append(centers[i])
        centers = new_centers
    centers.sort(key=_luminance, reverse=True)
    return centers


def extract_theme(image_path: Path) -> Theme:
    """从一张图片生成一套主题配色。"""
    colors = _extract_colors(image_path)
    bg = _lighten(colors[0], 0.30)
    border = colors[1]
    button = colors[2]
    text = colors[-1]
    if _luminance(text) > 150:
        text = _blend(text, (31, 58, 77), 0.65)
    if _luminance(bg) < 150:
        bg = _lighten(bg, 0.45)
    card = _lighten(colors[0], 0.75)
    hint = _blend(text, (255, 255, 255), 0.45)
    return Theme(
        id=image_path.stem,
        name="",
        bg=_hex(bg),
        border=_hex(border),
        button=_hex(button),
        button_hover=_hex(_darken(button, 0.08)),
        button_pressed=_hex(_darken(button, 0.16)),
        text=_hex(text),
        hint=_hex(hint),
        card=_hex(card),
        checkbox=_hex(border),
    )


_cache: dict = {}


def load_themes(folder: Path = THEME_FOLDER) -> dict:
    """读取配色文件夹中的图片主题（结果带缓存）。"""
    key = str(folder)
    if key in _cache:
        return dict(_cache[key])
    themes = {}
    if folder.exists():
        files = sorted(
            f
            for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTS
        )
        items = []
        for f in files:
            try:
                t = extract_theme(f)
                items.append((_hue(_from_hex(t.border)), t))
            except Exception:
                continue
        items.sort(key=lambda x: x[0])
        for i, (_, t) in enumerate(items):
            t.name = THEME_NAMES[i % len(THEME_NAMES)]
            themes[t.id] = t
    _cache[key] = dict(themes)
    return dict(themes)


def get_theme(settings: dict, themes: dict) -> Theme:
    """按设置中的主题 id 返回主题，找不到时回退默认淡蓝。"""
    theme_id = settings.get("theme") or DEFAULT_THEME_ID
    if theme_id in themes:
        return themes[theme_id]
    return DEFAULT_THEME


def latest_image(folder: Path = SCREENSHOT_FOLDER) -> Path | None:
    """返回文件夹中最新的图片文件；不存在时返回 None。"""
    if not folder.exists():
        return None
    files = [
        f
        for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS
    ]
    if not files:
        return None
    return max(files, key=lambda f: f.stat().st_mtime)


def date_display_colors(folder: Path = SCREENSHOT_FOLDER) -> tuple[str, str] | None:
    """从最新截图中提取两个主色，用于日期显示的生动渐变配色。"""
    image = latest_image(folder)
    if image is None:
        return None
    try:
        colors = _extract_colors(image)
    except Exception:
        return None
    return _hex(colors[2]), _hex(colors[1])
