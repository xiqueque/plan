"""日历跳转对话框：大气圆角卡片 + 自绘大方块日历，方块内显示任务名。"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .calendar_widget import CalendarGrid, DayDetailDialog, build_calendar_export

CALENDAR_QSS = """
QDialog { background: transparent; }
QWidget#card {
    background: #F2FAFF;
    border: 2px solid #7FB8D4;
    border-radius: 18px;
}
QWidget {
    font-family: "幼圆", "Microsoft YaHei";
    font-size: 14px;
    color: #1F3A4D;
}
QLabel#dialogTitle { font-size: 20px; font-weight: bold; color: #1F3A4D; }
QPushButton {
    background: #ADD8E6;
    border: 1px solid #7FB8D4;
    border-radius: 10px;
    padding: 8px 20px;
    font-size: 14px;
}
QPushButton:hover { background: #9CCFE0; }
QPushButton#closeBtn {
    background: transparent;
    border: none;
    font-size: 16px;
    color: #6B8CA3;
}
QPushButton#closeBtn:hover { color: #1F3A4D; }
"""


class CalendarDialog(QDialog):
    def __init__(self, parent=None, current: date | None = None, data: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("选择日期")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(680, 720)
        self.setMinimumSize(600, 660)
        self.setStyleSheet(CALENDAR_QSS)
        self.data = data or {}
        self._drag_offset = None

        card = QWidget()
        card.setObjectName("card")
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 16, 22, 18)
        layout.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel("选择日期")
        title.setObjectName("dialogTitle")
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setToolTip("关闭")
        close_btn.clicked.connect(self.reject)
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(close_btn)
        layout.addLayout(top)

        self.grid = CalendarGrid(data)
        if current is not None:
            self.grid.month = current.replace(day=1)
            self.grid.selected = current
            self.grid._rebuild()
        self.grid.dateClicked.connect(self._show_detail)
        self.grid.dateDoubleClicked.connect(self.accept)
        layout.addWidget(self.grid, 1)

        bottom = QHBoxLayout()
        detail_btn = QPushButton("查看详情")
        detail_btn.clicked.connect(self._show_selected_detail)
        shot_btn = QPushButton("截图")
        shot_btn.setToolTip("保存月度计划图片")
        shot_btn.clicked.connect(self.export_screenshot)
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        bottom.addWidget(detail_btn)
        bottom.addWidget(shot_btn)
        bottom.addStretch(1)
        bottom.addWidget(ok_btn)
        bottom.addWidget(cancel_btn)
        layout.addLayout(bottom)

    def selected_date(self) -> date:
        return self.grid.selected_date()

    def _show_detail(self, day: date) -> None:
        dialog = DayDetailDialog(self, self.data, day)
        dialog.exec()

    def _show_selected_detail(self) -> None:
        self._show_detail(self.grid.selected_date())

    def export_screenshot(self) -> None:
        widget = build_calendar_export(self.data, self.grid.month)
        widget.setMinimumWidth(720)
        widget.adjustSize()
        pixmap = widget.grab()
        default_name = (
            f"月度计划_{self.grid.month.year:04d}-{self.grid.month.month:02d}.png"
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "保存月度计划截图", str(Path.home() / default_name), "PNG 图片 (*.png)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        if pixmap.save(path, "PNG"):
            box = QMessageBox(self)
            box.setWindowTitle("截图")
            box.setText(f"截图已保存：\n{path}")
            box.setIcon(QMessageBox.NoIcon)
            box.addButton("好的", QMessageBox.AcceptRole)
            box.exec()

    def mousePressEvent(self, event):
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
