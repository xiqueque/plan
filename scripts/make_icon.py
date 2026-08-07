"""生成应用图标：淡蓝色日历 + 绿色对勾。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPolygonF

ASSETS = Path(__file__).resolve().parent.parent / "app" / "assets"
PNG_PATH = ASSETS / "app_icon.png"
ICO_PATH = ASSETS / "app_icon.ico"


def draw(size: int) -> QImage:
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    s = float(size)
    m = s * 0.05

    # 背景圆角方块（淡蓝）
    painter.setPen(QPen(QColor("#7FB8D4"), max(1.0, s * 0.02)))
    painter.setBrush(QColor("#A8D8EA"))
    painter.drawRoundedRect(QRectF(m, m, s - 2 * m, s - 2 * m), s * 0.16, s * 0.16)

    # 日历主体（白色圆角矩形）
    body = QRectF(s * 0.14, s * 0.24, s * 0.72, s * 0.64)
    painter.setPen(QPen(QColor("#7FB8D4"), max(1.0, s * 0.015)))
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(body, s * 0.06, s * 0.06)

    # 顶部绑带圆环
    painter.setBrush(QColor("#7FB8D4"))
    for cx in (0.30, 0.62):
        ring = QRectF(s * cx - s * 0.045, s * 0.16, s * 0.09, s * 0.09)
        painter.drawEllipse(ring)

    # 网格线
    grid_pen = QPen(QColor("#C9DCE8"), max(1.0, s * 0.008))
    painter.setPen(grid_pen)
    for fy in (0.42, 0.58, 0.74):
        y = body.top() + body.height() * fy
        painter.drawLine(
            QPointF(body.left() + s * 0.02, y), QPointF(body.right() - s * 0.02, y)
        )
    for fx in (0.35, 0.62):
        x = body.left() + body.width() * fx
        painter.drawLine(
            QPointF(x, body.top() + s * 0.02), QPointF(x, body.bottom() - s * 0.02)
        )

    # 对勾（绿色）
    check_pen = QPen(QColor("#4C9E63"), max(2.0, s * 0.055))
    check_pen.setCapStyle(Qt.RoundCap)
    check_pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(check_pen)
    painter.drawPolyline(
        QPolygonF(
            [
                QPointF(s * 0.30, s * 0.54),
                QPointF(s * 0.44, s * 0.68),
                QPointF(s * 0.70, s * 0.40),
            ]
        )
    )
    painter.end()
    return img


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    img = draw(256)
    ok_png = img.save(str(PNG_PATH), "PNG")
    ok_ico = img.save(str(ICO_PATH), "ICO")
    if not ok_png:
        raise SystemExit("PNG 图标生成失败")
    if not ok_ico:
        try:
            from PIL import Image

            Image.open(PNG_PATH).save(
                ICO_PATH,
                sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
            )
            ok_ico = True
        except Exception:
            pass
    print(f"PNG: {ok_png}, ICO: {ok_ico}")
    print(f"图标已生成：{PNG_PATH} / {ICO_PATH}")


if __name__ == "__main__":
    main()
