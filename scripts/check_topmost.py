"""真实显示环境验证：进入迷你窗口后系统层不置顶。"""
from __future__ import annotations

import ctypes
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app.core import storage  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402

WS_EX_TOPMOST = 0x8
GWL_EXSTYLE = -20
user32 = ctypes.windll.user32


def os_topmost(w) -> bool:
    hwnd = int(w.winId())
    ex = user32.GetWindowLongPtrW(ctypes.c_void_p(hwnd), GWL_EXSTYLE)
    return bool(ex & WS_EX_TOPMOST)


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    storage.DATA_DIR = tmp
    storage.DATA_FILE = tmp / "plan.json"
    data = storage.empty_data()
    data["settings"]["topmost"] = True  # 模拟设置了「总在最前」
    data["tasks"].append(storage.new_task("测试任务", "2026-08-07"))
    storage.save_data(data)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.data["settings"]["topmost"] = True
    window.setWindowFlag(Qt.WindowStaysOnTopHint, True)
    window.show()
    app.processEvents()
    print("full os_topmost:", os_topmost(window))

    window._enter_mini_mode()
    app.processEvents()
    print(
        "mini os_topmost:",
        os_topmost(window),
        "qt flag:",
        bool(window.windowFlags() & Qt.WindowStaysOnTopHint),
    )

    window._exit_mini_mode()
    app.processEvents()
    print("after exit os_topmost:", os_topmost(window))


if __name__ == "__main__":
    main()
