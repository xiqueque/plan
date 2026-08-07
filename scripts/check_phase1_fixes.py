"""开发检查：验证勾选框点击区域、点击切换、加粗与截图导出。"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import date
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QLabel  # noqa: E402

from app.core import storage  # noqa: E402
from app.ui.main_window import BigCheckBox, MainWindow  # noqa: E402


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    storage.DATA_DIR = tmp
    storage.DATA_FILE = tmp / "plan.json"

    data = storage.empty_data()
    today = date.today().isoformat()
    task = storage.new_task("勾选测试任务", today, color="#E05252")
    data["tasks"].append(task)
    storage.save_data(data)

    app = QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()

    boxes = window.findChildren(BigCheckBox)
    assert boxes, "未找到勾选框"
    box = boxes[0]

    # 1) 整个 30x30 区域都应可点击
    assert box.hitButton(QPoint(28, 28)), "勾选框角落点击区域未生效"
    assert box.hitButton(QPoint(2, 2)), "勾选框角落点击区域未生效"
    print("hitButton OK")

    # 2) 点击中心应切换状态并保存
    assert not box.isChecked()
    QTest.mouseClick(box, Qt.LeftButton, Qt.NoModifier, QPoint(15, 15))
    app.processEvents()
    assert box.isChecked(), "第一次点击未勾选成功"
    assert storage.is_done(window.data, task["id"], today), "完成状态未保存"
    QTest.mouseClick(box, Qt.LeftButton, Qt.NoModifier, QPoint(15, 15))
    app.processEvents()
    assert not box.isChecked(), "第二次点击未取消勾选"
    print("click toggle OK")

    # 3) 任务文字加粗（weight 600 -> Qt 内部 DemiBold=63）
    labels = [lbl for lbl in window.findChildren(QLabel) if lbl.objectName() == "taskText"]
    assert labels, "未找到任务文字"
    weight = labels[0].font().weight()
    print("task weight:", weight)
    assert weight >= 63, f"任务文字未加粗（weight={weight}）"
    print("bold OK")

    # 4) 截图导出可生成非空 PNG
    widget = window._build_export_widget(today, storage.tasks_for_date(window.data, today))
    widget.setMinimumWidth(560)
    widget.adjustSize()
    pixmap = widget.grab()
    out = tmp / "export_test.png"
    assert pixmap.save(str(out), "PNG")
    assert out.stat().st_size > 1000, "导出的截图太小，可能渲染失败"
    print("export OK, size:", out.stat().st_size)


if __name__ == "__main__":
    main()
