"""新增 / 编辑计划对话框。"""
from __future__ import annotations

from PySide6.QtCore import QTime
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
)

TASK_COLORS = [
    ("#1F3A4D", "黑色（默认）"),
    ("#E05252", "红色（紧急）"),
    ("#E8963A", "橙色（重要）"),
    ("#3B7DBF", "蓝色（常规）"),
    ("#4C9E63", "绿色（轻松）"),
    ("#7B5EA7", "紫色（备忘）"),
]


class TaskDialog(QDialog):
    def __init__(self, parent=None, task: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("编辑计划" if task else "添加计划")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("内容："))
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("要做什么？例如：写数学作业")
        layout.addWidget(self.text_edit)

        self.time_check = QCheckBox("设置时间段（可选）")
        layout.addWidget(self.time_check)

        time_row = QHBoxLayout()
        self.start_edit = QTimeEdit(QTime(9, 0))
        self.end_edit = QTimeEdit(QTime(10, 0))
        self.start_edit.setDisplayFormat("HH:mm")
        self.end_edit.setDisplayFormat("HH:mm")
        time_row.addWidget(QLabel("开始："))
        time_row.addWidget(self.start_edit, 1)
        time_row.addWidget(QLabel("结束："))
        time_row.addWidget(self.end_edit, 1)
        layout.addLayout(time_row)
        self.time_check.toggled.connect(self._update_time_enabled)
        self._update_time_enabled(False)

        self.daily_check = QCheckBox("每天重复出现（每天自动出现在列表）")
        layout.addWidget(self.daily_check)

        # 字体颜色选择
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("字体颜色："))
        self.color_buttons = []
        self.color_group = QButtonGroup(self)
        self.color_group.setExclusive(True)
        for hex_color, label in TASK_COLORS:
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setFixedSize(28, 28)
            btn.setToolTip(label)
            btn.setStyleSheet(
                f"QPushButton {{ background:{hex_color}; border:1px solid #9AA5AC; "
                f"border-radius:6px; }}"
            )
            btn.clicked.connect(lambda _, c=hex_color: self._select_color(c))
            self.color_group.addButton(btn)
            self.color_buttons.append((btn, hex_color))
            color_row.addWidget(btn)
        color_row.addStretch(1)
        layout.addLayout(color_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("保存")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if task:
            self.text_edit.setText(task.get("text", ""))
            if task.get("time_start"):
                self.time_check.setChecked(True)
                self.start_edit.setTime(QTime.fromString(task["time_start"], "HH:mm"))
                if task.get("time_end"):
                    self.end_edit.setTime(QTime.fromString(task["time_end"], "HH:mm"))
            self.daily_check.setChecked(bool(task.get("is_daily")))
        self._select_color((task or {}).get("color") or "#1F3A4D")

    def _update_time_enabled(self, enabled: bool) -> None:
        self.start_edit.setEnabled(enabled)
        self.end_edit.setEnabled(enabled)

    def values(self):
        """返回 (内容, 开始时间, 结束时间, 是否每天重复)。"""
        text = self.text_edit.text().strip()
        start = end = None
        if self.time_check.isChecked():
            start = self.start_edit.time().toString("HH:mm")
            end = self.end_edit.time().toString("HH:mm")
        return text, start, end, self.daily_check.isChecked()

    def _select_color(self, hex_color: str) -> None:
        self._selected_color_value = hex_color
        for btn, c in self.color_buttons:
            btn.setChecked(c == hex_color)
            border = "2px solid #1F3A4D" if c == hex_color else "1px solid #9AA5AC"
            btn.setStyleSheet(
                f"QPushButton {{ background:{c}; border:{border}; border-radius:6px; }}"
            )

    def selected_color(self) -> str:
        return getattr(self, "_selected_color_value", "#1F3A4D")
