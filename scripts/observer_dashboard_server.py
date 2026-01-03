#!/usr/bin/env python3
import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from workspace_root import get_workspace_root

WS_ROOT = get_workspace_root()
OUTPUTS = WS_ROOT / "outputs"
DEFAULT_DASH = OUTPUTS / "monitoring_dashboard_latest.html"
DEFAULT_METRICS = OUTPUTS / "monitoring_metrics_latest.json"
DEFAULT_STATUS = WS_ROOT / "outputs" / "quick_status_latest.json"

class Handler(BaseHTTPRequestHandler):
    def _send(self, code:int, body:bytes, ctype:str="text/plain; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        p = parsed.path or "/"
        if p == "/health":
            body = json.dumps({
                "ok": True,
                "time": time.time(),
                "workspace": str(WS_ROOT),
                "outputs_exists": OUTPUTS.exists(),
            }).encode("utf-8")
            return self._send(200, body, "application/json; charset=utf-8")

        if p == "/metrics":
            if DEFAULT_METRICS.exists():
                try:
                    data = DEFAULT_METRICS.read_bytes()
                    return self._send(200, data, "application/json; charset=utf-8")
                except Exception as e:
                    err = json.dumps({"error": str(e)}).encode("utf-8")
                    return self._send(500, err, "application/json; charset=utf-8")
            else:
                return self._send(404, b"metrics not found", "text/plain; charset=utf-8")

        if p == "/status":
            if DEFAULT_STATUS.exists():
                try:
                    data = DEFAULT_STATUS.read_bytes()
                    return self._send(200, data, "application/json; charset=utf-8")
                except Exception as e:
                    err = json.dumps({"error": str(e)}).encode("utf-8")
                    return self._send(500, err, "application/json; charset=utf-8")
            else:
                return self._send(404, b"status not found", "text/plain; charset=utf-8")

        if p == "/" or p == "/dashboard":
            if DEFAULT_DASH.exists():
                try:
                    data = DEFAULT_DASH.read_bytes()
                    # inject light auto-refresh (30s) without touching file on disk
                    html = data.decode("utf-8", errors="ignore")
                    if "<head>" in html and "meta http-equiv=\"refresh\"" not in html:
                        html = html.replace("<head>", "<head>\n<meta http-equiv=\"refresh\" content=\"30\">")
                    return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
                except Exception as e:
                    err = f"failed to read dashboard: {e}".encode("utf-8")
                    return self._send(500, err, "text/plain; charset=utf-8")
            else:
                # Friendly landing with pointers
                body = f"""
<!doctype html>
<html lang=\"ko\">
<head>
  <meta charset=\"utf-8\" />
  <title>Observer Dashboard</title>
  <style>body{{font:14px/1.5 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial; margin:24px;}} code{{background:#f4f4f4; padding:2px 4px;}} a{{color:#0366d6; text-decoration:none;}}</style>
</head>
<body>
  <h1>Observer Dashboard</h1>
  <p>대시보드 HTML이 아직 생성되지 않았습니다.</p>
  <ul>
    <li>VS Code 태스크: <code>Monitoring: Generate Dashboard (24h HTML)</code> 실행</li>
    <li>또는: <code>📊 Dashboard: Enhanced (no browser)</code> / <code>🚀 Dashboard: Enhanced (GPU+Queue+LLM)</code></li>
  </ul>
  <p>생성 후 이 페이지를 새로고침하면 최신 대시보드가 표시됩니다.</p>
  <p>보조 엔드포인트: <a href=\"/health\">/health</a>, <a href=\"/metrics\">/metrics</a>, <a href=\"/status\">/status</a></p>
</body>
</html>
""".encode("utf-8")
                return self._send(200, body, "text/html; charset=utf-8")

        # Attempt to serve any file under outputs for convenience
        candidate = OUTPUTS / p.lstrip("/")
        if candidate.is_file():
            try:
                data = candidate.read_bytes()
                ctype = "application/octet-stream"
                if candidate.suffix in (".html", ".htm"):
                    ctype = "text/html; charset=utf-8"
                elif candidate.suffix == ".json":
                    ctype = "application/json; charset=utf-8"
                elif candidate.suffix == ".md":
                    ctype = "text/markdown; charset=utf-8"
                return self._send(200, data, ctype)
            except Exception as e:
                err = f"failed to read file: {e}".encode("utf-8")
                return self._send(500, err, "text/plain; charset=utf-8")

        return self._send(404, b"not found", "text/plain; charset=utf-8")


def run(port:int):
    addr = ("127.0.0.1", port)
    httpd = HTTPServer(addr, Handler)
    print(f"Observer server listening on http://{addr[0]}:{addr[1]}")
    print(f"Workspace: {WS_ROOT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    port = 8095
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except Exception:
            pass
    run(port)
