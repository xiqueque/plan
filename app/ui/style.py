"""共享样式片段。"""
from __future__ import annotations

from string import Template

# 通用复选框样式：更大的勾选框
CHECKBOX_QSS = """
QCheckBox {
    font-size: 15px;
    spacing: 8px;
    padding: 2px 0;
}
QCheckBox::indicator {
    width: 22px;
    height: 22px;
    border: 2px solid #7FB8D4;
    border-radius: 6px;
    background: white;
}
QCheckBox::indicator:hover { border-color: #3B7DBF; }
QCheckBox::indicator:checked {
    background: #7FB8D4;
    border-color: #6FB1CE;
}
QCheckBox:disabled { color: #9AA5AC; }
QCheckBox::indicator:disabled {
    background: #E5EEF4;
    border-color: #C9DCE8;
}
"""


def build_main_qss(theme) -> str:
    """根据主题生成主窗口样式。"""
    qss = Template(
        """
QWidget {
    font-family: "幼圆", "Microsoft YaHei", "微软雅黑", sans-serif;
    font-size: 15px;
    color: $text;
}
QMainWindow { background: transparent; }
QWidget#central {
    background: $bg;
    border: 2px solid $border;
    border-radius: 16px;
}
QPushButton#dateLabel {
    border: none;
    background: transparent;
    font-size: 20px;
    font-weight: bold;
    text-align: left;
    padding: 0;
}
QPushButton#dateLabel:hover { color: $border; }
QPushButton#dateLabel:pressed { color: $text; }
QLabel#emptyLabel {
    color: $hint;
    padding: 24px;
}
QLabel#taskText {
    font-size: 18px;
    font-weight: 600;
}
QLabel#timeLabel {
    font-size: 13px;
    color: $hint;
}
QLineEdit, QSpinBox {
    background: white;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: $button;
}
QPushButton {
    background: $button;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover { background: $button_hover; }
QPushButton:pressed { background: $button_pressed; }
QPushButton#primary {
    background: $border;
    color: white;
    font-weight: bold;
}
QPushButton#primary:hover { background: $button_pressed; }
QPushButton#smallBtn {
    padding: 7px 14px;
    font-size: 15px;
}
QPushButton#smallDanger {
    padding: 7px 14px;
    font-size: 15px;
    background: $danger;
    border-color: $danger_border;
}
QPushButton#smallDanger:hover { background: $danger_hover; }
QPushButton#winBtn {
    padding: 2px 10px;
    font-size: 14px;
    background: transparent;
    border: none;
}
QPushButton#winBtn:hover { background: $button; }
QPushButton#winClose:hover { background: $danger; color: #7A2E2A; }
QScrollArea { border: none; background: transparent; }
QFrame#taskRow {
    background: $card;
    border: 1px solid $border;
    border-radius: 8px;
}
"""
    ).substitute(
        bg=theme.bg,
        border=theme.border,
        button=theme.button,
        button_hover=theme.button_hover,
        button_pressed=theme.button_pressed,
        text=theme.text,
        hint=theme.hint,
        card=theme.card,
        danger=theme.danger,
        danger_hover=theme.danger_hover,
        danger_border=theme.danger_border,
    )
    return qss + CHECKBOX_QSS
