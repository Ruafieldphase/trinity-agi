#!/usr/bin/env python3
"""
Health Gate Manual Reset

Health gate를 수동으로 초기화하여 정상 상태로 복원합니다.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
OUTPUTS_DIR = REPO_ROOT / "outputs"
HEALTH_GATE_STATE = OUTPUTS_DIR / "health_gate_state.json"


def log(message: str):
    """로그 출력"""
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"[{timestamp}] {message}")


def load_gate_state():
    """현재 gate 상태 로드"""
    if not HEALTH_GATE_STATE.exists():
        log(f"⚠️  Health gate state file not found: {HEALTH_GATE_STATE}")
        return None
    
    try:
        with open(HEALTH_GATE_STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"❌ Failed to load gate state: {e}")
        return None


def save_gate_state(state: dict):
    """Gate 상태 저장"""
    try:
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(HEALTH_GATE_STATE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        log(f"✅ Gate state saved to {HEALTH_GATE_STATE}")
        return True
    except Exception as e:
        log(f"❌ Failed to save gate state: {e}")
        return False


def reset_gate():
    """Health gate 수동 리셋"""
    log("🔄 Starting health gate manual reset...")
    
    # 현재 상태 로드
    current_state = load_gate_state()
    if current_state:
        log(f"📊 Current state:")
        log(f"   - gate_open: {current_state.get('gate_open')}")
        log(f"   - failure_streak: {current_state.get('failure_streak')}")
        log(f"   - success_streak: {current_state.get('success_streak')}")
        log(f"   - cooldown_until: {current_state.get('cooldown_until')}")
        log(f"   - last_updated: {current_state.get('last_updated')}")
    
    # 새로운 상태: gate open, streak 초기화
    new_state = {
        "failure_streak": 0,
        "success_streak": 3,  # 3회 연속 성공으로 설정
        "cooldown_until": None,
        "gate_open": True,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "manual_reset": True,
        "reset_reason": "Manual reset via reset_health_gate.py"
    }
    
    log("🔧 Applying new state:")
    log(f"   - gate_open: True")
    log(f"   - failure_streak: 0")
    log(f"   - success_streak: 3")
    log(f"   - cooldown_until: None")
    
    if save_gate_state(new_state):
        log("✅ Health gate successfully reset!")
        log("🚀 AGI can now accept new tasks.")
        return 0
    else:
        log("❌ Failed to reset health gate.")
        return 1


def main():
    """메인 실행"""
    return reset_gate()


if __name__ == "__main__":
    import sys
    sys.exit(main())
