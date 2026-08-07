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
from PySide6.QtWidgets import QApplication, QLabel, QPushButton  # noqa: E402

from app.core import storage  # noqa: E402
from app.ui.main_window import BigCheckBox, MainWindow, PinIcon  # noqa: E402


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    storage.DATA_DIR = tmp
    storage.DATA_FILE = tmp / "plan.json"

    data = storage.empty_data()
    today = date.today().isoformat()
    task = storage.new_task("勾选测试任务", today, color="#E05252")
    pinned = storage.new_task("置顶测试任务", today)
    pinned["pinned"] = True
    pinned["pinned_at"] = 1.0
    data["tasks"].extend([task, pinned])
    storage.save_data(data)

    app = QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()
    window._play_check_sound = lambda: None  # 测试期间不发声
    window._confirm_complete = lambda: True  # 测试期间自动确认
    window._show_completion_message = lambda: None

    boxes = window.findChildren(BigCheckBox)
    assert len(boxes) >= 2, "未找到足够的勾选框"
    box = boxes[1]  # 第一个是置顶任务，第二个是普通任务
    assert (box.width(), box.height()) == (36, 36), f"勾选框尺寸 {box.width()}x{box.height()}"
    print("checkbox size OK")

    # 0) 最小窗口尺寸应为 480x340
    assert (window.minimumWidth(), window.minimumHeight()) == (480, 340), (
        f"最小尺寸不符：{window.minimumWidth()}x{window.minimumHeight()}"
    )
    print("min size OK")

    # 1) 整个 36x36 区域都应可点击
    assert box.hitButton(QPoint(28, 28)), "勾选框角落点击区域未生效"
    assert box.hitButton(QPoint(2, 2)), "勾选框角落点击区域未生效"
    print("hitButton OK")

    # 2) 点击中心应切换状态并保存
    assert not box.isChecked()
    QTest.mouseClick(box, Qt.LeftButton, Qt.NoModifier, QPoint(15, 15))
    app.processEvents()
    assert box.isChecked(), "第一次点击未勾选成功"
    assert storage.is_done(window.data, task["id"], today), "完成状态未保存"
    # 等待动画完成，确认出现划线（完成样式）
    QTest.qWait(450)
    labels = [lbl for lbl in window.findChildren(QLabel) if lbl.objectName() == "taskText"]
    assert len(labels) >= 2 and "line-through" in labels[1].styleSheet(), "完成划线样式未生效"
    print("done style OK")
    QTest.mouseClick(box, Qt.LeftButton, Qt.NoModifier, QPoint(15, 15))
    app.processEvents()
    assert not box.isChecked(), "第二次点击未取消勾选"
    QTest.qWait(450)
    labels = [lbl for lbl in window.findChildren(QLabel) if lbl.objectName() == "taskText"]
    assert len(labels) >= 2 and "line-through" not in labels[1].styleSheet(), "取消勾选后划线未移除"
    print("click toggle OK")

    # 3) 任务文字加粗（weight 600 -> Qt 内部 DemiBold=63）
    labels = [lbl for lbl in window.findChildren(QLabel) if lbl.objectName() == "taskText"]
    assert labels, "未找到任务文字"
    weight = labels[0].font().weight()
    print("task weight:", weight)
    assert weight >= 63, f"任务文字未加粗（weight={weight}）"
    print("bold OK")

    # 5) 置顶图标与更大的行按钮
    pin_icons = window.findChildren(PinIcon)
    assert pin_icons, "未找到置顶图标"
    pin_btns = [
        btn
        for btn in window.findChildren(QPushButton)
        if btn.text() in ("置顶", "编辑", "删除")
    ]
    assert pin_btns and min(b.font().pixelSize() for b in pin_btns) >= 14
    print("pin icon + bigger buttons OK")

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
