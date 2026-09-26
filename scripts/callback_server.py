#!/usr/bin/env python3
"""Spark Joy 本地回调服务，接收飞书卡片按钮点击。"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sys
import socket

# 确保能导入同目录模块
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prefs import record_feedback

PORT = 18789
HOST = "127.0.0.1"


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, port))
            return True
        except ConnectionRefusedError:
            return False


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        action = params.get("action", [""])[0]
        item_id = params.get("id", [""])[0]

        if action in ("like", "dislike") and item_id:
            record_feedback(item_id, liked=(action == "like"))

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = "<html><body><h2>已记录你的偏好</h2><p>可以关闭此页面</p></body></html>"
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # 禁用日志


def run_server():
    server = HTTPServer((HOST, PORT), CallbackHandler)
    print(f"Callback server running on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
