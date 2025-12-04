"""
Autonomic Nerve Center

Goal
- 산발적으로 늘어나는 PowerShell/터미널 기반 모니터/워치독을 하나의 조용한 백그라운드 프로세스로 통합 관리합니다.
- 핵심 리소스(큐 서버, 워커 등)의 헬스 체크 → 이상 시 자동 복구(기존 ensure 스크립트 호출) → 상태를 파일로 기록.
- 인간에게는 불필요한 소음(터미널 탭 생성)을 줄이고, 문제 시에만 "통증 신호"(알림/보고서)를 내보냅니다.

Design
- 설정 파일(config/autonomic_monitors.json)로 관리 대상을 선언적 구성
- 헬스체크 타입: http, process
- 보정(ensure) 타입: ps1 (기존 스크립트 이용)
- 출력: outputs/nerve_center_status_latest.{json,md}

No external deps
- 표준 라이브러리만 사용 (psutil 불필요)
- HTTP는 urllib, 프로세스 조회는 Windows tasklist 파싱(간단한 부분 문자열 매칭)

Usage
  python fdo_agi_repo/autonomic/nerve_center.py --once --dry-run
  python fdo_agi_repo/autonomic/nerve_center.py --interval 5
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import csv
import io

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config" / "autonomic_monitors.json"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class HealthSpec:
    type: str  # "http" | "process"
    url: Optional[str] = None
    expect: Optional[str] = None  # for http-json: expect status == this string
    match: Optional[str] = None   # for process: substring to match
    minCount: int = 1             # for process: at least this many


@dataclass
class EnsureSpec:
    type: str  # "ps1"
    path: str
    args: List[str]


@dataclass
class ResourceSpec:
    name: str
    health: HealthSpec
    ensure: EnsureSpec
    processMatch: Optional[str] = None
    singleton: bool = True
    required: bool = True


@dataclass
class Config:
    interval_sec: float
    resources: List[ResourceSpec]


# ---------- helpers ----------

def _read_json_config(path: Path) -> Config:
    obj = json.loads(path.read_text(encoding="utf-8"))
    resources: List[ResourceSpec] = []
    for r in obj.get("resources", []):
        h = r.get("health", {})
        e = r.get("ensure", {})
        resources.append(
            ResourceSpec(
                name=r["name"],
                health=HealthSpec(
                    type=h.get("type"),
                    url=h.get("url"),
                    expect=h.get("expect"),
                    match=h.get("match"),
                    minCount=int(h.get("minCount", 1)),
                ),
                ensure=EnsureSpec(
                    type=e.get("type"),
                    path=e.get("path"),
                    args=list(e.get("args", [])),
                ),
                processMatch=r.get("processMatch"),
                singleton=bool(r.get("singleton", True)),
                required=bool(r.get("required", True)),
            )
        )
    return Config(
        interval_sec=float(obj.get("interval_sec", 5.0)),
        resources=resources,
    )


def _http_health_ok(url: str, expect: Optional[str]) -> bool:
    try:
        req = Request(url, headers={"User-Agent": "nerve-center/1.0"})
        with urlopen(req, timeout=3) as resp:
            if resp.status != 200:
                return False
            # try parse json
            try:
                import json as _json
                data = _json.loads(resp.read().decode("utf-8", errors="ignore"))
                if expect is None:
                    return True
                return str(data.get("status")) == expect
            except Exception:
                # if no json expected, 200 is good enough
                return expect is None
    except (URLError, HTTPError):
        return False


def _tasklist_rows() -> List[Dict[str, str]]:
    # Use CSV to simplify parsing on various locales
    try:
        completed = subprocess.run(
            ["tasklist", "/v", "/fo", "csv"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        content = completed.stdout
        f = io.StringIO(content)
        reader = csv.DictReader(f)
        return list(reader)
    except Exception:
        return []


def _count_process_contains(substr: str) -> int:
    substr_low = substr.lower()
    cnt = 0
    for row in _tasklist_rows():
        # Fields: Image Name, PID, Session Name, Session#, Mem Usage, Status, User Name, CPU Time, Window Title
        cmdline = " ".join([row.get("Image Name", ""), row.get("Window Title", "")])
        if substr_low in cmdline.lower():
            cnt += 1
    return cnt


def _run_ps1(ps1_path: str, args: List[str], wait: bool = False) -> bool:
    try:
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / ps1_path) if not os.path.isabs(ps1_path) else ps1_path,
        ] + args
        if wait:
            subprocess.run(cmd, check=True)
        else:
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception:
        return False


# ---------- core loop ----------

def check_resource(res: ResourceSpec, dry_run: bool = False) -> Dict[str, Any]:
    healthy = False
    reason = None

    if res.health.type == "http" and res.health.url:
        healthy = _http_health_ok(res.health.url, res.health.expect)
        if not healthy:
            reason = f"http_unhealthy: {res.health.url}"
    elif res.health.type == "process" and res.health.match:
        cnt = _count_process_contains(res.health.match)
        healthy = cnt >= res.health.minCount
        if not healthy:
            reason = f"process_missing: {res.health.match} count={cnt}"

    action = None
    ensured = False
    if not healthy and not dry_run:
        if res.ensure.type == "ps1" and res.ensure.path:
            action = f"ensure:{res.ensure.path} {res.ensure.args}"
            ensured = _run_ps1(res.ensure.path, res.ensure.args, wait=False)

    return {
        "name": res.name,
        "healthy": healthy,
        "reason": reason,
        "action": action,
        "ensured": ensured,
    }


def write_status(status: Dict[str, Any]):
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    (OUTPUT_DIR / "nerve_center_status_latest.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / f"nerve_center_status_{ts}.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md = [
        f"# Nerve Center Status ({status['timestamp']})",
        "",
        f"- config: {status['config']}",
        f"- dry_run: {status['dry_run']}",
        "",
        "## resources",
    ]
    for item in status.get("resources", []):
        md.append(f"- {item['name']}: {'✅ healthy' if item['healthy'] else '❌ unhealthy'}"
                  + (f" ({item['reason']})" if item.get('reason') else "")
                  + (f" → action={item['action']}" if item.get('action') else ""))
    (OUTPUT_DIR / "nerve_center_status_latest.md").write_text("\n".join(md), encoding="utf-8")


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Autonomic Nerve Center - unify monitors and auto-heal quietly")
    p.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to autonomic_monitors.json")
    p.add_argument("--interval", type=float, default=5.0, help="Polling interval seconds")
    p.add_argument("--once", action="store_true", help="Run single check and exit")
    p.add_argument("--dry-run", action="store_true", help="Do not run ensure actions; just report")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"[nerve] Config not found: {cfg_path}")
        sys.exit(2)

    cfg = _read_json_config(cfg_path)

    def do_cycle():
        items = []
        for res in cfg.resources:
            items.append(check_resource(res, dry_run=args.dry_run))
        status = {
            "timestamp": utc_now(),
            "config": str(cfg_path),
            "dry_run": bool(args.dry_run),
            "resources": items,
        }
        write_status(status)
        # Optional: pain signal escalation (severe)
        if any(not it["healthy"] and it.get("ensured") is False for it in items):
            # call alert system (best-effort)
            _run_ps1("scripts/alert_system.ps1", ["-NoAlert"], wait=False)  # keep silent unless configured
        return status

    if args.once:
        st = do_cycle()
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return

    print(f"[nerve] start (interval={args.interval}s) with config={cfg_path}")
    try:
        while True:
            do_cycle()
            time.sleep(float(args.interval))
    except KeyboardInterrupt:
        print("[nerve] stop by user")


if __name__ == "__main__":
    main()
