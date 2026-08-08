"""便签：俏皮绿色样式，随手记小事，自动保存。"""
from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from ..core import storage

NOTES_QSS = """
QDialog {
    background: #F2FFF6;
    font-family: "幼圆", "Microsoft YaHei";
    font-size: 15px;
    color: #2E4A38;
}
QTextEdit {
    background: white;
    border: 2px solid #9CD6AE;
    border-radius: 14px;
    font-size: 16px;
    padding: 10px;
}
QPushButton {
    background: #C8F0D6;
    border: 2px solid #7FC99B;
    border-radius: 12px;
    padding: 9px 16px;
    font-size: 15px;
    font-weight: bold;
}
QPushButton:hover { background: #AEE4C4; }
QPushButton:pressed { background: #7FC99B; }
"""


class NotesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("便签")
        self.resize(500, 440)
        self.setStyleSheet(NOTES_QSS)
        self.data = parent.data

        layout = QVBoxLayout(self)
        self.edit = QTextEdit()
        self.edit.setPlaceholderText("📝 记下一些小事…")
        self.edit.setText(self.data.get("notes", ""))
        layout.addWidget(self.edit, 1)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._save)
        self.edit.textChanged.connect(self._schedule_save)

        bottom = QHBoxLayout()
        hint = QPushButton("✨ 自动保存")
        hint.setEnabled(False)
        bottom.addWidget(hint)
        bottom.addStretch(1)
        save_btn = QPushButton("💾 保存")
        save_btn.clicked.connect(self._save)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(save_btn)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

    def _schedule_save(self) -> None:
        self._timer.start()

    def _save(self) -> None:
        self.data["notes"] = self.edit.toPlainText()
        storage.save_data(self.data)

    def accept(self) -> None:
        self._save()
        super().accept()
