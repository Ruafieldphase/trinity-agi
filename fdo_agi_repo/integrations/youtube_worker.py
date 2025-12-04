"""
YouTube Worker
- Polls the task queue server and processes tasks of type 'youtube_learn'
- Runs YouTubeLearner pipeline and submits results
"""
from __future__ import annotations


import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

# 에러 캡처 유틸
from .error_capture_utils import capture_and_ocr_on_error

import requests

# Ensure we can import rpa.youtube_learner without relying on PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rpa.youtube_learner import YouTubeLearner, YouTubeLearnerConfig  # type: ignore
from rpa.execution_engine import ExecutionEngine, ExecutionConfig, ExecutionMode  # type: ignore


@dataclass
class WorkerConfig:
    server_url: str = "http://127.0.0.1:8091"
    poll_interval: float = 0.5
    worker_name: str = "youtube-worker"
    log_level: str = "INFO"
    # RPA execution settings
    enable_rpa_execution: bool = False
    rpa_mode: str = "DRY_RUN"  # DRY_RUN, LIVE, VERIFY_ONLY
    rpa_enable_verification: bool = False
    rpa_enable_failsafe: bool = True
    # Retry settings
    max_retries: int = 3
    backoff_base: float = 1.0  # seconds
    backoff_max: float = 10.0  # seconds


