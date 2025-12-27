#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

# C:\workspace\agi\scripts\rhythm_whisper_intake.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(SCRIPT_DIR)
LEDGER_PATH = os.path.join(WORKSPACE_ROOT, "memory", "resonance_ledger.jsonl")

def whisper(message: str):
    """사용자의 속삭임을 Resonance Ledger에 기록합니다."""
    if not message.strip():
        print("❌ 메시지가 비어 있습니다.")
        return

    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "type": "user_whisper",
        "source": "rhythm_whisper",
        "message": message,
        "metadata": {
            "intent": "alignment",
            "priority": "normal"
        }
    }

    try:
        os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
        with open(LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"🌊 시안에게 속삭임을 전달했습니다: \"{message}\"")
    except Exception as e:
        print(f"❌ 속삭임 전달 실패: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python scripts/rhythm_whisper_intake.py \"시안에게 하고 싶은 말\"")
    else:
        msg = " ".join(sys.argv[1:])
        whisper(msg)
