"""设置对话框：自动清理天数、音效（音频 + 音量）。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from .style import CHECKBOX_QSS

AUDIO_FILTER = "音频文件 (*.wav *.mp3)"


class SettingsDialog(QDialog):
    def __init__(
        self,
        parent=None,
        cleanup_days: int = 15,
        sound_file: str = "",
        sound_volume: int = 12,
        default_sound_name: str = "",
        autostart_enabled: bool = False,
        image_viewer: str = "",
        on_preview=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(460)
        self.setStyleSheet(CHECKBOX_QSS)

        self.check_sound = sound_file or ""
        self._default_sound_name = default_sound_name
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

        # 音效音频
        sound_row = QHBoxLayout()
        sound_row.addWidget(QLabel("音效音频："))
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

        # 音量
        volume_row = QHBoxLayout()
        volume_row.addWidget(QLabel("音效音量："))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(sound_volume if 0 <= sound_volume <= 100 else 12)
        self.volume_label = QLabel(f"{self.volume_slider.value()}%")
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_label.setText(f"{v}%")
        )
        volume_row.addWidget(self.volume_slider, 1)
        volume_row.addWidget(self.volume_label)
        layout.addLayout(volume_row)

        # 开机自启动
        self.autostart_check = QCheckBox("开机自动启动（到点提醒需要程序在运行）")
        self.autostart_check.setChecked(autostart_enabled)
        layout.addWidget(self.autostart_check)

        # 图片打开方式
        viewer_row = QHBoxLayout()
        viewer_row.addWidget(QLabel("图片打开方式："))
        self.viewer_combo = QComboBox()
        self.viewer_combo.addItems(["系统默认程序", "自定义程序"])
        self.viewer_path_edit = QLineEdit(image_viewer or "")
        self.viewer_path_edit.setPlaceholderText("选择程序，如画图 mspaint.exe")
        self.viewer_browse_btn = QPushButton("浏览…")
        self.viewer_browse_btn.clicked.connect(self._browse_viewer)
        self.viewer_combo.currentIndexChanged.connect(self._update_viewer_enabled)
        viewer_row.addWidget(self.viewer_combo)
        viewer_row.addWidget(self.viewer_path_edit, 1)
        viewer_row.addWidget(self.viewer_browse_btn)
        layout.addLayout(viewer_row)
        if image_viewer:
            self.viewer_combo.setCurrentIndex(1)
        self._update_viewer_enabled()

        layout.addWidget(QLabel("提示：勾选完成与到点提醒共用此音效；支持 wav / mp3。"))

        layout.addWidget(QLabel("注意：标记为「每天重复」的计划不会被自动删除。"))

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("保存")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _sound_text(self) -> str:
        if not self.check_sound:
            if self._default_sound_name:
                return f"默认音频（{self._default_sound_name}）"
            return "默认音频"
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
            self._on_preview(self.check_sound, self.volume_slider.value())

    def _reset_sound(self) -> None:
        self.check_sound = ""
        self._update_sound_label()

    def cleanup_days(self) -> int:
        return self.days_spin.value()

    def sound_path(self) -> str:
        return self.check_sound

    def sound_volume(self) -> int:
        return self.volume_slider.value()

    def _update_viewer_enabled(self) -> None:
        custom = self.viewer_combo.currentIndex() == 1
        self.viewer_path_edit.setEnabled(custom)
        self.viewer_browse_btn.setEnabled(custom)

    def _browse_viewer(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片程序", str(Path.home()), "程序 (*.exe)"
        )
        if path:
            self.viewer_path_edit.setText(path)

    def image_viewer(self) -> str:
        if self.viewer_combo.currentIndex() != 1:
            return ""
        return self.viewer_path_edit.text().strip()

    def values(self):
        return (
            self.days_spin.value(),
            self.sound_path(),
            self.sound_volume(),
            self.autostart_check.isChecked(),
            self.image_viewer(),
        )
