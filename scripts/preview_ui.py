"""界面预览：生成一张主窗口截图，用于检查外观。

默认使用真实显示模式渲染（保证字体效果真实）；无窗口检查时设置
环境变量 QT_QPA_PLATFORM=offscreen 再运行。
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.core import storage  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="plan_preview_"))
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
    window.show()
    app.processEvents()

    out = Path(
        r"C:\Users\Junhong\.codex\visualizations\2026\08\07"
        r"\019fdb41-c37f-7cc0-98bc-853dbe47b082\phase1_preview.png"
    )
    window.grab().save(str(out))
    print(f"预览图已生成：{out}")


if __name__ == "__main__":
    main()
