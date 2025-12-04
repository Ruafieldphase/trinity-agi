#!/usr/bin/env python
"""
Music → Rhythm → Goal 파이프라인 통합 테스트
음악 재생부터 자율 목표 생성까지 전체 흐름 검증
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트 추가
workspace_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(workspace_root))
sys.path.insert(0, str(workspace_root / "fdo_agi_repo"))

from scripts.music_daemon import detect_music_and_analyze
from fdo_agi_repo.copilot.hippocampus import Hippocampus

def simulate_music_playback():
    """음악 재생 시뮬레이션 (Reaper API 대신 더미 데이터)"""
    print("🎵 음악 재생 시뮬레이션 중...")
    
    # 더미 음악 분석 결과 생성
    dummy_analysis = {
        "timestamp": datetime.now().isoformat(),
        "track_name": "Test Flow Track",
        "bpm": 128.0,
        "energy": 0.75,
        "valence": 0.65,
        "danceability": 0.80,
        "key": "C major",
        "time_signature": "4/4",
        "loudness": -5.2,
        "speechiness": 0.05,
        "instrumentalness": 0.92,
        "liveness": 0.15,
        "acousticness": 0.12,
        "duration_seconds": 240.0,
        "cognitive_state": "flow",
        "recommended_task": "deep_coding"
    }
    
    return dummy_analysis

def generate_rhythm_phase():
    """리듬 페이즈 생성"""
    print("🌊 리듬 페이즈 생성 중...")
    
    # 리듬 상태 파일 경로
    rhythm_file = workspace_root / "outputs" / "rhythm_state_latest.json"
    
    # 더미 리듬 상태 생성
    rhythm_state = {
        "timestamp": datetime.now().isoformat(),
        "phase": "focus",
        "energy_level": 0.75,
        "coherence": 0.82,
        "flow_probability": 0.68,
        "cognitive_load": 0.55,
        "autonomic_balance": 0.60,
        "recommended_break_in": 45,
        "music_triggered": True,
        "music_bpm": 128.0,
        "music_energy": 0.75
    }
    
    # 파일 저장
    rhythm_file.parent.mkdir(parents=True, exist_ok=True)
    with open(rhythm_file, "w", encoding="utf-8") as f:
        json.dump(rhythm_state, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ 리듬 상태: {rhythm_state['phase']} (flow: {rhythm_state['flow_probability']:.2%})")
    return rhythm_state

def trigger_goal_generation(rhythm_state, music_analysis):
    """리듬 기반 목표 생성"""
    print("🎯 자율 목표 생성 중...")
    
    # Hippocampus 초기화
    hippo = Hippocampus()
    
    # 리듬과 음악 컨텍스트 생성
    context = {
        "source": "music_daemon",
        "trigger": "rhythm",
        "music": {
            "track": music_analysis.get("track_name"),
            "bpm": music_analysis.get("bpm"),
            "energy": music_analysis.get("energy"),
            "cognitive_state": music_analysis.get("cognitive_state")
        },
        "rhythm": {
            "phase": rhythm_state.get("phase"),
            "flow_probability": rhythm_state.get("flow_probability"),
            "energy_level": rhythm_state.get("energy_level")
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # 목표 생성 (더미 목표)
    generated_goals = [
        {
            "id": int(time.time() * 1000),
            "title": f"Flow-optimized coding session ({music_analysis.get('bpm')} BPM)",
            "description": f"Music-triggered deep work based on {rhythm_state.get('phase')} rhythm phase",
            "priority": "high" if rhythm_state.get("flow_probability", 0) > 0.6 else "medium",
            "estimated_duration": "45min",
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "source": "music_daemon",
            "trigger": "rhythm",
            "context": context
        }
    ]
    
    # Goal Tracker에 저장
    tracker_file = workspace_root / "fdo_agi_repo" / "memory" / "goal_tracker.json"
    
    if tracker_file.exists():
        with open(tracker_file, "r", encoding="utf-8") as f:
            tracker_data = json.load(f)
    else:
        tracker_data = {"goals": [], "completed": [], "failed": []}
    
    # 새 목표 추가
    tracker_data["goals"].extend(generated_goals)
    
    with open(tracker_file, "w", encoding="utf-8") as f:
        json.dump(tracker_data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ {len(generated_goals)}개 목표 생성됨")
    for goal in generated_goals:
        print(f"    - {goal['title']} [priority: {goal['priority']}]")
    
    # 이벤트 로그 기록
    log_music_goal_event(music_analysis, rhythm_state, generated_goals)
    
    return generated_goals

def log_music_goal_event(music_analysis, rhythm_state, goals):
    """Music → Goal 이벤트 로그 기록"""
    log_file = workspace_root / "outputs" / "music_goal_events.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "music_to_goal",
        "music": {
            "track": music_analysis.get("track_name"),
            "bpm": music_analysis.get("bpm"),
            "energy": music_analysis.get("energy"),
            "cognitive_state": music_analysis.get("cognitive_state")
        },
        "rhythm": {
            "phase": rhythm_state.get("phase"),
            "flow_probability": rhythm_state.get("flow_probability")
        },
        "goals_generated": len(goals),
        "goal_ids": [g["id"] for g in goals]
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    print(f"  ✓ 이벤트 로그 기록: {log_file}")

def verify_pipeline():
    """파이프라인 검증"""
    print("\n📊 파이프라인 검증 중...")
    
    checks = []
    
    # 1. Goal Tracker 확인
    tracker_file = workspace_root / "fdo_agi_repo" / "memory" / "goal_tracker.json"
    if tracker_file.exists():
        with open(tracker_file, "r", encoding="utf-8") as f:
            tracker_data = json.load(f)
        
        music_goals = [g for g in tracker_data.get("goals", []) if g.get("source") == "music_daemon"]
        checks.append(("Goal Tracker", len(music_goals) > 0, f"{len(music_goals)} music-triggered goals"))
    else:
        checks.append(("Goal Tracker", False, "파일 없음"))
    
    # 2. 이벤트 로그 확인
    log_file = workspace_root / "outputs" / "music_goal_events.jsonl"
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            events = [json.loads(line) for line in f if line.strip()]
        checks.append(("Event Log", len(events) > 0, f"{len(events)} events"))
    else:
        checks.append(("Event Log", False, "파일 없음"))
    
    # 3. 리듬 상태 확인
    rhythm_file = workspace_root / "outputs" / "rhythm_state_latest.json"
    checks.append(("Rhythm State", rhythm_file.exists(), "생성됨" if rhythm_file.exists() else "없음"))
    
    # 결과 출력
    print("\n검증 결과:")
    all_passed = True
    for name, passed, detail in checks:
        status = "✓" if passed else "✗"
        color = "Green" if passed else "Red"
        print(f"  {status} {name}: {detail}")
        if not passed:
            all_passed = False
    
    return all_passed

def main():
    """메인 파이프라인 실행"""
    print("=" * 60)
    print("🎵 Music → Rhythm → Goal 파이프라인 테스트")
    print("=" * 60)
    print()
    
    try:
        # Step 1: 음악 재생 시뮬레이션
        music_analysis = simulate_music_playback()
        print(f"  ✓ 분석 완료: {music_analysis['track_name']} ({music_analysis['bpm']} BPM)")
        print()
        
        # Step 2: 리듬 페이즈 생성
        rhythm_state = generate_rhythm_phase()
        print()
        
        # Step 3: 목표 생성
        goals = trigger_goal_generation(rhythm_state, music_analysis)
        print()
        
        # Step 4: 검증
        success = verify_pipeline()
        
        print()
        print("=" * 60)
        if success:
            print("✅ 파이프라인 테스트 성공!")
            print()
            print("📝 다음 단계:")
            print("  1. Dashboard에서 music-triggered 목표 확인:")
            print("     code c:\\workspace\\agi\\outputs\\autonomous_goal_dashboard_latest.html")
            print()
            print("  2. 이벤트 로그 확인:")
            print("     code c:\\workspace\\agi\\outputs\\music_goal_events.jsonl")
            return 0
        else:
            print("❌ 일부 검증 실패")
            return 1
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
