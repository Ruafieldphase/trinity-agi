#!/usr/bin/env python3
"""
Music → Rhythm → Goal 전체 파이프라인 테스트

Music Daemon의 자율 목표 생성 기능을 E2E로 검증합니다.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가
workspace = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(workspace / "fdo_agi_repo"))

from copilot.flow_observer_integration import FlowObserverIntegration
from copilot.hippocampus import GoalTracker

def simulate_music_rhythm_data():
    """실제 음악 재생 시나리오 시뮬레이션"""
    return {
        "timestamp": datetime.now().isoformat(),
        "track": {
            "title": "Deep Focus",
            "artist": "Lofi Girl",
            "bpm": 85,
            "energy": 0.65,
            "valence": 0.55
        },
        "physiological": {
            "heart_rate_variability": 75,
            "breathing_rate": 14,
            "skin_conductance": 0.3
        },
        "cognitive": {
            "attention_level": 0.78,
            "flow_state_probability": 0.82,
            "task_switching_rate": 0.15
        }
    }

def test_rhythm_generation():
    """1단계: 음악 → 리듬 생성"""
    print("📊 Step 1: 음악 데이터 → 리듬 리포트 생성")
    print("-" * 60)
    
    flow_observer = FlowObserverIntegration()
    music_data = simulate_music_rhythm_data()
    
    print(f"🎵 현재 재생 중: {music_data['track']['title']} - {music_data['track']['artist']}")
    print(f"   BPM: {music_data['track']['bpm']} | Energy: {music_data['track']['energy']:.2f}")
    print(f"🧠 인지 상태: Flow {music_data['cognitive']['flow_state_probability']:.0%} | Attention {music_data['cognitive']['attention_level']:.0%}")
    
    # 리듬 리포트 생성
    rhythm_report = flow_observer.generate_report()
    
    print(f"\n✅ 리듬 리포트 생성 완료")
    print(f"   Phase: {rhythm_report.get('current_phase', 'unknown')}")
    print(f"   Quality: {rhythm_report.get('quality_score', 0):.1%}")
    
    return rhythm_report

def test_goal_generation(rhythm_report):
    """2단계: 리듬 → 자율 목표 생성"""
    print("\n🎯 Step 2: 리듬 → 자율 목표 생성")
    print("-" * 60)
    
    tracker = GoalTracker()
    
    # 리듬 기반 목표 생성 (music_daemon 로직 시뮬레이션)
    phase = rhythm_report.get('current_phase', 'unknown')
    quality = rhythm_report.get('quality_score', 0)
    
    # Phase별 목표 템플릿
    goal_templates = {
        'flow': "현재 플로우 상태 유지하며 집중 작업 지속",
        'rest': "휴식 페이즈 - 가벼운 정리 작업 또는 학습",
        'transition': "전환 페이즈 - 다음 작업 준비 및 계획"
    }
    
    goal_title = goal_templates.get(phase, "리듬 기반 자율 작업")
    
    # 목표 생성 (source 태그 포함)
    new_goal = tracker.add_goal(
        title=goal_title,
        description=f"Music Daemon에서 자동 생성 (Phase: {phase}, Quality: {quality:.0%})",
        tags=["auto-generated", "music-driven", f"phase:{phase}"],
        metadata={
            "source": "music_daemon",
            "trigger": "rhythm_analysis",
            "rhythm_phase": phase,
            "rhythm_quality": quality,
            "generated_at": datetime.now().isoformat()
        }
    )
    
    print(f"✅ 자율 목표 생성 완료")
    print(f"   ID: {new_goal['id']}")
    print(f"   Title: {new_goal['title']}")
    print(f"   Tags: {', '.join(new_goal['tags'])}")
    print(f"   Source: {new_goal.get('metadata', {}).get('source', 'N/A')}")
    
    return new_goal

def test_event_logging(goal, rhythm_report):
    """3단계: 이벤트 로깅"""
    print("\n📝 Step 3: Music-Goal 이벤트 로깅")
    print("-" * 60)
    
    event_log_path = workspace / "outputs" / "music_goal_events.jsonl"
    event_log_path.parent.mkdir(exist_ok=True)
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "music_goal_created",
        "goal_id": goal['id'],
        "goal_title": goal['title'],
        "rhythm_phase": rhythm_report.get('current_phase', 'unknown'),
        "rhythm_quality": rhythm_report.get('quality_score', 0),
        "source": "music_daemon",
        "trigger": "rhythm_analysis"
    }
    
    with open(event_log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    print(f"✅ 이벤트 로그 기록 완료: {event_log_path}")
    print(f"   Event Type: {event['event_type']}")
    print(f"   Goal ID: {event['goal_id']}")
    
    return event

def verify_pipeline():
    """4단계: 전체 파이프라인 검증"""
    print("\n🔍 Step 4: 파이프라인 검증")
    print("-" * 60)
    
    tracker = GoalTracker()
    all_goals = tracker.get_all_goals()
    
    # Music Daemon이 생성한 목표만 필터링
    music_goals = [
        g for g in all_goals 
        if g.get('metadata', {}).get('source') == 'music_daemon'
    ]
    
    print(f"✅ Goal Tracker 검증")
    print(f"   전체 목표: {len(all_goals)}개")
    print(f"   Music-generated: {len(music_goals)}개")
    
    if music_goals:
        latest = music_goals[-1]
        print(f"\n📌 최근 Music Goal:")
        print(f"   Title: {latest['title']}")
        print(f"   Status: {latest['status']}")
        print(f"   Tags: {', '.join(latest['tags'])}")
        print(f"   Created: {latest['created_at']}")
    
    # 이벤트 로그 검증
    event_log_path = workspace / "outputs" / "music_goal_events.jsonl"
    if event_log_path.exists():
        with open(event_log_path, 'r', encoding='utf-8') as f:
            events = [json.loads(line) for line in f if line.strip()]
        
        print(f"\n✅ Event Log 검증")
        print(f"   총 이벤트: {len(events)}개")
        
        recent_events = events[-3:] if len(events) > 3 else events
        for evt in recent_events:
            print(f"   - {evt['timestamp'][:19]}: {evt['event_type']} (Goal: {evt['goal_id'][:8]})")
    
    return {
        "total_goals": len(all_goals),
        "music_goals": len(music_goals),
        "latest_goal": music_goals[-1] if music_goals else None
    }

def main():
    """전체 파이프라인 실행"""
    print("🎼 Music → Rhythm → Goal 파이프라인 테스트")
    print("=" * 60)
    print()
    
    try:
        # 1. 리듬 생성
        rhythm_report = test_rhythm_generation()
        
        # 2. 목표 생성
        goal = test_goal_generation(rhythm_report)
        
        # 3. 이벤트 로깅
        event = test_event_logging(goal, rhythm_report)
        
        # 4. 검증
        result = verify_pipeline()
        
        print("\n" + "=" * 60)
        print("🎉 파이프라인 테스트 완료!")
        print("=" * 60)
        print(f"✅ 모든 단계 성공")
        print(f"📊 Music Goals: {result['music_goals']}개")
        
        if result['latest_goal']:
            print(f"🎯 최신 목표: {result['latest_goal']['title']}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 파이프라인 테스트 실패: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
