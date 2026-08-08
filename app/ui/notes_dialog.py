"""便签：俏皮绿色样式，随手记小事，自动保存。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from ..core import storage
from .style import build_notes_qss


class NotesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("便签")
        self.resize(500, 440)
        self.data = parent.data
        self.setStyleSheet(build_notes_qss(parent.theme))

        layout = QVBoxLayout(self)
        self.edit = QTextEdit()
        self.edit.setPlaceholderText("📝 记下一些小事…")
        self.edit.setText(self.data.get("notes", ""))
        layout.addWidget(self.edit, 1)

        # 只要更改就立即自动保存
        self.edit.textChanged.connect(self._save)

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

    def _save(self) -> None:
        self.data["notes"] = self.edit.toPlainText()
        storage.save_data(self.data)

    def accept(self) -> None:
        self._save()
        super().accept()