class YouTubeWorker:
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.logger = logging.getLogger("YouTubeWorker")
        self.logger.setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO))
        self.session = requests.Session()
        self.session.headers.update({"X-Worker-Name": self.config.worker_name})

    def _health(self) -> bool:
        try:
            r = self.session.get(f"{self.config.server_url}/api/health", timeout=5)
            return r.status_code == 200 and r.json().get("status") == "ok"
        except Exception:
            return False

    def _fetch_next_task(self) -> Optional[Dict[str, Any]]:
        for method in ("post", "get"):
            try:
                resp = getattr(self.session, method)(
                    f"{self.config.server_url}/api/tasks/next", timeout=10
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                if not data:
                    return None
                if isinstance(data, dict) and "task" in data:
                    return data.get("task")
                if isinstance(data, dict) and data.get("task_id"):
                    return data
            except Exception:
                pass
        return None

    def _submit_result(self, task_id: str, success: bool, data: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> bool:
        payload = {"success": success, "data": data or {}, "error": error}
        try:
            r = self.session.post(
                f"{self.config.server_url}/api/tasks/{task_id}/result",
                json=payload,
                timeout=20,
            )
            return r.status_code == 200
        except Exception as e:
            self.logger.error(f"Submit result failed: {e}")
            return False

    def _run_youtube_learn(self, data: Dict[str, Any]) -> Dict[str, Any]:
        url = str(data.get("url") or data.get("video_url") or "").strip()
        if not url:
            raise ValueError("Missing 'url' in task data")

        # Build config with safe, small defaults
        cfg = YouTubeLearnerConfig(
            enable_ocr=bool(data.get("enable_ocr", False)),
            max_frames=int(data.get("max_frames", 3)),
            frame_interval=float(data.get("frame_interval", 30.0)),
            sample_clip_seconds=int(data.get("clip_seconds", 10)),
        )

        learner = YouTubeLearner(cfg)

        import asyncio
        analysis = asyncio.run(learner.analyze_video(url))
        out_file = cfg.output_dir / f"{analysis.video_id}_analysis.json"
        
        result = {
            "video_id": analysis.video_id,
            "title": analysis.title,
            "keywords": analysis.keywords[:10],
            "summary": analysis.summary,
            "output_file": str(out_file),
            "subtitles": len(analysis.subtitles),
            "frames": len(analysis.frames),
            "duration": analysis.duration,
        }
        
        # Optional: Execute RPA if enabled and tutorial detected
        if self.config.enable_rpa_execution and analysis.summary:
            try:
                rpa_result = self._execute_rpa_from_tutorial(analysis.summary)
                result["rpa_execution"] = rpa_result
                self.logger.info(f"RPA execution completed: {rpa_result['total_steps']} steps")
            except Exception as e:
                self.logger.error(f"RPA execution failed: {e}")
                result["rpa_execution"] = {"error": str(e)}
        
        return result
    
    def _execute_rpa_from_tutorial(self, tutorial_text: str) -> Dict[str, Any]:
        """Execute RPA actions from tutorial text"""
        mode_map = {
            "DRY_RUN": ExecutionMode.DRY_RUN,
            "LIVE": ExecutionMode.LIVE,
            "VERIFY_ONLY": ExecutionMode.VERIFY_ONLY,
        }
        
        exec_config = ExecutionConfig(
            mode=mode_map.get(self.config.rpa_mode, ExecutionMode.DRY_RUN),
            enable_verification=self.config.rpa_enable_verification,
            enable_failsafe=self.config.rpa_enable_failsafe,
            timeout=30.0,
            max_retries=2,
        )
        
        engine = ExecutionEngine(exec_config)
        result = engine.execute_tutorial(tutorial_text)
        
        return {
            "success": result.success,
            "total_actions": result.total_actions,
            "executed_actions": result.executed_actions,
            "verified_actions": result.verified_actions,
            "failed_actions": result.failed_actions,
            "execution_time": result.execution_time,
            "execution_mode": self.config.rpa_mode,
            "errors": result.errors,
        }


    def _run_with_retry(self, func, *args, **kwargs):
        """재시도 래퍼: func 실행 시 실패하면 max_retries까지 지수 백오프하며 재시도"""
        last_exc = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                backoff = min(self.config.backoff_base * (2 ** (attempt - 1)), self.config.backoff_max)
                self.logger.warning(f"[Retry {attempt}/{self.config.max_retries}] {func.__name__} failed: {e}. Retrying in {backoff:.1f}s...")
                time.sleep(backoff)
        # 최종 실패
        self.logger.error(f"All retries failed for {func.__name__}: {last_exc}")
        if last_exc is not None:
            raise last_exc
        else:
            raise RuntimeError(f"Unknown error in {func.__name__} (no exception captured)")

    def run(self):
        self.logger.info("Starting YouTube Worker...")
        if not self._health():
            self.logger.warning("Task Queue server not healthy yet; will keep polling...")

        while True:
            task = self._fetch_next_task()
            if not task:
                time.sleep(self.config.poll_interval)
                continue

            task_id = str(task.get("task_id") or "")
            ttype = task.get("type")
            data = task.get("data", {}) or {}
            if not task_id:
                time.sleep(self.config.poll_interval)
                continue

            try:
                if ttype == "youtube_learn":
                    # 자동 재시도 래퍼 적용
                    result = self._run_with_retry(self._run_youtube_learn, data)
                    ok = self._submit_result(task_id, True, result, None)
                    self.logger.info(f"Submitted youtube_learn result: {'OK' if ok else 'FAIL'}")
                else:
                    err = f"Unsupported task type: {ttype}"
                    self._submit_result(task_id, False, {}, err)
                    self.logger.warning(err)
            except Exception as e:
                # 에러 발생 시 화면 캡처 및 OCR 결과 저장
                capture_info = None
                try:
                    capture_info = capture_and_ocr_on_error(prefix=f"ytworker_{task_id}")
                except Exception as ce:
                    self.logger.error(f"Error during error capture: {ce}")
                err_msg = str(e)
                if capture_info:
                    err_msg += f"\n[ScreenCapture] {capture_info['screenshot_path']}\n[OCR] {capture_info['ocr_path']}\n[Preview] {capture_info['ocr_preview']}"
                self._submit_result(task_id, False, {}, err_msg)
                self.logger.exception("Task failed (after retries)")

            time.sleep(self.config.poll_interval)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="YouTube Worker for Task Queue Server")
    p.add_argument("--server", default="http://127.0.0.1:8091", help="Task Queue server base URL")
    p.add_argument("--interval", type=float, default=0.5, help="Polling interval seconds")
    p.add_argument("--worker-name", default="youtube-worker", help="Worker name for bookkeeping")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    # RPA execution arguments
    p.add_argument("--enable-rpa", action="store_true", help="Enable RPA execution from tutorials")
    p.add_argument("--rpa-mode", default="DRY_RUN", choices=["DRY_RUN", "LIVE", "VERIFY_ONLY"], help="RPA execution mode")
    p.add_argument("--rpa-verify", action="store_true", help="Enable RPA verification")
    p.add_argument("--rpa-failsafe", action="store_true", default=True, help="Enable RPA failsafe")
    # Retry arguments
    p.add_argument("--max-retries", type=int, default=3, help="Max retries per task on failure")
    p.add_argument("--backoff-base", type=float, default=1.0, help="Base seconds for exponential backoff")
    p.add_argument("--backoff-max", type=float, default=10.0, help="Max seconds for exponential backoff")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None):
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(asctime)s [%(levelname)s] %(message)s")
    cfg = WorkerConfig(
        server_url=args.server,
        poll_interval=args.interval,
        worker_name=args.worker_name,
        log_level=args.log_level,
        enable_rpa_execution=args.enable_rpa,
        rpa_mode=args.rpa_mode,
        rpa_enable_verification=args.rpa_verify,
        rpa_enable_failsafe=args.rpa_failsafe,
        max_retries=args.max_retries,
        backoff_base=args.backoff_base,
        backoff_max=args.backoff_max,
    )
    worker = YouTubeWorker(cfg)
    worker.run()


if __name__ == "__main__":
    main()
