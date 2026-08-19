"""局域网同步服务单元测试。"""
from __future__ import annotations

import http.client
import json
import tempfile
import unittest
from pathlib import Path

from app.core import storage, sync_server


class SyncServerTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._old_dir = storage.DATA_DIR
        self._old_file = storage.DATA_FILE
        storage.DATA_DIR = Path(self.tmp.name)
        storage.DATA_FILE = storage.DATA_DIR / "plan.json"
        self.server = sync_server.SyncServer(port=0)
        ok, _ = self.server.start()
        self.assertTrue(ok)
        self.port = self.server._server.server_address[1]
        self.conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)

    def tearDown(self):
        try:
            self.conn.close()
        except Exception:
            pass
        self.server.stop()
        storage.DATA_DIR = self._old_dir
        storage.DATA_FILE = self._old_file
        self.tmp.cleanup()

    def test_ping(self):
        self.conn.request("GET", "/api/ping")
        resp = self.conn.getresponse()
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(body["status"], "ok")

    def test_get_plan_returns_saved_data(self):
        data = storage.empty_data()
        data["tasks"].append(storage.new_task("同步测试", storage.today_str()))
        storage.save_data(data)
        self.conn.request("GET", "/api/plan")
        resp = self.conn.getresponse()
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(body["tasks"][0]["text"], "同步测试")

    def test_post_plan_saves_and_backs_up(self):
        # 先保存一份旧数据，用于验证备份
        old = storage.empty_data()
        old["tasks"].append(storage.new_task("旧数据", storage.today_str()))
        storage.save_data(old)
        new = storage.empty_data()
        new["tasks"].append(storage.new_task("手机推送", storage.today_str()))
        payload = json.dumps(new, ensure_ascii=False).encode("utf-8")
        self.conn.request("POST", "/api/plan", body=payload)
        resp = self.conn.getresponse()
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(body["ok"])
        loaded = storage.load_data()
        self.assertEqual(loaded["tasks"][0]["text"], "手机推送")
        self.assertTrue(storage.DATA_FILE.with_suffix(".bak.json").exists())

    def test_unknown_path_returns_404(self):
        self.conn.request("GET", "/nope")
        resp = self.conn.getresponse()
        self.assertEqual(resp.status, 404)


if __name__ == "__main__":
    unittest.main()
