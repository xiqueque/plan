"""每日计划 —— 程序入口。

运行方式：
  python -m app.main      （在项目根目录）
  pythonw app\\main.py     （任意目录，供开机自启 / 桌面快捷方式使用）
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QEvent, QLockFile, QObject  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton  # noqa: E402

from app.core import click_sound, storage  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402

if getattr(sys, "frozen", False):
    ICON_FILE = Path(__file__).resolve().parent / "app" / "assets" / "app_icon.ico"
else:
    ICON_FILE = Path(__file__).resolve().parent / "assets" / "app_icon.ico"


class ClickSoundFilter(QObject):
    """按键点击时播放提示音。"""

    def eventFilter(self, obj, event):
        if (
            event.type() == QEvent.MouseButtonRelease
            and isinstance(obj, QPushButton)
            and obj.isEnabled()
            and obj.rect().contains(event.position().toPoint())
        ):
            click_sound.play_click_sound()
        return super().eventFilter(obj, event)


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
    app._click_filter = ClickSoundFilter()
    app.installEventFilter(app._click_filter)
    if ICON_FILE.exists():
        app.setWindowIcon(QIcon(str(ICON_FILE)))

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
