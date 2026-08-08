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
    border: 2px solid $border;
    border-radius: 12px;
    padding: 8px 16px;
    font-size: 15px;
    font-weight: 600;
}
QPushButton:hover { background: $button_hover; }
QPushButton:pressed { background: $button_pressed; }
QPushButton#primary {
    background: $border;
    color: white;
    font-weight: bold;
    padding: 10px 22px;
    font-size: 16px;
    min-height: 34px;
}
QPushButton#primary:hover { background: $button_pressed; }
QPushButton#smallBtn {
    padding: 8px 14px;
    font-size: 15px;
    font-weight: 600;
}
QPushButton#smallDanger {
    padding: 8px 14px;
    font-size: 15px;
    background: $danger;
    border-color: $danger_border;
}
QPushButton#smallDanger:hover { background: $danger_hover; }
QPushButton#winBtn {
    padding: 4px 12px;
    font-size: 15px;
    background: transparent;
    border: none;
}
QPushButton#winBtn:hover { background: $button; }
QPushButton#winClose:hover { background: $danger; color: #7A2E2A; }
QPushButton#miniIcon {
    background: transparent;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    padding: 3px;
}
QPushButton#miniIcon:hover { background: $button; }
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


def build_music_qss(theme) -> str:
    """音乐播放器样式：跟随主题配色，俏皮圆润。"""
    return Template(
        """
QDialog {
    background: $bg;
    font-family: "幼圆", "Microsoft YaHei";
    font-size: 15px;
    color: $text;
}
QLabel#nowLabel { font-size: 20px; font-weight: bold; color: $border; }
QLabel#timeLabel { font-size: 14px; color: $hint; }
QListWidget {
    background: $card;
    border: 2px solid $border;
    border-radius: 14px;
    font-size: 17px;
    padding: 6px;
}
QListWidget::item { padding: 7px 10px; border-radius: 9px; }
QListWidget::item:selected { background: $button; color: $text; }
QPushButton {
    background: $button;
    border: 2px solid $border;
    border-radius: 13px;
    padding: 9px 14px;
    font-size: 15px;
    font-weight: bold;
}
QPushButton:hover { background: $button_hover; }
QPushButton:pressed { background: $button_pressed; }
QProgressBar {
    background: $button;
    border: none;
    border-radius: 9px;
    height: 14px;
}
QProgressBar::chunk { background: $border; border-radius: 9px; }
QSlider::groove:horizontal {
    height: 9px;
    background: $button;
    border-radius: 4px;
}
QSlider::handle:horizontal {
    width: 19px;
    height: 19px;
    margin: -5px 0;
    background: $border;
    border-radius: 9px;
}
"""
    ).substitute(
        bg=theme.bg,
        text=theme.text,
        border=theme.border,
        hint=theme.hint,
        card=theme.card,
        button=theme.button,
        button_hover=theme.button_hover,
        button_pressed=theme.button_pressed,
    )


def build_notes_qss(theme) -> str:
    """便签样式：跟随主题配色，清新圆润。"""
    return Template(
        """
QDialog {
    background: $bg;
    font-family: "幼圆", "Microsoft YaHei";
    font-size: 15px;
    color: $text;
}
QTextEdit {
    background: $card;
    border: 2px solid $border;
    border-radius: 14px;
    font-size: 16px;
    padding: 10px;
}
QPushButton {
    background: $button;
    border: 2px solid $border;
    border-radius: 12px;
    padding: 9px 16px;
    font-size: 15px;
    font-weight: bold;
}
QPushButton:hover { background: $button_hover; }
QPushButton:pressed { background: $button_pressed; }
"""
    ).substitute(
        bg=theme.bg,
        text=theme.text,
        border=theme.border,
        card=theme.card,
        button=theme.button,
        button_hover=theme.button_hover,
        button_pressed=theme.button_pressed,
    )
