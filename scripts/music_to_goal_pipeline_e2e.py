#!/usr/bin/env python
"""
음악 → 리듬 → 목표 생성 E2E 파이프라인 테스트

Music Daemon의 전체 플로우를 시뮬레이션:
1. 음악 감지 (시뮬레이션)
2. 리듬 상태 분석
3. 자율 목표 생성
4. Goal Tracker 기록
5. 이벤트 로깅
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from workspace_root import get_workspace_root

# 프로젝트 루트 추가
workspace_root = get_workspace_root()
sys.path.insert(0, str(workspace_root / "fdo_agi_repo"))

from goal_tracker import GoalTracker
from scripts.rhythm_state_detector import RhythmStateDetector


class MusicToGoalPipelineE2E:
    """음악 → 리듬 → 목표 생성 E2E 파이프라인"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.outputs_dir = workspace_root / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)
        
        # 컴포넌트 초기화
        self.goal_tracker = GoalTracker(workspace_root / "fdo_agi_repo" / "memory" / "goal_tracker.json")
        self.rhythm_detector = RhythmStateDetector()
        
        # 이벤트 로그
        self.event_log_path = self.outputs_dir / "music_goal_events.jsonl"
        
    def simulate_music_detection(self):
        """음악 감지 시뮬레이션"""
        print("🎵 Simulating music detection...")
        
        # 시뮬레이션: 현재 재생 중인 음악 정보
        music_info = {
            "detected": True,
            "title": "Focus Flow - Binaural Beats",
            "tempo_bpm": 120,
            "energy_level": 0.75,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"   ✓ Detected: {music_info['title']}")
        print(f"   ✓ Tempo: {music_info['tempo_bpm']} BPM")
        print(f"   ✓ Energy: {music_info['energy_level']:.2%}")
        
        return music_info
    
    def analyze_rhythm_state(self):
        """리듬 상태 분석"""
        print("\n🌊 Analyzing rhythm state...")
        
        # 최근 24시간 리듬 분석
        rhythm_state = self.rhythm_detector.analyze_recent_rhythm(hours=24)
        
        print(f"   ✓ Current Phase: {rhythm_state.get('current_phase', 'UNKNOWN')}")
        print(f"   ✓ Health Score: {rhythm_state.get('health_score', 0):.1f}%")
        print(f"   ✓ Resonance: {rhythm_state.get('resonance_level', 0):.2f}")
        
        return rhythm_state
    
    def generate_autonomous_goal(self, music_info: dict, rhythm_state: dict):
        """음악과 리듬 기반 자율 목표 생성"""
        print("\n🎯 Generating autonomous goal...")
        
        # 리듬 상태에 따른 목표 타입 결정
        phase = rhythm_state.get('current_phase', 'FOCUS')
        tempo = music_info.get('tempo_bpm', 120)
        energy = music_info.get('energy_level', 0.5)
        
        # 목표 생성 로직
        if phase == 'FOCUS' and energy > 0.6:
            goal_type = "deep_work"
            goal_title = "Deep Focus Session"
            goal_description = f"음악 리듬({tempo} BPM)에 맞춰 깊은 작업 수행"
            duration_min = 25  # Pomodoro
        elif phase == 'REST':
            goal_type = "recovery"
            goal_title = "Active Recovery"
            goal_description = "리듬이 휴식을 요청하고 있습니다. 짧은 휴식 또는 가벼운 작업"
            duration_min = 5
        else:
            goal_type = "balanced"
            goal_title = "Balanced Work Session"
            goal_description = f"현재 리듬({phase})에 맞춘 균형 잡힌 작업"
            duration_min = 15
        
        # GoalTracker에 목표 추가
        goal_id = self.goal_tracker.add_goal(
            title=goal_title,
            description=goal_description,
            source="music_daemon",
            tags=[
                f"type:{goal_type}",
                f"tempo:{tempo}",
                f"phase:{phase}",
                "trigger:rhythm",
                "origin:music"
            ],
            metadata={
                "music_title": music_info.get('title'),
                "tempo_bpm": tempo,
                "energy_level": energy,
                "rhythm_phase": phase,
                "health_score": rhythm_state.get('health_score'),
                "duration_minutes": duration_min
            }
        )
        
        print(f"   ✓ Created Goal: {goal_title}")
        print(f"   ✓ Type: {goal_type}")
        print(f"   ✓ Duration: {duration_min} minutes")
        print(f"   ✓ Goal ID: {goal_id}")
        
        return {
            "goal_id": goal_id,
            "title": goal_title,
            "type": goal_type,
            "duration_min": duration_min
        }
    
    def log_event(self, event_type: str, data: dict):
        """이벤트 로깅"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        with open(self.event_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    def run_pipeline(self):
        """전체 파이프라인 실행"""
        print("=" * 60)
        print("🎼 Music → Rhythm → Goal Pipeline E2E Test")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Step 1: 음악 감지
            music_info = self.simulate_music_detection()
            self.log_event("music_detected", music_info)
            
            # Step 2: 리듬 분석
            rhythm_state = self.analyze_rhythm_state()
            self.log_event("rhythm_analyzed", rhythm_state)
            
            # Step 3: 목표 생성
            goal_info = self.generate_autonomous_goal(music_info, rhythm_state)
            self.log_event("goal_generated", goal_info)
            
            # Step 4: 결과 리포트
            elapsed = time.time() - start_time
            
            print("\n" + "=" * 60)
            print("✅ Pipeline Execution Complete")
            print("=" * 60)
            print(f"⏱️  Total Time: {elapsed:.2f}s")
            print(f"📁 Event Log: {self.event_log_path}")
            print(f"📁 Goal Tracker: {self.goal_tracker.tracker_file}")
            
            # 최종 상태 확인
            recent_goals = self.goal_tracker.list_goals(limit=5, source_filter="music_daemon")
            print(f"\n📊 Recent Music-Generated Goals: {len(recent_goals)}")
            
            return {
                "success": True,
                "elapsed": elapsed,
                "goal_id": goal_info["goal_id"],
                "event_log": str(self.event_log_path)
            }
            
        except Exception as e:
            print(f"\n❌ Pipeline Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }


def main():
    workspace_root = get_workspace_root()
    pipeline = MusicToGoalPipelineE2E(workspace_root)
    
    result = pipeline.run_pipeline()
    
    # 결과 저장
    result_path = workspace_root / "outputs" / "music_goal_pipeline_result_latest.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Result saved: {result_path}")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
