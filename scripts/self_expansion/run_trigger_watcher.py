"""
코어 트리거 파일을 감지해 자율 실행하는 워처.

동작:
- 기본 트리거 위치: /home/bino/agi/signals/lua_trigger.json (리눅스)
- 대체: {workspace_root}/signals/lua_trigger.json (윈도우/로컬 테스트)
- 트리거 발견 → Self-Expansion Engine 단일 사이클 실행 → 상태를 outputs/sync_cache/self_expansion_state.json에 기록 → 트리거 삭제

사용 예:
    python scripts/self_expansion/run_trigger_watcher.py --interval 5
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

SCRIPTS_DIR = get_workspace_root()
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from workspace_root import get_workspace_root

ROOT = get_workspace_root()
sys.path.append(str(ROOT))

from scripts.self_expansion import SelfExpansionEngine  # noqa: E402


def resolve_trigger_path(root: Path) -> Path:
    # On Windows, always prefer workspace-local path (avoid split-brain triggers).
    if os.name != "posix":
        return root / "signals" / "lua_trigger.json"
    linux_path = Path("/home/bino/agi/signals/lua_trigger.json")
    if linux_path.exists():
        return linux_path
    return root / "signals" / "lua_trigger.json"


def load_trigger(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
    except Exception:
        return None


def handle_trigger(root: Path, trigger_path: Path) -> None:
    engine = SelfExpansionEngine(root)
    result = engine.run_once()

    cache_dir = root / "outputs" / "sync_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    state_file = cache_dir / "self_expansion_state.json"
    try:
        state_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    try:
        trigger_path.unlink(missing_ok=True)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=5, help="polling interval seconds")
    args = parser.parse_args()

    root = ROOT
    trigger_path = resolve_trigger_path(root)
    trigger_path.parent.mkdir(parents=True, exist_ok=True)

    while True:
        if trigger_path.exists():
            handle_trigger(root, trigger_path)
        time.sleep(max(1, args.interval))


if __name__ == "__main__":
    main()
