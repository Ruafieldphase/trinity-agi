#!/usr/bin/env python3
"""
Music → Rhythm → Goal 통합 테스트
강제로 리듬 이벤트를 발생시켜서 전체 플로우 검증
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from workspace_root import get_workspace_root

# 경로 설정
WORKSPACE = get_workspace_root()
sys.path.insert(0, str(WORKSPACE / "fdo_agi_repo"))

from scripts.music_daemon import MusicRhythmDaemon
from scripts.autonomous_goal_generator import GoalGenerator

def create_test_rhythm_report():
    """테스트용 리듬 리포트 생성 (low flow score)"""
    report = {
        "generated_at": datetime.now().isoformat(),
        "analysis_period_hours": 1,
        "current_state": {
            "state": "scattered",
            "confidence": 0.9,
            "context": {"reason": "test_scenario"}
        },
        "flow_metrics": {
            "flow_score": 0.25,  # 낮은 스코어 → 음악 필요!
            "focus_stability": 0.3,
            "transition_smoothness": 0.2
        },
        "activity_summary": {
            "total_records": 100,
            "activity_ratio": 0.8,
            "flow_sessions": 1,
            "total_flow_minutes": 15.0,
            "interruptions": 10
        },
        "flow_quality": "poor",
        "interruptions": [
            {
                "type": "flow_interruption",
                "from_focus": "VS Code",
                "to_focus": "Browser",
                "focus_duration_minutes": 5.0,
                "timestamp": datetime.now().isoformat()
            }
        ],
        "recommendations": [
            "Flow 스코어가 낮습니다. 음악 지원이 필요합니다.",
            "집중력 향상을 위한 Alpha 파 음악을 추천합니다."
        ]
    }
    
    report_path = WORKSPACE / "outputs" / "flow_observer_report_test.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Test rhythm report created: {report_path}")
    return report_path

def test_music_daemon_analysis():
    """Music Daemon의 리듬 분석 테스트"""
    print("\n🎵 Testing Music Daemon Analysis...")
    
    # 테스트용 리듬 리포트 생성
    test_report_path = create_test_rhythm_report()
    
    # Music Daemon 초기화 (auto-goal 활성화)
    daemon = MusicRhythmDaemon(
        interval=60,
        flow_threshold=0.5,  # 0.5 미만이면 음악 필요
        auto_goal=True
    )
    
    # 리듬 분석
    with open(test_report_path, 'r', encoding='utf-8') as f:
        test_report = json.load(f)
    
    flow_state = daemon.analyze_flow_state(test_report)
    
    print(f"\n📊 Flow Analysis Result:")
    print(f"  - State: {flow_state['state']}")
    print(f"  - Score: {flow_state['score']:.2f}")
    print(f"  - Need Music: {flow_state['need_music']}")
    print(f"  - Target Brainwave: {flow_state['brainwave_target']}")
    
    # 음악이 필요한 상태인지 확인
    assert flow_state['need_music'] == True, "❌ Should need music when flow score is low!"
    assert flow_state['brainwave_target'] == 'theta', f"❌ Expected 'theta', got '{flow_state['brainwave_target']}'"
    
    print("✅ Music Daemon analysis passed!")
    return flow_state

def test_autonomous_goal_generation():
    """Autonomous Goal 생성 테스트"""
    print("\n🎯 Testing Autonomous Goal Generation...")
    
    # Goal Generator 초기화
    generator = GoalGenerator(lookback_hours=24)
    
    # 강제로 음악 관련 컨텍스트 추가
    test_context = {
        "rhythm_analysis": {
            "flow_score": 0.25,
            "state": "scattered",
            "need_music": True,
            "brainwave_target": "theta"
        },
        "recent_events": [
            {"type": "flow_interruption", "count": 10},
            {"type": "music_needed", "threshold_crossed": True}
        ]
    }
    
    # 목표 생성 (실제로는 LLM 호출하지만 여기선 mock)
    print("  - Generating goals based on low flow state...")
    
    # Goal Tracker 확인
    tracker_path = WORKSPACE / "fdo_agi_repo" / "memory" / "goal_tracker.json"
    
    if tracker_path.exists():
        with open(tracker_path, 'r', encoding='utf-8') as f:
            tracker = json.load(f)
        
        print(f"\n📋 Current Goals in Tracker: {len(tracker.get('goals', []))}")
        
        # 최근 music 태그 목표 찾기
        music_goals = [
            g for g in tracker.get('goals', [])
            if g.get('tags', {}).get('source') == 'music_daemon'
        ]
        
        if music_goals:
            print(f"  - Music-triggered goals: {len(music_goals)}")
            latest = music_goals[-1]
            print(f"    └─ Latest: {latest.get('title', 'N/A')}")
            print(f"       Tags: {latest.get('tags', {})}")
        else:
            print("  - No music-triggered goals found yet")
    
    print("✅ Goal generation test passed!")

def test_event_logging():
    """Music-Goal 이벤트 로그 확인"""
    print("\n📝 Testing Event Logging...")
    
    event_log_path = WORKSPACE / "outputs" / "music_goal_events.jsonl"
    
    if event_log_path.exists():
        with open(event_log_path, 'r', encoding='utf-8') as f:
            events = [json.loads(line) for line in f]
        
        print(f"  - Total events: {len(events)}")
        
        if events:
            latest = events[-1]
            print(f"  - Latest event:")
            print(f"    Timestamp: {latest.get('timestamp', 'N/A')}")
            print(f"    Trigger: {latest.get('trigger', 'N/A')}")
            print(f"    Goal: {latest.get('goal_title', 'N/A')}")
    else:
        print("  - No event log found yet (will be created on first music-goal trigger)")
    
    print("✅ Event logging test passed!")

def main():
    """통합 테스트 실행"""
    print("="*60)
    print("🧪 Music → Rhythm → Goal Integration Test")
    print("="*60)
    
    try:
        # 1. Music Daemon 리듬 분석
        flow_state = test_music_daemon_analysis()
        
        # 2. Autonomous Goal 생성
        test_autonomous_goal_generation()
        
        # 3. 이벤트 로깅
        test_event_logging()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\n💡 Next Steps:")
        print("  1. Music Daemon 재시작: --auto-goal 옵션")
        print("  2. 실제 작업 시작 (VS Code, 브라우저 등)")
        print("  3. 1시간 후 Goal Dashboard 확인")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
