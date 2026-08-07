"""每日计划 —— 程序入口。

运行方式：在项目根目录执行  python -m app.main
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QLockFile
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from .core import storage
from .ui.main_window import MainWindow

ICON_FILE = Path(__file__).resolve().parent / "assets" / "app_icon.ico"


def main() -> int:
    # 防止同时打开两个窗口导致数据冲突
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(storage.DATA_DIR / "app.lock"))
    if not lock.tryLock(100):
        QMessageBox.information(None, "每日计划", "每日计划已经在运行，请直接使用已打开的窗口。")
        return 0

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("每日计划")
    if ICON_FILE.exists():
        app.setWindowIcon(QIcon(str(ICON_FILE)))

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
