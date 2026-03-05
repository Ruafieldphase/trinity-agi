#!/usr/bin/env python3
"""
Background Self Heartbeat Bridge
- Background Self API (port 8102)의 상태를 주기적으로 파일로 기록
- 메타 감독 시스템(rhythm_health_checker)이 이 파일을 읽어 배경자아 연결 상태를 판단
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

BACKGROUND_SELF_URL = "http://127.0.0.1:8102"
OUTPUTS_DIR = Path("C:/workspace/agi/outputs")
THOUGHT_STREAM_FILE = OUTPUTS_DIR / "thought_stream_latest.json"
MITOCHONDRIA_FILE = OUTPUTS_DIR / "mitochondria_state.json"
HEARTBEAT_INTERVAL = 60  # 1분 주기


def fetch_json(endpoint: str) -> dict:
    """Background Self API에서 JSON 가져오기"""
    try:
        url = f"{BACKGROUND_SELF_URL}{endpoint}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}


def write_json(path: Path, data: dict):
    """원자적 JSON 파일 쓰기"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def run_heartbeat_cycle():
    """한 사이클 실행"""
    now = datetime.now().isoformat()

    # 1. health 체크 → thought_stream으로 기록
    health = fetch_json("/health")
    context = fetch_json("/context")

    thought_stream = {
        "timestamp": now,
        "source": "background_self_api",
        "health": health,
        "field_status": context.get("field_status", {}),
        "rejuvenation": context.get("rejuvenation", {}),
        "observation": context.get("observation", {}),
        "connected": "error" not in health,
    }
    write_json(THOUGHT_STREAM_FILE, thought_stream)

    # 2. 에너지 상태 (이미 context에 포함된 정보를 활용)
    mitochondria = {
        "timestamp": now,
        "source": "background_self_api",
        "integrity_status": "connected" if "error" not in health else "disconnected",
        "symmetry": context.get("field_status", {}).get("symmetry", 0),
        "momentum": context.get("field_status", {}).get("momentum", 0),
        "chaos_mode": context.get("field_status", {}).get("chaos_mode", False),
        "connected": "error" not in health,
    }
    write_json(MITOCHONDRIA_FILE, mitochondria)

    connected = thought_stream["connected"] and mitochondria["connected"]
    return connected


def main():
    """메인 루프"""
    print("🌊 Background Self Heartbeat Bridge 시작")
    print(f"   API: {BACKGROUND_SELF_URL}")
    print(f"   출력: {THOUGHT_STREAM_FILE}")
    print(f"   주기: {HEARTBEAT_INTERVAL}초")
    print()

    cycle = 0
    while True:
        cycle += 1
        try:
            connected = run_heartbeat_cycle()
            status = "✅ 연결됨" if connected else "⚠️ 단절"
            print(f"  [{cycle}] {datetime.now().strftime('%H:%M:%S')} {status}")
        except Exception as e:
            print(f"  [{cycle}] ❌ 오류: {e}")

        time.sleep(HEARTBEAT_INTERVAL)


if __name__ == "__main__":
    # 단독 실행: 한 번만 실행하고 종료 (--once 옵션)
    import sys
    if "--once" in sys.argv:
        connected = run_heartbeat_cycle()
        status = "connected" if connected else "disconnected"
        print(f"Background Self: {status}")
        sys.exit(0 if connected else 1)
    else:
        main()
