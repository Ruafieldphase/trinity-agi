import json
from pathlib import Path

def get_latest_session_id():
    history_file = Path.home() / ".codex" / "history.jsonl"
    if not history_file.exists():
        return None
    
    last_session_id = None
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        last_session_id = data.get("session_id")
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Error reading history: {e}")
        return None
    
    return last_session_id

if __name__ == "__main__":
    sid = get_latest_session_id()
    if sid:
        print(sid)
    else:
        exit(1)
