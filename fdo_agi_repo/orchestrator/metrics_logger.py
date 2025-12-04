"""
Lightweight JSONL event logger for operational telemetry.

Usage:
    logger = JsonlEventLogger("fdo_agi_repo/memory/glymphatic_ledger.jsonl", component="glymphatic")
    logger.log("decision", {"workload": 42.5})

Writes one JSON object per line with fields:
    - ts: unix epoch seconds (float)
    - timestamp: ISO-8601 local time
    - event: event name (str)
    - component: logical component (optional, str)
    - payload: arbitrary dict payload
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional
import json
import time


@dataclass
class JsonlEventLogger:
    path: Path | str
    component: Optional[str] = None

    def __post_init__(self) -> None:
        self._path = Path(self.path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def log(self, event: str, payload: Optional[Dict[str, Any]] = None) -> None:
        payload = payload or {}
        record: Dict[str, Any] = {
            "ts": time.time(),
            "timestamp": datetime.now().isoformat(),
            "event": str(event),
            "payload": payload,
        }
        if self.component:
            record["component"] = self.component

        line = json.dumps(record, ensure_ascii=False)
        with self._lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

