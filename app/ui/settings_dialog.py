"""设置对话框：自动清理天数、完成音效。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

AUDIO_FILTER = "音频文件 (*.wav *.mp3)"


class SettingsDialog(QDialog):
    def __init__(
        self,
        parent=None,
        cleanup_days: int = 15,
        check_sound: str = "",
        on_preview=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(460)

        self.check_sound = check_sound or ""
        self._on_preview = on_preview

        layout = QVBoxLayout(self)

        # 自动清理天数
        cleanup_row = QHBoxLayout()
        cleanup_row.addWidget(QLabel("自动清理：超过多少天的计划自动删除"))
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 365)
        self.days_spin.setValue(cleanup_days)
        self.days_spin.setSuffix(" 天")
        cleanup_row.addWidget(self.days_spin)
        layout.addLayout(cleanup_row)

        # 完成音效
        sound_row = QHBoxLayout()
        sound_row.addWidget(QLabel("完成音效："))
        self.sound_label = QLabel(self._sound_text())
        sound_row.addWidget(self.sound_label, 1)
        self.choose_btn = QPushButton("选择音频…")
        self.choose_btn.clicked.connect(self._choose_sound)
        self.preview_btn = QPushButton("试听")
        self.preview_btn.clicked.connect(self._preview_sound)
        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.clicked.connect(self._reset_sound)
        sound_row.addWidget(self.choose_btn)
        sound_row.addWidget(self.preview_btn)
        sound_row.addWidget(self.reset_btn)
        layout.addLayout(sound_row)
        layout.addWidget(QLabel("提示：勾选任务完成时播放所选音频，支持 wav / mp3。"))

        layout.addWidget(QLabel("注意：标记为「每天重复」的计划不会被自动删除。"))

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("保存")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _sound_text(self) -> str:
        if not self.check_sound:
            return "内置可爱音效（默认）"
        return Path(self.check_sound).name

    def _update_sound_label(self) -> None:
        self.sound_label.setText(self._sound_text())

    def _choose_sound(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择完成音效", str(Path.home()), AUDIO_FILTER
        )
        if path:
            self.check_sound = path
            self._update_sound_label()

    def _preview_sound(self) -> None:
        if self._on_preview:
            self._on_preview(self.check_sound)

    def _reset_sound(self) -> None:
        self.check_sound = ""
        self._update_sound_label()

    def cleanup_days(self) -> int:
        return self.days_spin.value()

    def sound_path(self) -> str:
        return self.check_sound
