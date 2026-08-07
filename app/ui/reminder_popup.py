"""右下角提醒弹窗：滑入动画、自动消失、点击关闭。"""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

DISPLAY_MS = 8000


class ReminderPopup(QWidget):
    """屏幕右下角的小提醒弹窗。"""

    closed = Signal()

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(340, 130)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName("reminderCard")
        card.setStyleSheet(
            "QFrame#reminderCard { background:#FFFFFF; border:2px solid #7FB8D4; "
            "border-radius:14px; }"
        )
        root.addWidget(card)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)

        top = QHBoxLayout()
        title = QLabel("⏰ 提醒")
        title.setStyleSheet("font-size:14px; color:#3B7DBF; font-weight:bold;")
        time_label = QLabel(task.get("reminder_time") or "")
        time_label.setStyleSheet("font-size:13px; color:#6B8CA3;")
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(time_label)
        lay.addLayout(top)

        text = QLabel(task.get("text", ""))
        text.setWordWrap(True)
        color = task.get("color") or "#1F3A4D"
        text.setStyleSheet(
            f"font-size:16px; font-weight:600; color:{color};"
        )
        lay.addWidget(text, 1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        ok_btn = QPushButton("知道了")
        ok_btn.setStyleSheet(
            "QPushButton { background:#ADD8E6; border:1px solid #7FB8D4; "
            "border-radius:8px; padding:5px 16px; font-size:13px; }"
            "QPushButton:hover { background:#9CCFE0; }"
        )
        ok_btn.clicked.connect(self.close)
        bottom.addWidget(ok_btn)
        lay.addLayout(bottom)

        self._fade_effect = None

    def slide_in(self) -> None:
        """从屏幕右侧滑入到当前位置。"""
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return
        start_x = screen.availableGeometry().right()
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(300)
        anim.setStartValue(QPoint(start_x, self.y()))
        anim.setEndValue(QPoint(self.x(), self.y()))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        QTimer.singleShot(DISPLAY_MS, self, self._start_fade)

    def _start_fade(self) -> None:
        self._fade_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._fade_effect)
        anim = QPropertyAnimation(self._fade_effect, b"opacity", self)
        anim.setDuration(350)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.finished.connect(self.close)
        anim.start()

    def mousePressEvent(self, event):
        self.close()
        super().mousePressEvent(event)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
