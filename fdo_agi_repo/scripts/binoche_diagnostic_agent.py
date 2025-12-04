#!/usr/bin/env python3
"""
Binoche Diagnostic Agent

- Gathers server/worker diagnostics
- Produces a markdown report with analysis and recommended fixes in Binoche's concise, confident style
- Optional --auto-fix triggers auto_recover.py

Usage:
  python fdo_agi_repo/scripts/binoche_diagnostic_agent.py --server http://127.0.0.1:8091 --auto-fix
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests

THIS_DIR = Path(__file__).parent
REPO_ROOT = THIS_DIR.parent
OUT_DIR = REPO_ROOT / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)


class Client:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.sess = requests.Session()

    def get(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            r = self.sess.get(f"{self.base_url}{path}", timeout=4)
            if r.status_code == 200:
                try:
                    return r.json()
                except Exception:
                    return {"raw": r.text}
        except Exception:
            return None
        return None


def ps(cmd: str) -> str:
    try:
        out = subprocess.check_output([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd
        ], stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        return e.output.decode("utf-8", errors="replace")
    except Exception as e:
        return str(e)


def run_auto_fix(server: str) -> Dict[str, Any]:
    exe = REPO_ROOT / "scripts" / "auto_recover.py"
    if not exe.exists():
        exe = THIS_DIR / "auto_recover.py"  # local path fallback
    py = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    if py.exists():
        cmd = f"& '{py}' '{exe}' --server '{server}' --once"
    else:
        cmd = f"python '{exe}' --server '{server}' --once"
    code = subprocess.call(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd])
    return {"exit_code": code}


def main(argv=None):
    p = argparse.ArgumentParser(description="Binoche Diagnostic Agent")
    p.add_argument("--server", default="http://127.0.0.1:8091", help="Task Queue base URL")
    p.add_argument("--auto-fix", action="store_true", help="Attempt auto recovery if issues found")
    args = p.parse_args(argv)

    client = Client(args.server)

    health = client.get("/api/health")
    tasks = client.get("/api/tasks")
    inflight = client.get("/api/inflight")
    results = client.get("/api/results")

    procs_worker = ps("Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*rpa_worker.py*' } | Select-Object Id,CPU,WorkingSet,StartTime,Path,CommandLine | Format-List | Out-String")
    procs_server = ps("Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*task_queue_server.py*' } | Select-Object Id,CPU,WorkingSet,StartTime,Path,CommandLine | Format-List | Out-String")
    net_8091 = ps("Get-NetTCPConnection -LocalPort 8091 -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,State,OwningProcess | Format-Table -AutoSize | Out-String")

    issues = []
    recs = []

    if not (health and health.get("status") == "ok"):
        issues.append("server_down")
        recs.append("서버가 응답하지 않습니다. 백그라운드 서버를 기동하세요.")
    else:
        qsize = int((tasks or {}).get("queue_size", 0)) if tasks else None
        if qsize and qsize > 0:
            issues.append("queue_backlog")
            recs.append(f"큐 적체 {qsize}건. 워커가 실행 중인지 점검하세요.")
        if inflight and int(inflight.get("count", 0)) > 0:
            recs.append(f"inflight {inflight.get('count')}건 존재. 리스 만료 시 자동 재배치됩니다.")

    # Quick worker presence check
    worker_present = "RPA_Worker" in ps("Get-Job | Select-Object Name | Out-String") or ("rpa_worker.py" in procs_worker)
    if not worker_present:
        issues.append("worker_absent")
        recs.append("워커가 보이지 않습니다. 백그라운드 워커를 시작하세요.")

    ts = datetime.utcnow().isoformat() + "Z"
    report: Dict[str, Any] = {
        "timestamp": ts,
        "server": args.server,
        "health": health,
        "tasks": tasks,
        "inflight": inflight,
        "results": results,
        "processes": {
            "worker": procs_worker.strip(),
            "server": procs_server.strip(),
        },
        "net_8091": net_8091.strip(),
        "issues": issues,
        "recommendations": recs,
    }

    # Optional auto-fix
    fix_out = None
    if args.auto_fix and issues:
        fix_out = run_auto_fix(args.server)
        report["auto_fix"] = fix_out

    # Write JSON and MD
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "binoche_diag_latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        f"# Binoche Diagnostic Report ({ts})",
        "",
        f"- server: {args.server}",
        f"- health: {health.get('status') if isinstance(health, dict) else health}",
        f"- queue_size: {(tasks or {}).get('queue_size') if tasks else 'n/a'}",
        f"- inflight: {(inflight or {}).get('count') if inflight else 'n/a'}",
        f"- results_count: {(results or {}).get('count') if results else 'n/a'}",
        "",
        "## quick look",
        f"- issues: {', '.join(issues) if issues else 'none'}",
        "",
        "## proposed fixes (Binoche)",
    ] + [f"- {r}" for r in recs]

    if fix_out is not None:
        md_lines += ["", "## auto-fix", f"- exit_code: {fix_out.get('exit_code')} (0이면 성공)"]

    md_lines += [
        "",
        "## processes: worker",
        "```",
        report["processes"]["worker"],
        "```",
        "",
        "## processes: server",
        "```",
        report["processes"]["server"],
        "```",
        "",
        "## netstat 8091",
        "```",
        report["net_8091"],
        "```",
    ]

    (OUT_DIR / "binoche_diag_latest.md").write_text("\n".join(md_lines), encoding="utf-8")
    print("\n".join(md_lines))


if __name__ == "__main__":
    main()
