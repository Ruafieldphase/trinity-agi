"""
Adaptive Orchestrator - 적응형 조율자

생명체처럼 리듬을 감지하고 자원을 재분배하는 메타층 관찰자.

동작 원리:
1. Rhythm Detector: 시스템 리듬 감지 (NORMAL/BUSY/EMERGENCY/LEARNING)
2. Resource Allocator: 리듬에 맞는 자원 예산 계산
3. System Applier: 실제 시스템에 예산 적용
4. Feedback Loop: 결과 모니터링 & 적응

생명체 비유:
- 탄수화물 (NORMAL): 평상시 기본 대사
- 단백질 (BUSY): 바쁠 때 지속 가능한 운영
- 전투 모드 (EMERGENCY): 위기 시 모든 에너지 집중
- 보충 모드 (LEARNING): 휴식 시 학습 & 최적화
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# 상위 디렉토리를 경로에 추가
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from orchestrator.rhythm_detector import RhythmDetector, SystemRhythm, RhythmState
from orchestrator.resource_allocator import ResourceAllocator, ResourceBudget


class AdaptiveOrchestrator:
    """적응형 조율자 - 메타층 관찰자"""
    
    def __init__(self):
        self.detector = RhythmDetector()
        self.allocator = ResourceAllocator()
        self.repo_root = REPO_ROOT
        self.outputs_dir = self.repo_root / "outputs"
        
        # 현재 상태
        self.current_rhythm: Optional[SystemRhythm] = None
        self.current_budget: Optional[ResourceBudget] = None
        
        # 전환 히스토리
        self.transition_history = []
        
        # 설정 파일 경로
        self.resonance_config = self.repo_root / "config" / "resonance_config.json"
        self.worker_config = self.repo_root / "config" / "worker_config.json"
    
    def run_once(self) -> dict:
        """한 번 실행 (단일 사이클)"""
        # 1. 리듬 감지
        rhythm_state = self.detector.detect_rhythm()
        new_rhythm = SystemRhythm[rhythm_state.mode]
        
        # 2. 리듬 변화 감지
        rhythm_changed = (self.current_rhythm != new_rhythm)
        
        result = {
            "timestamp": rhythm_state.timestamp,
            "rhythm_state": rhythm_state,
            "rhythm_changed": rhythm_changed,
            "actions_taken": []
        }
        
        if rhythm_changed:
            print(f"\n🎵 Rhythm Changed: {self.current_rhythm or 'None'} → {new_rhythm.value}")
            print(f"   Reason: {rhythm_state.reason}")
            
            # 3. 자원 재분배
            new_budget = self.allocator.allocate_for_rhythm(new_rhythm, rhythm_state.timestamp)
            print(f"   Budget: {new_budget.budget_usage_percent}% usage, {new_budget.target_latency_sec}s target")
            
            # 4. 시스템에 적용
            actions = self._apply_resource_budget(new_budget, rhythm_state)
            result["actions_taken"] = actions
            
            # 5. 상태 업데이트
            self.current_rhythm = new_rhythm
            self.current_budget = new_budget
            
            # 6. 전환 기록
            self._record_transition(rhythm_state, new_budget, actions)
            
            # 7. 저장
            self.detector.save_state(rhythm_state)
            self.allocator.save_budget(new_budget)
        else:
            print(f"✅ Rhythm Stable: {new_rhythm.value} ({rhythm_state.confidence:.0%} confidence)")
        
        return result
    
    def run_continuous(self, interval_sec: int = 10, duration_sec: Optional[int] = None):
        """지속적 실행 (데몬 모드)"""
        print(f"\n{'=' * 70}")
        print(f"🎵 Adaptive Orchestrator - Continuous Mode")
        print(f"{'=' * 70}")
        print(f"Interval: {interval_sec}s")
        if duration_sec:
            print(f"Duration: {duration_sec}s")
        print(f"Press Ctrl+C to stop\n")
        
        start_time = time.time()
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                print(f"\n[Cycle {cycle_count}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                result = self.run_once()
                
                # Duration 체크
                if duration_sec:
                    elapsed = time.time() - start_time
                    if elapsed >= duration_sec:
                        print(f"\n⏱️ Duration limit reached ({duration_sec}s)")
                        break
                
                # 대기
                time.sleep(interval_sec)
        
        except KeyboardInterrupt:
            print(f"\n\n⏹️ Stopped by user")
        
        finally:
            print(f"\n{'=' * 70}")
            print(f"Summary:")
            print(f"  Total Cycles: {cycle_count}")
            print(f"  Transitions: {len(self.transition_history)}")
            print(f"  Final Rhythm: {self.current_rhythm.value if self.current_rhythm else 'None'}")
            print(f"{'=' * 70}\n")
    
    def _apply_resource_budget(self, budget: ResourceBudget, rhythm_state: RhythmState) -> list:
        """실제 시스템에 예산 적용"""
        actions = []
        
        try:
            # 1. Resonance 설정 업데이트
            if self._update_resonance_config(budget.resonance_mode, budget.resonance_policy):
                actions.append(f"✅ Resonance: {budget.resonance_mode} ({budget.resonance_policy})")
            else:
                actions.append(f"⚠️ Resonance: Config not found (would set {budget.resonance_mode})")
            
            # 2. Worker 설정 업데이트
            if self._update_worker_config(budget.worker_poll_ms):
                actions.append(f"✅ Worker: Poll interval → {budget.worker_poll_ms}ms")
            else:
                actions.append(f"⚠️ Worker: Config not found (would set {budget.worker_poll_ms}ms)")
            
            # 3. BQI 학습 제어
            bqi_action = "enable" if budget.bqi_learning_enabled else "pause"
            actions.append(f"ℹ️ BQI Learning: {bqi_action} (intensity {budget.bqi_learning_intensity:.0%})")
            
            # 4. Direct Mode 제어
            if budget.direct_mode:
                actions.append(f"🚀 Direct Mode: ENABLED (queue bypass)")
            
            # 5. 모니터링 제어
            monitor_action = "enabled" if budget.monitoring_enabled else "disabled"
            actions.append(f"📊 Monitoring: {monitor_action} ({budget.monitoring_interval_sec}s)")
            
        except Exception as e:
            actions.append(f"❌ Error applying budget: {e}")
        
        return actions
    
    def _update_resonance_config(self, mode: str, policy: str) -> bool:
        """Resonance 설정 업데이트"""
        try:
            if not self.resonance_config.exists():
                # 기본 설정 생성
                self.resonance_config.parent.mkdir(parents=True, exist_ok=True)
                config = {
                    "mode": mode,
                    "policy": policy,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "updated_by": "adaptive_orchestrator"
                }
            else:
                # 기존 설정 로드 & 업데이트
                with open(self.resonance_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                config["mode"] = mode
                config["policy"] = policy
                config["updated_at"] = datetime.now(timezone.utc).isoformat()
                config["updated_by"] = "adaptive_orchestrator"
            
            # 저장
            with open(self.resonance_config, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"⚠️ Resonance config update failed: {e}")
            return False
    
    def _update_worker_config(self, poll_ms: int) -> bool:
        """Worker 설정 업데이트"""
        try:
            if not self.worker_config.exists():
                # 기본 설정 생성
                self.worker_config.parent.mkdir(parents=True, exist_ok=True)
                config = {
                    "poll_interval_ms": poll_ms,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "updated_by": "adaptive_orchestrator"
                }
            else:
                # 기존 설정 로드 & 업데이트
                with open(self.worker_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                config["poll_interval_ms"] = poll_ms
                config["updated_at"] = datetime.now(timezone.utc).isoformat()
                config["updated_by"] = "adaptive_orchestrator"
            
            # 저장
            with open(self.worker_config, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"⚠️ Worker config update failed: {e}")
            return False
    
    def _record_transition(self, rhythm_state: RhythmState, budget: ResourceBudget, actions: list):
        """전환 기록"""
        transition = {
            "timestamp": rhythm_state.timestamp,
            "from_rhythm": self.current_rhythm.value if self.current_rhythm else None,
            "to_rhythm": rhythm_state.mode,
            "confidence": rhythm_state.confidence,
            "reason": rhythm_state.reason,
            "budget_usage": budget.budget_usage_percent,
            "target_latency": budget.target_latency_sec,
            "actions": actions
        }
        
        self.transition_history.append(transition)
        
        # 히스토리 저장
        history_file = self.outputs_dir / "orchestrator_transitions.jsonl"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(transition, ensure_ascii=False) + '\n')


def main():
    """메인 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Adaptive Orchestrator - 적응형 조율자",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 한 번 실행
  python adaptive_orchestrator.py --once
  
  # 지속 실행 (10초 간격)
  python adaptive_orchestrator.py --interval 10
  
  # 지속 실행 (5분간)
  python adaptive_orchestrator.py --interval 10 --duration 300
        """
    )
    
    parser.add_argument("--once", action="store_true", 
                       help="한 번만 실행")
    parser.add_argument("--interval", type=int, default=10,
                       help="지속 실행 시 간격 (초, 기본: 10)")
    parser.add_argument("--duration", type=int,
                       help="지속 실행 시 최대 시간 (초)")
    
    args = parser.parse_args()
    
    orchestrator = AdaptiveOrchestrator()
    
    if args.once:
        # 한 번만 실행
        result = orchestrator.run_once()
        print(f"\n✅ Done")
    else:
        # 지속 실행
        orchestrator.run_continuous(
            interval_sec=args.interval,
            duration_sec=args.duration
        )


if __name__ == "__main__":
    main()
