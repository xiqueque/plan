"""共享样式片段。"""
from __future__ import annotations

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
