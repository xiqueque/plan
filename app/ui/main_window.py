"""主窗口：日期显示、计划列表、搜索、设置。"""
from __future__ import annotations

import time
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QUrl, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..core import storage
from .calendar_dialog import CalendarDialog
from .settings_dialog import SettingsDialog
from .task_dialog import TaskDialog

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

    _HAS_QT_MULTIMEDIA = True
except Exception:
    _HAS_QT_MULTIMEDIA = False

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
SOUND_FILE = Path(__file__).resolve().parent.parent / "assets" / "check.wav"
DEFAULT_SOUND_FILE = Path(__file__).resolve().parent.parent / "assets" / "8月7日_裁剪.wav"
BASE_TASK_FONT_PX = 18

APP_QSS = """
QWidget {
    font-family: "幼圆", "Microsoft YaHei", "微软雅黑", sans-serif;
    font-size: 15px;
    color: #1F3A4D;
}
QMainWindow, QWidget#central, QDialog, QMessageBox {
    background: #EAF6FC;
}
QPushButton#dateLabel {
    border: none;
    background: transparent;
    font-size: 20px;
    font-weight: bold;
    text-align: left;
    padding: 0;
}
QPushButton#dateLabel:hover { color: #3B7DBF; }
QPushButton#dateLabel:pressed { color: #1F3A4D; }
QLabel#emptyLabel {
    color: #6B8CA3;
    padding: 24px;
}
QLabel#taskText {
    font-size: 18px;
    font-weight: 600;
}
QLabel#timeLabel {
    font-size: 13px;
    color: #6B8CA3;
}
QLineEdit, QSpinBox {
    background: white;
    border: 1px solid #7FB8D4;
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: #ADD8E6;
}
QPushButton {
    background: #ADD8E6;
    border: 1px solid #7FB8D4;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover { background: #9CCFE0; }
QPushButton:pressed { background: #8BC4D8; }
QPushButton#primary {
    background: #7FB8D4;
    color: white;
    font-weight: bold;
}
QPushButton#primary:hover { background: #6FB1CE; }
QPushButton#smallBtn {
    padding: 3px 6px;
    font-size: 13px;
}
QPushButton#smallDanger {
    padding: 3px 6px;
    font-size: 13px;
    background: #F4C7C3;
    border-color: #D9A29C;
}
QPushButton#smallDanger:hover { background: #EFB4AE; }
QScrollArea { border: none; background: transparent; }
QFrame#taskRow {
    background: white;
    border: 1px solid #D5E8F2;
    border-radius: 8px;
}
"""


