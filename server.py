"""Small dependency-free API server for the ATLAS dashboard."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from engine.atlas_engine import AtlasEngine

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

def load_demo() -> AtlasEngine:
    files = {}
    if DATA.exists():
        for path in DATA.glob("*.csv"):
            files[path.name] = path.read_text(encoding="utf-8")
    return AtlasEngine.from_csv_texts(files)

ENGINE = load_demo()

class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self._send(200, {"ok": True, "engine": "ATLAS"})
        if path == "/api/summary":
            return self._send(200, ENGINE.summary())
        if path == "/api/signals":
            return self._send(200, {"signals": ENGINE.safety_signals()})
        return self._send(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "Invalid JSON"})
        if path == "/api/query":
            question = str(payload.get("question", ""))
            return self._send(200, ENGINE.query(question))
        if path == "/api/load":
            files = payload.get("files", {})
            if not isinstance(files, dict):
                return self._send(400, {"error": "files must be an object"})
            global ENGINE
            ENGINE = AtlasEngine.from_csv_texts({str(k): str(v) for k, v in files.items()})
            return self._send(200, {"ok": True, "summary": ENGINE.summary()})
        return self._send(404, {"error": "Not found"})

if __name__ == "__main__":
    print("ATLAS API running at http://localhost:8000")
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
