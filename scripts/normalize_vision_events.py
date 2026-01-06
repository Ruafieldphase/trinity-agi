#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from workspace_root import get_workspace_root


ROOT = get_workspace_root()
VISION_LOG = ROOT / "memory" / "vision_events.jsonl"


def _load_events(text: str) -> List[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)]
        if isinstance(data, dict):
            return [data]
    except Exception:
        pass

    decoder = json.JSONDecoder()
    idx = 0
    length = len(text)
    events: List[Dict[str, Any]] = []
    while idx < length:
        while idx < length and text[idx].isspace():
            idx += 1
        if idx >= length:
            break
        try:
            obj, end = decoder.raw_decode(text, idx)
        except Exception:
            # Fallback: line-based parsing
            events = []
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if isinstance(obj, dict):
                    events.append(obj)
            return events
        if isinstance(obj, dict):
            events.append(obj)
        idx = end
    return events


def main() -> int:
    if not VISION_LOG.exists():
        return 0
    text = VISION_LOG.read_text(encoding="utf-8", errors="ignore")
    events = _load_events(text)
    if not events:
        return 0
    tmp = VISION_LOG.with_suffix(".jsonl.tmp")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    with tmp.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    os.replace(tmp, VISION_LOG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
