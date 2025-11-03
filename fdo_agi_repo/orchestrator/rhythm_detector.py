"""
Rhythm Detector - 시스템 리듬 감지기

생명체처럼 시스템의 현재 "리듬"을 감지하여 적절한 모드를 결정합니다.

리듬 모드:
- 🟢 NORMAL (평상시): 모든 기능 활성화
- 🟡 BUSY (바쁨): 필수 기능만 활성화
- 🔴 EMERGENCY (위기): 생존 최우선
- 🔵 LEARNING (휴식): 학습 & 최적화
"""

import os
import sys
import json
import psutil
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Optional
from pathlib import Path

# 상위 디렉토리를 경로에 추가 (Resonance import용)
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from orchestrator.resonance_bridge import get_resonance_config_path
except ImportError:
    get_resonance_config_path = None


class SystemRhythm(Enum):
    """시스템 리듬 모드 (생명체 비유)"""
    NORMAL = "NORMAL"        # 평상시 (탄수화물 모드)
    BUSY = "BUSY"            # 바쁨 (단백질 모드)
    EMERGENCY = "EMERGENCY"  # 위기 (전투 모드)
    LEARNING = "LEARNING"    # 휴식 (보충 모드)


@dataclass
class RhythmState:
    """리듬 상태"""
    timestamp: str
    mode: str  # SystemRhythm.value
    confidence: float  # 0.0-1.0
    
    # 시스템 메트릭
    cpu_usage: float  # 0-100
    memory_usage: float  # 0-100
    disk_usage: float  # 0-100
    
    # AGI 메트릭
    queue_size: int
    error_rate: float  # 0.0-1.0
    
    # Lumen 메트릭
    lumen_rhythm: Optional[str]  # "RESONANT" / "DISSONANT" / "CHAOTIC"
    
    # 시간대
    hour: int
    is_night: bool  # 03:00-06:00
    
    # 판단 이유
    reason: str


