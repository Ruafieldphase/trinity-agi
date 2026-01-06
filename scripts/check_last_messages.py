import json
from pathlib import Path
from workspace_root import get_workspace_root

ledger_path = get_workspace_root() / "fdo_agi_repo/memory/resonance_ledger.jsonl"

with open(ledger_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Get last 5 entries
for line in lines[-5:]:
    if line.strip():
        try:
            entry = json.loads(line)
            print(f"\n[{entry.get('timestamp', 'NO_TIME')}]")
            print(f"  Source: {entry.get('source', 'NO_SOURCE')}")
            print(f"  Type: {entry.get('type', 'N/A')}")
            if 'message' in entry:
                msg = entry['message']
                if len(msg) > 200:
                    print(f"  Message: {msg[:200]}...")
                else:
                    print(f"  Message: {msg}")
        except Exception as e:
            print(f"  Error parsing: {e}")
