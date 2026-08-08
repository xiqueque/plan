"""批量修改计划对话框。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from .style import CHECKBOX_QSS
from .time_picker import TimeButton

COLORS = [
    ("#1F3A4D", "黑色（默认）"),
    ("#E05252", "红色（紧急）"),
    ("#E8963A", "橙色（重要）"),
    ("#3B7DBF", "蓝色（常规）"),
    ("#4C9E63", "绿色（轻松）"),
    ("#7B5EA7", "紫色（备忘）"),
]


class BatchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量修改计划")
        self.setMinimumWidth(440)
        self.setStyleSheet(CHECKBOX_QSS)
        layout = QVBoxLayout(self)

        # 字体颜色
        color_box = QGroupBox("字体颜色")
        cb = QVBoxLayout(color_box)
        self.color_enable = QCheckBox("修改字体颜色")
        self.color_combo = QComboBox()
        for hexv, name in COLORS:
            self.color_combo.addItem(name, hexv)
        self.color_enable.toggled.connect(self.color_combo.setEnabled)
        self.color_combo.setEnabled(False)
        cb.addWidget(self.color_enable)
        cb.addWidget(self.color_combo)
        layout.addWidget(color_box)

        # 时间段
        period_box = QGroupBox("时间段")
        pb = QVBoxLayout(period_box)
        self.period_enable = QCheckBox("修改时间段")
        self.period_clear = QCheckBox("清除时间段")
        row = QHBoxLayout()
        row.addWidget(QLabel("开始："))
        self.start_btn = TimeButton("09:00")
        row.addWidget(self.start_btn, 1)
        row.addWidget(QLabel("结束："))
        self.end_btn = TimeButton("10:00")
        row.addWidget(self.end_btn, 1)
        self.period_enable.toggled.connect(self._update_period_enabled)
        self.period_clear.toggled.connect(self._update_period_enabled)
        self._update_period_enabled()
        pb.addWidget(self.period_enable)
        pb.addWidget(self.period_clear)
        pb.addLayout(row)
        layout.addWidget(period_box)

        # 提醒
        remind_box = QGroupBox("提醒")
        rb = QVBoxLayout(remind_box)
        self.remind_enable = QCheckBox("修改提醒")
        self.remind_clear = QCheckBox("清除提醒")
        self.remind_mode = QComboBox()
        self.remind_mode.addItem("仅当日提醒", "once")
        self.remind_mode.addItem("每天提醒", "daily")
        rrow = QHBoxLayout()
        rrow.addWidget(QLabel("提醒时间："))
        self.remind_time_btn = TimeButton("08:00")
        rrow.addWidget(self.remind_time_btn, 1)
        self.remind_enable.toggled.connect(self._update_remind_enabled)
        self.remind_clear.toggled.connect(self._update_remind_enabled)
        self._update_remind_enabled()
        rb.addWidget(self.remind_enable)
        rb.addWidget(self.remind_clear)
        rb.addWidget(self.remind_mode)
        rb.addLayout(rrow)
        layout.addWidget(remind_box)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("确定")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_period_enabled(self) -> None:
        enabled = self.period_enable.isChecked() and not self.period_clear.isChecked()
        self.start_btn.setEnabled(enabled)
        self.end_btn.setEnabled(enabled)

    def _update_remind_enabled(self) -> None:
        enabled = self.remind_enable.isChecked() and not self.remind_clear.isChecked()
        self.remind_mode.setEnabled(enabled)
        self.remind_time_btn.setEnabled(enabled)

    def values(self) -> dict:
        mods = {}
        if self.color_enable.isChecked():
            mods["color"] = self.color_combo.currentData()
        if self.period_enable.isChecked():
            if self.period_clear.isChecked():
                mods["period"] = "clear"
            else:
                mods["period"] = (self.start_btn.time(), self.end_btn.time())
        if self.remind_enable.isChecked():
            if self.remind_clear.isChecked():
                mods["reminder"] = "clear"
            else:
                mods["reminder"] = (
                    self.remind_mode.currentData(),
                    self.remind_time_btn.time(),
                )
        return mods
