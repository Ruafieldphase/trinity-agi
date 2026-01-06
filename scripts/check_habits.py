import json
from pathlib import Path

history_file = Path("outputs/thought_stream_history.jsonl")
if not history_file.exists():
    print("History file not found")
else:
    with open(history_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"Total cycles: {len(lines)}")
    print("Recent 10 decisions:")
    for line in lines[-10:]:
        if line.strip():
            data = json.loads(line)
            decision = data.get('decision', 'N/A')
            habits = data.get('active_habits', [])
            print(f"  - {decision} (Habits: {len(habits)})")
