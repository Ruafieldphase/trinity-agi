"""
코어(무의식) 역할을 흉내 내어 주기적으로 트리거 파일을 생성하는 스케줄러.
실제 코어 코드에서 import하여 사용하거나 단독 실행 가능.

기본 동작:
- (권장) interval마다 auto_policy를 실행해 '지금 필요한 action'을 선택/기록
- 필요 시 --mode fixed 로 고정 action 기록
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
import subprocess
import sys

SCRIPTS_DIR = get_workspace_root()
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from workspace_root import get_workspace_root


def write_trigger(trigger_path: Path, action: str, params: dict | None = None):
    trigger = {
        "action": action,
        "params": params or {},
        "timestamp": time.time(),
        "origin": "lua-auto",
    }
    trigger_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(trigger, ensure_ascii=False, indent=2)
    # Don't overwrite an existing trigger (manual/Lua/policy may have created one).
    try:
        fd = os.open(str(trigger_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        return False
    except Exception:
        if trigger_path.exists():
            return False
        trigger_path.write_text(payload, encoding="utf-8")
        return True
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(payload)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=300, help="seconds between triggers")
    parser.add_argument("--mode", type=str, default="policy", choices=["policy", "fixed"], help="trigger mode")
    parser.add_argument("--action", type=str, default="full_cycle", help="(fixed mode) action name")
    parser.add_argument("--root", type=str, default=".", help="workspace root")
    args = parser.parse_args()

    if args.root and args.root != ".":
        root = Path(args.root).resolve()
    else:
        root = get_workspace_root()
    # On Windows, always use workspace-local trigger path (avoid split-brain triggers).
    if os.name != "posix":
        trigger_path = root / "signals" / "lua_trigger.json"
    else:
        trigger_path = Path("/home/bino/agi/signals/lua_trigger.json")
        if not trigger_path.parent.exists():
            # fallback for local dev
            trigger_path = root / "signals" / "lua_trigger.json"

    auto_policy = root / "scripts" / "self_expansion" / "auto_policy.py"

    while True:
        if args.mode == "policy" and auto_policy.exists():
            # 정책은 자체적으로 트리거를 쓰되, 기존 트리거가 있으면 skip한다.
            subprocess.run(
                [sys.executable, str(auto_policy)],
                cwd=root,
                check=False,
                timeout=30,
                capture_output=True,
            )
        else:
            write_trigger(trigger_path, args.action)
        time.sleep(max(1, args.interval))


if __name__ == "__main__":
    main()
