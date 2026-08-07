"""主窗口：日期显示、计划列表、搜索、设置。"""
from __future__ import annotations

import time
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, QUrl, QVariantAnimation
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from ..core import autostart, storage, theme
from ..core.reminder import ReminderScheduler
from .calendar_dialog import CalendarDialog
from .reminder_popup import ReminderPopup
from .settings_dialog import SettingsDialog
from .style import build_main_qss
from .task_dialog import TaskDialog
from .thumb import IMAGE_FILTER, ThumbButton

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

    _HAS_QT_MULTIMEDIA = True
except Exception:
    _HAS_QT_MULTIMEDIA = False

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
SOUND_FILE = Path(__file__).resolve().parent.parent / "assets" / "check.wav"
DEFAULT_SOUND_FILE = Path(__file__).resolve().parent.parent / "assets" / "8月7日_裁剪.wav"
BASE_TASK_FONT_PX = 18
APP_ICON = Path(__file__).resolve().parent.parent / "assets" / "app_icon.ico"


class BigCheckBox(QCheckBox):
    """自绘的大号圆角完成勾选框（更醒目、更可爱）。"""

    def __init__(self, parent=None, size: int = 36):
        super().__init__(parent)
        self.setFixedSize(size, size)
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


class PinIcon(QWidget):
    """柔和的置顶图钉小图标（淡蓝色，不刺眼）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 26)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = float(self.width())
        h = float(self.height())
        color = QColor("#8FB8D4")

        # 针
        pen = QPen(color, max(1.5, w * 0.09))
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(QPointF(w * 0.5, h * 0.62), QPointF(w * 0.5, h * 0.95))

        # 大头
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QRectF(w * 0.12, h * 0.12, w * 0.76, w * 0.76))

        # 顶部小钮
        painter.drawRoundedRect(QRectF(w * 0.36, 0, w * 0.28, h * 0.20), 2, 2)
        painter.end()


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

        self._themes = theme.load_themes()
        self.theme = theme.get_theme(self.data["settings"], self._themes)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_offset = None
        self._quitting = False
        self._tray_hint_shown = False
        self._mini_mode = False
        self._full_geometry = None
        self._full_central = None

        self._build_ui()
        self.refresh()

        # 提醒调度
        self._popups = []
        self._scheduler = ReminderScheduler(self)
        self._scheduler.reminderReady.connect(self._on_reminder)
        self._scheduler.set_data(self.data)
        self._scheduler.check()
        self._warm_up_audio()
        self._setup_tray()

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
        self.min_btn = QPushButton("—")
        self.min_btn.setObjectName("winBtn")
        self.min_btn.setToolTip("最小化到托盘")
        self.min_btn.setToolTip("最小化（可设置收托盘）")
        self.min_btn.clicked.connect(self._on_minimize)
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("winClose")
        self.close_btn.setToolTip("关闭（可设置直接退出）")
        self.close_btn.clicked.connect(self._on_close)
        top.addWidget(self.min_btn)
        top.addWidget(self.close_btn)
        root.addLayout(top)

        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索计划…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._on_search)
        root.addWidget(self.search_edit)

        # 独立图片区
        img_header = QHBoxLayout()
        self.img_toggle_btn = QPushButton("▸ 图片")
        self.img_toggle_btn.setObjectName("smallBtn")
        self.img_toggle_btn.setCheckable(True)
        self.img_toggle_btn.clicked.connect(self._toggle_images)
        self.img_count_label = QLabel("0 张")
        self.img_count_label.setStyleSheet("color:#6B8CA3; font-size:13px;")
        img_add = QPushButton("＋ 添加图片")
        img_add.setObjectName("smallBtn")
        img_add.clicked.connect(self.add_day_images)
        img_header.addWidget(self.img_toggle_btn)
        img_header.addWidget(self.img_count_label)
        img_header.addStretch(1)
        img_header.addWidget(img_add)
        root.addLayout(img_header)

        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_scroll.setFixedHeight(120)
        self.image_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_container = QWidget()
        self.image_layout = QHBoxLayout(self.image_container)
        self.image_layout.setContentsMargins(0, 0, 0, 0)
        self.image_layout.setSpacing(6)
        self.image_layout.addStretch(1)
        self.image_scroll.setWidget(self.image_container)
        self.image_scroll.hide()  # 默认折叠，只留一行
        root.addWidget(self.image_scroll)

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
        bottom.addWidget(QSizeGrip(self), 0, Qt.AlignBottom | Qt.AlignRight)
        root.addLayout(bottom)

        self.setStyleSheet(build_main_qss(self.theme))

    # ---------- 刷新列表 ----------
    def refresh(self) -> None:
        self.date_label.setText(self.format_date(self.current_date))
        self._rebuild_list()
        self._refresh_images()

    # ---------- 窗口与托盘 ----------
    def _setup_tray(self) -> None:
        self._tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        tray = QSystemTrayIcon(self)
        if APP_ICON.exists():
            tray.setIcon(QIcon(str(APP_ICON)))
        menu = QMenu(self)
        act_show = menu.addAction("显示每日计划")
        act_show.triggered.connect(self._show_from_tray)
        menu.addSeparator()
        act_quit = menu.addAction("退出")
        act_quit.triggered.connect(self._quit)
        tray.setContextMenu(menu)
        tray.activated.connect(self._tray_activated)
        tray.show()
        self._tray = tray

    def _tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self._show_from_tray()

    def _show_from_tray(self) -> None:
        if self._mini_mode:
            self._exit_mini_mode()
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_minimize(self) -> None:
        action = self.data.get("settings", {}).get("minimize_action", "mini")
        if action == "mini":
            self._enter_mini_mode()
        else:
            self._hide_to_tray()

    def _on_close(self) -> None:
        action = self.data.get("settings", {}).get("close_action", "tray")
        if action == "quit":
            self._quit()
        else:
            self._hide_to_tray()

    def _enter_mini_mode(self) -> None:
        if self._mini_mode:
            return
        self._full_central = self.takeCentralWidget()
        self._full_geometry = self.geometry()
        self._mini_mode = True
        self.setCentralWidget(self._build_mini_widget())
        screen = self.screen() or QGuiApplication.primaryScreen()
        geo = None
        if screen is not None:
            try:
                geo = screen.availableGeometry()
            except AttributeError:
                geo = None
        self.setMinimumSize(260, 180)
        self.resize(320, 240)
        if geo is not None:
            self.move(geo.right() - self.width() - 24, geo.top() + 24)
        self.setWindowFlag(Qt.Tool, True)  # 迷你窗口不显示在任务栏
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)  # 迷你窗口不置顶，降低存在感
        self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)  # 点击不激活、不跳到最前
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.show()
        self._force_not_topmost()
        # 沉到其他窗口后面：迷你窗口永不抢在最前
        self.lower()
        QTimer.singleShot(0, self.lower)

    def _exit_mini_mode(self) -> None:
        if not self._mini_mode:
            return
        mini = self.takeCentralWidget()
        if mini is not None:
            mini.deleteLater()
        self.setCentralWidget(self._full_central)
        self.setWindowOpacity(1.0)
        self.setMinimumSize(480, 340)
        self.setWindowFlag(Qt.Tool, False)
        self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, False)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self._full_topmost())
        if self._full_geometry is not None:
            self.setGeometry(self._full_geometry)
        self._mini_mode = False
        # 展开时不抢焦点、不跳到最前
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.show()
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        if self._full_topmost():
            self._force_topmost()

    def _build_mini_widget(self) -> QWidget:
        """桌面右上角的半透明迷你窗口内容。"""
        widget = QWidget()
        widget.setObjectName("central")
        widget.setStyleSheet(self._mini_bg_qss())
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        date_col = QVBoxLayout()
        date_col.setSpacing(0)
        big_date = QLabel(
            f"{self.current_date.month}月{self.current_date.day}日"
        )
        big_date.setStyleSheet(
            f"font-size:30px; font-weight:bold; color:{self.theme.text};"
        )
        sub_date = QLabel(
            f"{self.current_date.year}年 · {WEEKDAYS[self.current_date.weekday()]}"
        )
        sub_date.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{self.theme.hint};"
        )
        date_col.addWidget(big_date)
        date_col.addWidget(sub_date)
        header.addLayout(date_col)
        header.addStretch(1)
        self.mini_pin_btn = QPushButton("…")
        self.mini_pin_btn.setObjectName("winBtn")
        self.mini_pin_btn.setToolTip("固定（置顶）")
        self.mini_pin_btn.clicked.connect(self._toggle_mini_pin)
        header.addWidget(self.mini_pin_btn, 0, Qt.AlignTop)
        self._update_mini_pin_style()
        expand_btn = QPushButton("↗ 展开")
        expand_btn.setObjectName("smallBtn")
        expand_btn.clicked.connect(self._exit_mini_mode)
        header.addWidget(expand_btn, 0, Qt.AlignTop)
        layout.addLayout(header)

        self._mini_scroll = QScrollArea()
        self._mini_scroll.setWidgetResizable(True)
        self._mini_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._mini_tasks_container = QWidget()
        self._mini_tasks_grid = QGridLayout(self._mini_tasks_container)
        self._mini_tasks_grid.setContentsMargins(2, 2, 2, 2)
        self._mini_tasks_grid.setHorizontalSpacing(8)
        self._mini_tasks_grid.setVerticalSpacing(6)
        self._mini_scroll.setWidget(self._mini_tasks_container)
        layout.addWidget(self._mini_scroll, 1)
        self._refresh_mini_tasks()

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(QSizeGrip(self), 0, Qt.AlignBottom | Qt.AlignRight)
        layout.addLayout(bottom)
        return widget

    def _mini_bg_qss(self) -> str:
        """迷你窗口半透明背景：只影响背景，不影响文字与按钮。"""
        try:
            opacity = int(self.data.get("settings", {}).get("mini_opacity", 80))
        except (TypeError, ValueError):
            opacity = 80
        opacity = max(30, min(100, opacity))
        alpha = round(255 * opacity / 100)
        bg = QColor(self.theme.bg)
        return (
            f"QWidget#central {{ background: rgba({bg.red()},{bg.green()},"
            f"{bg.blue()},{alpha}); border: 2px solid {self.theme.border}; "
            "border-radius: 16px; }"
        )

    def _refresh_mini_tasks(self) -> None:
        while self._mini_tasks_grid.count():
            item = self._mini_tasks_grid.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()

        date_str = self.current_date.isoformat()
        tasks = storage.tasks_for_date(self.data, date_str)
        if not tasks:
            hint = QLabel("今日暂无计划")
            hint.setStyleSheet(f"color:{self.theme.hint}; padding:10px;")
            self._mini_tasks_grid.addWidget(hint, 0, 0, 1, 2)
            return
        for i, task in enumerate(tasks):
            self._mini_tasks_grid.addWidget(
                self._make_mini_task_cell(task, date_str), i // 2, i % 2
            )
        self._mini_tasks_grid.setColumnStretch(0, 1)
        self._mini_tasks_grid.setColumnStretch(1, 1)

    def _make_mini_task_cell(self, task: dict, date_str: str) -> QWidget:
        cell = QWidget()
        vbox = QVBoxLayout(cell)
        vbox.setContentsMargins(4, 4, 4, 4)
        vbox.setSpacing(2)

        done = storage.is_done(self.data, task["id"], date_str)
        color = "#9AA5AC" if done else (task.get("color") or self.theme.text)
        deco = " text-decoration: line-through;" if done else ""
        mark = "✓ " if done else "□ "
        label = QLabel(mark + task.get("text", ""))
        label.setWordWrap(True)
        label.setStyleSheet(
            f"font-size:16px; font-weight:bold; color:{color};{deco}"
        )
        vbox.addWidget(label)
        time_text = ""
        if task.get("time_start"):
            time_text = task["time_start"]
            if task.get("time_end"):
                time_text += f" – {task['time_end']}"
        if time_text:
            time_label = QLabel(time_text)
            time_label.setStyleSheet("color:#A8B4BF; font-size:12px;")
            vbox.addWidget(time_label)
        vbox.addStretch(1)
        return cell

    def _full_topmost(self) -> bool:
        return bool(self.data.get("settings", {}).get("topmost", False))

    def _force_not_topmost(self) -> None:
        """用系统 API 强制解除置顶，防止 Windows 残留置顶状态。"""
        try:
            import ctypes

            hwnd = int(self.winId())
            HWND_NOTOPMOST = -2
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOACTIVATE = 0x0010
            ctypes.windll.user32.SetWindowPos(
                ctypes.c_void_p(hwnd),
                ctypes.c_void_p(HWND_NOTOPMOST),
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
            )
        except Exception:
            pass

    def _force_topmost(self) -> None:
        """展开后若开启了「总在最前」，用系统 API 确保真正置顶。"""
        try:
            import ctypes

            hwnd = int(self.winId())
            HWND_TOPMOST = -1
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOACTIVATE = 0x0010
            ctypes.windll.user32.SetWindowPos(
                ctypes.c_void_p(hwnd),
                ctypes.c_void_p(HWND_TOPMOST),
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
            )
        except Exception:
            pass

    def _mini_pinned(self) -> bool:
        return bool(self.data.get("settings", {}).get("mini_pinned", False))

    def _toggle_mini_pin(self) -> None:
        settings = self.data.setdefault("settings", {})
        settings["mini_pinned"] = not settings.get("mini_pinned", False)
        storage.save_data(self.data)
        self._update_mini_pin_style()

    def _update_mini_pin_style(self) -> None:
        pinned = self._mini_pinned()
        self.mini_pin_btn.setToolTip("取消固定" if pinned else "固定（不可拖动）")
        if pinned:
            self.mini_pin_btn.setStyleSheet(
                f"QPushButton {{ background:{self.theme.button}; "
                f"border:1px solid {self.theme.border}; border-radius:6px; "
                "padding:2px 8px; font-size:15px; }"
            )
        else:
            self.mini_pin_btn.setStyleSheet("")

    def _hide_to_tray(self) -> None:
        self.hide()
        if self._tray and not self._tray_hint_shown:
            self._tray_hint_shown = True
            self._tray.showMessage(
                "每日计划",
                "已最小化到托盘，提醒功能继续运行。",
                QSystemTrayIcon.NoIcon,
                2500,
            )

    def _show_msg(self, title: str, text: str) -> None:
        """无系统提示音的弹窗。"""
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(QMessageBox.NoIcon)
        box.addButton("好的", QMessageBox.AcceptRole)
        box.exec()

    def _quit(self) -> None:
        self._quitting = True
        if self._tray:
            self._tray.hide()
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self._quitting:
            event.accept()
            return
        event.ignore()
        action = self.data.get("settings", {}).get("close_action", "tray")
        if action == "quit":
            self._quit()
        else:
            self._hide_to_tray()

    def mousePressEvent(self, event):
        if self._mini_mode and self._mini_pinned():
            # 固定状态：锁定位置，不可拖动
            super().mousePressEvent(event)
            return
        if event.button() == Qt.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)

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
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()

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
        text_line = QHBoxLayout()
        text_line.setSpacing(4)
        text_line.addWidget(text_label, 1)
        if task.get("pinned"):
            pin_icon = PinIcon()
            pin_icon.setToolTip("已置顶")
            text_line.addWidget(pin_icon, 0, Qt.AlignTop)
        text_col.addLayout(text_line)
        check.toggled.connect(
            lambda checked, t=task, lbl=text_label, ck=check: self._on_toggle_done(
                t, date_str, checked, lbl, ck
            )
        )

        time_text = ""
        if task.get("time_start"):
            time_text = task["time_start"]
            if task.get("time_end"):
                time_text += f" – {task['time_end']}"
        if task.get("is_daily"):
            time_text = (time_text + "  ·  " if time_text else "") + "每天"
        if task.get("reminder_time"):
            time_text += ("  ·  " if time_text else "") + "提醒 " + task["reminder_time"]
            time_text += storage.format_weekdays(task.get("reminder_weekdays"))
        if task.get("images"):
            time_text += ("  ·  " if time_text else "") + f"图片 {len(task['images'])}"
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
        self,
        task: dict,
        date_str: str,
        checked: bool,
        text_label: QLabel,
        check_widget,
    ) -> None:
        if checked and not self._confirm_complete():
            # 用户反悔：恢复未勾选状态
            check_widget.blockSignals(True)
            check_widget.setChecked(False)
            check_widget.blockSignals(False)
            return
        storage.set_done(self.data, task["id"], date_str, checked)
        storage.save_data(self.data)
        if checked:
            self._play_check_sound()
            self._show_completion_message()
        self._animate_task_text(text_label, task, checked)

    def _confirm_complete(self) -> bool:
        box = QMessageBox(self)
        box.setWindowTitle("完成任务")
        box.setIcon(QMessageBox.NoIcon)
        box.setText("你确定完成任务了吗( •̀ ω •́ )✧")
        box.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        yes_btn = box.addButton("确定(●'◡'●)", QMessageBox.AcceptRole)
        box.addButton("我再想想¯\\_(ツ)_/¯", QMessageBox.RejectRole)
        box.exec()
        return box.clickedButton() is yes_btn

    def _show_completion_message(self) -> None:
        message = self.data.get("settings", {}).get(
            "complete_message", "终于完成任务了耶o(*≧▽≦)ツ┏━┓！！！"
        )
        box = QMessageBox(self)
        box.setWindowTitle("太棒了")
        box.setIcon(QMessageBox.NoIcon)
        box.setText(message)
        box.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        box.addButton("好的！", QMessageBox.AcceptRole)
        box.exec()

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
            path = self._resolve_sound_path()
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

    def _resolve_sound_path(self) -> str:
        path = self.data.get("settings", {}).get("sound_file", "") or ""
        if not path or not Path(path).exists():
            if DEFAULT_SOUND_FILE.exists():
                path = str(DEFAULT_SOUND_FILE)
        if not path or not Path(path).exists():
            path = str(SOUND_FILE)
        return path

    def _warm_up_audio(self) -> None:
        """启动时预热播放器，避免第一次点击勾选框时音效延迟。"""
        if not _HAS_QT_MULTIMEDIA:
            return
        try:
            self._ensure_player()
            self._player.setSource(QUrl.fromLocalFile(self._resolve_sound_path()))
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
        text, start, end, is_daily, mode, remind_time, weekdays = dialog.values()
        if not text:
            return
        images = dialog.images()
        task = storage.new_task(
            text,
            self.current_date.isoformat(),
            start,
            end,
            is_daily,
            dialog.selected_color(),
            mode,
            remind_time,
            weekdays,
            images,
        )
        self.data["tasks"].append(task)
        storage.save_data(self.data)
        self._rebuild_list()

    def _edit_task(self, task: dict) -> None:
        dialog = TaskDialog(self, task)
        if dialog.exec() != TaskDialog.Accepted:
            return
        text, start, end, is_daily, mode, remind_time, weekdays = dialog.values()
        if not text:
            return
        task["text"] = text
        task["time_start"] = start
        task["time_end"] = end
        task["is_daily"] = is_daily
        task["reminder_mode"] = mode
        task["reminder_time"] = remind_time
        task["reminder_weekdays"] = weekdays
        task["images"] = dialog.images()
        task["color"] = dialog.selected_color()
        storage.save_data(self.data)
        self._rebuild_list()

    def _on_reminder(self, task: dict) -> None:
        storage.save_data(self.data)  # 保存已提醒记录，防止重复
        self._show_reminder_popup(task)

    def _show_reminder_popup(self, task: dict) -> None:
        popup = ReminderPopup(task)
        popup.closed.connect(lambda: self._popup_closed(popup))
        self._popups.append(popup)

        screen = self.screen() or QGuiApplication.primaryScreen()
        geo = None
        if screen is not None:
            try:
                geo = screen.availableGeometry()
            except AttributeError:
                geo = None
        margin = 16
        index = len(self._popups) - 1
        if geo is not None:
            x = geo.right() - popup.width() - margin
            y = geo.bottom() - (index + 1) * (popup.height() + 10) - margin
            popup.move(max(geo.left() + margin, x), max(geo.top() + margin, y))
        popup.show()
        popup.slide_in()
        self._play_sound_file()

    def _popup_closed(self, popup) -> None:
        if popup in self._popups:
            self._popups.remove(popup)

    def _delete_task(self, task: dict) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("删除计划")
        box.setIcon(QMessageBox.NoIcon)
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

    # ---------- 独立图片区 ----------
    def _refresh_images(self) -> None:
        while self.image_layout.count() > 1:
            item = self.image_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()

        entries = self._day_image_entries(self.current_date.isoformat())
        self.img_count_label.setText(f"{len(entries)} 张")
        if not entries:
            hint = QLabel("暂无图片，点右上角「添加图片」可放课程表等图片")
            hint.setStyleSheet("color:#6B8CA3; padding:8px;")
            self.image_layout.insertWidget(0, hint)
            return
        for name, source in entries:
            path = storage.image_path(name)
            if not path.exists():
                continue
            display = self.data.get("image_names", {}).get(name, name)
            deletable = source in ("day", "daily")
            markable = source in ("day", "daily")
            marked = bool(self.data.get("image_daily", {}).get(name))
            thumb = ThumbButton(
                path,
                display_name=display,
                show_delete=deletable,
                marked=marked,
                mark_enabled=markable,
            )
            thumb.deleted.connect(
                lambda _n, short=name: self._delete_day_image(short)
            )
            thumb.renamed.connect(
                lambda _n, new, short=name: self._rename_day_image(short, new)
            )
            thumb.mark_toggled.connect(
                lambda _n, short=name: self._toggle_daily_image(short)
            )
            self.image_layout.insertWidget(self.image_layout.count() - 1, thumb)

    def _day_image_entries(self, date_str: str) -> list:
        """某天图片区的条目：当天图片 + 每日标记图片 + 每天任务附带的图片。"""
        entries = []
        seen = set()
        day = self.data.get("day_images", {}).get(date_str, [])
        for name in day:
            if name not in seen and storage.image_path(name).exists():
                seen.add(name)
                entries.append((name, "day"))
        for name, flag in self.data.get("image_daily", {}).items():
            if flag and name not in seen and storage.image_path(name).exists():
                seen.add(name)
                entries.append((name, "daily"))
        for task in self.data.get("tasks", []):
            if task.get("is_daily"):
                for name in task.get("images") or []:
                    if name not in seen and storage.image_path(name).exists():
                        seen.add(name)
                        entries.append((name, "task"))
        return entries

    def _toggle_images(self) -> None:
        show = self.img_toggle_btn.isChecked()
        self.image_scroll.setVisible(show)
        self.img_toggle_btn.setText("▾ 图片" if show else "▸ 图片")

    def add_day_images(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", str(Path.home()), IMAGE_FILTER
        )
        if not paths:
            return
        date_str = self.current_date.isoformat()
        day = self.data.setdefault("day_images", {}).setdefault(date_str, [])
        for p in paths:
            name = storage.import_image(p)
            if name:
                day.append(name)
        storage.save_data(self.data)
        self._refresh_images()

    def _delete_day_image(self, name: str) -> None:
        # 从所有日期的图片区移除该图片
        for day in self.data.get("day_images", {}).values():
            if name in day:
                day.remove(name)
        self.data.get("image_daily", {}).pop(name, None)
        storage.forget_image_display(name)
        if name not in storage.referenced_image_names(self.data):
            storage.delete_image_file(name)
        storage.save_data(self.data)
        self._refresh_images()

    def _toggle_daily_image(self, name: str) -> None:
        daily = self.data.setdefault("image_daily", {})
        daily[name] = not daily.get(name)
        storage.save_data(self.data)
        self._refresh_images()

    def _rename_day_image(self, name: str, display: str) -> None:
        self.data.setdefault("image_names", {})[name] = display
        storage.save_data(self.data)
        self._refresh_images()

    def open_settings(self) -> None:
        settings = self.data["settings"]
        dialog = SettingsDialog(
            self,
            settings.get("cleanup_days", 15),
            settings.get("sound_file", ""),
            settings.get("sound_volume", 12),
            DEFAULT_SOUND_FILE.name if DEFAULT_SOUND_FILE.exists() else "",
            autostart.is_enabled(),
            settings.get("image_viewer", ""),
            [(t.id, t.name) for t in self._themes.values()],
            settings.get("theme", theme.DEFAULT_THEME_ID),
            bool(settings.get("topmost", False)),
            settings.get("minimize_action", "mini"),
            settings.get("close_action", "tray"),
            settings.get("mini_opacity", 80),
            settings.get("complete_message", ""),
            self._play_sound_file,
        )
        if dialog.exec() != SettingsDialog.Accepted:
            return
        (
            days,
            sound_path,
            volume,
            start_on_boot,
            image_viewer,
            theme_id,
            topmost,
            minimize_action,
            close_action,
            mini_opacity,
            complete_message,
        ) = dialog.values()
        settings["cleanup_days"] = days
        settings["sound_file"] = sound_path
        settings["sound_volume"] = volume
        settings["image_viewer"] = image_viewer
        settings["theme"] = theme_id
        settings["topmost"] = topmost
        settings["minimize_action"] = minimize_action
        settings["close_action"] = close_action
        settings["mini_opacity"] = mini_opacity
        settings["complete_message"] = complete_message
        storage.save_data(self.data)
        try:
            if start_on_boot:
                autostart.enable()
            else:
                autostart.disable()
        except OSError:
            self._show_msg("开机自启", "设置开机自启动失败，请稍后重试。")
        # 应用主题与总在最前
        self.theme = theme.get_theme(settings, self._themes)
        self.setStyleSheet(build_main_qss(self.theme))
        self.setWindowFlag(Qt.WindowStaysOnTopHint, topmost)
        self.show()
        if topmost:
            self._force_topmost()
        removed = storage.run_cleanup(self.data)
        if removed:
            storage.save_data(self.data)
            self._show_msg("清理完成", f"已自动清理 {removed} 条过期计划。")
        self._rebuild_list()

    # ---------- 截图导出 ----------
    def export_screenshot(self) -> None:
        date_str = self.current_date.isoformat()
        tasks = storage.tasks_for_date(self.data, date_str)
        if not tasks:
            self._show_msg("截图", "这一天还没有计划，先添加几条再截图吧。")
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
            self._show_msg("截图", f"截图已保存：\n{path}")
        else:
            self._show_msg("截图", "保存失败，请换个位置再试。")

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
        if task.get("reminder_time"):
            extra.append(
                "提醒 "
                + task["reminder_time"]
                + storage.format_weekdays(task.get("reminder_weekdays"))
            )
        if task.get("images"):
            extra.append(f"图片{len(task['images'])}")
        if task.get("pinned"):
            extra.append("置顶")
        if extra:
            tag = QLabel("  ".join(extra))
            tag.setStyleSheet(
                "font-family:'幼圆','Microsoft YaHei'; font-size:14px; color:#6B8CA3;"
            )
            lay.addWidget(tag)
        return row