class RhythmDetector:
    """리듬 감지기"""
    
    def __init__(self):
        self.repo_root = REPO_ROOT
        self.outputs_dir = self.repo_root / "outputs"
        self.queue_status_file = self.repo_root.parent / "LLM_Unified" / "ion-mentoring" / "outputs" / "queue_status.json"
        self.ledger_file = self.repo_root / "memory" / "resonance_ledger.jsonl"
        
        # 임계값 (튜닝 가능)
        self.thresholds = {
            "cpu_emergency": 80,
            "cpu_busy": 50,
            "cpu_learning": 30,
            "queue_emergency": 50,
            "queue_busy": 10,
            "queue_learning": 5,
            "error_rate_emergency": 0.10,
            "error_rate_busy": 0.05,
        }
    
    def detect_rhythm(self) -> RhythmState:
        """현재 리듬 감지"""
        now = datetime.now(timezone.utc)
        
        # 1. 시스템 메트릭 수집
        cpu = self._get_cpu_usage()
        memory = self._get_memory_usage()
        disk = self._get_disk_usage()
        
        # 2. AGI 메트릭 수집
        queue_size = self._get_queue_size()
        error_rate = self._get_error_rate()
        
        # 3. Lumen 리듬 가져오기
        lumen_rhythm = self._get_lumen_rhythm()
        
        # 4. 시간대 확인
        hour = now.hour
        is_night = 3 <= hour < 6
        
        # 5. 리듬 판단
        mode, confidence, reason = self._decide_rhythm(
            cpu, memory, queue_size, error_rate, lumen_rhythm, is_night
        )
        
        # 6. 상태 객체 생성
        state = RhythmState(
            timestamp=now.isoformat(),
            mode=mode.value,
            confidence=confidence,
            cpu_usage=cpu,
            memory_usage=memory,
            disk_usage=disk,
            queue_size=queue_size,
            error_rate=error_rate,
            lumen_rhythm=lumen_rhythm,
            hour=hour,
            is_night=is_night,
            reason=reason
        )
        
        return state
    
    def _decide_rhythm(
        self,
        cpu: float,
        memory: float,
        queue_size: int,
        error_rate: float,
        lumen_rhythm: Optional[str],
        is_night: bool
    ) -> tuple:
        """리듬 판단 로직 (생명체 비유)"""
        reasons = []
        
        # 우선순위 1: EMERGENCY (위기)
        if error_rate > self.thresholds["error_rate_emergency"]:
            reasons.append(f"Error rate critical: {error_rate:.1%}")
        if cpu > self.thresholds["cpu_emergency"]:
            reasons.append(f"CPU overload: {cpu:.1f}%")
        if queue_size > self.thresholds["queue_emergency"]:
            reasons.append(f"Queue overflow: {queue_size} tasks")
        if lumen_rhythm == "CHAOTIC":
            reasons.append("Lumen: CHAOTIC rhythm")
        
        if reasons:
            return (
                SystemRhythm.EMERGENCY,
                0.95,
                "⚠️ EMERGENCY: " + ", ".join(reasons)
            )
        
        # 우선순위 2: BUSY (바쁨)
        reasons = []
        if cpu > self.thresholds["cpu_busy"]:
            reasons.append(f"CPU busy: {cpu:.1f}%")
        if queue_size > self.thresholds["queue_busy"]:
            reasons.append(f"Queue busy: {queue_size} tasks")
        if error_rate > self.thresholds["error_rate_busy"]:
            reasons.append(f"Error rate elevated: {error_rate:.1%}")
        if lumen_rhythm == "DISSONANT":
            reasons.append("Lumen: DISSONANT rhythm")
        
        if reasons:
            return (
                SystemRhythm.BUSY,
                0.85,
                "⚡ BUSY: " + ", ".join(reasons)
            )
        
        # 우선순위 3: LEARNING (휴식)
        if is_night and cpu < self.thresholds["cpu_learning"] and queue_size < self.thresholds["queue_learning"]:
            return (
                SystemRhythm.LEARNING,
                0.90,
                f"🌙 LEARNING: Night time (CPU {cpu:.1f}%, queue {queue_size})"
            )
        
        # 기본: NORMAL (평상시)
        return (
            SystemRhythm.NORMAL,
            0.80,
            f"✅ NORMAL: Healthy system (CPU {cpu:.1f}%, queue {queue_size}, errors {error_rate:.1%})"
        )
    
    def _get_cpu_usage(self) -> float:
        """CPU 사용률"""
        try:
            return psutil.cpu_percent(interval=1)
        except Exception:
            return 0.0
    
    def _get_memory_usage(self) -> float:
        """메모리 사용률"""
        try:
            return psutil.virtual_memory().percent
        except Exception:
            return 0.0
    
    def _get_disk_usage(self) -> float:
        """디스크 사용률"""
        try:
            return psutil.disk_usage('/').percent
        except Exception:
            return 0.0
    
    def _get_queue_size(self) -> int:
        """큐 크기 (Task Queue Server)"""
        try:
            if self.queue_status_file.exists():
                with open(self.queue_status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("queue_size", 0)
            return 0
        except Exception:
            return 0
    
    def _get_error_rate(self) -> float:
        """에러율 (최근 1시간)"""
        try:
            if not self.ledger_file.exists():
                return 0.0
            
            # 최근 1시간 이벤트 수집
            cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
            total = 0
            errors = 0
            
            with open(self.ledger_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        ts_str = event.get("timestamp", "")
                        if not ts_str:
                            continue
                        
                        # 타임스탬프 파싱 (여러 형식 지원)
                        ts = None
                        for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"]:
                            try:
                                ts = datetime.strptime(ts_str.replace("+00:00", ""), fmt.replace("Z", ""))
                                ts = ts.replace(tzinfo=timezone.utc)
                                break
                            except ValueError:
                                continue
                        
                        if not ts or ts < cutoff:
                            continue
                        
                        total += 1
                        outcome = event.get("outcome", "").lower()
                        if "error" in outcome or "fail" in outcome:
                            errors += 1
                    except Exception:
                        continue
            
            if total == 0:
                return 0.0
            
            return errors / total
        
        except Exception:
            return 0.0
    
    def _get_lumen_rhythm(self) -> Optional[str]:
        """Lumen Cost Rhythm 상태"""
        try:
            # Lumen outputs 경로
            lumen_output = self.repo_root.parent / "LLM_Unified" / "ion-mentoring" / "lumen" / "monitoring" / "outputs"
            rhythm_file = lumen_output / "cost_rhythm_state.json"
            
            if rhythm_file.exists():
                with open(rhythm_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("rhythm_status")
            
            return None
        except Exception:
            return None
    
    def save_state(self, state: RhythmState):
        """상태 저장"""
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 최신 상태 (덮어쓰기)
        latest_file = self.outputs_dir / "rhythm_state_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(state), f, indent=2, ensure_ascii=False)
        
        # 2. 히스토리 (추가)
        history_file = self.outputs_dir / "rhythm_state_history.jsonl"
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(state), ensure_ascii=False) + '\n')


def main():
    """테스트 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rhythm Detector - 시스템 리듬 감지")
    parser.add_argument("--save", action="store_true", help="상태 저장")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()
    
    detector = RhythmDetector()
    state = detector.detect_rhythm()
    
    if args.save:
        detector.save_state(state)
        print(f"✅ Saved to: {detector.outputs_dir / 'rhythm_state_latest.json'}")
    
    if args.json:
        print(json.dumps(asdict(state), indent=2, ensure_ascii=False))
    else:
        # 예쁘게 출력
        print(f"\n{'=' * 70}")
        print(f"🎵 System Rhythm Detection")
        print(f"{'=' * 70}\n")
        print(f"Mode:       {state.mode} ({state.confidence:.0%} confidence)")
        print(f"Reason:     {state.reason}")
        print(f"\nSystem Metrics:")
        print(f"  CPU:      {state.cpu_usage:.1f}%")
        print(f"  Memory:   {state.memory_usage:.1f}%")
        print(f"  Disk:     {state.disk_usage:.1f}%")
        print(f"\nAGI Metrics:")
        print(f"  Queue:    {state.queue_size} tasks")
        print(f"  Errors:   {state.error_rate:.1%}")
        print(f"\nLumen:")
        print(f"  Rhythm:   {state.lumen_rhythm or 'N/A'}")
        print(f"\nTime:")
        print(f"  Hour:     {state.hour}:00")
        print(f"  Night:    {'Yes' if state.is_night else 'No'}")
        print(f"\nTimestamp: {state.timestamp}")
        print()


if __name__ == "__main__":
    main()
