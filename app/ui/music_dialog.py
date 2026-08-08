"""音乐播放器：俏皮暖色样式、大字体曲名、可拖动进度条。"""
from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from ..core import storage
from .style import build_music_qss

AUDIO_FILTER = "音频文件 (*.mp3 *.wav *.m4a *.wma *.ogg *.flac *.aac)"


class SeekBar(QProgressBar):
    """可点击 / 拖动的进度条。"""

    seekRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setRange(0, 0)

    def _seek(self, x: float) -> None:
        maximum = max(1, self.maximum())
        ratio = max(0.0, min(1.0, x / max(1, self.width())))
        self.seekRequested.emit(int(ratio * maximum))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.maximum() > 0:
            self._seek(event.position().x())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.maximum() > 0:
            self._seek(event.position().x())
            event.accept()
            return
        super().mouseMoveEvent(event)


def _fmt(ms: int) -> str:
    secs = max(0, ms // 1000)
    return f"{secs // 60}:{secs % 60:02d}"


class MusicPlayerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("音乐播放器")
        self.resize(500, 460)
        self.mw = parent
        self.data = self.mw.data
        self.setStyleSheet(build_music_qss(self.mw.theme))
        self._loop_timer = QTimer(self)
        self._loop_timer.setInterval(150)
        self._loop_timer.timeout.connect(self._check_single_loop)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.now_label = QLabel("🎵 未播放")
        self.now_label.setObjectName("nowLabel")
        self.now_label.setWordWrap(True)
        layout.addWidget(self.now_label)

        progress_row = QHBoxLayout()
        self.seek_bar = SeekBar()
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setObjectName("timeLabel")
        progress_row.addWidget(self.seek_bar, 1)
        progress_row.addWidget(self.time_label)
        layout.addLayout(progress_row)

        self.playlist = QListWidget()
        self.playlist.setContextMenuPolicy(Qt.CustomContextMenu)
        self.playlist.customContextMenuRequested.connect(self._context_menu)
        layout.addWidget(self.playlist, 1)

        controls = QHBoxLayout()
        self.play_btn = QPushButton("▶ 播放")
        self.pause_btn = QPushButton("⏸ 暂停")
        self.stop_btn = QPushButton("⏹ 停止")
        self.prev_btn = QPushButton("⏮ 上一首")
        self.next_btn = QPushButton("⏭ 下一首")
        self.play_btn.clicked.connect(self.play_current)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.stop_btn.clicked.connect(self.stop)
        self.prev_btn.clicked.connect(self.prev_track)
        self.next_btn.clicked.connect(self.next_track)
        for b in (
            self.play_btn,
            self.pause_btn,
            self.stop_btn,
            self.prev_btn,
            self.next_btn,
        ):
            controls.addWidget(b)
        layout.addLayout(controls)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("播放模式："))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("顺序播放", "order")
        self.mode_combo.addItem("单曲循环", "single")
        self.mode_combo.addItem("随机播放", "random")
        self.mode_combo.addItem("自定义优先级", "priority")
        mode = self.data.get("settings", {}).get("music_mode", "order")
        idx = self.mode_combo.findData(mode)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_combo, 1)
        layout.addLayout(mode_row)

        manage = QHBoxLayout()
        self.add_btn = QPushButton("＋ 添加音频…")
        self.add_btn.clicked.connect(self.add_files)
        self.remove_btn = QPushButton("－ 移除选中")
        self.remove_btn.clicked.connect(self.remove_selected)
        manage.addWidget(self.add_btn)
        manage.addWidget(self.remove_btn)
        manage.addStretch(1)
        layout.addLayout(manage)

        volume_row = QHBoxLayout()
        volume_row.addWidget(QLabel("🔊 音量："))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(
            self.data.get("settings", {}).get("music_volume", 50)
        )
        self.volume_label = QLabel(f"{self.volume_slider.value()}%")
        self.volume_slider.valueChanged.connect(self._on_volume)
        volume_row.addWidget(self.volume_slider, 1)
        volume_row.addWidget(self.volume_label)
        layout.addLayout(volume_row)

        self._init_playlist()
        player, output = self.mw._ensure_music_player()
        self._player = player
        if player is not None:
            player.positionChanged.connect(self._on_position)
            player.durationChanged.connect(self._on_duration)
            player.playbackStateChanged.connect(self._on_state)
            player.mediaStatusChanged.connect(self._on_media_status)
            output.setVolume(self.volume_slider.value() / 100.0)
            self.seek_bar.seekRequested.connect(player.setPosition)
            duration = player.duration()
            if duration > 0:
                self.seek_bar.setRange(0, duration)
                self.time_label.setText(
                    f"{_fmt(player.position())} / {_fmt(duration)}"
                )
        else:
            for b in (
                self.play_btn,
                self.pause_btn,
                self.stop_btn,
                self.prev_btn,
                self.next_btn,
            ):
                b.setEnabled(False)
        self._on_volume(self.volume_slider.value())

    def _init_playlist(self) -> None:
        paths = list(self.data.get("settings", {}).get("music_playlist", []))
        if not paths:
            builtin = storage.default_music()
            if builtin:
                paths = [str(builtin)]
        for p in paths:
            priority = self._priority_map().get(p, 50)
            item = QListWidgetItem(f"{Path(p).name}（{priority}级）")
            item.setToolTip(f"优先级：{priority}")
            self.playlist.addItem(item)
        if self.playlist.count() > 0:
            self.playlist.setCurrentRow(0)

    def _current_path(self):
        row = self.playlist.currentRow()
        if row < 0:
            return None
        paths = list(self.data.get("settings", {}).get("music_playlist", []))
        if not paths:
            builtin = storage.default_music()
            paths = [str(builtin)] if builtin else []
        return paths[row] if row < len(paths) else None

    def play_current(self, restart: bool = False) -> None:
        path = self._current_path()
        if not path or self._player is None:
            return
        if restart:
            self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()

    def toggle_pause(self) -> None:
        if self._player is None:
            return
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def stop(self) -> None:
        if self._player is not None:
            self._player.stop()

    def prev_track(self) -> None:
        self._step(-1)

    def next_track(self) -> None:
        self._step(1)

    def _step(self, delta: int) -> None:
        count = self.playlist.count()
        if count == 0:
            return
        row = self.playlist.currentRow()
        if row < 0:
            row = 0
        self.playlist.setCurrentRow((row + delta) % count)
        self.play_current()

    def add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择音频", str(Path.home()), AUDIO_FILTER
        )
        if not paths:
            return
        playlist = self.data.setdefault("settings", {}).setdefault(
            "music_playlist", []
        )
        for p in paths:
            if p not in playlist:
                playlist.append(p)
                priority = self._priority_map().get(p, 50)
                item = QListWidgetItem(f"{Path(p).name}（{priority}级）")
                item.setToolTip(f"优先级：{priority}")
                self.playlist.addItem(item)
        storage.save_data(self.data)

    def remove_selected(self) -> None:
        row = self.playlist.currentRow()
        if row < 0:
            return
        playlist = self.data.get("settings", {}).get("music_playlist", [])
        if row < len(playlist):
            del playlist[row]
        self.playlist.takeItem(row)
        storage.save_data(self.data)

    def _context_menu(self, pos) -> None:
        item = self.playlist.itemAt(pos)
        if item is None:
            return
        menu = QMenu(self)
        act_priority = menu.addAction("设置优先级（1-100，数字小先播）")
        chosen = menu.exec(self.playlist.mapToGlobal(pos))
        if chosen is act_priority:
            path = self._current_path()
            if path is None:
                return
            current = self._priority_map().get(path, 50)
            value, ok = QInputDialog.getInt(
                self, "设置优先级", "优先级（1-100，数字小先播）：",
                current, 1, 100,
            )
            if ok:
                self._set_priority(path, value)

    def _priority_map(self) -> dict:
        return self.data.setdefault("music_priority", {})

    def _set_priority(self, path: str, value: int) -> None:
        self._priority_map()[path] = value
        storage.save_data(self.data)
        row = self.playlist.currentRow()
        item = self.playlist.item(row) if row >= 0 else None
        if item is not None:
            item.setText(f"{Path(path).name}（{value}级）")
            item.setToolTip(f"优先级：{value}")

    def _mode(self) -> str:
        return self.data.get("settings", {}).get("music_mode", "order")

    def _on_mode_changed(self, _index=None) -> None:
        self.data.setdefault("settings", {})["music_mode"] = (
            self.mode_combo.currentData() or "order"
        )
        storage.save_data(self.data)

    def _paths(self) -> list:
        paths = list(self.data.get("settings", {}).get("music_playlist", []))
        if not paths:
            builtin = storage.default_music()
            paths = [str(builtin)] if builtin else []
        return paths

    def _pick_next(self, current: int) -> int:
        """按播放模式选择下一首；返回 -1 表示停止。"""
        count = self.playlist.count()
        if count == 0:
            return -1
        mode = self._mode()
        if mode == "single":
            return current
        if mode == "random":
            return random.randrange(count)
        if mode == "priority":
            paths = self._paths()
            order = sorted(
                range(len(paths)),
                key=lambda i: self._priority_map().get(paths[i], 50),
            )
            if current in order:
                idx = order.index(current)
            else:
                idx = 0
            return order[(idx + 1) % len(order)]
        nxt = current + 1
        return nxt if nxt < count else -1

    def _on_volume(self, value: int) -> None:
        self.volume_label.setText(f"{value}%")
        self.data.setdefault("settings", {})["music_volume"] = value
        storage.save_data(self.data)
        _, output = self.mw._ensure_music_player()
        if output is not None:
            output.setVolume(value / 100.0)

    def _on_position(self, pos: int) -> None:
        self.seek_bar.setValue(pos)
        duration = self.seek_bar.maximum()
        self.time_label.setText(f"{_fmt(pos)} / {_fmt(duration)}")

    def _on_duration(self, duration: int) -> None:
        self.seek_bar.setRange(0, duration)

    def _on_state(self, state) -> None:
        if state == QMediaPlayer.PlayingState:
            item = self.playlist.currentItem()
            name = item.text() if item else ""
            self.now_label.setText(f"♪ 正在播放：{name}")
            self._loop_timer.start()
        elif state == QMediaPlayer.StoppedState:
            self.now_label.setText("🎵 未播放")
            self._loop_timer.stop()

    def _check_single_loop(self) -> None:
        """单曲循环：检测到快播完时回到开头重播（不依赖 EndOfMedia，更可靠）。"""
        if self._player is None or self._mode() != "single":
            return
        duration = self._player.duration()
        position = self._player.position()
        if duration > 0 and position > 0 and position >= duration - 120:
            self._player.setPosition(0)
            self._player.play()

    def _on_media_status(self, status) -> None:
        if status == QMediaPlayer.EndOfMedia:
            row = self.playlist.currentRow()
            nxt = self._pick_next(row)
            if nxt >= 0:
                self.playlist.setCurrentRow(nxt)
                path = self._current_path()
                if self._player is not None and path:
                    # 先清除再重设音源，确保能重新开始播放（单曲循环可靠重播）
                    self._player.stop()
                    self._player.setSource(QUrl())
                    self._player.setSource(QUrl.fromLocalFile(path))
                    self._player.play()
            elif self._player is not None:
                self._player.stop()
