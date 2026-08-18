"""从 peise 图片提取主题配色，输出 Dart 主题表（与电脑版算法一致）。"""
import colorsys
import random
from pathlib import Path

from PIL import Image

THEME_FOLDER = Path(r"C:\Users\Junhong\Pictures\peise")
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


def _hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _from_hex(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _hue(rgb):
    r, g, b = (v / 255.0 for v in rgb)
    h, _, _ = colorsys.rgb_to_hsv(r, g, b)
    return h


def _luminance(rgb):
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def _blend(rgb1, rgb2, t):
    return tuple(round(a + (b - a) * t) for a, b in zip(rgb1, rgb2))


def _darken(rgb, t):
    return _blend(rgb, (0, 0, 0), t)


def _lighten(rgb, t):
    return _blend(rgb, (255, 255, 255), t)


def _dist2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def _extract_colors(image_path):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((64, 64), Image.LANCZOS)
    points = list(img.getdata())
    rng = random.Random(7)
    k = 5
    centers = rng.sample(points, k)
    for _ in range(15):
        groups = [[] for _ in range(k)]
        for p in points:
            idx = min(range(k), key=lambda i: _dist2(p, centers[i]))
            groups[idx].append(p)
        new_centers = []
        for group in groups:
            if group:
                n = len(group)
                new_centers.append(
                    tuple(sum(p[j] for p in group) // n for j in range(3))
                )
            else:
                new_centers.append(centers[0])
        centers = new_centers
    centers.sort(key=_luminance, reverse=True)
    return centers


def extract_theme(image_path):
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
    return {
        "bg": _hex(bg),
        "border": _hex(border),
        "button": _hex(button),
        "button_hover": _hex(_darken(button, 0.08)),
        "button_pressed": _hex(_darken(button, 0.16)),
        "text": _hex(text),
        "hint": _hex(hint),
        "card": _hex(card),
        "checkbox": _hex(border),
        "_hue": _hue(border),
    }


def main():
    items = []
    for f in sorted(THEME_FOLDER.iterdir()):
        if f.is_file() and f.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}:
            try:
                items.append((extract_theme(f), f.name))
            except Exception as e:
                print(f"# skip {f.name}: {e}")
    items.sort(key=lambda x: x[0]["_hue"])
    lines = []
    lines.append("// 由 scripts/extract_themes.py 从 peise 图片自动生成，与电脑版配色一致")
    lines.append("import 'package:flutter/material.dart';")
    lines.append("")
    lines.append("/// 一套主题配色")
    lines.append("class AppTheme {")
    lines.append("  final String id;")
    lines.append("  final Color bg;")
    lines.append("  final Color primary;")
    lines.append("  final Color button;")
    lines.append("  final Color text;")
    lines.append("  final Color hint;")
    lines.append("  final Color card;")
    lines.append("")
    lines.append("  const AppTheme({")
    lines.append("    required this.id,")
    lines.append("    required this.bg,")
    lines.append("    required this.primary,")
    lines.append("    required this.button,")
    lines.append("    required this.text,")
    lines.append("    required this.hint,")
    lines.append("    required this.card,")
    lines.append("  });")
    lines.append("}")
    lines.append("")
    lines.append("/// 默认淡蓝主题")
    lines.append("const appThemeDefault = AppTheme(")
    lines.append("  id: '默认淡蓝',")
    lines.append("  bg: Color(0xFFEAF6FC),")
    lines.append("  primary: Color(0xFF7FB8D4),")
    lines.append("  button: Color(0xFFADD8E6),")
    lines.append("  text: Color(0xFF1F3A4D),")
    lines.append("  hint: Color(0xFF6B8CA3),")
    lines.append("  card: Color(0xFFFFFFFF),")
    lines.append(");")
    lines.append("")
    lines.append("/// 8 套图片主题")
    lines.append("final Map<String, AppTheme> appThemes = {")
    for i, (t, fname) in enumerate(items):
        name = THEME_NAMES[i % len(THEME_NAMES)]
        lines.append(f"  '{name}': AppTheme(")
        lines.append(f"    id: '{name}',")
        lines.append(f"    bg: Color(0xFF{t['bg'][1:]}),")
        lines.append(f"    primary: Color(0xFF{t['border'][1:]}),")
        lines.append(f"    button: Color(0xFF{t['button'][1:]}),")
        lines.append(f"    text: Color(0xFF{t['text'][1:]}),")
        lines.append(f"    hint: Color(0xFF{t['hint'][1:]}),")
        lines.append(f"    card: Color(0xFF{t['card'][1:]}),")
        lines.append("  ),")
    lines.append("};")
    out = Path(__file__).resolve().parent.parent / "mobile" / "lib" / "app_theme.dart"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written: {out}")


if __name__ == "__main__":
    main()
