"""大图查看对话框。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

VIEWER_QSS = """
QDialog { background:#EAF6FC; }
QScrollArea { border:1px solid #D5E8F2; border-radius:8px; background:white; }
QPushButton { background:#ADD8E6; border:1px solid #7FB8D4; border-radius:8px; padding:7px 20px; }
QPushButton:hover { background:#9CCFE0; }
"""


class ImageViewerDialog(QDialog):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(Path(path).name)
        self.resize(720, 560)
        self.setStyleSheet(VIEWER_QSS)

        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            max_w, max_h = 900, 640
            if pixmap.width() > max_w or pixmap.height() > max_h:
                pixmap = pixmap.scaled(
                    max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            label.setPixmap(pixmap)
        scroll.setWidget(label)
        layout.addWidget(scroll, 1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)
