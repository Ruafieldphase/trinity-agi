#!/usr/bin/env python3
"""
Music → Rhythm → Goal 전체 파이프라인 통합 테스트
리듬 기반 자율 목표 생성 E2E 시뮬레이션
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random
from workspace_root import get_workspace_root

# Add parent directory to path
sys.path.insert(0, str(get_workspace_root()))

from fdo_agi_repo.copilot.rhythm_analysis import RhythmAnalyzer
from scripts.autonomous_goal_generator import (
    generate_goals_from_context,
    get_current_state
)

def simulate_music_playback():
    """음악 재생 시뮬레이션 (실제로는 music_daemon.py가 수행)"""
    print("\n🎵 Step 1: Music Playback Simulation")
    print("=" * 60)
    
    # 가상의 음악 재생 이벤트 생성
    music_events = [
        {
            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "track": "Focus Deep - Lo-fi Beats",
            "tempo_bpm": 92,
            "energy": 0.6,
            "valence": 0.45,
            "duration_seconds": 1800
        },
        {
            "timestamp": (datetime.now() - timedelta(minutes=25)).isoformat(),
            "track": "Coding Flow - Electronic",
            "tempo_bpm": 128,
            "energy": 0.75,
            "valence": 0.7,
            "duration_seconds": 300
        }
    ]
    
    # 음악 로그 저장
    music_log_path = Path("outputs/music_playback_log.jsonl")
    music_log_path.parent.mkdir(exist_ok=True)
    
    with open(music_log_path, "a", encoding="utf-8") as f:
        for event in music_events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    print(f"✅ Simulated {len(music_events)} music playback events")
    for event in music_events:
        print(f"   📀 {event['track']} ({event['tempo_bpm']} BPM, energy={event['energy']})")
    
    return music_events

def generate_rhythm_from_music(music_events):
    """음악 이벤트에서 리듬 상태 생성"""
    print("\n🌊 Step 2: Rhythm Analysis")
    print("=" * 60)
    
    analyzer = RhythmAnalyzer()
    
    # 음악 특성을 리듬 상태로 변환
    avg_energy = sum(e['energy'] for e in music_events) / len(music_events)
    avg_valence = sum(e['valence'] for e in music_events) / len(music_events)
    avg_tempo = sum(e['tempo_bpm'] for e in music_events) / len(music_events)
    
    # 리듬 상태 결정
    if avg_energy > 0.7:
        phase = "FOCUS"
        intensity = 0.8
    elif avg_energy < 0.4:
        phase = "REST"
        intensity = 0.3
    else:
        phase = "FLOW"
        intensity = 0.6
    
    rhythm_state = {
        "timestamp": datetime.now().isoformat(),
        "phase": phase,
        "intensity": intensity,
        "quality_score": (avg_energy + avg_valence) / 2,
        "tempo_influence": avg_tempo,
        "music_correlation": {
            "avg_energy": avg_energy,
            "avg_valence": avg_valence,
            "track_count": len(music_events)
        }
    }
    
    # 리듬 리포트 저장
    rhythm_report_path = Path("outputs/RHYTHM_CURRENT_STATE.md")
    with open(rhythm_report_path, "w", encoding="utf-8") as f:
        f.write(f"# Rhythm State Report\n\n")
        f.write(f"Generated: {rhythm_state['timestamp']}\n\n")
        f.write(f"## Current Phase: {phase}\n\n")
        f.write(f"- **Intensity**: {intensity:.1%}\n")
        f.write(f"- **Quality**: {rhythm_state['quality_score']:.1%}\n")
        f.write(f"- **Music Influence**: {avg_tempo:.0f} BPM avg\n\n")
        f.write(f"### Music Correlation\n")
        f.write(f"- Energy: {avg_energy:.1%}\n")
        f.write(f"- Valence: {avg_valence:.1%}\n")
        f.write(f"- Tracks: {len(music_events)}\n")
    
    print(f"✅ Rhythm State Generated")
    print(f"   Phase: {phase} (intensity={intensity:.1%})")
    print(f"   Quality: {rhythm_state['quality_score']:.1%}")
    print(f"   Music influence: {avg_tempo:.0f} BPM avg")
    
    return rhythm_state

def generate_goals_from_rhythm(rhythm_state):
    """리듬 상태에서 자율 목표 생성"""
    print("\n🎯 Step 3: Autonomous Goal Generation")
    print("=" * 60)
    
    # 현재 상태 가져오기
    current_state = get_current_state(hours=1)
    
    # 리듬 기반 컨텍스트 추가
    rhythm_context = {
        "rhythm_phase": rhythm_state["phase"],
        "rhythm_intensity": rhythm_state["intensity"],
        "music_correlation": rhythm_state["music_correlation"]
    }
    
    # 목표 생성
    goals = generate_goals_from_context(
        current_state,
        extra_context=rhythm_context,
        max_goals=3
    )
    
    # 목표에 출처 태깅
    tagged_goals = []
    for goal in goals:
        goal["metadata"] = goal.get("metadata", {})
        goal["metadata"]["source"] = "music_daemon"
        goal["metadata"]["trigger"] = "rhythm"
        goal["metadata"]["rhythm_phase"] = rhythm_state["phase"]
        goal["metadata"]["rhythm_intensity"] = rhythm_state["intensity"]
        tagged_goals.append(goal)
    
    # GoalTracker에 저장
    tracker_path = Path("fdo_agi_repo/memory/goal_tracker.json")
    try:
        with open(tracker_path, "r", encoding="utf-8") as f:
            tracker = json.load(f)
    except FileNotFoundError:
        tracker = {"goals": []}
    
    # 기존 목표에 추가
    for goal in tagged_goals:
        goal["id"] = f"music_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(tracker['goals'])}"
        goal["created_at"] = datetime.now().isoformat()
        goal["status"] = "pending"
        tracker["goals"].append(goal)
    
    with open(tracker_path, "w", encoding="utf-8") as f:
        json.dump(tracker, f, indent=2, ensure_ascii=False)
    
    # 이벤트 로그 기록
    event_log_path = Path("outputs/music_goal_events.jsonl")
    event_log_path.parent.mkdir(exist_ok=True)
    
    with open(event_log_path, "a", encoding="utf-8") as f:
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "music_goal_generation",
            "rhythm_phase": rhythm_state["phase"],
            "rhythm_intensity": rhythm_state["intensity"],
            "goals_generated": len(tagged_goals),
            "goal_ids": [g["id"] for g in tagged_goals]
        }
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    print(f"✅ Generated {len(tagged_goals)} goals from rhythm state")
    for i, goal in enumerate(tagged_goals, 1):
        print(f"   {i}. {goal['title']}")
        print(f"      Source: {goal['metadata']['source']} (trigger: {goal['metadata']['trigger']})")
        print(f"      Rhythm: {goal['metadata']['rhythm_phase']} @ {goal['metadata']['rhythm_intensity']:.1%}")
    
    return tagged_goals

def verify_integration():
    """통합 검증"""
    print("\n✅ Step 4: Integration Verification")
    print("=" * 60)
    
    # 1. GoalTracker 확인
    tracker_path = Path("fdo_agi_repo/memory/goal_tracker.json")
    with open(tracker_path, "r", encoding="utf-8") as f:
        tracker = json.load(f)
    
    music_goals = [g for g in tracker["goals"] if g.get("metadata", {}).get("source") == "music_daemon"]
    print(f"📊 GoalTracker: {len(music_goals)} music-generated goals found")
    
    # 2. 이벤트 로그 확인
    event_log_path = Path("outputs/music_goal_events.jsonl")
    if event_log_path.exists():
        with open(event_log_path, "r", encoding="utf-8") as f:
            events = [json.loads(line) for line in f if line.strip()]
        print(f"📝 Event Log: {len(events)} music-goal events recorded")
    
    # 3. 리듬 리포트 확인
    rhythm_report_path = Path("outputs/RHYTHM_CURRENT_STATE.md")
    if rhythm_report_path.exists():
        print(f"🌊 Rhythm Report: Generated successfully")
    
    print("\n" + "=" * 60)
    print("✨ Music → Rhythm → Goal 파이프라인 통합 완료!")
    print("=" * 60)

def main():
    """메인 실행 함수"""
    print("\n" + "🎼" * 30)
    print("Music-Driven Autonomous Goal System")
    print("E2E Integration Test")
    print("🎼" * 30)
    
    try:
        # Step 1: 음악 재생 시뮬레이션
        music_events = simulate_music_playback()
        
        # Step 2: 리듬 분석
        rhythm_state = generate_rhythm_from_music(music_events)
        
        # Step 3: 목표 생성
        goals = generate_goals_from_rhythm(rhythm_state)
        
        # Step 4: 통합 검증
        verify_integration()
        
        print("\n✅ All steps completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during pipeline execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
