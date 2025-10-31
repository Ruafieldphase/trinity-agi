"""
RPA Worker
Phase 2.5 Day 5: Task Queue 폴링 → RPA 명령 실행 → 결과 제출

- 서버 엔드포인트 (ion-mentoring/task_queue_server.py 기준):
  - GET/POST /api/tasks/next        → 다음 작업 가져오기
  - POST      /api/tasks/{id}/result → 결과 제출 (body: {success, data?, error?})
  - GET       /api/health            → 상태

지원 액션 (RPAAction과 호환):
  - click: 좌표 클릭 또는 템플릿/텍스트 기반 클릭
  - type: 텍스트 입력
  - hotkey: 단축키 조합
  - screenshot: 화면 캡처 (옵션: region, save_path)
  - ocr: OCR (tesseract/easyocr)
  - find_element: 템플릿/텍스트 찾기
  - wait: 대기
  - open_browser: URL 열기

주의: PyAutoGUI가 설치되지 않은 환경을 고려하여 선택적 임포트 처리합니다.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from typing import Any, Dict, Optional, Tuple, List

# 에러 캡처 유틸
try:
    # Package execution
    from .error_capture_utils import capture_and_ocr_on_error
except ImportError:
    # Direct script execution fallback
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).parent))
    from error_capture_utils import capture_and_ocr_on_error

import requests

# Optional runtime deps
try:
    import pyautogui  # type: ignore
    PYAUTO_AVAILABLE = True
    # Fail-safe off for deterministic behavior
    pyautogui.FAILSAFE = False
except Exception as e:  # broad: import/runtime errors
    PYAUTO_AVAILABLE = False

# Local integrations - handle both direct execution and package import
try:
    from .rpa_bridge import RPAAction, RPACommand, RPAResult
    from .screen_recognizer import ScreenRecognizer
except ImportError:
    # Direct execution - add parent to path
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from rpa_bridge import RPAAction, RPACommand, RPAResult
    from screen_recognizer import ScreenRecognizer


@dataclass
class WorkerConfig:
    server_url: str = "http://127.0.0.1:8091"
    poll_interval: float = 0.5
    worker_name: str = "rpa-worker"
    results_timeout: float = 30.0


class RPAWorker:
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.logger = logging.getLogger("RPAWorker")
        self.session = requests.Session()
        # Identify worker to server for lease tracking/diagnostics
        self.session.headers.update({"X-Worker-Name": self.config.worker_name})
        self.screen = ScreenRecognizer()

    # ------------- HTTP helpers -------------
    def _health(self) -> bool:
        try:
            r = self.session.get(f"{self.config.server_url}/api/health", timeout=5)
            if r.status_code == 200 and r.json().get("status") == "ok":
                return True
        except Exception:
            pass
        return False

    def _fetch_next_task(self) -> Optional[Dict[str, Any]]:
        # Server supports both GET and POST for compatibility
        for method in ("post", "get"):
            try:
                resp = getattr(self.session, method)(
                    f"{self.config.server_url}/api/tasks/next", timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.logger.debug(f"Received response: {data}")
                    # FastAPI server returns empty object {"task": null} when queue empty
                    if not data:
                        return None
                    # If wrapped (some servers return {"task": null} or {"task": {...}})
                    if isinstance(data, dict) and "task" in data:
                        self.logger.debug("Detected wrapped response format")
                        return data.get("task")  # Return unwrapped task or None
                    # Direct task object (current server behavior)
                    if isinstance(data, dict) and "task_id" in data:
                        self.logger.info(f"Fetched task: {data.get('task_id')} (type: {data.get('type')})")
                        return data
                    self.logger.warning(f"Unrecognized response format: {data}")
                    return None
            except Exception as e:
                self.logger.debug(f"fetch_next_task {method} error: {e}")
        return None

    def _submit_result(self, task_id: str, success: bool, data: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> bool:
        payload = {
            "success": success,
            "data": data or {},
            "error": error
        }
        try:
            r = self.session.post(
                f"{self.config.server_url}/api/tasks/{task_id}/result",
                json=payload,
                timeout=15
            )
            return r.status_code == 200
        except Exception as e:
            self.logger.error(f"Submit result failed: {e}")
            return False

    # ------------- Action executors -------------
    def _ensure_pyauto(self):
        if not PYAUTO_AVAILABLE:
            raise RuntimeError("pyautogui not installed. Install with: pip install pyautogui")

    def _do_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_pyauto()
        x = params.get("x")
        y = params.get("y")
        button = params.get("button", "left")
        clicks = int(params.get("clicks", 1))
        interval = float(params.get("interval", 0.0))
        duration = float(params.get("duration", 0.1))

        # If no direct coords, try template/text search
        if x is None or y is None:
            screenshot = self.screen.capture_screen()
            if "template" in params:
                match = self.screen.find_template(screenshot, params["template"], threshold=float(params.get("threshold", 0.8)))
                if match.found and match.location:
                    x, y = match.location
            elif "text" in params:
                loc = self.screen.find_text(screenshot, params["text"], engine=params.get("engine", "tesseract"))
                if loc:
                    x, y = loc

        if x is None or y is None:
            raise ValueError("click requires x,y or resolvable template/text")

        pyautogui.moveTo(int(x), int(y), duration=duration)
        pyautogui.click(clicks=clicks, interval=interval, button=button)
        return {"x": int(x), "y": int(y), "button": button, "clicks": clicks}

    def _do_type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_pyauto()
        text = params.get("text", "")
        interval = float(params.get("interval", 0.0))
        if not isinstance(text, str):
            raise ValueError("type.text must be a string")
        pyautogui.typewrite(text, interval=interval)
        return {"typed": len(text)}

    def _do_hotkey(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_pyauto()
        keys = params.get("keys")
        if not keys or not isinstance(keys, (list, tuple)):
            raise ValueError("hotkey.keys must be a list of key names")
        pyautogui.hotkey(*[str(k) for k in keys])
        return {"keys": [str(k) for k in keys]}

    def _do_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        region = params.get("region")  # [x,y,w,h]
        save_path = params.get("save_path")
        if save_path is None:
            out_dir = Path("outputs")
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            save_path = str(out_dir / f"screenshot_{ts}.png")
        img = self.screen.capture_screen(region=tuple(region) if region else None, save_path=save_path)
        h, w = img.shape[:2]
        return {"path": save_path, "width": w, "height": h}

    def _do_ocr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        source = params.get("source")  # path or None for live capture
        lang = params.get("lang", "eng+kor")
        engine = params.get("engine", "tesseract")
        if source:
            image = source
        else:
            image = self.screen.capture_screen()
        if engine == "easyocr":
            results = self.screen.ocr_easyocr(image, languages=params.get("languages", ["en", "ko"]))
            return {"engine": "easyocr", "count": len(results), "results": [r.to_dict() for r in results[:200]]}
        else:
            text = self.screen.ocr_tesseract(image, lang=lang)
            preview = text[:1000]
            return {"engine": "tesseract", "chars": len(text), "preview": preview}

    def _do_find_element(self, params: Dict[str, Any]) -> Dict[str, Any]:
        screenshot = self.screen.capture_screen()
        if "template" in params:
            match = self.screen.find_template(screenshot, params["template"], threshold=float(params.get("threshold", 0.8)))
            return match.to_dict()
        elif "text" in params:
            loc = self.screen.find_text(screenshot, params["text"], engine=params.get("engine", "tesseract"))
            return {"found": bool(loc), "location": loc}
        else:
            raise ValueError("find_element requires 'template' or 'text'")

    def _do_wait(self, params: Dict[str, Any]) -> Dict[str, Any]:
        seconds = float(params.get("seconds", 1.0))
        time.sleep(seconds)
        return {"slept": seconds}

    def _do_open_browser(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = params.get("url")
        if not url:
            raise ValueError("open_browser requires 'url'")
        webbrowser.open(url)
        return {"opened": url}

    def _execute_rpa_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Normalize to RPACommand
        try:
            cmd = RPACommand.from_dict(data)
        except Exception:
            # Accept direct schema: {action: 'click', params:{...}}
            cmd = RPACommand(action=RPAAction(str(data.get("action", "wait"))), params=data.get("params", {}))

        action = cmd.action.value
        params = cmd.params or {}
        self.logger.info(f"[RPA] Execute: {action} | params={json.dumps(params)[:200]}")

        start = time.time()
        try:
            if action == RPAAction.CLICK.value:
                out = self._do_click(params)
            elif action == RPAAction.TYPE.value:
                out = self._do_type(params)
            elif action == RPAAction.HOTKEY.value:
                out = self._do_hotkey(params)
            elif action == RPAAction.SCREENSHOT.value:
                out = self._do_screenshot(params)
            elif action == RPAAction.OCR.value:
                out = self._do_ocr(params)
            elif action == RPAAction.FIND_ELEMENT.value:
                out = self._do_find_element(params)
            elif action == RPAAction.WAIT.value:
                out = self._do_wait(params)
            elif action == RPAAction.OPEN_BROWSER.value:
                out = self._do_open_browser(params)
            else:
                raise ValueError(f"Unsupported action: {action}")

            elapsed = time.time() - start
            return {"success": True, "data": {**out, "execution_time": round(elapsed, 3)}}
        except Exception as e:
            elapsed = time.time() - start
            return {"success": False, "error": str(e), "data": {"execution_time": round(elapsed, 3)}}

    # ------------- Main loop -------------
    def run(self):
        self.logger.info("Starting RPA Worker...")
        healthy = self._health()
        if not healthy:
            self.logger.warning("Task Queue server not healthy yet. Proceeding with polling...")

        while True:
            try:
                task = self._fetch_next_task()
                if not task:
                    time.sleep(self.config.poll_interval)
                    continue

                raw_task_id = task.get("task_id") or task.get("id")
                if not isinstance(raw_task_id, str) or not raw_task_id:
                    self.logger.error(f"Invalid task id in payload: {task}")
                    time.sleep(self.config.poll_interval)
                    continue
                task_id: str = raw_task_id
                task_type = task.get("type")
                data = task.get("data", {})
                self.logger.info(f"Dequeued task: {task_id} (type={task_type})")

                # Execute
                if task_type == "ping":
                    result_data = {"message": "pong", "worker": self.config.worker_name, "timestamp": datetime.utcnow().isoformat() + "Z"}
                    ok = self._submit_result(task_id, True, result_data, None)
                    self.logger.info(f"Submitted ping result: {'OK' if ok else 'FAIL'}")
                elif task_type in ("rpa_command", "rpa"):
                    exec_out = self._execute_rpa_command(data)
                    ok = self._submit_result(task_id, bool(exec_out.get("success", False)), exec_out.get("data") or {}, exec_out.get("error"))
                    self.logger.info(f"Submitted rpa result: {'OK' if ok else 'FAIL'} | success={exec_out.get('success')}")
                elif task_type in ("screenshot", "ocr", "wait", "open_browser"):
                    # Compatibility: map simple task types to RPA command actions
                    mapped_cmd = {"action": task_type, "params": data or {}}
                    exec_out = self._execute_rpa_command(mapped_cmd)
                    ok = self._submit_result(task_id, bool(exec_out.get("success", False)), exec_out.get("data") or {}, exec_out.get("error"))
                    self.logger.info(
                        f"Submitted mapped result: {'OK' if ok else 'FAIL'} | type={task_type} success={exec_out.get('success')}"
                    )
                else:
                    # Unknown task → mark failed
                    err = f"Unsupported task type: {task_type}"
                    ok = self._submit_result(task_id, False, {}, err)
                    self.logger.warning(f"Submitted failure for unknown task: {'OK' if ok else 'FAIL'} | {err}")
            except Exception as e:
                # 에러 발생 시 화면 캡처 및 OCR 결과 저장
                capture_info = None
                try:
                    capture_info = capture_and_ocr_on_error(prefix=f"rpaworker_{task_id}")
                except Exception as ce:
                    self.logger.error(f"Error during error capture: {ce}")
                err_msg = str(e)
                if capture_info:
                    err_msg += f"\n[ScreenCapture] {capture_info['screenshot_path']}\n[OCR] {capture_info['ocr_path']}\n[Preview] {capture_info['ocr_preview']}"
                self._submit_result(task_id if 'task_id' in locals() else 'unknown', False, {}, err_msg)
                self.logger.exception("Task failed (after retries)")

            # small breather to avoid tight loop
            time.sleep(self.config.poll_interval)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RPA Worker for Task Queue Server")
    p.add_argument("--server", default="http://127.0.0.1:8091", help="Task Queue server base URL")
    p.add_argument("--interval", type=float, default=0.5, help="Polling interval seconds")
    p.add_argument("--worker-name", default="rpa-worker", help="Worker name for bookkeeping")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None):
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(asctime)s [%(levelname)s] %(message)s")
    cfg = WorkerConfig(server_url=args.server, poll_interval=args.interval, worker_name=args.worker_name)
    worker = RPAWorker(cfg)
    worker.run()


if __name__ == "__main__":
    main()
