import json
import sys
from datetime import datetime
from pathlib import Path

def main():
    res = {
        "ok": False,
        "error": "offline_stub_active",
        "reason": "network/external_execution_forbidden",
        "tool": "code_executor",
        "timestamp": datetime.now().isoformat()
    }
    try:
        ws = Path(__file__).resolve().parents[2]
        out = ws / "outputs" / "tools" / "tool_run_latest.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    print(json.dumps(res))

if __name__ == "__main__":
    main()
