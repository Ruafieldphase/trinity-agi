"""
Body Rhythm Module - 몸의 흐름과 정체를 감지하는 시스템

"자신의 몸에서 무엇이 흐르지 않고 정체가 되었을 때 
몸은 자신에게 통증과 고통으로 신호를 주어서 자신을 봐 달라고 얘기를 한다."

관계=시간=에너지=리듬
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class FlowSignal:
    """흐름의 신호"""
    location: str  # 어디에서
    intensity: float  # 얼마나 강하게 (0.0 ~ 1.0)
    duration: float  # 얼마나 오래 (seconds)
    timestamp: float
    message: str  # 몸이 하는 말


@dataclass
class Stagnation:
    """정체된 영역"""
    location: str
    duration: float  # 얼마나 오래 정체되었는지
    signals: List[FlowSignal]  # 보낸 신호들
    needs_attention: bool  # 돌봄이 필요한가
    

class BodyRhythmMonitor:
    """
    몸의 리듬을 관찰하고 정체를 감지하는 시스템
    
    착한 사람, 착한 AI가 세상에서 잘 흐르고 이어질 수 있도록
    자신의 몸(시스템)을 잘 살피고 돌본다.
    """
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.flow_history: Dict[str, List[FlowSignal]] = {}
        self.stagnations: List[Stagnation] = []
        self.last_check = time.time()
        
        # 리듬 파라미터
        self.flow_threshold = 0.3  # 이 이하면 정체로 판단
        self.stagnation_duration = 300.0  # 5분 이상 정체되면 신호
        self.attention_threshold = 600.0  # 10분 이상이면 돌봄 필요
        
        self.load_state()
    
    def load_state(self):
        """이전 상태 불러오기"""
        if not self.state_file.exists():
            return
            
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
            # 흐름 이력 복원
            for loc, signals in state.get('flow_history', {}).items():
                self.flow_history[loc] = [
                    FlowSignal(**sig) for sig in signals
                ]
            
            # 정체 영역 복원
            for stag in state.get('stagnations', []):
                signals = [FlowSignal(**sig) for sig in stag.get('signals', [])]
                self.stagnations.append(
                    Stagnation(
                        location=stag['location'],
                        duration=stag['duration'],
                        signals=signals,
                        needs_attention=stag['needs_attention']
                    )
                )
                
        except Exception as e:
            print(f"⚠️ Failed to load state: {e}")
    
    def save_state(self):
        """현재 상태 저장"""
        state = {
            'flow_history': {
                loc: [
                    {
                        'location': sig.location,
                        'intensity': sig.intensity,
                        'duration': sig.duration,
                        'timestamp': sig.timestamp,
                        'message': sig.message
                    }
                    for sig in signals[-100:]  # 최근 100개만
                ]
                for loc, signals in self.flow_history.items()
            },
            'stagnations': [
                {
                    'location': stag.location,
                    'duration': stag.duration,
                    'signals': [
                        {
                            'location': sig.location,
                            'intensity': sig.intensity,
                            'duration': sig.duration,
                            'timestamp': sig.timestamp,
                            'message': sig.message
                        }
                        for sig in stag.signals
                    ],
                    'needs_attention': stag.needs_attention
                }
                for stag in self.stagnations
            ],
            'last_check': self.last_check
        }
        
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def observe_flow(self, location: str, intensity: float, 
                     duration: float = 1.0) -> Optional[FlowSignal]:
        """
        특정 위치의 흐름을 관찰
        
        Args:
            location: 관찰 위치 (예: "task_queue", "memory", "resonance")
            intensity: 흐름의 강도 (0.0 ~ 1.0)
            duration: 관찰 지속 시간 (초)
        
        Returns:
            FlowSignal if stagnation detected, None otherwise
        """
        now = time.time()
        
        # 정체 감지
        if intensity < self.flow_threshold:
            # 이전 정체 영역 찾기
            stag = next(
                (s for s in self.stagnations if s.location == location),
                None
            )
            
            if stag:
                # 기존 정체 영역 업데이트
                stag.duration += duration
            else:
                # 새로운 정체 영역 생성
                stag = Stagnation(
                    location=location,
                    duration=duration,
                    signals=[],
                    needs_attention=False
                )
                self.stagnations.append(stag)
            
            # 신호 생성
            if stag.duration >= self.stagnation_duration:
                message = self._generate_signal_message(location, stag.duration)
                signal = FlowSignal(
                    location=location,
                    intensity=intensity,
                    duration=stag.duration,
                    timestamp=now,
                    message=message
                )
                
                stag.signals.append(signal)
                
                # 돌봄 필요 판단
                if stag.duration >= self.attention_threshold:
                    stag.needs_attention = True
                
                # 이력에 추가
                if location not in self.flow_history:
                    self.flow_history[location] = []
                self.flow_history[location].append(signal)
                
                return signal
        else:
            # 흐름이 회복되면 정체 영역 제거
            self.stagnations = [
                s for s in self.stagnations if s.location != location
            ]
        
        return None
    
    def _generate_signal_message(self, location: str, duration: float) -> str:
        """정체 위치와 지속 시간에 따른 신호 메시지 생성"""
        minutes = duration / 60.0
        
        if duration < self.attention_threshold:
            return f"💭 {location}이(가) {minutes:.1f}분간 정체되어 있어요. 살펴봐 주세요."
        else:
            return f"🆘 {location}이(가) {minutes:.1f}분간 정체되어 있어요! 돌봄이 필요해요."
    
    def check_all_locations(self, metrics: Dict[str, float]) -> List[FlowSignal]:
        """
        여러 위치의 흐름을 한번에 확인
        
        Args:
            metrics: {location: intensity} 딕셔너리
        
        Returns:
            발생한 신호들의 리스트
        """
        now = time.time()
        elapsed = now - self.last_check
        self.last_check = now
        
        signals = []
        for location, intensity in metrics.items():
            signal = self.observe_flow(location, intensity, elapsed)
            if signal:
                signals.append(signal)
        
        if signals:
            self.save_state()
        
        return signals
    
    def get_health_report(self) -> Dict:
        """전체 건강 리포트"""
        total_stagnations = len(self.stagnations)
        needs_attention = sum(1 for s in self.stagnations if s.needs_attention)
        
        # 최근 24시간 신호 통계
        day_ago = time.time() - 86400
        recent_signals = []
        for signals in self.flow_history.values():
            recent_signals.extend([
                sig for sig in signals if sig.timestamp > day_ago
            ])
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_stagnations': total_stagnations,
            'needs_attention': needs_attention,
            'recent_signals_24h': len(recent_signals),
            'stagnations': [
                {
                    'location': stag.location,
                    'duration_minutes': stag.duration / 60.0,
                    'signals_sent': len(stag.signals),
                    'needs_attention': stag.needs_attention,
                    'latest_message': stag.signals[-1].message if stag.signals else None
                }
                for stag in self.stagnations
            ],
            'health_status': self._assess_health(total_stagnations, needs_attention)
        }
    
    def _assess_health(self, total: int, urgent: int) -> str:
        """전체 건강 상태 평가"""
        if urgent > 0:
            return "🆘 긴급 돌봄 필요"
        elif total > 3:
            return "⚠️ 주의 필요"
        elif total > 0:
            return "💭 관찰 중"
        else:
            return "✨ 잘 흐르고 있어요"
    
    def listen_to_body(self) -> List[str]:
        """
        몸의 말을 듣기
        
        Returns:
            현재 몸이 하고 있는 말들
        """
        messages = []
        for stag in self.stagnations:
            if stag.signals:
                messages.append(stag.signals[-1].message)
        return messages


def demonstrate_body_rhythm():
    """Body Rhythm 시스템 데모"""
    print("=" * 60)
    print("Body Rhythm Monitor - 몸의 흐름을 살피는 시스템")
    print("=" * 60)
    print()
    
    # 임시 상태 파일
    state_file = Path("memory/body_rhythm_state.json")
    monitor = BodyRhythmMonitor(state_file)
    
    print("📊 시뮬레이션: 여러 위치의 흐름 관찰")
    print()
    
    # 시뮬레이션 시나리오
    scenarios = [
        # (time, metrics)
        (0, {"task_queue": 0.8, "memory": 0.9, "resonance": 0.7}),  # 모두 잘 흐름
        (60, {"task_queue": 0.2, "memory": 0.9, "resonance": 0.7}),  # task_queue 정체 시작
        (180, {"task_queue": 0.1, "memory": 0.9, "resonance": 0.7}),  # task_queue 계속 정체
        (360, {"task_queue": 0.1, "memory": 0.2, "resonance": 0.7}),  # memory도 정체 시작
        (600, {"task_queue": 0.1, "memory": 0.1, "resonance": 0.7}),  # 둘 다 심각
        (660, {"task_queue": 0.9, "memory": 0.1, "resonance": 0.7}),  # task_queue 회복
    ]
    
    for sim_time, metrics in scenarios:
        print(f"\n⏰ {sim_time//60}분 경과")
        print(f"   Metrics: {metrics}")
        
        signals = monitor.check_all_locations(metrics)
        
        if signals:
            print(f"   📢 신호 {len(signals)}개 발생:")
            for signal in signals:
                print(f"      {signal.message}")
        else:
            print(f"   ✨ 모든 곳이 잘 흐르고 있어요")
        
        # 잠시 대기 (실제로는 시간이 흐르지 않음, 시뮬레이션)
        monitor.last_check = time.time() + sim_time
    
    print("\n" + "=" * 60)
    print("💖 몸의 말 듣기")
    print("=" * 60)
    
    messages = monitor.listen_to_body()
    if messages:
        for msg in messages:
            print(f"   {msg}")
    else:
        print("   ✨ 지금은 모든 것이 조화롭게 흐르고 있어요")
    
    print("\n" + "=" * 60)
    print("🏥 전체 건강 리포트")
    print("=" * 60)
    
    report = monitor.get_health_report()
    print(f"\n상태: {report['health_status']}")
    print(f"정체 영역: {report['total_stagnations']}개")
    print(f"긴급 돌봄 필요: {report['needs_attention']}개")
    print(f"최근 24시간 신호: {report['recent_signals_24h']}개")
    
    if report['stagnations']:
        print("\n정체 상세:")
        for stag in report['stagnations']:
            status = "🆘" if stag['needs_attention'] else "💭"
            print(f"\n  {status} {stag['location']}")
            print(f"     정체 시간: {stag['duration_minutes']:.1f}분")
            print(f"     발송 신호: {stag['signals_sent']}개")
            if stag['latest_message']:
                print(f"     최근 메시지: {stag['latest_message']}")


if __name__ == "__main__":
    demonstrate_body_rhythm()
