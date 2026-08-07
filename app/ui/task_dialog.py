"""新增 / 编辑计划对话框。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from ..core.storage import ALL_WEEKDAYS, WEEKDAY_NAMES
from .time_picker import TimeButton

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
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("内容："))
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("要做什么？例如：写数学作业")
        layout.addWidget(self.text_edit)

        self.time_check = QCheckBox("设置时间段（可选）")
        layout.addWidget(self.time_check)

        time_row = QHBoxLayout()
        self.start_btn = TimeButton("09:00")
        self.end_btn = TimeButton("10:00")
        time_row.addWidget(QLabel("开始："))
        time_row.addWidget(self.start_btn, 1)
        time_row.addWidget(QLabel("结束："))
        time_row.addWidget(self.end_btn, 1)
        layout.addLayout(time_row)
        self.time_check.toggled.connect(self._update_time_enabled)
        self._update_time_enabled(False)

        # 提醒设置
        reminder_box = QGroupBox("提醒")
        reminder_layout = QVBoxLayout(reminder_box)
        mode_row = QHBoxLayout()
        self.mode_none = QRadioButton("不提醒")
        self.mode_once = QRadioButton("仅当日提醒")
        self.mode_daily = QRadioButton("每天提醒")
        self.reminder_group = QButtonGroup(self)
        self.reminder_group.setExclusive(True)
        self.reminder_group.addButton(self.mode_none)
        self.reminder_group.addButton(self.mode_once)
        self.reminder_group.addButton(self.mode_daily)
        self.mode_none.setChecked(True)
        mode_row.addWidget(self.mode_none)
        mode_row.addWidget(self.mode_once)
        mode_row.addWidget(self.mode_daily)
        reminder_layout.addLayout(mode_row)

        remind_time_row = QHBoxLayout()
        remind_time_row.addWidget(QLabel("提醒时间："))
        self.reminder_time_btn = TimeButton("08:00")
        remind_time_row.addWidget(self.reminder_time_btn, 1)
        reminder_layout.addLayout(remind_time_row)

        weekday_label = QLabel("提醒日：")
        reminder_layout.addWidget(weekday_label)
        weekday_grid = QGridLayout()
        weekday_grid.setHorizontalSpacing(8)
        weekday_grid.setVerticalSpacing(4)
        self.weekday_checks: dict[int, QCheckBox] = {}
        for i, name in enumerate(WEEKDAY_NAMES):
            check = QCheckBox(name)
            check.setChecked(True)
            self.weekday_checks[i] = check
            row, col = divmod(i, 4)
            weekday_grid.addWidget(check, row, col)
        reminder_layout.addLayout(weekday_grid)

        quick_row = QHBoxLayout()
        all_btn = QPushButton("全选")
        work_btn = QPushButton("工作日（周一~五）")
        all_btn.clicked.connect(lambda: self._set_weekdays(ALL_WEEKDAYS))
        work_btn.clicked.connect(lambda: self._set_weekdays([0, 1, 2, 3, 4]))
        quick_row.addWidget(all_btn)
        quick_row.addWidget(work_btn)
        quick_row.addStretch(1)
        reminder_layout.addLayout(quick_row)

        layout.addWidget(reminder_box)
        self.mode_none.toggled.connect(self._update_reminder_enabled)
        self.mode_once.toggled.connect(self._update_reminder_enabled)
        self.mode_daily.toggled.connect(self._update_reminder_enabled)

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
                self.start_btn.set_time(task["time_start"])
                if task.get("time_end"):
                    self.end_btn.set_time(task["time_end"])
            mode = task.get("reminder_mode") or (
                "daily" if task.get("is_daily") else "none"
            )
            if mode == "daily":
                self.mode_daily.setChecked(True)
            elif mode == "once":
                self.mode_once.setChecked(True)
            else:
                self.mode_none.setChecked(True)
            if task.get("reminder_time"):
                self.reminder_time_btn.set_time(task["reminder_time"])
            weekdays = task.get("reminder_weekdays")
            if isinstance(weekdays, list):
                self._set_weekdays(weekdays)
        self._select_color((task or {}).get("color") or "#1F3A4D")

    def _update_time_enabled(self, enabled: bool) -> None:
        self.start_btn.setEnabled(enabled)
        self.end_btn.setEnabled(enabled)

    def _update_reminder_enabled(self) -> None:
        enabled = not self.mode_none.isChecked()
        self.reminder_time_btn.setEnabled(enabled)
        for check in self.weekday_checks.values():
            check.setEnabled(enabled)

    def _set_weekdays(self, weekdays) -> None:
        chosen = set(weekdays)
        for i, check in self.weekday_checks.items():
            check.setChecked(i in chosen)

    def values(self):
        """返回 (内容, 开始, 结束, 是否每天出现, 提醒模式, 提醒时间, 提醒周几)。"""
        text = self.text_edit.text().strip()
        start = end = None
        if self.time_check.isChecked():
            start = self.start_btn.time()
            end = self.end_btn.time()
        mode = "none"
        if self.mode_once.isChecked():
            mode = "once"
        elif self.mode_daily.isChecked():
            mode = "daily"
        remind_time = self.reminder_time_btn.time() if mode != "none" else None
        weekdays = (
            [i for i, check in self.weekday_checks.items() if check.isChecked()]
            if mode != "none"
            else list(ALL_WEEKDAYS)
        )
        return text, start, end, mode == "daily", mode, remind_time, weekdays

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