class BigCheckBox(QCheckBox):
    """自绘的大号圆角完成勾选框（更醒目、更可爱）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self._hover = False

    def hitButton(self, pos) -> bool:
        """让整个 30x30 区域都可点击（修复只能点中心小范围的问题）。"""
        return self.rect().contains(pos)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = float(self.width())
        h = float(self.height())
        rect = QRectF(1.5, 1.5, w - 3.0, h - 3.0)
        border_color = "#3B7DBF" if self._hover else "#7FB8D4"
        if self.isChecked():
            painter.setPen(QPen(QColor(border_color), 2))
            painter.setBrush(QColor("#7FB8D4"))
        else:
            painter.setPen(QPen(QColor(border_color), 2))
            painter.setBrush(QColor("#FFFFFF"))
        painter.drawRoundedRect(rect, 8, 8)
        if self.isChecked():
            pen = QPen(QColor("#FFFFFF"), max(2.5, w * 0.11))
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(w * 0.24, h * 0.53), QPointF(w * 0.44, h * 0.72)
            )
            painter.drawLine(
                QPointF(w * 0.44, h * 0.72), QPointF(w * 0.76, h * 0.30)
            )
        painter.end()


class AnimatedTextLabel(QLabel):
    """任务文字标签：支持颜色渐变与完成切换小动画。"""

    def __init__(self, text: str, color: str, parent=None):
        super().__init__(text, parent)
        self._cur_color = QColor(color)
        self.setWordWrap(True)
        self.setObjectName("taskText")
        self._apply_color()

    def current_color(self) -> QColor:
        return QColor(self._cur_color)

    def set_animated_color(self, color) -> None:
        self._cur_color = QColor(color)
        self._apply_color()

    def _apply_color(self) -> None:
        self.setStyleSheet(f"color:{self._cur_color.name()}; font-weight:600;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("每日计划")
        self.resize(820, 540)
        self.setMinimumSize(480, 340)

        self.data = storage.load_data()
        removed = storage.run_cleanup(self.data)
        if removed:
            storage.save_data(self.data)

        self.current_date = date.today()
        self.keyword = ""

        self._build_ui()
        self.refresh()

    # ---------- 界面构建 ----------
    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # 顶栏：日期（左上角）+ 日期切换
        top = QHBoxLayout()
        self.date_label = QPushButton()
        self.date_label.setObjectName("dateLabel")
        self.date_label.setToolTip("点击弹出日历，快速跳转日期")
        self.date_label.setCursor(Qt.PointingHandCursor)
        self.date_label.clicked.connect(self.open_calendar)
        top.addWidget(self.date_label)
        top.addStretch(1)
        self.prev_btn = QPushButton("前一天")
        self.today_btn = QPushButton("今天")
        self.next_btn = QPushButton("后一天")
        self.prev_btn.clicked.connect(self.go_prev)
        self.today_btn.clicked.connect(self.go_today)
        self.next_btn.clicked.connect(self.go_next)
        top.addWidget(self.prev_btn)
        top.addWidget(self.today_btn)
        top.addWidget(self.next_btn)
        root.addLayout(top)

        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索计划…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._on_search)
        root.addWidget(self.search_edit)

        # 计划列表（滚动区域）
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch(1)
        self.scroll.setWidget(self.list_container)
        root.addWidget(self.scroll, 1)

        self.empty_label = QLabel()
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setObjectName("emptyLabel")

        # 底部按钮
        bottom = QHBoxLayout()
        self.add_btn = QPushButton("＋ 添加计划")
        self.add_btn.setObjectName("primary")
        self.add_btn.clicked.connect(self.add_task)
        self.screenshot_btn = QPushButton("截图")
        self.screenshot_btn.setToolTip("生成今天的计划截图，保存为图片发送到手机")
        self.screenshot_btn.clicked.connect(self.export_screenshot)
        self.settings_btn = QPushButton("设置")
        self.settings_btn.clicked.connect(self.open_settings)
        bottom.addWidget(self.add_btn, 1)
        bottom.addWidget(self.screenshot_btn)
        bottom.addWidget(self.settings_btn)
        root.addLayout(bottom)

        self.setStyleSheet(APP_QSS)

    # ---------- 刷新列表 ----------
    def refresh(self) -> None:
        self.date_label.setText(self.format_date(self.current_date))
        self._rebuild_list()

    @staticmethod
    def format_date(d: date) -> str:
        return f"{d.year}年{d.month}月{d.day}日 {WEEKDAYS[d.weekday()]}"

    def _rebuild_list(self, keep_scroll: bool = False) -> None:
        scroll_bar = self.scroll.verticalScrollBar()
        old_value = scroll_bar.value() if keep_scroll else 0

        # 清空（保留最后的 stretch）
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        date_str = self.current_date.isoformat()
        tasks = storage.tasks_for_date(self.data, date_str)
        keyword = self.keyword.strip().lower()
        if keyword:
            tasks = [t for t in tasks if keyword in t.get("text", "").lower()]

        if not tasks:
            self.empty_label.setText(
                "没有找到匹配的计划" if keyword else "今天还没有计划，点下方「添加计划」"
            )
            self.list_layout.insertWidget(0, self.empty_label)
        else:
            for task in tasks:
                self.list_layout.insertWidget(
                    self.list_layout.count() - 1, self._make_row(task, date_str)
                )

        if keep_scroll:
            scroll_bar.setValue(old_value)

    # ---------- 列表行 ----------
    def _make_row(self, task: dict, date_str: str) -> QWidget:
        row = QFrame()
        row.setObjectName("taskRow")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(6)

        done = storage.is_done(self.data, task["id"], date_str)
        check = BigCheckBox()
        check.setToolTip("标记完成")
        check.blockSignals(True)
        check.setChecked(done)
        check.blockSignals(False)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        initial_color = "#9AA5AC" if done else (task.get("color") or "#1F3A4D")
        text_label = AnimatedTextLabel(task.get("text", ""), initial_color)
        text_col.addWidget(text_label)
        check.toggled.connect(
            lambda checked, t=task, lbl=text_label: self._on_toggle_done(
                t, date_str, checked, lbl
            )
        )

        time_text = ""
        if task.get("time_start"):
            time_text = task["time_start"]
            if task.get("time_end"):
                time_text += f" – {task['time_end']}"
        if task.get("is_daily"):
            time_text = (time_text + "  ·  " if time_text else "") + "每天"
        if time_text:
            time_label = QLabel(time_text)
            time_label.setObjectName("timeLabel")
            text_col.addWidget(time_label)
        text_col.addStretch(1)

        pin_btn = QPushButton("取消置顶" if task.get("pinned") else "置顶")
        pin_btn.setObjectName("smallBtn")
        pin_btn.clicked.connect(lambda _, t=task: self._on_toggle_pin(t))
        edit_btn = QPushButton("编辑")
        edit_btn.setObjectName("smallBtn")
        edit_btn.clicked.connect(lambda _, t=task: self._edit_task(t))
        del_btn = QPushButton("删除")
        del_btn.setObjectName("smallDanger")
        del_btn.clicked.connect(lambda _, t=task: self._delete_task(t))

        lay.addWidget(check)
        lay.addLayout(text_col, 1)
        lay.addWidget(pin_btn)
        lay.addWidget(edit_btn)
        lay.addWidget(del_btn)

        return row

    # ---------- 操作 ----------
    def _on_toggle_done(
        self, task: dict, date_str: str, checked: bool, text_label: QLabel
    ) -> None:
        storage.set_done(self.data, task["id"], date_str, checked)
        storage.save_data(self.data)
        if checked:
            self._play_check_sound()
        self._animate_task_text(text_label, task, checked)

    def _animate_task_text(
        self, label: AnimatedTextLabel, task: dict, checked: bool
    ) -> None:
        """完成 / 未完成切换：颜色渐变 + 字体轻微弹跳，过渡不生硬。"""
        start = label.current_color()
        end = QColor("#9AA5AC") if checked else QColor(task.get("color") or "#1F3A4D")

        anim = QVariantAnimation(self)
        anim.setDuration(260)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)

        def safe_stop() -> None:
            try:
                anim.stop()
            except RuntimeError:
                pass

        label.destroyed.connect(safe_stop)
        anim.finished.connect(anim.deleteLater)

        def on_value(v: float) -> None:
            try:
                color = QColor(
                    round(start.red() + (end.red() - start.red()) * v),
                    round(start.green() + (end.green() - start.green()) * v),
                    round(start.blue() + (end.blue() - start.blue()) * v),
                )
                label.set_animated_color(color)
                if v < 0.5:
                    size = BASE_TASK_FONT_PX + round(6 * v * 2)
                else:
                    size = BASE_TASK_FONT_PX + round(6 * (1 - (v - 0.5) * 2))
                font = label.font()
                font.setPixelSize(max(12, size))
                label.setFont(font)
            except RuntimeError:
                safe_stop()

        def on_finish() -> None:
            try:
                font = label.font()
                font.setPixelSize(BASE_TASK_FONT_PX)
                label.setFont(font)
                label.set_animated_color(end)
                if checked:
                    label.setStyleSheet(
                        "color:#9AA5AC; text-decoration: line-through; font-weight:600;"
                    )
            except RuntimeError:
                pass

        anim.valueChanged.connect(on_value)
        anim.finished.connect(on_finish)
        anim.start()

    def _play_check_sound(self) -> None:
        self._play_sound_file()

    def _play_sound_file(self, path: str = "", volume: int | None = None) -> None:
        """播放音效：优先设置中的音频，其次默认音频（Music 文件夹），最后内置音效。"""
        path = (path or "").strip()
        if not path:
            path = self.data.get("settings", {}).get("sound_file", "") or ""
        if not path or not Path(path).exists():
            if DEFAULT_SOUND_FILE.exists():
                path = str(DEFAULT_SOUND_FILE)
        if not path or not Path(path).exists():
            path = str(SOUND_FILE)
        if not Path(path).exists():
            return

        if volume is None:
            try:
                volume = int(self.data.get("settings", {}).get("sound_volume", 12))
            except (TypeError, ValueError):
                volume = 12
        volume = max(0, min(100, volume))

        # 首选 Qt 多媒体（支持 wav / mp3）
        if _HAS_QT_MULTIMEDIA:
            try:
                self._ensure_player()
                self._audio_output.setVolume(volume / 100.0)
                self._player.stop()
                self._player.setSource(QUrl.fromLocalFile(path))
                self._player.play()
                return
            except Exception:
                pass

        # 备用 1：wav 用系统播放
        try:
            import winsound

            if path.lower().endswith(".wav"):
                winsound.PlaySound(
                    path,
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
                )
                return
        except Exception:
            pass

        # 备用 2：其他格式尝试系统 MCI 播放
        try:
            import ctypes

            winmm = ctypes.windll.winmm
            alias = "dailyplan_sound"
            winmm.mciSendStringW("close " + alias, None, 0, None)
            winmm.mciSendStringW(f'open "{path}" alias {alias}', None, 0, None)
            winmm.mciSendStringW(
                f"setaudio {alias} volume to {volume * 10}", None, 0, None
            )
            winmm.mciSendStringW("play " + alias, None, 0, None)
        except Exception:
            pass

    def _ensure_player(self) -> None:
        if getattr(self, "_player", None) is None:
            self._player = QMediaPlayer(self)
            self._audio_output = QAudioOutput(self)
            self._audio_output.setVolume(1.0)
            self._player.setAudioOutput(self._audio_output)

    def _on_toggle_pin(self, task: dict) -> None:
        task["pinned"] = not task.get("pinned")
        task["pinned_at"] = time.time() if task["pinned"] else None
        storage.save_data(self.data)
        self._rebuild_list()

    def add_task(self) -> None:
        dialog = TaskDialog(self)
        if dialog.exec() != TaskDialog.Accepted:
            return
        text, start, end, is_daily = dialog.values()
        if not text:
            return
        task = storage.new_task(
            text, self.current_date.isoformat(), start, end, is_daily, dialog.selected_color()
        )
        self.data["tasks"].append(task)
        storage.save_data(self.data)
        self._rebuild_list()

    def _edit_task(self, task: dict) -> None:
        dialog = TaskDialog(self, task)
        if dialog.exec() != TaskDialog.Accepted:
            return
        text, start, end, is_daily = dialog.values()
        if not text:
            return
        task["text"] = text
        task["time_start"] = start
        task["time_end"] = end
        task["is_daily"] = is_daily
        task["color"] = dialog.selected_color()
        storage.save_data(self.data)
        self._rebuild_list()

    def _delete_task(self, task: dict) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("删除计划")
        box.setIcon(QMessageBox.Question)
        box.setText(f"确定删除「{task.get('text', '')}」吗？")
        yes_btn = box.addButton("删除", QMessageBox.DestructiveRole)
        box.addButton("取消", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is not yes_btn:
            return
        self.data["tasks"] = [t for t in self.data["tasks"] if t.get("id") != task.get("id")]
        storage.save_data(self.data)
        self._rebuild_list()

    def go_prev(self) -> None:
        self.current_date -= timedelta(days=1)
        self.refresh()

    def go_next(self) -> None:
        self.current_date += timedelta(days=1)
        self.refresh()

    def go_today(self) -> None:
        self.current_date = date.today()
        self.refresh()

    def open_calendar(self) -> None:
        dialog = CalendarDialog(self, self.current_date)
        if dialog.exec() == CalendarDialog.Accepted:
            selected = dialog.selected_date()
            if selected != self.current_date:
                self.current_date = selected
                self.refresh()

    def _on_search(self, text: str) -> None:
        self.keyword = text
        self._rebuild_list()

    def open_settings(self) -> None:
        settings = self.data["settings"]
        dialog = SettingsDialog(
            self,
            settings.get("cleanup_days", 15),
            settings.get("sound_file", ""),
            settings.get("sound_volume", 12),
            DEFAULT_SOUND_FILE.name if DEFAULT_SOUND_FILE.exists() else "",
            self._play_sound_file,
        )
        if dialog.exec() != SettingsDialog.Accepted:
            return
        settings["cleanup_days"] = dialog.cleanup_days()
        settings["sound_file"] = dialog.sound_path()
        settings["sound_volume"] = dialog.sound_volume()
        storage.save_data(self.data)
        removed = storage.run_cleanup(self.data)
        if removed:
            storage.save_data(self.data)
            QMessageBox.information(self, "清理完成", f"已自动清理 {removed} 条过期计划。")
        self._rebuild_list()

    # ---------- 截图导出 ----------
    def export_screenshot(self) -> None:
        date_str = self.current_date.isoformat()
        tasks = storage.tasks_for_date(self.data, date_str)
        if not tasks:
            QMessageBox.information(self, "截图", "这一天还没有计划，先添加几条再截图吧。")
            return

        widget = self._build_export_widget(date_str, tasks)
        widget.setMinimumWidth(560)
        widget.adjustSize()
        pixmap = widget.grab()

        default_name = f"每日计划_{date_str}.png"
        path, _ = QFileDialog.getSaveFileName(
            self, "保存每日计划截图", str(Path.home() / default_name), "PNG 图片 (*.png)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        if pixmap.save(path, "PNG"):
            QMessageBox.information(self, "截图", f"截图已保存：\n{path}")
        else:
            QMessageBox.warning(self, "截图", "保存失败，请换个位置再试。")

    def _build_export_widget(self, date_str: str, tasks: list) -> QWidget:
        """生成一张干净的计划卡片（不含按钮，方便发手机查看）。"""
        widget = QWidget()
        widget.setStyleSheet("background:#EAF6FC;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)

        header = QLabel(f"每日计划 · {self.format_date(self.current_date)}")
        header.setStyleSheet(
            "font-family:'幼圆','Microsoft YaHei'; font-size:22px; font-weight:bold; "
            "color:#1F3A4D;"
        )
        layout.addWidget(header)

        for task in tasks:
            layout.addWidget(self._make_export_row(task, date_str))
        return widget

    def _make_export_row(self, task: dict, date_str: str) -> QFrame:
        row = QFrame()
        row.setStyleSheet(
            "QFrame { background:white; border:1px solid #D5E8F2; border-radius:10px; }"
        )
        lay = QHBoxLayout(row)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(8)

        done = storage.is_done(self.data, task["id"], date_str)
        color = "#9AA5AC" if done else (task.get("color") or "#1F3A4D")
        text = QLabel(task.get("text", ""))
        deco = " text-decoration: line-through;" if done else ""
        text.setStyleSheet(
            f"font-family:'幼圆','Microsoft YaHei'; font-size:18px; font-weight:600; "
            f"color:{color};{deco}"
        )
        lay.addWidget(text, 1)

        extra = []
        if task.get("time_start"):
            t = task["time_start"]
            if task.get("time_end"):
                t += f"–{task['time_end']}"
            extra.append(t)
        if task.get("is_daily"):
            extra.append("每天")
        if task.get("pinned"):
            extra.append("置顶")
        if extra:
            tag = QLabel("  ".join(extra))
            tag.setStyleSheet(
                "font-family:'幼圆','Microsoft YaHei'; font-size:14px; color:#6B8CA3;"
            )
            lay.addWidget(tag)
        return row
