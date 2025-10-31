#!/usr/bin/env python3
"""
Auto-Recovery for Task Queue + RPA Worker

- Checks server health, inflight tasks, and presence of worker process
- Starts server (background) if down
- Starts worker (background) if not running or not consuming

Usage:
  python fdo_agi_repo/scripts/auto_recover.py --server http://127.0.0.1:8091 --once
  python fdo_agi_repo/scripts/auto_recover.py --server http://127.0.0.1:8091 --loop --interval 15

Notes:
- Uses PowerShell to start background jobs (same commands as VS Code tasks)
- Idempotent: safely skips when components are already healthy
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

THIS_DIR = Path(__file__).parent
REPO_ROOT = THIS_DIR.parent


class Client:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.sess = requests.Session()

    def health(self) -> Optional[Dict[str, Any]]:
        try:
            r = self.sess.get(f"{self.base_url}/api/health", timeout=3)
            if r.status_code == 200:
                return r.json()
        except Exception:
            return None
        return None

    def results_count(self) -> Optional[int]:
        try:
            r = self.sess.get(f"{self.base_url}/api/results", timeout=3)
            if r.status_code == 200:
                return int(r.json().get("count", 0))
        except Exception:
            return None
        return None

    def queue_info(self) -> Optional[Dict[str, Any]]:
        try:
            r = self.sess.get(f"{self.base_url}/api/tasks", timeout=3)
            if r.status_code == 200:
                return r.json()
        except Exception:
            return None
        return None

    def inflight(self) -> Optional[Dict[str, Any]]:
        try:
            r = self.sess.get(f"{self.base_url}/api/inflight", timeout=3)
            if r.status_code == 200:
                return r.json()
        except Exception:
            return None
        return None


def _run_powershell(cmd: str) -> int:
    return subprocess.call([
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        cmd,
    ])


def start_server_background() -> bool:
    script = REPO_ROOT.parent / "LLM_Unified" / "ion-mentoring" / "start_task_queue_server_background.ps1"
    if not script.exists():
        return False
    ec = _run_powershell(f"& '{script}'")
    return ec == 0


def start_worker_background(server_url: str = "http://127.0.0.1:8091") -> bool:
    # mirrors tasks.json 'RPA: Start Worker (Background Job)'
    workdir = REPO_ROOT
    if not workdir.exists():
        return False
    cmd = (
        f"cd {workdir}; "
        f"if (Test-Path .venv\\Scripts\\python.exe) {{ "
        f"Start-Job -ScriptBlock {{ Set-Location '{workdir}'; .venv\\Scripts\\python.exe integrations\\rpa_worker.py --server '{server_url}' --interval 0.5 --log-level INFO }} -Name 'RPA_Worker' | Out-Null; "
        f"Write-Host 'RPA Worker started (Job: RPA_Worker)' -ForegroundColor Green }} else {{ "
        f"Start-Job -ScriptBlock {{ Set-Location '{workdir}'; python integrations\\rpa_worker.py --server '{server_url}' --interval 0.5 --log-level INFO }} -Name 'RPA_Worker' | Out-Null; "
        f"Write-Host 'RPA Worker started (Job: RPA_Worker)' -ForegroundColor Green }}"
    )
    ec = _run_powershell(cmd)
    return ec == 0


def is_worker_running() -> bool:
    # Check background jobs containing rpa_worker
    cmd = (
        "$jobs = Get-Job | Where-Object { $_.Name -like 'RPA_Worker' -or $_.Command -like '*rpa_worker.py*' }; "
        "if ($jobs) { exit 0 } else { exit 1 }"
    )
    ec = _run_powershell(cmd)
    return ec == 0


def auto_recover_once(server: str) -> Dict[str, Any]:
    client = Client(server)
    health = client.health()
    actions = []
    status: Dict[str, Any] = {
        "server": server,
        "health_ok": bool(health and health.get("status") == "ok"),
        "before": {
            "health": health,
            "queue": client.queue_info(),
            "results": client.results_count(),
            "inflight": client.inflight(),
            "worker_running": is_worker_running(),
        },
        "actions": actions,
    }

    # Start server if down
    if not status["health_ok"]:
        if start_server_background():
            actions.append("start_server")
            # small wait + re-check
            time.sleep(2)
            health = client.health()
            status["health_ok"] = bool(health and health.get("status") == "ok")

    # Start worker if not running and queue not empty (or inflight high)
    q = client.queue_info() or {}
    queue_size = int(q.get("queue_size", 0))
    inflight = client.inflight() or {"count": 0}
    worker_ok = is_worker_running()

    if (queue_size > 0 or int(inflight.get("count", 0)) > 0) and not worker_ok:
        if start_worker_background(server):
            actions.append("start_worker")

    status["after"] = {
        "health": client.health(),
        "queue": client.queue_info(),
        "results": client.results_count(),
        "inflight": client.inflight(),
        "worker_running": is_worker_running(),
    }
    return status


def main(argv=None):
    p = argparse.ArgumentParser(description="Auto-Recovery for Task Queue + RPA Worker")
    p.add_argument("--server", default="http://127.0.0.1:8091", help="Task Queue base URL")
    p.add_argument("--loop", action="store_true", help="Run continuously with interval")
    p.add_argument("--interval", type=float, default=15.0, help="Loop interval seconds")
    p.add_argument("--out", default=str(REPO_ROOT / "outputs"), help="Output directory")
    args = p.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.loop:
        rep = auto_recover_once(args.server)
        (out_dir / "auto_recover_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return

    print(f"[Auto-Recover] Watching {args.server} every {args.interval}s ... (Ctrl+C to stop)")
    try:
        while True:
            rep = auto_recover_once(args.server)
            (out_dir / "auto_recover_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("[Auto-Recover] Stopped.")


if __name__ == "__main__":
    main()
