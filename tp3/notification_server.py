#!/usr/bin/env python3
"""Petit serveur de notification oneM2M utilisé pour la ressource SUB du TP3."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from datetime import datetime

LOG = Path(__file__).with_name("notifications.log")

class Handler(BaseHTTPRequestHandler):
    def _reply(self, code=200, body=b"{}"):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        # oneM2M: succès d'une opération
        self.send_header("X-M2M-RSC", "2000")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._reply(200, json.dumps({"status": "ok"}).encode())
        else:
            self._reply(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        text = raw.decode("utf-8", errors="replace")
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] {self.path}\n{text}\n")
        print(f"[NOTIFY] {self.path}: {text}", flush=True)
        self._reply(200)

    def log_message(self, fmt, *args):
        print("[HTTP] " + fmt % args, flush=True)

if __name__ == "__main__":
    print("Notification server: http://127.0.0.1:5000/notify", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 5000), Handler).serve_forever()
