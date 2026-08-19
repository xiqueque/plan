"""同步弹窗：局域网同步服务状态、IP 地址与开关。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ..core import storage, sync_server


class SyncDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("同步")
        self.setModal(True)
        self.resize(400, 360)
        self.setObjectName("syncDialog")

        if parent is not None and getattr(parent, "_sync_server", None) is not None:
            self.server = parent._sync_server
        else:
            self.server = sync_server.SyncServer()
            if parent is not None:
                parent._sync_server = self.server

        lay = QVBoxLayout(self)
        title = QLabel("🔄 电脑 ↔ 手机同步（同一 WiFi）")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F3A4D;")
        lay.addWidget(title)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        lay.addWidget(self.status_label)

        self.ip_label = QLabel()
        self.ip_label.setWordWrap(True)
        self.ip_label.setStyleSheet(
            "color: #1F3A4D; background: #EAF6FC;"
            "border-radius: 8px; padding: 8px; font-family: Consolas;"
        )
        lay.addWidget(self.ip_label)

        self.toggle_btn = QPushButton()
        self.toggle_btn.setObjectName("smallBtn")
        self.toggle_btn.clicked.connect(self._toggle)
        lay.addWidget(self.toggle_btn)

        tip = QLabel(
            "使用步骤：\n"
            "1. 手机和电脑连同一个 WiFi；\n"
            "2. 打开手机版「设置 → 同步」；\n"
            "3. 输入上面的 IP 地址，端口 47520；\n"
            "4. 点「拉取」= 电脑数据传到手机；"
            "点「推送」= 手机数据传到电脑。\n\n"
            "注意：手机推送到电脑前，电脑数据会自动备份为 plan.bak.json。"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #6B8CA3; font-size: 12px;")
        lay.addWidget(tip)

        btn_row = QHBoxLayout()
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("smallBtn")
        close_btn.clicked.connect(self.accept)
        btn_row.addStretch(1)
        btn_row.addWidget(close_btn)
        lay.addLayout(btn_row)

        self.refresh()

    def refresh(self) -> None:
        if self.server.running:
            self.status_label.setText("服务状态：运行中 ✓（手机可以连接）")
            self.status_label.setStyleSheet("color: #2E7D32; font-weight: bold;")
            self.toggle_btn.setText("停止同步服务")
            ips = self.server.addresses() or ["（未检测到 IP）"]
            lines = "\n".join(f"  手机输入：{ip}:47520" for ip in ips)
            self.ip_label.setText("电脑的局域网地址：\n" + lines)
        else:
            self.status_label.setText("服务状态：已停止")
            self.status_label.setStyleSheet("color: #B23A3A; font-weight: bold;")
            self.toggle_btn.setText("启动同步服务")
            self.ip_label.setText("启动后，这里会显示手机的连接地址")

    def _toggle(self) -> None:
        if self.server.running:
            self.server.stop()
            self._set_setting(False)
        else:
            ok, msg = self.server.start()
            if ok:
                self._set_setting(True)
            self.status_label.setText(f"服务状态：{msg}")
        self.refresh()

    def _set_setting(self, enabled: bool) -> None:
        try:
            data = storage.load_data()
            data.setdefault("settings", {})["sync_server"] = enabled
            storage.save_data(data)
        except Exception:
            pass
