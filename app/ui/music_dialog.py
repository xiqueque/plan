"""音乐播放器：俏皮暖色样式、大字体曲名、可拖动进度条、拖拽排序、随机模式。"""
from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from ..core import storage
from .style import build_music_qss

AUDIO_FILTER = "音频文件 (*.mp3 *.wav *.m4a *.wma *.ogg *.flac *.aac)"
PATH_ROLE = Qt.UserRole


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
        self._last_label_ms = 0

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
        self.playlist.setDragDropMode(QAbstractItemView.InternalMove)
        self.playlist.setDefaultDropAction(Qt.MoveAction)
        self.playlist.itemDoubleClicked.connect(lambda _item: self.play_current())
        self.playlist.model().rowsMoved.connect(self._sync_order)
        layout.addWidget(self.playlist, 1)

        controls = QHBoxLayout()
        self.toggle_btn = QPushButton("▶ 播放")
        self.stop_btn = QPushButton("⏹ 停止")
        self.prev_btn = QPushButton("⏮ 上一首")
        self.next_btn = QPushButton("⏭ 下一首")
        self.toggle_btn.clicked.connect(self.toggle_play)
        self.stop_btn.clicked.connect(self.stop)
        self.prev_btn.clicked.connect(self.prev_track)
        self.next_btn.clicked.connect(self.next_track)
        for b in (self.toggle_btn, self.stop_btn, self.prev_btn, self.next_btn):
            controls.addWidget(b)
        layout.addLayout(controls)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("播放模式："))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("顺序播放", "order")
        self.mode_combo.addItem("单曲循环", "single")
        self.mode_combo.addItem("随机播放", "random")
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
            for b in (self.toggle_btn, self.stop_btn, self.prev_btn, self.next_btn):
                b.setEnabled(False)
        self._update_toggle_text()
        self._on_volume(self.volume_slider.value())

    # ---------- 播放列表 ----------
    def _init_playlist(self) -> None:
        paths = self._paths()
        for p in paths:
            self._append_item(p)
        if self.playlist.count() > 0:
            self.playlist.setCurrentRow(0)

    def _append_item(self, path: str) -> QListWidgetItem:
        item = QListWidgetItem(Path(path).name)
        item.setData(PATH_ROLE, path)
        self.playlist.addItem(item)
        return item

    def _paths(self) -> list:
        paths = list(self.data.get("settings", {}).get("music_playlist", []))
        if not paths:
            builtin = storage.default_music()
            paths = [str(builtin)] if builtin else []
        return paths

    def _current_path(self):
        row = self.playlist.currentRow()
        if row < 0:
            return None
        item = self.playlist.item(row)
        if item is None:
            return None
        path = item.data(PATH_ROLE)
        return path if path else None

    def _ensure_builtin(self) -> str | None:
        """添加新音乐时保证内置音乐不丢失。"""
        playlist = self.data.setdefault("settings", {}).setdefault(
            "music_playlist", []
        )
        builtin = storage.default_music()
        if builtin and str(builtin) not in playlist:
            playlist.insert(0, str(builtin))
            item = QListWidgetItem(builtin.name)
            item.setData(PATH_ROLE, str(builtin))
            self.playlist.insertItem(0, item)
        return str(builtin) if builtin else None

    def _sync_order(self, *args) -> None:
        """拖拽排序后，把新顺序同步到设置并保存。"""
        ordered = []
        for i in range(self.playlist.count()):
            item = self.playlist.item(i)
            if item is not None:
                path = item.data(PATH_ROLE)
                if path:
                    ordered.append(path)
        if ordered:
            self.data.setdefault("settings", {})["music_playlist"] = ordered
            storage.save_data(self.data)

    # ---------- 播放控制 ----------
    def play_current(self, restart: bool = False) -> None:
        path = self._current_path()
        if not path or self._player is None:
            return
        self._reset_progress()
        if restart:
            self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()

    def toggle_play(self) -> None:
        """播放/暂停切换；随机模式下从随机一首开始。"""
        if self._player is None:
            return
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
            return
        if self._mode() == "random" and self.playlist.count() > 0:
            self.playlist.setCurrentRow(random.randrange(self.playlist.count()))
            self.play_current()
            return
        if self._player.source().isEmpty():
            self.play_current()
        else:
            self._player.play()

    def stop(self) -> None:
        if self._player is not None:
            self._player.stop()
            self._reset_progress()

    def prev_track(self) -> None:
        self._step(-1)

    def next_track(self) -> None:
        if self._mode() == "random":
            nxt = self._pick_next(self.playlist.currentRow())
            if nxt >= 0:
                self.playlist.setCurrentRow(nxt)
                self.play_current()
            return
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

    def _mode(self) -> str:
        return self.data.get("settings", {}).get("music_mode", "order")

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
        nxt = current + 1
        return nxt if nxt < count else -1

    # ---------- 添加 / 移除 ----------
    def add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择音频", str(Path.home()), AUDIO_FILTER
        )
        if not paths:
            return
        self._ensure_builtin()  # 内置音乐保留
        playlist = self.data.setdefault("settings", {}).setdefault(
            "music_playlist", []
        )
        for p in paths:
            if p not in playlist:
                playlist.append(p)
                self._append_item(p)
        storage.save_data(self.data)

    def remove_selected(self) -> None:
        row = self.playlist.currentRow()
        if row < 0:
            return
        item = self.playlist.item(row)
        path = item.data(PATH_ROLE) if item is not None else None
        self.playlist.takeItem(row)
        if path:
            playlist = self.data.get("settings", {}).get("music_playlist", [])
            if path in playlist:
                playlist.remove(path)
        storage.save_data(self.data)

    # ---------- 音量 ----------
    def _on_volume(self, value: int) -> None:
        self.volume_label.setText(f"{value}%")
        self.data.setdefault("settings", {})["music_volume"] = value
        storage.save_data(self.data)
        _, output = self.mw._ensure_music_player()
        if output is not None:
            output.setVolume(value / 100.0)

    # ---------- 状态与进度 ----------
    def _on_mode_changed(self, _index=None) -> None:
        self.data.setdefault("settings", {})["music_mode"] = (
            self.mode_combo.currentData() or "order"
        )
        storage.save_data(self.data)
        self._update_toggle_text()
        if self._player is not None and (
            self._player.playbackState() == QMediaPlayer.PlayingState
        ):
            if self._mode() == "single":
                self._loop_timer.start()
            else:
                self._loop_timer.stop()

    def _update_toggle_text(self) -> None:
        if self._player is not None and (
            self._player.playbackState() == QMediaPlayer.PlayingState
        ):
            self.toggle_btn.setText("⏸ 暂停")
        elif self._mode() == "random":
            self.toggle_btn.setText("🔀 随机播放")
        else:
            self.toggle_btn.setText("▶ 播放")

    def _on_position(self, pos: int) -> None:
        self.seek_bar.setValue(pos)
        if pos - self._last_label_ms >= 500 or pos < self._last_label_ms:
            self._last_label_ms = pos
            duration = self.seek_bar.maximum()
            self.time_label.setText(f"{_fmt(pos)} / {_fmt(duration)}")

    def _on_duration(self, duration: int) -> None:
        self.seek_bar.setRange(0, duration)
        if self._player is not None:
            self.time_label.setText(
                f"{_fmt(self._player.position())} / {_fmt(duration)}"
            )

    def _reset_progress(self) -> None:
        self.seek_bar.setValue(0)
        self.time_label.setText("0:00 / 0:00")
        self._last_label_ms = 0

    def _on_state(self, state) -> None:
        if state == QMediaPlayer.PlayingState:
            item = self.playlist.currentItem()
            name = item.text() if item else ""
            self.now_label.setText(f"♪ 正在播放：{name}")
            self.toggle_btn.setText("⏸ 暂停")
            if self._mode() == "single":
                self._loop_timer.start()
            else:
                self._loop_timer.stop()
        elif state == QMediaPlayer.PausedState:
            self._update_toggle_text()
        elif state == QMediaPlayer.StoppedState:
            self.now_label.setText("🎵 未播放")
            self._update_toggle_text()
            self._loop_timer.stop()

    def _check_single_loop(self) -> None:
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
                    self._player.stop()
                    self._player.setSource(QUrl())
                    self._player.setSource(QUrl.fromLocalFile(path))
                    self._player.play()
            elif self._player is not None:
                self._player.stop()
