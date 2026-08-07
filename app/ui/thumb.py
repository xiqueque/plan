"""图片缩略图：左键系统默认打开，右键菜单（打开 / 重命名 / 删除）。"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QInputDialog,
    QLabel,
    QMenu,
    QToolButton,
    QVBoxLayout,
)

IMAGE_FILTER = "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"

THUMB_QSS = """
QFrame {
    background: white;
    border: 1px solid #D5E8F2;
    border-radius: 8px;
}
QFrame:hover { border-color: #7FB8D4; }
QToolButton { background: transparent; border: none; }
QLabel { color: #6B8CA3; font-size: 11px; }
"""


def _current_viewer() -> str:
    """读取设置中的自定义图片程序路径（空 = 系统默认）。"""
    try:
        from ..core import storage

        return (storage.load_data().get("settings", {}).get("image_viewer", "") or "").strip()
    except Exception:
        return ""


def open_image_external(path) -> None:
    """用系统默认程序（或设置中的自定义程序）打开图片。"""
    viewer = _current_viewer()
    try:
        if viewer:
            subprocess.Popen([viewer, str(path)])
        else:
            os.startfile(str(path))
    except OSError:
        pass


class ThumbButton(QFrame):
    """图片缩略图：左键打开，右键菜单支持打开 / 重命名 / 删除。"""

    deleted = Signal(str)
    renamed = Signal(str, str)
    mark_toggled = Signal(str)

    def __init__(
        self,
        image_path,
        display_name: str = "",
        show_delete: bool = True,
        marked: bool = False,
        mark_enabled: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.path = Path(image_path)
        self.display_name = display_name or self.path.name
        self._show_delete = show_delete
        self._marked = marked
        self._mark_enabled = mark_enabled
        self.setStyleSheet(THUMB_QSS)
        self.setFixedWidth(106)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 2)
        lay.setSpacing(2)

        self.icon_btn = QToolButton()
        self.icon_btn.setFixedSize(94, 94)
        pixmap = QPixmap(str(self.path))
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                QSize(90, 90), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.icon_btn.setIcon(QIcon(scaled))
        self.icon_btn.setIconSize(QSize(90, 90))
        self.icon_btn.setToolTip(self.display_name)
        self.icon_btn.clicked.connect(self._open)
        lay.addWidget(self.icon_btn, 0, Qt.AlignCenter)

        self.caption = QLabel(self._elide(self.display_name))
        self.caption.setAlignment(Qt.AlignCenter)
        self.caption.setToolTip(self.display_name)
        lay.addWidget(self.caption)

    def _elide(self, text: str) -> str:
        metrics = QFontMetrics(self.font())
        return metrics.elidedText(text, Qt.ElideMiddle, 96)

    def set_display_name(self, name: str) -> None:
        self.display_name = name
        self.caption.setText(self._elide(name))
        self.caption.setToolTip(name)
        self.icon_btn.setToolTip(name)

    def set_marked(self, marked: bool) -> None:
        self._marked = marked
        self.update()

    def paintEvent(self, event):
        """把每日星标直接画在缩略图左上角（不会飘到屏幕角落）。"""
        super().paintEvent(event)
        if not self._marked:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = painter.font()
        font.setPixelSize(18)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#F0B429"))
        painter.drawText(QRectF(2, 0, 24, 22), Qt.AlignCenter, "★")
        painter.end()

    def _open(self) -> None:
        open_image_external(self.path)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        act_open = menu.addAction("打开")
        act_rename = menu.addAction("重命名")
        act_mark = None
        if self._mark_enabled:
            act_mark = menu.addAction(
                "取消每日图片" if self._marked else "标记为每日图片"
            )
        act_delete = menu.addAction("删除")
        act_delete.setEnabled(self._show_delete)
        chosen = menu.exec(event.globalPos())
        if chosen is act_open:
            open_image_external(self.path)
        elif chosen is act_rename:
            self._rename()
        elif act_mark is not None and chosen is act_mark:
            self.mark_toggled.emit(str(self.path))
        elif chosen is act_delete:
            self.deleted.emit(str(self.path))

    def _rename(self) -> None:
        text, ok = QInputDialog.getText(
            self,
            "重命名图片",
            "给这张图片一个新名字（仅改显示名，不会修改原文件）：\n"
            "支持中文、英文和 ASCII 字符",
            text=self.display_name,
        )
        if ok and text.strip():
            self.renamed.emit(str(self.path), text.strip())
