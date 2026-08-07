"""设置对话框：自动清理天数。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    def __init__(self, parent=None, cleanup_days: int = 15):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        row.addWidget(QLabel("自动清理：超过多少天的计划自动删除"))
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 365)
        self.days_spin.setValue(cleanup_days)
        self.days_spin.setSuffix(" 天")
        row.addWidget(self.days_spin)
        layout.addLayout(row)
        layout.addWidget(QLabel("注意：标记为「每天重复」的计划不会被自动删除。"))

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("保存")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def cleanup_days(self) -> int:
        return self.days_spin.value()
