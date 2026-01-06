import json
import sys
from datetime import datetime
from pathlib import Path
from workspace_root import get_workspace_root
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def main():
    res = {
        "ok": False,
        "error": "offline_stub_active",
        "reason": "network/external_execution_forbidden",
        "tool": "file_read",
        "timestamp": datetime.now().isoformat()
    }
    # Write to log
    try:
        ws = get_workspace_root()
        out = ws / "outputs" / "tools" / "tool_run_latest.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    print(json.dumps(res))

if __name__ == "__main__":
    main()
