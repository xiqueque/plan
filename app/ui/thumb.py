"""图片缩略图按钮：点击查看大图，右上角小 × 删除。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QPushButton, QToolButton

from .image_viewer import ImageViewerDialog

IMAGE_FILTER = "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"

THUMB_QSS = """
QToolButton {
    background: white;
    border: 1px solid #D5E8F2;
    border-radius: 8px;
}
QToolButton:hover { border-color: #7FB8D4; }
QPushButton {
    background: #F4C7C3;
    border: 1px solid #D9A29C;
    border-radius: 11px;
    color: #7A2E2A;
    font-size: 13px;
    font-weight: bold;
}
QPushButton:hover { background: #EFB4AE; }
"""


class ThumbButton(QToolButton):
    """缩略图：点击查看大图；右上角 × 删除（发出 deleted 信号）。"""

    deleted = Signal(str)

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.path = Path(image_path)
        self.setStyleSheet(THUMB_QSS)
        self.setFixedSize(100, 100)
        self.setToolTip(self.path.name)

        pixmap = QPixmap(str(self.path))
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                QSize(92, 92), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setIcon(QIcon(scaled))
            self.setIconSize(QSize(92, 92))

        self.clicked.connect(self._show_viewer)

        self.del_btn = QPushButton("×", self)
        self.del_btn.setFixedSize(22, 22)
        self.del_btn.move(74, 2)
        self.del_btn.clicked.connect(lambda: self.deleted.emit(str(self.path)))

    def _show_viewer(self) -> None:
        dialog = ImageViewerDialog(self.path, self.window())
        dialog.exec()
