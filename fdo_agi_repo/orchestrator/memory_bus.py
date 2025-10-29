from __future__ import annotations
import json, time, os
from typing import Any, Dict, List

MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory")
COORD_PATH = os.path.join(MEMORY_DIR, "coordinate.jsonl")
LEDGER_PATH = os.path.join(MEMORY_DIR, "resonance_ledger.jsonl")

def _append_jsonl(path: str, obj: Dict[str, Any]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def append_coordinate(record: Dict[str, Any]) -> None:
    record.setdefault("ts", time.time())
    _append_jsonl(COORD_PATH, record)

def append_ledger(record: Dict[str, Any]) -> None:
    record.setdefault("ts", time.time())
    _append_jsonl(LEDGER_PATH, record)

def tail_ledger(n: int = 20) -> List[Dict[str, Any]]:
    if not os.path.exists(LEDGER_PATH):
        return []
    lines = open(LEDGER_PATH, "r", encoding="utf-8").read().splitlines()
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out

def snapshot_memory() -> Dict[str, Any]:
    return {"coordinate_path": COORD_PATH, "ledger_path": LEDGER_PATH}
