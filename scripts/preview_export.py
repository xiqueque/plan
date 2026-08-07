"""导出卡片预览：生成计划截图样式的预览图。"""
from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.core import storage  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    storage.DATA_DIR = tmp
    storage.DATA_FILE = tmp / "plan.json"

    data = storage.empty_data()
    today = date.today().isoformat()
    tasks = [
        storage.new_task("写数学作业（红色·紧急）", today, "09:00", "10:00", color="#E05252"),
        storage.new_task("买菜做饭（橙色·重要）", today, color="#E8963A"),
        storage.new_task("背英语单词（绿色·轻松）", today, is_daily=True, color="#4C9E63"),
        storage.new_task("跑步 30 分钟（蓝色·常规）", today, "18:30", "19:00", color="#3B7DBF"),
    ]
    data["tasks"].extend(tasks)
    storage.set_done(data, tasks[3]["id"], today, True)
    storage.save_data(data)

    app = QApplication([])
    window = MainWindow()
    widget = window._build_export_widget(today, tasks)
    widget.setMinimumWidth(560)
    widget.adjustSize()

    out = Path(
        r"C:\Users\Junhong\.codex\visualizations\2026\08\07"
        r"\019fdb41-c37f-7cc0-98bc-853dbe47b082\export_preview.png"
    )
    widget.grab().save(str(out))
    print(f"导出卡片预览图已生成：{out}")


if __name__ == "__main__":
    main()
