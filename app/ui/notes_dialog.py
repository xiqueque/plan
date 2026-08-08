"""便签：俏皮绿色样式，随手记小事，自动保存。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
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

    def _save(self) -> None:
        self.data["notes"] = self.edit.toPlainText()
        storage.save_data(self.data)
