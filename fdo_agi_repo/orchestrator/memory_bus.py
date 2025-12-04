from __future__ import annotations
import json, time, os
from typing import Any, Dict, List
import psutil  # For system metrics

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

def _enrich_with_metrics(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 1 Goal #2: Increase Data Collection
    Automatically enrich ledger events with system metrics
    """
    # Skip if already has metrics (prevent double-enrichment)
    if "metrics" in record and record["metrics"]:
        return record
    
    try:
        # Collect system metrics
        metrics = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_mb": psutil.virtual_memory().used / (1024 * 1024),
            "disk_io_read_mb": psutil.disk_io_counters().read_bytes / (1024 * 1024) if psutil.disk_io_counters() else 0,
            "disk_io_write_mb": psutil.disk_io_counters().write_bytes / (1024 * 1024) if psutil.disk_io_counters() else 0,
            "process_count": len(psutil.pids()),
        }
        
        # Add network metrics if available
        net_io = psutil.net_io_counters()
        if net_io:
            metrics["net_sent_mb"] = net_io.bytes_sent / (1024 * 1024)
            metrics["net_recv_mb"] = net_io.bytes_recv / (1024 * 1024)
        
        record["metrics"] = metrics
    except Exception as e:
        # Graceful degradation: add error metric but don't fail
        record["metrics"] = {"error": str(e)}
    
    return record

def append_ledger(record: Dict[str, Any]) -> None:
    record.setdefault("ts", time.time())
    # Phase 1 Goal #2: Auto-enrich with metrics
    record = _enrich_with_metrics(record)
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
