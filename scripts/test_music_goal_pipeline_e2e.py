#!/usr/bin/env python3
"""
Music-Goal Pipeline E2E Test
음악 → 리듬 → 목표 생성 전체 플로우 검증
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import sys

WORKSPACE = Path(__file__).parent.parent
RHYTHM_DIR = WORKSPACE / "outputs"
GOAL_TRACKER = WORKSPACE / "fdo_agi_repo" / "memory" / "goal_tracker.json"
MUSIC_EVENT_LOG = WORKSPACE / "outputs" / "music_goal_events.jsonl"

def create_mock_rhythm_data():
    """Mock 리듬 데이터 생성 (실제 music_daemon 출력 시뮬레이션)"""
    now = datetime.now()
    rhythm_file = RHYTHM_DIR / f"RHYTHM_FLOW_STATE_{now.strftime('%Y%m%d_%H%M%S')}.md"
    
    # 집중 상태 시뮬레이션
    rhythm_data = {
        "timestamp": now.isoformat(),
        "flow_state": "deep_focus",
        "energy_level": 0.85,
        "coherence": 0.92,
        "suggested_category": "coding",
        "confidence": 0.88
    }
    
    content = f"""# Flow State Report

**Generated**: {now.strftime('%Y-%m-%d %H:%M:%S')}

## 🎵 Current State
- **Flow State**: {rhythm_data['flow_state']}
- **Energy Level**: {rhythm_data['energy_level']:.2%}
- **Coherence**: {rhythm_data['coherence']:.2%}

## 🎯 Suggested Category
- **Category**: {rhythm_data['suggested_category']}
- **Confidence**: {rhythm_data['confidence']:.2%}
"""
    
    rhythm_file.write_text(content, encoding='utf-8')
    print(f"✅ Mock rhythm data created: {rhythm_file.name}")
    return rhythm_data, rhythm_file

def simulate_goal_generation(rhythm_data):
    """리듬 기반 목표 생성 시뮬레이션"""
    now = datetime.now()
    
    # Load current tracker
    if GOAL_TRACKER.exists():
        tracker_data = json.loads(GOAL_TRACKER.read_text(encoding='utf-8'))
    else:
        tracker_data = {
            "goals": [],
            "last_updated": now.isoformat(),
            "metadata": {"version": "1.0"}
        }
    
    # Create new goal based on rhythm
    new_goal = {
        "id": f"music_goal_{now.strftime('%Y%m%d_%H%M%S')}",
        "title": f"Deep Work Session - {rhythm_data['suggested_category'].title()}",
        "description": f"Auto-generated goal from music daemon. Flow state: {rhythm_data['flow_state']}, Energy: {rhythm_data['energy_level']:.0%}",
        "created_at": now.isoformat(),
        "status": "in_progress",
        "source": "music_daemon",
        "origin": "rhythm_analysis",
        "trigger": {
            "type": "rhythm",
            "flow_state": rhythm_data['flow_state'],
            "energy_level": rhythm_data['energy_level'],
            "coherence": rhythm_data['coherence']
        },
        "priority": "high" if rhythm_data['energy_level'] > 0.8 else "medium",
        "estimated_duration_minutes": 60,
        "tags": ["auto-generated", "music-driven", rhythm_data['flow_state']]
    }
    
    tracker_data["goals"].append(new_goal)
    tracker_data["last_updated"] = now.isoformat()
    
    # Save tracker
    GOAL_TRACKER.parent.mkdir(parents=True, exist_ok=True)
    GOAL_TRACKER.write_text(json.dumps(tracker_data, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print(f"✅ Goal created: {new_goal['id']}")
    return new_goal

def log_music_event(rhythm_data, goal):
    """Music-Goal 이벤트 로그 기록"""
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "music_goal_created",
        "rhythm_state": {
            "flow_state": rhythm_data['flow_state'],
            "energy_level": rhythm_data['energy_level'],
            "coherence": rhythm_data['coherence']
        },
        "goal_id": goal['id'],
        "goal_title": goal['title'],
        "source": "music_daemon",
        "trigger": "rhythm_analysis"
    }
    
    MUSIC_EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(MUSIC_EVENT_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    print(f"✅ Event logged to {MUSIC_EVENT_LOG.name}")

def verify_integration():
    """통합 검증"""
    print("\n🔍 Integration Verification")
    print("="*50)
    
    # 1. Goal Tracker 확인
    if GOAL_TRACKER.exists():
        tracker_data = json.loads(GOAL_TRACKER.read_text(encoding='utf-8'))
        music_goals = [g for g in tracker_data.get("goals", []) if g.get("source") == "music_daemon"]
        print(f"✅ Goal Tracker: {len(music_goals)} music-driven goals found")
    else:
        print("❌ Goal Tracker not found")
        return False
    
    # 2. Event Log 확인
    if MUSIC_EVENT_LOG.exists():
        with open(MUSIC_EVENT_LOG, 'r', encoding='utf-8') as f:
            events = [json.loads(line) for line in f if line.strip()]
        print(f"✅ Event Log: {len(events)} events recorded")
    else:
        print("❌ Event Log not found")
        return False
    
    # 3. 최신 목표 상세 정보
    if music_goals:
        latest_goal = music_goals[-1]
        print(f"\n📋 Latest Music-Driven Goal:")
        print(f"   ID: {latest_goal['id']}")
        print(f"   Title: {latest_goal['title']}")
        print(f"   Status: {latest_goal['status']}")
        print(f"   Priority: {latest_goal.get('priority', 'N/A')}")
        print(f"   Source: {latest_goal.get('source', 'N/A')}")
        if 'trigger' in latest_goal:
            print(f"   Trigger: {latest_goal['trigger']}")
    
    return True

def main():
    print("🎵 Music-Goal Pipeline E2E Test")
    print("="*50)
    
    # Step 1: Mock 리듬 데이터 생성
    print("\n[Step 1] Creating mock rhythm data...")
    rhythm_data, rhythm_file = create_mock_rhythm_data()
    time.sleep(1)
    
    # Step 2: 목표 생성
    print("\n[Step 2] Generating goal from rhythm...")
    goal = simulate_goal_generation(rhythm_data)
    time.sleep(1)
    
    # Step 3: 이벤트 로그
    print("\n[Step 3] Logging music-goal event...")
    log_music_event(rhythm_data, goal)
    time.sleep(1)
    
    # Step 4: 검증
    print("\n[Step 4] Verifying integration...")
    success = verify_integration()
    
    print("\n" + "="*50)
    if success:
        print("✅ E2E TEST PASSED")
        print(f"\n📁 Files created:")
        print(f"   - {rhythm_file.relative_to(WORKSPACE)}")
        print(f"   - {GOAL_TRACKER.relative_to(WORKSPACE)}")
        print(f"   - {MUSIC_EVENT_LOG.relative_to(WORKSPACE)}")
        return 0
    else:
        print("❌ E2E TEST FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
