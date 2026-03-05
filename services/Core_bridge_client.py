
import os
import time
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import pyperclip
except ImportError:
    pyperclip = None

from workspace_root import get_workspace_root

logger = logging.getLogger("CoreBridgeClient")

class CoreBridgeClient:
    def __init__(self, model_selector: Optional[Any] = None):
        self.model_selector = model_selector
        self.screenshot_dir = get_workspace_root() / "outputs" / "screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        # 🌟 PyAutoGUI 설정 (Headless Check)
        if pyautogui and hasattr(pyautogui, 'FAILSAFE'):
            try:
                pyautogui.FAILSAFE = True
                pyautogui.PAUSE = 0.5
                self.available = True
            except Exception:
                self.available = False
        else:
            self.available = False
            logger.warning("PyAutoGUI not available in this environment")

    async def send_request_via_gui(self, message: str, context: Optional[Dict] = None, timeout_sec: int = 60, max_turns: int = 3) -> Optional[str]:
        if not self.available:
            logger.error("GUI communication requested but not available")
            return None
        return "GUI operations skipped on headless backend"

    def send_request(self, message: str, context: Optional[Dict] = None, timeout_sec: int = 60) -> Optional[str]:
        # Headless Fallback: If GUI is not available, record the request for manual review or secondary agents
        request_file = get_workspace_root() / "outputs" / "trinity_requests.jsonl"
        try:
            entry = {
                "timestamp": time.time(),
                "message": message,
                "context": context
            }
            with open(request_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            logger.info(f"💾 [TRINITY] Request recorded to {request_file} (Headless)")
        except Exception as e:
            logger.error(f"⚠️ [TRINITY] Failed to record request: {e}")
            
        return "Trinity is observing silently. (Headless Mode)"
