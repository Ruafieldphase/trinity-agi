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

import requests

# Ensure we can import rpa.youtube_learner without relying on PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rpa.youtube_learner import YouTubeLearner, YouTubeLearnerConfig  # type: ignore


@dataclass
class WorkerConfig:
    server_url: str = "http://127.0.0.1:8091"
    poll_interval: float = 0.5
    worker_name: str = "youtube-worker"
    log_level: str = "INFO"


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
        return {
            "video_id": analysis.video_id,
            "title": analysis.title,
            "keywords": analysis.keywords[:10],
            "summary": analysis.summary,
            "output_file": str(out_file),
            "subtitles": len(analysis.subtitles),
            "frames": len(analysis.frames),
            "duration": analysis.duration,
        }

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
                    result = self._run_youtube_learn(data)
                    ok = self._submit_result(task_id, True, result, None)
                    self.logger.info(f"Submitted youtube_learn result: {'OK' if ok else 'FAIL'}")
                else:
                    err = f"Unsupported task type: {ttype}"
                    self._submit_result(task_id, False, {}, err)
                    self.logger.warning(err)
            except Exception as e:
                self._submit_result(task_id, False, {}, str(e))
                self.logger.exception("Task failed")

            time.sleep(self.config.poll_interval)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="YouTube Worker for Task Queue Server")
    p.add_argument("--server", default="http://127.0.0.1:8091", help="Task Queue server base URL")
    p.add_argument("--interval", type=float, default=0.5, help="Polling interval seconds")
    p.add_argument("--worker-name", default="youtube-worker", help="Worker name for bookkeeping")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None):
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(asctime)s [%(levelname)s] %(message)s")
    cfg = WorkerConfig(server_url=args.server, poll_interval=args.interval, worker_name=args.worker_name, log_level=args.log_level)
    worker = YouTubeWorker(cfg)
    worker.run()


if __name__ == "__main__":
    main()
