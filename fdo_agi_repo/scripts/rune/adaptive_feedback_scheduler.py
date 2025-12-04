#!/usr/bin/env python3
"""
Adaptive Feedback Loop Scheduler

Adjusts feedback loop interval based on:
- Event rate (YouTube + RPA)
- System load (CPU, Memory)
- Ledger growth rate

Intervals:
- Fast: 5 min (high activity)
- Normal: 10 min (steady state)
- Slow: 30 min (low activity)
- Idle: 60 min (no events)
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timedelta
import psutil
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ROOT / "outputs"


def get_event_rate() -> Tuple[int, int]:
    """Get event counts from last hour."""
    youtube_count = 0
    rpa_count = 0
    cutoff = datetime.utcnow() - timedelta(hours=1)
    
    # Check YouTube augmented ledger
    yt_ledger = ROOT / "outputs" / "resonance_ledger_youtube_augmented.jsonl"
    if yt_ledger.exists():
        for line in yt_ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                evt = json.loads(line)
                ts = datetime.fromisoformat(evt["ts"].replace("Z", "+00:00"))
                if ts >= cutoff:
                    youtube_count += 1
            except:
                pass
    
    # Check RPA results from task queue
    try:
        import requests
        resp = requests.get("http://127.0.0.1:8091/api/results", timeout=2)
        if resp.ok:
            results = resp.json()
            for r in results:
                ts = datetime.fromisoformat(r["completed_at"])
                if ts >= cutoff:
                    rpa_count += 1
    except:
        pass
    
    return youtube_count, rpa_count


def get_system_load() -> Dict[str, float]:
    """Get current system load."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_io": psutil.disk_io_counters().read_count + psutil.disk_io_counters().write_count
    }


def calculate_interval(youtube_events: int, rpa_events: int, load: Dict[str, float]) -> int:
    """
    Calculate optimal interval in minutes.
    
    Rules:
    - High activity (>20 events/hour): 5 min
    - Medium activity (5-20 events/hour): 10 min
    - Low activity (1-5 events/hour): 30 min
    - Idle (0 events/hour): 60 min
    - High load (CPU>80% or Mem>85%): double interval
    """
    total_events = youtube_events + rpa_events
    
    # Base interval by event rate
    if total_events > 20:
        interval = 5
    elif total_events >= 5:
        interval = 10
    elif total_events >= 1:
        interval = 30
    else:
        interval = 60
    
    # Adjust for system load
    if load["cpu_percent"] > 80 or load["memory_percent"] > 85:
        interval = min(interval * 2, 120)  # cap at 2 hours
    
    return interval


def main() -> int:
    """Calculate and save adaptive interval."""
    print("[adaptive] Checking event rates...")
    youtube, rpa = get_event_rate()
    print(f"[adaptive] YouTube: {youtube}, RPA: {rpa} (last hour)")
    
    print("[adaptive] Checking system load...")
    load = get_system_load()
    print(f"[adaptive] CPU: {load['cpu_percent']:.1f}%, Mem: {load['memory_percent']:.1f}%")
    
    interval = calculate_interval(youtube, rpa, load)
    print(f"[adaptive] Recommended interval: {interval} minutes")
    
    # Save recommendation
    recommendation = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "interval_minutes": interval,
        "reasoning": {
            "youtube_events_1h": youtube,
            "rpa_events_1h": rpa,
            "total_events": youtube + rpa,
            "cpu_percent": load["cpu_percent"],
            "memory_percent": load["memory_percent"]
        }
    }
    
    output_path = OUTPUTS / "adaptive_feedback_interval.json"
    output_path.write_text(json.dumps(recommendation, indent=2), encoding="utf-8")
    print(f"[adaptive] Saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
