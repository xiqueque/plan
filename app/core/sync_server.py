"""局域网同步服务：手机通过 HTTP 拉取/推送计划数据（同一 WiFi）。"""
from __future__ import annotations

import json
import shutil
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import storage

DEFAULT_PORT = 47520
MAX_BODY = 20 * 1024 * 1024  # 20MB


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass  # 静默日志

    def _send_json(self, obj: dict, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/ping":
            self._send_json({"name": "每日计划", "status": "ok"})
        elif self.path == "/api/plan":
            self._send_json(storage.load_data())
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        if self.path != "/api/plan":
            self._send_json({"error": "not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            if length <= 0 or length > MAX_BODY:
                self._send_json({"error": "数据大小不合法"}, 400)
                return
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("不是有效的计划数据")
            # 覆盖前备份当前数据
            if storage.DATA_FILE.exists():
                bak = storage.DATA_FILE.with_suffix(".bak.json")
                try:
                    shutil.copy2(storage.DATA_FILE, bak)
                except OSError:
                    pass
            storage.save_data(data)
            self._send_json({"ok": True, "message": "电脑数据已更新"})
            callback = getattr(self.server, "on_update", None)
            if callback is not None:
                try:
                    callback()
                except Exception:
                    pass
        except (OSError, ValueError, json.JSONDecodeError) as e:
            self._send_json({"error": str(e)}, 400)


class SyncServer:
    """后台线程运行的局域网同步服务。"""

    def __init__(self, port: int = DEFAULT_PORT, on_update=None):
        self.port = port
        self.on_update = on_update
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._server is not None

    def start(self) -> tuple[bool, str]:
        if self._server:
            return True, "已在运行"
        try:
            self._server = ThreadingHTTPServer(("0.0.0.0", self.port), _Handler)
        except OSError as e:
            return False, f"启动失败：{e}"
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )
        self._thread.start()
        return True, f"运行中（端口 {self.port}）"

    def stop(self) -> None:
        if self._server:
            try:
                self._server.shutdown()
            except Exception:
                pass
            try:
                self._server.server_close()
            except Exception:
                pass
            self._server = None
        self._thread = None

    def addresses(self) -> list[str]:
        """列出本机局域网 IPv4 地址。"""
        ips: set[str] = set()
        try:
            ips.add(socket.gethostbyname(socket.gethostname()))
        except Exception:
            pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("223.5.5.5", 80))  # 不实际发包，仅取本机出口 IP
            ips.add(s.getsockname()[0])
            s.close()
        except Exception:
            pass
        return sorted(ips)
