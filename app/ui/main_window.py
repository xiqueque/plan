"""主窗口：日期显示、计划列表、搜索、设置。"""
from __future__ import annotations

import time
from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
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

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

APP_QSS = """
QWidget {
    font-family: "Microsoft YaHei";
    font-size: 14px;
    color: #1F3A4D;
}
QMainWindow, QWidget#central, QDialog, QMessageBox {
    background: #EAF6FC;
}
QPushButton#dateLabel {
    border: none;
    background: transparent;
    font-size: 18px;
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
    font-size: 15px;
}
QLabel#timeLabel {
    font-size: 12px;
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
    padding: 3px 8px;
    font-size: 12px;
}
QPushButton#smallDanger {
    padding: 3px 8px;
    font-size: 12px;
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("每日计划")
        self.resize(820, 540)
        self.setMinimumSize(680, 420)

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
        self.settings_btn = QPushButton("设置")
        self.settings_btn.clicked.connect(self.open_settings)
        bottom.addWidget(self.add_btn, 1)
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
        check = QCheckBox()
        check.setToolTip("标记完成")
        check.blockSignals(True)
        check.setChecked(done)
        check.blockSignals(False)
        check.toggled.connect(
            lambda checked, t=task: self._on_toggle_done(t, date_str, checked)
        )

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_label = QLabel(task.get("text", ""))
        text_label.setWordWrap(True)
        text_label.setObjectName("taskText")
        text_col.addWidget(text_label)

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

        if done:
            text_label.setStyleSheet("color:#9AA5AC; text-decoration: line-through;")
        else:
            color = task.get("color") or "#1F3A4D"
            text_label.setStyleSheet(f"color:{color};")
        return row

    # ---------- 操作 ----------
    def _on_toggle_done(self, task: dict, date_str: str, checked: bool) -> None:
        storage.set_done(self.data, task["id"], date_str, checked)
        storage.save_data(self.data)
        self._rebuild_list(keep_scroll=True)

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
        dialog = SettingsDialog(self, self.data["settings"].get("cleanup_days", 15))
        if dialog.exec() != SettingsDialog.Accepted:
            return
        self.data["settings"]["cleanup_days"] = dialog.cleanup_days()
        storage.save_data(self.data)
        removed = storage.run_cleanup(self.data)
        if removed:
            storage.save_data(self.data)
            QMessageBox.information(self, "清理完成", f"已自动清理 {removed} 条过期计划。")
        self._rebuild_list()
