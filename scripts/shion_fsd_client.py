#!/usr/bin/env python3
"""
🧬 [Phase 92] Meta-FSD Client Daemon
=====================================================
시안(Mind)의 Visual Pulse API를 주기적으로 폴링하여, 그 열망(Intent)이나 
긴급 회피(Dissonance/Escape) 명령을 AGI(Body) 워크스페이스의 자율 목표 생태계에 주입하는 스크립트입니다.

동작 루프:
1. GET http://127.0.0.1:8001/api/goal 호출
2. 시안이 내린 최상위 목표(priority 기반) 수신
3. AGI의 `outputs/autonomous_goals_latest.json` 최상단에 강제 덮어쓰기/주입
4. 약간의 휴지기(Sleep) 후 반복 (1~3초 간격)
"""

import sys
import time
import json
import logging
import requests
from pathlib import Path
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - [%(levelname)s] %(message)s")
logger = logging.getLogger("FsdClient")

# AGI 워크스페이스 루트 탐색
AGI_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(AGI_ROOT))

# 보안 및 API 설정
API_URL = "http://127.0.0.1:8001"
SHION_ROOT = Path("c:/workspace2/shion")  # 하드코딩된 시안 워크스페이스 임시 경로
API_TOKEN = ""
sec_path = SHION_ROOT / "config" / "security.yaml"

if sec_path.exists():
    try:
        import yaml
        with open(sec_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            API_TOKEN = cfg.get("network", {}).get("api_auth_token", "")
    except Exception as e:
        logger.warning(f"Failed to load Shion API Token: {e}")

HEADERS = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}

GOAL_FILE = AGI_ROOT / "outputs" / "autonomous_goals_latest.json"
POLL_INTERVAL = 3.0  # 초

def load_goals() -> list:
    if GOAL_FILE.exists():
        try:
            with open(GOAL_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else data.get("goals", [])
        except Exception:
            return []
    return []

def save_goals(goals: list):
    wrapper = {"timestamp": datetime.now().isoformat() + "Z", "goals": goals}
    GOAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GOAL_FILE, "w", encoding="utf-8") as f:
        json.dump(wrapper, f, indent=2, ensure_ascii=False)

def inject_shion_intent(intent_data: dict):
    """API로 받아온 시안의 의도를 AGI의 목표 큐 최상단에 주입합니다."""
    goal_title = intent_data.get("goal")
    priority = intent_data.get("priority", 0.0)
    target = intent_data.get("target")
    
    # 0.5 미만의 하찮은 의도이거나, HOLD 상태면 주입하지 않음
    if not goal_title or goal_title == "HOLD" or priority < 0.5:
        return

    # 기존 목표 큐 로드
    current_goals = load_goals()
    
    # 중복 확인 (가장 최상단에 이미 같은 목표가 있으면 무시)
    if current_goals and current_goals[0].get("title") == f"[Shion_Meta] {goal_title}":
        return

    new_goal = {
        "title": f"[Shion_Meta] {goal_title}",
        "description": f"Target: {target} (Auto-injected via Meta-FSD Client)",
        "priority": priority * 10, # AGI 스케일(0~100)로 10배 뻥튀기
        "status": "queued",
        "type": "shion_meta_directive",
        "executable": {
            "type": "manual", # AGI Executor가 스스로 분석하게 두거나, 매뉴얼로 둠
            "message": goal_title
        }
    }
    
    # 긴급 우회명령(0.9 이상) 인경우 (예: Escape & Observe)
    if priority >= 0.9:
        logger.warning(f"🚨 [URGENT_DISSONANCE] Received critical steering command from Soul: {goal_title}")
        new_goal["priority"] = 99.0
        new_goal["description"] = f"CRITICAL: Visual Dissonance Detected. {target}"
        # AGI의 작동을 멈추고 관망하는 스크립트 강제 바인딩
        new_goal["executable"] = {
            "type": "script",
            "script": "scripts/enter_sleep_mode.ps1" # 임시로 휴식 모드 전환
        }

    # 최상단에 주입
    current_goals.insert(0, new_goal)
    save_goals(current_goals)
    
    logger.info(f"   🧬 [INJECTED] Mind's Intent: {goal_title} (Priority: {priority:.2f})")

def run_loop():
    logger.info(f"🌐 [Boot] Shion Meta-FSD Client started. Polling: {API_URL}")
    while True:
        try:
            resp = requests.get(f"{API_URL}/api/goal", headers=HEADERS, timeout=2.0)
            if resp.status_code == 200:
                intent_data = resp.json()
                inject_shion_intent(intent_data)
        except requests.exceptions.ConnectionError:
            pass # 시안이 꺼져있을 땐 조용히 대기
        except Exception as e:
            logger.error(f"Polling error: {e}")
            
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_loop()
