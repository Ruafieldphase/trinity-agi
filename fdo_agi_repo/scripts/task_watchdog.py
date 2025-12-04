"""
Task Watchdog

Purpose
- 주기적으로 Task Queue 서버 상태를 점검하고, 이상 패턴(무한 루프/소비 중단/서버 다운)을 감지합니다.
- 선택적으로 자가 진단(Self-test)을 위해 ping 작업을 주입하고, 처리 결과를 확인합니다.
- 결과를 outputs/ 디렉터리에 JSON/Markdown으로 기록합니다.
- 필요 시(옵션) 간단한 자동 복구 시도를 수행합니다.

Server API (ion-mentoring/task_queue_server.py 기준)
- GET    /api/health
- GET    /api/tasks
- GET    /api/results
- GET    /api/results/{task_id}
- POST   /api/tasks/create

Detects
- server_down: 서버에 접근 불가 상태가 일정 시간 지속
- queue_stuck: 큐에 작업이 남아 있는데 결과가 증가하지 않음(소비 중단)
- consumers_not_consuming: ping 작업을 넣었는데 일정 시간 내 소비되지 않음

Usage (examples)
  python scripts/task_watchdog.py --server http://127.0.0.1:8091 --interval 5 --self-test --out outputs
  python scripts/task_watchdog.py --server http://127.0.0.1:8091 --interval 5 --auto-recover

Notes
- 자동 복구는 기본 비활성화이며, --auto-recover 플래그로 명시적으로 활성화합니다.
- 서버 스크립트 경로를 알고 있다면 --server-script 로 지정해 자동 기동 시도 가능.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import requests


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WatchdogConfig:
    server_url: str = "http://127.0.0.1:8091"
    interval: float = 5.0
    server_down_seconds: float = 10.0
    queue_stuck_seconds: float = 30.0
    self_test: bool = False
    self_test_timeout: float = 15.0
    out_dir: str = "outputs"
    auto_recover: bool = False
    server_script_path: Optional[str] = None  # e.g., LLM_Unified/ion-mentoring/task_queue_server.py


class TaskQueueClient:
    def __init__(self, base_url: str, session: Optional[requests.Session] = None):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()

    def health(self) -> Optional[Dict[str, Any]]:
        try:
            r = self.session.get(f"{self.base_url}/api/health", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            return None
        return None

    def list_tasks(self) -> Optional[Dict[str, Any]]:
        try:
            r = self.session.get(f"{self.base_url}/api/tasks", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            return None
        return None

    def list_results(self) -> Optional[Dict[str, Any]]:
        try:
            r = self.session.get(f"{self.base_url}/api/results", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            return None
        return None

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            r = self.session.get(f"{self.base_url}/api/results/{task_id}", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            return None
        return None

    def create_task(self, task_type: str, data: Dict[str, Any]) -> Optional[str]:
        try:
            r = self.session.post(
                f"{self.base_url}/api/tasks/create",
                json={"type": task_type, "data": data},
                timeout=10,
            )
            if r.status_code == 200:
                return r.json().get("task_id")
        except Exception:
            return None
        return None


@dataclass
class WatchdogState:
    last_ok_health_ts: Optional[str] = None
    last_results_count: int = 0
    no_progress_since_ts: Optional[str] = None
    last_report: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "last_ok_health_ts": self.last_ok_health_ts,
            "last_results_count": self.last_results_count,
            "no_progress_since_ts": self.no_progress_since_ts,
            "last_report": self.last_report,
        }


class TaskWatchdog:
    def __init__(self, cfg: WatchdogConfig):
        self.cfg = cfg
        self.client = TaskQueueClient(cfg.server_url)
        self.state = WatchdogState()
        self.out_dir = Path(cfg.out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.out_dir / "watchdog_state.json"
        self._load_state()

    # ---- persistence ----
    def _load_state(self):
        try:
            if self.state_file.exists():
                obj = json.loads(self.state_file.read_text(encoding="utf-8"))
                self.state = WatchdogState(
                    last_ok_health_ts=obj.get("last_ok_health_ts"),
                    last_results_count=int(obj.get("last_results_count", 0)),
                    no_progress_since_ts=obj.get("no_progress_since_ts"),
                    last_report=obj.get("last_report"),
                )
        except Exception:
            # ignore corrupt state
            pass

    def _save_state(self):
        try:
            self.state_file.write_text(json.dumps(self.state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    # ---- detection helpers ----
    def _seconds_since(self, iso_ts: Optional[str]) -> Optional[float]:
        if not iso_ts:
            return None
        try:
            t_then = datetime.fromisoformat(iso_ts)
            delta = datetime.now(timezone.utc) - t_then.astimezone(timezone.utc)
            return delta.total_seconds()
        except Exception:
            return None

    def _compute_oldest_age_seconds(self, queue_obj: Dict[str, Any]) -> Optional[float]:
        try:
            items = queue_obj.get("queue", [])
            oldest = None
            for it in items:
                created = it.get("created_at")
                if created:
                    try:
                        ts = datetime.fromisoformat(created)
                        if oldest is None or ts < oldest:
                            oldest = ts
                    except Exception:
                        continue
            if oldest is None:
                return None
            return (datetime.now(timezone.utc) - oldest.astimezone(timezone.utc)).total_seconds()
        except Exception:
            return None

    # ---- actions ----
    def _maybe_autostart_server(self):
        if not self.cfg.auto_recover:
            return False
        script_path = self.cfg.server_script_path
        if not script_path:
            # best-effort: try relative common path
            guess = Path(__file__).resolve().parents[2] / "LLM_Unified" / "ion-mentoring" / "task_queue_server.py"
            if guess.exists():
                script_path = str(guess)
        if not script_path or not Path(script_path).exists():
            return False
        try:
            import subprocess
            subprocess.Popen([sys.executable, script_path, "--port", self._port_from_url()], cwd=str(Path(script_path).parent))
            return True
        except Exception:
            return False

    def _port_from_url(self) -> str:
        # crude parse; default 8091
        try:
            from urllib.parse import urlparse
            p = urlparse(self.cfg.server_url)
            return str(p.port or 8091)
        except Exception:
            return "8091"

    # ---- report ----
    def _write_report(self, report: Dict[str, Any]):
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        (self.out_dir / "watchdog_status_latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        (self.out_dir / f"watchdog_status_{ts}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        # also a tiny md
        md = [
            f"# Task Watchdog Status ({report.get('timestamp')})",
            "",
            f"- server_url: {self.cfg.server_url}",
            f"- health_ok: {report.get('health_ok')}",
            f"- queue_size: {report.get('queue_size')}",
            f"- results_count: {report.get('results_count')}",
            f"- oldest_task_age_sec: {report.get('oldest_task_age_sec')}",
            f"- anomalies: {', '.join(report.get('anomalies', [])) or 'none'}",
            "",
            "## recommendations",
            *(f"- {rec}" for rec in report.get("recommendations", [])),
        ]
        (self.out_dir / "watchdog_status_latest.md").write_text("\n".join(md), encoding="utf-8")

    # ---- main check ----
    def single_check(self) -> Dict[str, Any]:
        now = utc_now_iso()
        health = self.client.health()
        health_ok = bool(health and health.get("status") == "ok")

        if health_ok:
            self.state.last_ok_health_ts = now
        queue_obj = self.client.list_tasks() if health_ok else None
        results_obj = self.client.list_results() if health_ok else None

        queue_size = int(queue_obj.get("queue_size", 0)) if queue_obj else None
        results_count = int(results_obj.get("count", 0)) if results_obj else None
        oldest_age = self._compute_oldest_age_seconds(queue_obj) if queue_obj else None

        anomalies = []
        recommendations = []

        # server_down detection
        since_ok = self._seconds_since(self.state.last_ok_health_ts)
        if not health_ok and (since_ok is None or since_ok >= self.cfg.server_down_seconds):
            anomalies.append("server_down")
            recommendations.append("서버가 응답하지 않습니다. 서버 프로세스를 기동하거나 포트를 확인하세요.")
            if self._maybe_autostart_server():
                recommendations.append("자동 복구: 서버 기동을 시도했습니다.")

        # queue_stuck detection (queue > 0 and results not progressing)
        if health_ok and queue_size is not None and results_count is not None:
            if queue_size > 0:
                # progress tracking
                if results_count > self.state.last_results_count:
                    self.state.last_results_count = results_count
                    self.state.no_progress_since_ts = None
                else:
                    if not self.state.no_progress_since_ts:
                        self.state.no_progress_since_ts = now
                    no_prog_sec = self._seconds_since(self.state.no_progress_since_ts) or 0.0
                    if (oldest_age or 0.0) >= self.cfg.queue_stuck_seconds and no_prog_sec >= self.cfg.queue_stuck_seconds:
                        anomalies.append("queue_stuck")
                        recommendations.append("작업이 소비되지 않습니다. 워커가 실행 중인지 확인하고 로그를 점검하세요.")

        # optional self-test
        selftest_outcome = None
        test_task_id = None
        if self.cfg.self_test and health_ok:
            test_task_id = self.client.create_task("ping", {})
            if test_task_id:
                deadline = time.time() + self.cfg.self_test_timeout
                while time.time() < deadline:
                    res = self.client.get_result(test_task_id)
                    if res and res.get("success") is True:
                        selftest_outcome = True
                        break
                    time.sleep(0.5)
            if selftest_outcome is None:
                selftest_outcome = False
        if self.cfg.self_test and selftest_outcome is False:
            anomalies.append("consumers_not_consuming")
            recommendations.append("Self-test ping이 처리되지 않았습니다. 워커를 재시작하세요.")

        report = {
            "timestamp": now,
            "server_url": self.cfg.server_url,
            "health_ok": health_ok,
            "queue_size": queue_size,
            "results_count": results_count,
            "oldest_task_age_sec": oldest_age,
            "anomalies": anomalies,
            "recommendations": recommendations,
            "self_test": self.cfg.self_test,
            "self_test_task_id": test_task_id,
        }

        self.state.last_report = report
        self._save_state()
        self._write_report(report)
        return report

    def run_loop(self):
        print(f"[Watchdog] Start monitoring: {self.cfg.server_url} (interval={self.cfg.interval}s)")
        try:
            while True:
                rep = self.single_check()
                anomalies = rep.get("anomalies", [])
                if anomalies:
                    print(f"[!] Anomalies detected: {anomalies}")
                time.sleep(self.cfg.interval)
        except KeyboardInterrupt:
            print("[Watchdog] Stopped by user")


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Task Watchdog - detect stuck queues and server outages")
    p.add_argument("--server", default="http://127.0.0.1:8091", help="Task Queue server base URL")
    p.add_argument("--interval", type=float, default=5.0, help="Polling interval seconds")
    p.add_argument("--server-down-seconds", type=float, default=10.0, help="How long until server_down is reported")
    p.add_argument("--queue-stuck-seconds", type=float, default=30.0, help="Threshold for queue_stuck detection")
    p.add_argument("--self-test", action="store_true", help="Inject ping task and verify consumption")
    p.add_argument("--self-test-timeout", type=float, default=15.0, help="Timeout for self-test task consumption")
    p.add_argument("--out", default="outputs", help="Output directory for status files")
    p.add_argument("--auto-recover", action="store_true", help="Attempt best-effort auto start of server when down")
    p.add_argument("--server-script", dest="server_script", default=None, help="Path to task_queue_server.py for auto start")
    p.add_argument("--once", action="store_true", help="Run single check and exit")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    cfg = WatchdogConfig(
        server_url=args.server,
        interval=args.interval,
        server_down_seconds=args.server_down_seconds,
        queue_stuck_seconds=args.queue_stuck_seconds,
        self_test=args.self_test,
        self_test_timeout=args.self_test_timeout,
        out_dir=args.out,
        auto_recover=args.auto_recover,
        server_script_path=args.server_script,
    )
    wd = TaskWatchdog(cfg)
    if args.once:
        rep = wd.single_check()
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        wd.run_loop()


if __name__ == "__main__":
    main()
