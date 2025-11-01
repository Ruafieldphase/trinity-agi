#!/usr/bin/env python3
import argparse
import json
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from original_data_index import load_index, search_index


class OriginalDataHandler(BaseHTTPRequestHandler):
    server_version = "OriginalDataHTTP/1.0"

    def _send(self, code: int, body: dict, headers: dict | None = None):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        # simple CORS for local use
        self.send_header("Access-Control-Allow-Origin", "*")
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802 (httphandler)
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send(200, {"ok": True, "service": "original-data", "time": time.time()})
            return
        if parsed.path == "/search":
            qs = parse_qs(parsed.query)
            q = qs.get("q", [None])[0]
            tags = _split(qs.get("tags", [None])[0])
            exts = _split(qs.get("ext", [None])[0])
            since_days = _to_int(qs.get("since_days", [None])[0])
            top = _to_int(qs.get("top", ["20"])[0]) or 20

            started = time.time()
            try:
                items = self.server.index_items  # type: ignore[attr-defined]
            except Exception:
                self._send(500, {"ok": False, "error": "index_not_loaded"})
                return
            results = search_index(items, query=q, tags=tags, exts=exts, since_days=since_days, top=top)
            took_ms = int((time.time() - started) * 1000)
            self._send(200, {"ok": True, "count": len(results), "took_ms": took_ms, "items": results})
            return

        self._send(404, {"ok": False, "error": "not_found", "path": parsed.path})

    def log_message(self, fmt, *args):  # reduce noise
        return


def _split(s):
    if not s:
        return None
    import re

    parts = [p for p in re.split(r"[,;\s]+", s) if p]
    return parts or None


def _to_int(v):
    try:
        return int(v) if v is not None else None
    except Exception:
        return None


class OriginalDataHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, index_path: str):
        super().__init__(server_address, RequestHandlerClass)
        self.index_path = index_path
        self.index_items = load_index(index_path)


def find_free_port(default: int) -> int:
    try:
        with socket.create_server(("127.0.0.1", default)) as s:
            return default
    except OSError:
        with socket.create_server(("127.0.0.1", 0)) as s:
            return s.getsockname()[1]


def main():
    ap = argparse.ArgumentParser(description="Serve Original Data index via HTTP JSON API")
    ap.add_argument("--index", default=os.path.join("outputs", "original_data_index.json"))
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8093)
    args = ap.parse_args()

    port = find_free_port(args.port)
    httpd = OriginalDataHTTPServer((args.host, port), OriginalDataHandler, index_path=args.index)
    print(f"[original-data] Serving on http://{args.host}:{port} (index='{args.index}')")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
