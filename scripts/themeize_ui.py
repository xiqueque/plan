"""把界面里写死的颜色批量替换为当前主题色（一次性机械改写）。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "mobile" / "lib"
FILES = ["main_screen.dart", "task_dialog.dart", "calendar_page.dart"]

REPL = {
    "Color(0xFF1F3A4D)": "T.t.text",
    "Color(0xFF6B8CA3)": "T.t.hint",
    "Color(0xFF8A9BA8)": "T.t.hint",
    "Color(0xFF7FB8D4)": "T.t.primary",
    "Color(0xFFADD8E6)": "T.t.button",
    "Color(0xFFEAF6FC)": "T.t.bg",
    "Color(0xFFD5E8F2)": "T.t.borderSoft",
    "Color(0xFFA8D8EA)": "T.t.borderSoft",
    "Color(0xFFB9DEEE)": "T.t.borderSoft",
}

for name in FILES:
    p = ROOT / name
    text = p.read_text(encoding="utf-8")
    for old, new in REPL.items():
        text = text.replace(old, new)
    # 含有 T.t 的行去掉 const（避免常量表达式错误）
    lines = []
    for line in text.splitlines():
        if "T.t." in line and "const " in line:
            line = line.replace("const ", "", 1)
        lines.append(line)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"done: {name}")
