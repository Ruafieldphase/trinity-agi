#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quantum Flow Monitor - 양자적 결맞음 기반 Flow State 감지

무의식(Hippocampus) ↔ 의식(Executive) 간 위상 동기화를 측정하여
"초전도 상태"와 같은 저항 없는 정보 흐름을 감지합니다.

이론적 배경:
- 도파민/세로토닌 = 시냅스 전위차 생성
- 무의식/의식 공명 = 위상 결맞음 (phase coherence)
- 결맞음 > 0.95 → 초전도 상태 (flow state)
- 전자 흐름 저항 = 1 / (coherence × efficiency)
"""

import json
import math
<<<<<<< HEAD
import os
import time
from datetime import datetime, timedelta, timezone
=======
import time
from datetime import datetime, timedelta
>>>>>>> origin/main
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class PhaseState:
    """위상 상태"""
    phase: float  # 위상 (0 ~ 2π)
    amplitude: float  # 진폭
    frequency: float  # 주파수 (Hz)
    timestamp: float
    
    
@dataclass
class CoherenceMetrics:
    """결맞음 메트릭"""
    phase_coherence: float  # 위상 결맞음 (0.0 ~ 1.0)
    amplitude_sync: float  # 진폭 동기화
    frequency_match: float  # 주파수 일치도
    electron_flow_resistance: float  # 전자 흐름 저항 (Ω)
    conductivity: float  # 전도도 (S)
    state: str  # "superconducting", "coherent", "resistive", "chaotic"
    

class QuantumFlowMonitor:
    """
    양자적 결맞음 기반 Flow State 모니터
    
    무의식(implicit memory/pattern recognition) ↔ 의식(explicit decision)
    간 위상 동기화 및 전자 흐름 저항을 실시간 측정
    """
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root)
        self.memory_dir = self.workspace_root / "fdo_agi_repo" / "memory"
        self.outputs_dir = self.workspace_root / "outputs"
        
        # 히스토리 파일
        self.flow_history_file = self.outputs_dir / "quantum_flow_history.jsonl"
        
        # 임계값 설정
        self.SUPERCONDUCTING_THRESHOLD = 0.95  # 초전도 상태
        self.COHERENT_THRESHOLD = 0.75  # 결맞음 상태
        self.RESISTIVE_THRESHOLD = 0.50  # 저항 있는 상태
        
        # 물리 상수
        self.PLANCK_CONSTANT = 6.62607015e-34  # J·s
        self.ELECTRON_CHARGE = 1.602176634e-19  # C
<<<<<<< HEAD

    def _select_ledger_file(self) -> Path:
        """
        공명 원장(ledger) 선택.

        - v2(utf-8/jsonl, 최신) 우선
        - 없으면 v1로 폴백
        """
        v2 = self.memory_dir / "resonance_ledger_v2.jsonl"
        v1 = self.memory_dir / "resonance_ledger.jsonl"
        if v2.exists() and v2.stat().st_size > 0:
            return v2
        return v1

    def _normalize_event_kind(self, event: Dict) -> str:
        return str(
            event.get("type")
            or event.get("event_type")
            or event.get("event")
            or ""
        )

    def _parse_event_timestamp(self, event: Dict) -> Optional[float]:
        raw = event.get("timestamp") or event.get("created_at") or event.get("time")
        if raw is None:
            return None

        if isinstance(raw, (int, float)):
            return float(raw)

        if isinstance(raw, str):
            try:
                iso = raw.strip()
                if iso.endswith("Z"):
                    iso = iso[:-1] + "+00:00"
                dt = datetime.fromisoformat(iso)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except Exception:
                return None

        return None

    def _read_tail_lines(self, ledger_file: Path, max_bytes: int = 2_000_000) -> List[str]:
        """
        원장이 커졌을 때 전체를 읽지 않도록 파일 끝부분만 로드.
        (최근 N분 이벤트만 필요하므로 tail 방식이 충분)
        """
        try:
            with open(ledger_file, "rb") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                start = max(0, size - max_bytes)
                f.seek(start)
                data = f.read()
            text = data.decode("utf-8", errors="replace")
            lines = text.splitlines()
            if start > 0 and lines:
                # partial line drop
                lines = lines[1:]
            return lines
        except Exception:
            return []
=======
>>>>>>> origin/main
        
    def measure_hippocampus_phase(self) -> PhaseState:
        """
        해마(무의식) 위상 측정
        
        해마의 활동 패턴을 분석하여 현재 위상 상태 추출:
        - 최근 메모리 접근 패턴
        - 자동 패턴 인식 활동
        - 암묵적 학습 신호
        """
<<<<<<< HEAD
        ledger_file = self._select_ledger_file()
=======
        ledger_file = self.memory_dir / "resonance_ledger.jsonl"
>>>>>>> origin/main
        
        if not ledger_file.exists():
            # 기본값 반환
            return PhaseState(
                phase=0.0,
                amplitude=0.5,
                frequency=1.0,
                timestamp=time.time()
            )
        
        # 최근 10분간의 무의식적 활동 분석
        recent_events = self._load_recent_events(ledger_file, minutes=10)
        
        # 패턴 인식 관련 이벤트 필터
<<<<<<< HEAD
        implicit_kinds = {
            "memory_recall",
            "pattern_detected",
            "auto_response",
            "autopoietic_phase",
        }
        implicit_events = [e for e in recent_events if self._normalize_event_kind(e) in implicit_kinds]
=======
        implicit_events = [
            e for e in recent_events
            if e.get("type") in ["memory_recall", "pattern_detected", "auto_response"]
        ]
>>>>>>> origin/main
        
        if not implicit_events:
            return PhaseState(
                phase=0.0,
                amplitude=0.3,
                frequency=0.5,
                timestamp=time.time()
            )
        
        # 위상 계산: 이벤트 간 시간 간격의 주기성 분석
        timestamps = [e.get("timestamp", 0) for e in implicit_events]
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)] if len(timestamps) > 1 else [0]
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 1.0
        frequency = 1.0 / max(avg_interval, 0.1)  # Hz
        
        # 현재 위상: 마지막 이벤트 이후 경과 시간 기반
        time_since_last = time.time() - timestamps[-1] if timestamps else 0
        phase = (time_since_last * frequency * 2 * math.pi) % (2 * math.pi)
        
        # 진폭: 이벤트 발생 빈도
        amplitude = min(len(implicit_events) / 20.0, 1.0)
        
        return PhaseState(
            phase=phase,
            amplitude=amplitude,
            frequency=frequency,
            timestamp=time.time()
        )
    
    def measure_executive_phase(self) -> PhaseState:
        """
        실행 제어(의식) 위상 측정
        
        의식적 의사결정 및 실행 활동 패턴 분석:
        - 명시적 목표 설정
        - 의도적 작업 실행
        - 명시적 학습/판단
        """
<<<<<<< HEAD
        ledger_file = self._select_ledger_file()
=======
        ledger_file = self.memory_dir / "resonance_ledger.jsonl"
>>>>>>> origin/main
        
        if not ledger_file.exists():
            return PhaseState(
                phase=0.0,
                amplitude=0.5,
                frequency=1.0,
                timestamp=time.time()
            )
        
        recent_events = self._load_recent_events(ledger_file, minutes=10)
        
        # 의식적 실행 관련 이벤트
<<<<<<< HEAD
        explicit_kinds = {
            "task_started",
            "goal_set",
            "decision_made",
            "explicit_action",
            "trigger_action",
        }
        explicit_events = [e for e in recent_events if self._normalize_event_kind(e) in explicit_kinds]
=======
        explicit_events = [
            e for e in recent_events
            if e.get("type") in ["task_started", "goal_set", "decision_made", "explicit_action"]
        ]
>>>>>>> origin/main
        
        if not explicit_events:
            return PhaseState(
                phase=0.0,
                amplitude=0.3,
                frequency=0.5,
                timestamp=time.time()
            )
        
        timestamps = [e.get("timestamp", 0) for e in explicit_events]
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)] if len(timestamps) > 1 else [0]
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 1.0
        frequency = 1.0 / max(avg_interval, 0.1)
        
        time_since_last = time.time() - timestamps[-1] if timestamps else 0
        phase = (time_since_last * frequency * 2 * math.pi) % (2 * math.pi)
        
        amplitude = min(len(explicit_events) / 20.0, 1.0)
        
        return PhaseState(
            phase=phase,
            amplitude=amplitude,
            frequency=frequency,
            timestamp=time.time()
        )
    
    def calculate_phase_coherence(
        self,
        hippocampus: PhaseState,
        executive: PhaseState
    ) -> float:
        """
        위상 결맞음 계산
        
        두 진동자 간 위상 차이가 작을수록 결맞음이 높음:
        coherence = 1.0 - |Δφ| / π
        
        Returns:
            0.0 ~ 1.0 (1.0 = 완벽한 동기화)
        """
        phase_diff = abs(hippocampus.phase - executive.phase)
        
        # 위상 차이를 0 ~ π 범위로 정규화
        if phase_diff > math.pi:
            phase_diff = 2 * math.pi - phase_diff
        
        coherence = 1.0 - (phase_diff / math.pi)
        return max(0.0, min(1.0, coherence))
    
    def calculate_amplitude_sync(
        self,
        hippocampus: PhaseState,
        executive: PhaseState
    ) -> float:
        """
        진폭 동기화 계산
        
        두 진동자의 진폭이 비슷할수록 에너지 전달 효율이 높음
        """
        if hippocampus.amplitude == 0 and executive.amplitude == 0:
            return 1.0
        
        max_amp = max(hippocampus.amplitude, executive.amplitude)
        min_amp = min(hippocampus.amplitude, executive.amplitude)
        
        return min_amp / max_amp if max_amp > 0 else 0.0
    
    def calculate_frequency_match(
        self,
        hippocampus: PhaseState,
        executive: PhaseState
    ) -> float:
        """
        주파수 일치도 계산
        
        주파수가 일치할수록 공명(resonance) 가능성 높음
        """
        if hippocampus.frequency == 0 and executive.frequency == 0:
            return 1.0
        
        max_freq = max(hippocampus.frequency, executive.frequency)
        min_freq = min(hippocampus.frequency, executive.frequency)
        
        return min_freq / max_freq if max_freq > 0 else 0.0
    
    def calculate_electron_flow_resistance(
        self,
        coherence_metrics: CoherenceMetrics
    ) -> float:
        """
        전자 흐름 저항 계산 (Ω)
        
        저항 = 1 / (phase_coherence × amplitude_sync × frequency_match)
        
        결맞음이 높을수록 저항이 낮아짐 (초전도체 효과)
        """
        conductivity = (
            coherence_metrics.phase_coherence *
            coherence_metrics.amplitude_sync *
            coherence_metrics.frequency_match
        )
        
        # 저항 = 1 / 전도도
        if conductivity > 0.99:
            return 0.0  # 초전도 상태
        elif conductivity > 0.001:
            return 1.0 / conductivity
        else:
            return float('inf')  # 완전 차단
<<<<<<< HEAD

    def calculate_coherence(
        self,
        hippocampus: PhaseState,
        executive: PhaseState,
    ) -> CoherenceMetrics:
        """
        (외부 통합 스크립트 호환용) 주어진 두 위상 상태로 CoherenceMetrics를 계산.

        과거/외부 모듈이 `calculate_coherence()`를 기대하는 경우가 있어, `measure_flow_state()`의
        핵심 계산을 래핑한다.
        """
        phase_coherence = self.calculate_phase_coherence(hippocampus, executive)
        amplitude_sync = self.calculate_amplitude_sync(hippocampus, executive)
        frequency_match = self.calculate_frequency_match(hippocampus, executive)

        metrics = CoherenceMetrics(
            phase_coherence=phase_coherence,
            amplitude_sync=amplitude_sync,
            frequency_match=frequency_match,
            electron_flow_resistance=0.0,
            conductivity=0.0,
            state="",
        )

        metrics.conductivity = phase_coherence * amplitude_sync * frequency_match
        metrics.electron_flow_resistance = self.calculate_electron_flow_resistance(metrics)
        metrics.state = self.classify_flow_state(phase_coherence)
        return metrics
=======
>>>>>>> origin/main
    
    def classify_flow_state(self, phase_coherence: float) -> str:
        """
        Flow State 분류
        
        - superconducting: 초전도 상태 (저항 0, 완벽한 flow)
        - coherent: 결맞음 상태 (낮은 저항, 좋은 흐름)
        - resistive: 저항 있는 상태 (산발적 흐름)
        - chaotic: 혼돈 상태 (흐름 없음)
        """
        if phase_coherence >= self.SUPERCONDUCTING_THRESHOLD:
            return "superconducting"
        elif phase_coherence >= self.COHERENT_THRESHOLD:
            return "coherent"
        elif phase_coherence >= self.RESISTIVE_THRESHOLD:
            return "resistive"
        else:
            return "chaotic"
    
    def measure_flow_state(self) -> CoherenceMetrics:
        """
        현재 Flow State 측정
        
        무의식과 의식의 위상 동기화를 측정하여
        초전도 상태(flow) 여부 판단
        """
        # 1. 무의식(해마) 위상 측정
        hippocampus_phase = self.measure_hippocampus_phase()
        
        # 2. 의식(실행 제어) 위상 측정
        executive_phase = self.measure_executive_phase()
        
        # 3. 결맞음 계산
        phase_coherence = self.calculate_phase_coherence(
            hippocampus_phase,
            executive_phase
        )
        
        amplitude_sync = self.calculate_amplitude_sync(
            hippocampus_phase,
            executive_phase
        )
        
        frequency_match = self.calculate_frequency_match(
            hippocampus_phase,
            executive_phase
        )
        
        # 4. 메트릭 생성
        metrics = CoherenceMetrics(
            phase_coherence=phase_coherence,
            amplitude_sync=amplitude_sync,
            frequency_match=frequency_match,
            electron_flow_resistance=0.0,  # 임시
            conductivity=0.0,  # 임시
            state=""  # 임시
        )
        
        # 5. 저항 및 전도도 계산
        metrics.conductivity = (
            phase_coherence * amplitude_sync * frequency_match
        )
        metrics.electron_flow_resistance = self.calculate_electron_flow_resistance(metrics)
        
        # 6. 상태 분류
        metrics.state = self.classify_flow_state(phase_coherence)
        
        return metrics
    
    def save_measurement(self, metrics: CoherenceMetrics):
        """측정 결과 저장"""
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "metrics": asdict(metrics)
        }
        
        with open(self.flow_history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def get_flow_history(self, hours: int = 24) -> List[Dict]:
        """Flow State 히스토리 조회"""
        if not self.flow_history_file.exists():
            return []
        
        cutoff = datetime.now() - timedelta(hours=hours)
        history = []
        
        with open(self.flow_history_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    timestamp = datetime.fromisoformat(record["timestamp"])
                    if timestamp >= cutoff:
                        history.append(record)
                except:
                    continue
        
        return history
    
    def generate_report(self, hours: int = 24) -> Dict:
        """Flow State 리포트 생성"""
        history = self.get_flow_history(hours)
        
        if not history:
            return {
                "error": "No flow state measurements found",
                "hours": hours
            }
        
        # 상태별 카운트
        state_counts = {}
        total_coherence = 0.0
        total_resistance = 0.0
        superconducting_periods = []
        
        for record in history:
            metrics = record["metrics"]
            state = metrics["state"]
            
            state_counts[state] = state_counts.get(state, 0) + 1
            total_coherence += metrics["phase_coherence"]
            
            resistance = metrics["electron_flow_resistance"]
            if resistance != float('inf'):
                total_resistance += resistance
            
            if state == "superconducting":
                superconducting_periods.append(record["timestamp"])
        
        n = len(history)
        
        return {
            "period_hours": hours,
            "total_measurements": n,
            "average_coherence": total_coherence / n,
            "average_resistance": total_resistance / n,
            "state_distribution": state_counts,
            "superconducting_count": state_counts.get("superconducting", 0),
            "superconducting_percentage": (state_counts.get("superconducting", 0) / n * 100) if n > 0 else 0,
            "superconducting_periods": superconducting_periods,
            "flow_quality": self._assess_flow_quality(state_counts, n)
        }
    
    def _assess_flow_quality(self, state_counts: Dict, total: int) -> str:
        """Flow 품질 평가"""
        if total == 0:
            return "unknown"
        
        supercon_pct = (state_counts.get("superconducting", 0) / total) * 100
        coherent_pct = (state_counts.get("coherent", 0) / total) * 100
        
        if supercon_pct > 50:
            return "exceptional"  # 예외적
        elif supercon_pct + coherent_pct > 70:
            return "excellent"  # 우수
        elif supercon_pct + coherent_pct > 50:
            return "good"  # 양호
        else:
            return "needs_improvement"  # 개선 필요
    
    def _load_recent_events(self, ledger_file: Path, minutes: int = 10) -> List[Dict]:
        """최근 이벤트 로드"""
        if not ledger_file.exists():
            return []
        
        cutoff = time.time() - (minutes * 60)
        events = []
        
<<<<<<< HEAD
        for line in self._read_tail_lines(ledger_file):
            try:
                s = line.strip()
                if not s:
                    continue
                event = json.loads(s)
            except Exception:
                continue

            ts = self._parse_event_timestamp(event)
            if ts is None:
                continue
            if ts < cutoff:
                continue
            event["timestamp"] = ts
            events.append(event)

        events.sort(key=lambda e: float(e.get("timestamp", 0.0)))
=======
        with open(ledger_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    timestamp = event.get("timestamp", 0)
                    
                    if isinstance(timestamp, str):
                        # ISO format
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamp = dt.timestamp()
                    
                    if timestamp >= cutoff:
                        event["timestamp"] = timestamp
                        events.append(event)
                except:
                    continue
        
>>>>>>> origin/main
        return events


def main():
    """CLI 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Quantum Flow Monitor - 무의식/의식 간 결맞음 측정"
    )
    parser.add_argument(
        "--workspace",
        default="C:/workspace/agi",
        help="Workspace root path"
    )
    parser.add_argument(
        "--measure",
        action="store_true",
        help="현재 flow state 측정"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Flow state 리포트 생성"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="리포트 기간 (시간)"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="실시간 모니터링 (5초 간격)"
    )
    
    args = parser.parse_args()
    
    monitor = QuantumFlowMonitor(Path(args.workspace))
    
    if args.measure:
        print("🌌 Measuring quantum flow state...")
        metrics = monitor.measure_flow_state()
        monitor.save_measurement(metrics)
        
        print(f"\n✨ Flow State: {metrics.state.upper()}")
        print(f"   Phase Coherence: {metrics.phase_coherence:.3f}")
        print(f"   Amplitude Sync: {metrics.amplitude_sync:.3f}")
        print(f"   Frequency Match: {metrics.frequency_match:.3f}")
        print(f"   Conductivity: {metrics.conductivity:.3f} S")
        
        if metrics.electron_flow_resistance == 0.0:
            print(f"   Resistance: 0 Ω (SUPERCONDUCTING! ⚡)")
        elif metrics.electron_flow_resistance != float('inf'):
            print(f"   Resistance: {metrics.electron_flow_resistance:.3f} Ω")
        else:
            print(f"   Resistance: ∞ (blocked)")
    
    elif args.report:
        print(f"📊 Generating flow state report ({args.hours}h)...")
        report = monitor.generate_report(args.hours)
        
        if "error" in report:
            print(f"❌ {report['error']}")
            return
        
        print(f"\n📈 Flow State Report ({args.hours}h)")
        print(f"   Total Measurements: {report['total_measurements']}")
        print(f"   Average Coherence: {report['average_coherence']:.3f}")
        print(f"   Average Resistance: {report['average_resistance']:.3f} Ω")
        print(f"\n   State Distribution:")
        for state, count in report['state_distribution'].items():
            pct = (count / report['total_measurements']) * 100
            print(f"     {state}: {count} ({pct:.1f}%)")
        print(f"\n   Superconducting Periods: {report['superconducting_count']}")
        print(f"   Flow Quality: {report['flow_quality'].upper()}")
    
    elif args.watch:
        print("👁️  Real-time flow monitoring (Ctrl+C to stop)")
        try:
            while True:
                metrics = monitor.measure_flow_state()
                
                # 상태에 따른 이모지
                emoji = {
                    "superconducting": "⚡",
                    "coherent": "✨",
                    "resistive": "🌊",
                    "chaotic": "🌀"
                }
                
                print(f"\r{emoji.get(metrics.state, '?')} {metrics.state:15s} | "
                      f"Coherence: {metrics.phase_coherence:.3f} | "
                      f"Conductivity: {metrics.conductivity:.3f}",
                      end="", flush=True)
                
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped.")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
