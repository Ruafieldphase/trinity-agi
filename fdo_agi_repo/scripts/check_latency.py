import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from workspace_utils import find_fdo_root

ledger_path = find_fdo_root(Path(__file__).parent) / "memory" / "resonance_ledger.jsonl"
lines = ledger_path.read_text(encoding="utf-8").splitlines()[-50:]

events = []
for line in lines:
    try:
        e = json.loads(line)
        if "thesis" in e.get("event", "") or "antithesis" in e.get("event", ""):
            events.append(e)
    except Exception:
        continue

print("=== Recent Thesis/Antithesis Events ===")
for e in events:
    event_name = e.get("event", "unknown")
    duration = e.get("duration_sec")
    task_id = e.get("task_id", "N/A")[:8]
    
    if duration is not None:
        print(f"  {event_name}: {duration:.2f}s (task: {task_id})")
    else:
        print(f"  {event_name} (task: {task_id})")

# 최근 thesis_end와 antithesis_end 찾기
thesis_ends = [e for e in events if e.get("event") == "thesis_end" and "duration_sec" in e]
anti_ends = [e for e in events if e.get("event") == "antithesis_end" and "duration_sec" in e]

if thesis_ends and anti_ends:
    print("\n=== Latest Measurements ===")
    print(f"Thesis: {thesis_ends[-1]['duration_sec']:.2f}s")
    print(f"Antithesis: {anti_ends[-1]['duration_sec']:.2f}s")
    print(f"Combined: {thesis_ends[-1]['duration_sec'] + anti_ends[-1]['duration_sec']:.2f}s")
