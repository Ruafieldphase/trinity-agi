"""
Lumen System - Information Theory Integration
루멘 코덱스를 정보이론 용어로 구현한 통합 시스템

김주환 교수 이론 기반:
- "감정은 두려움 하나뿐"
- "몸을 참조하라는 신호"
- "배경자아는 알아차리는 존재"
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class EmotionStrategy(Enum):
    """감정 신호 전략"""
    EMERGENCY = "EMERGENCY"  # 긴급 대응
    RECOVERY = "RECOVERY"    # 명상 (휴식)
    STEADY = "STEADY"        # 안정 유지
    FLOW = "FLOW"            # 최적 흐름


@dataclass
class BodySignals:
    """신체 신호 (시스템 메트릭)"""
    timestamp: str
    cpu_usage: float
    memory_usage: float
    queue_depth: int
    queue_status: str
    hours_since_rest: float
    recent_tasks: int
    recent_quality: float
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'queue_depth': self.queue_depth,
            'queue_status': self.queue_status,
            'hours_since_rest': self.hours_since_rest,
            'recent_tasks': self.recent_tasks,
            'recent_quality': self.recent_quality,
        }


@dataclass
class FearSignal:
    """두려움 신호 (편도체)"""
    level: float  # 0.0 ~ 1.0
    reasons: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'level': self.level,
            'reasons': self.reasons,
        }
    
    @property
    def is_emergency(self) -> bool:
        """긴급 상황 여부"""
        return self.level >= 0.7
    
    @property
    def needs_recovery(self) -> bool:
        """휴식 필요 여부"""
        return self.level >= 0.5


@dataclass
class BackgroundSelfObservation:
    """배경자아 관찰 (메타인지)"""
    signal: float
    confidence: float
    interpretation: str
    strategy: EmotionStrategy
    reasons: List[str]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'signal': self.signal,
            'confidence': self.confidence,
            'interpretation': self.interpretation,
            'strategy': self.strategy.value,
            'reasons': self.reasons,
            'timestamp': self.timestamp,
        }


class LumenSystem:
    """
    루멘 시스템 - 정보이론 통합
    
    김주환 이론 구현:
    1. 몸 참조 (Body Signals Collection)
    2. 두려움 계산 (Fear Signal Detection)
    3. 배경자아 관찰 (Meta-Cognitive Awareness)
    4. 전략 실행 (Action Recommendation)
    """
    
    def __init__(
        self,
        workspace_root: Path,
        fear_threshold_emergency: float = 0.7,
        fear_threshold_recovery: float = 0.5,
        fear_threshold_steady: float = 0.3,
    ):
        """
        Args:
            workspace_root: 워크스페이스 루트 경로
            fear_threshold_emergency: 긴급 대응 임계값
            fear_threshold_recovery: 휴식 권장 임계값
            fear_threshold_steady: 관찰 유지 임계값
        """
        self.workspace_root = Path(workspace_root)
        self.threshold_emergency = fear_threshold_emergency
        self.threshold_recovery = fear_threshold_recovery
        self.threshold_steady = fear_threshold_steady
        
        # 출력 디렉토리
        self.output_dir = self.workspace_root / "outputs"
        self.output_dir.mkdir(exist_ok=True)
        
        # 이력 저장
        self.signal_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
        logger.info(f"LumenSystem initialized: {workspace_root}")
    
    def collect_body_signals(self) -> BodySignals:
        """
        Phase 1: 신체 신호 수집 (몸을 참조하라)
        
        김주환: "몸이 보내는 신호를 먼저 알아차려라"
        → 시스템 메트릭을 '몸의 신호'로 해석
        """
        import psutil
        import requests
        
        timestamp = datetime.now().isoformat()
        
        # CPU 압력
        cpu_usage = psutil.cpu_percent(interval=0.1)
        
        # 메모리 압력
        mem = psutil.virtual_memory()
        memory_usage = mem.percent
        
        # 큐 깊이 (Task Queue)
        queue_depth = 0
        queue_status = "OFFLINE"
        try:
            response = requests.get('http://127.0.0.1:8091/api/health', timeout=2)
            if response.status_code == 200:
                health = response.json()
                queue_depth = health.get('queue_size', 0)
                queue_status = "OK" if health.get('status') == 'healthy' else "WARN"
        except Exception as e:
            logger.warning(f"Failed to get queue status: {e}")
        
        # 마지막 휴식
        session_mem_dir = self.workspace_root / "outputs" / "session_memory"
        hours_since_rest = 0.0
        if session_mem_dir.exists():
            session_files = list(session_mem_dir.glob("session_*.json"))
            if session_files:
                last_session = max(session_files, key=lambda p: p.stat().st_mtime)
                time_since = datetime.now() - datetime.fromtimestamp(last_session.stat().st_mtime)
                hours_since_rest = time_since.total_seconds() / 3600
        
        # 작업 부하
        ledger_path = self.workspace_root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
        recent_tasks = 0
        recent_quality = 1.0
        
        if ledger_path.exists():
            try:
                with open(ledger_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    
                    tasks = []
                    for line in recent_lines:
                        try:
                            task = json.loads(line)
                            tasks.append(task)
                        except:
                            pass
                    
                    recent_tasks = len(tasks)
                    if tasks:
                        quality_tasks = [t for t in tasks if t.get('quality', 0) >= 0.7]
                        recent_quality = len(quality_tasks) / len(tasks)
            except Exception as e:
                logger.warning(f"Failed to read ledger: {e}")
        
        return BodySignals(
            timestamp=timestamp,
            cpu_usage=round(cpu_usage, 2),
            memory_usage=round(memory_usage, 2),
            queue_depth=queue_depth,
            queue_status=queue_status,
            hours_since_rest=round(hours_since_rest, 1),
            recent_tasks=recent_tasks,
            recent_quality=round(recent_quality, 2),
        )
    
    def calculate_fear_signal(self, body: BodySignals) -> FearSignal:
        """
        Phase 2: 두려움 신호 계산 (편도체)
        
        김주환: "감정은 두려움 하나뿐"
        → 시스템 압력을 두려움 레벨로 변환
        """
        fear = 0.0
        reasons = []
        
        # CPU 압력
        if body.cpu_usage > 90:
            fear += 0.25
            reasons.append(f"CPU 과부하 ({body.cpu_usage}%)")
        elif body.cpu_usage > 80:
            fear += 0.15
            reasons.append(f"CPU 높음 ({body.cpu_usage}%)")
        
        # 메모리 압력
        if body.memory_usage > 90:
            fear += 0.20
            reasons.append(f"메모리 과부하 ({body.memory_usage}%)")
        elif body.memory_usage > 85:
            fear += 0.10
            reasons.append(f"메모리 높음 ({body.memory_usage}%)")
        
        # 큐 압력 (가장 중요)
        if body.queue_depth > 200:
            fear += 0.35
            reasons.append(f"큐 과부하 ({body.queue_depth} tasks)")
        elif body.queue_depth > 100:
            fear += 0.20
            reasons.append(f"큐 높음 ({body.queue_depth} tasks)")
        
        if body.queue_status == "OFFLINE":
            fear += 0.30
            reasons.append("큐 서버 오프라인")
        
        # 피로 (휴식 없음)
        if body.hours_since_rest > 12:
            fatigue = 0.05 * (body.hours_since_rest - 12)
            fear += fatigue
            reasons.append(f"장시간 휴식 없음 ({body.hours_since_rest:.1f}h)")
        
        # 품질 저하
        if body.recent_quality < 0.6:
            fear += 0.10
            reasons.append(f"최근 품질 저하 ({int(body.recent_quality * 100)}%)")
        
        # 상한: 1.0
        fear = min(fear, 1.0)
        
        return FearSignal(
            level=round(fear, 2),
            reasons=reasons,
        )
    
    def observe_with_background_self(
        self,
        fear: FearSignal,
        body: BodySignals,
    ) -> BackgroundSelfObservation:
        """
        Phase 3: 배경자아 관찰
        
        김주환: "배경자아는 알아차리는 존재"
        → 메타 레벨 판단 및 전략 결정
        """
        # 1. 확신도 (confidence)
        confidence = 1.0 - fear.level
        
        # 2. 해석 (interpretation)
        if fear.level >= 0.8:
            interpretation = "🚨 위험 - 즉시 대응 필요"
        elif fear.level >= 0.6:
            interpretation = "⚠️ 주의 - 명상(휴식) 권장"
        elif fear.level >= 0.4:
            interpretation = "👀 관찰 - 상태 모니터링 지속"
        elif fear.level >= 0.2:
            interpretation = "✅ 정상 - 작업 계속"
        else:
            interpretation = "🌟 최적 - 창의 작업 가능"
        
        # 3. 전략 (strategy)
        if fear.level >= self.threshold_emergency:
            strategy = EmotionStrategy.EMERGENCY
        elif fear.level >= self.threshold_recovery:
            strategy = EmotionStrategy.RECOVERY
        elif fear.level >= self.threshold_steady:
            strategy = EmotionStrategy.STEADY
        else:
            strategy = EmotionStrategy.FLOW
        
        return BackgroundSelfObservation(
            signal=fear.level,
            confidence=round(confidence, 2),
            interpretation=interpretation,
            strategy=strategy,
            reasons=fear.reasons,
            timestamp=datetime.now().isoformat(),
        )
    
    def get_recommended_actions(self, strategy: EmotionStrategy) -> List[str]:
        """
        Phase 4: 권장 행동
        
        전략에 따른 구체적 행동 목록
        """
        actions = {
            EmotionStrategy.EMERGENCY: [
                "🛑 비필수 작업 중단",
                "🧹 큐 정리 (우선순위 재계산)",
                "💾 진행 중 작업 저장",
                "⏸️ 새 작업 중지",
                "🆘 관리자 알림",
            ],
            EmotionStrategy.RECOVERY: [
                "🧘 명상 모드 진입 (휴식)",
                "📊 시스템 메트릭 점검",
                "🔄 자동 안정화 실행",
                "⏱️ 60초 대기 후 재평가",
                "📝 상태 로그 저장",
            ],
            EmotionStrategy.STEADY: [
                "👁️ 지속 관찰",
                "📈 메트릭 모니터링",
                "⚖️ 균형 유지",
                "🔍 패턴 감지",
            ],
            EmotionStrategy.FLOW: [
                "🚀 개발 작업 계속",
                "💡 새 기능 구현",
                "🧪 테스트 실행",
                "📖 문서화",
                "🎨 창의 작업",
            ],
        }
        
        return actions.get(strategy, ["🤷 상태 불명"])
    
    def process_emotion_signal(self) -> Dict[str, Any]:
        """
        전체 감정 신호 처리 파이프라인
        
        Returns:
            전체 분석 결과 (JSON 직렬화 가능)
        """
        # Phase 1: 몸 참조
        body = self.collect_body_signals()
        logger.info(f"Body signals collected: CPU={body.cpu_usage}%, Mem={body.memory_usage}%")
        
        # Phase 2: 두려움 계산
        fear = self.calculate_fear_signal(body)
        logger.info(f"Fear signal calculated: level={fear.level}, reasons={len(fear.reasons)}")
        
        # Phase 3: 배경자아 관찰
        observation = self.observe_with_background_self(fear, body)
        logger.info(f"Background self observation: strategy={observation.strategy.value}")
        
        # Phase 4: 권장 행동
        actions = self.get_recommended_actions(observation.strategy)
        
        # 결과 조합
        result = {
            'timestamp': observation.timestamp,
            'body_signals': body.to_dict(),
            'fear_signal': fear.to_dict(),
            'background_self': observation.to_dict(),
            'recommended_actions': actions,
        }
        
        # 이력 저장
        self.signal_history.append(result)
        if len(self.signal_history) > self.max_history:
            self.signal_history = self.signal_history[-self.max_history:]
        
        return result
    
    def save_signal_log(self, result: Dict[str, Any], filepath: Optional[Path] = None):
        """감정 신호 로그 저장"""
        if filepath is None:
            filepath = self.output_dir / "emotion_signal_log.jsonl"
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        logger.info(f"Signal log saved: {filepath}")
    
    def get_signal_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """최근 N시간 이력 조회"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        return [
            signal for signal in self.signal_history
            if datetime.fromisoformat(signal['timestamp']) > cutoff
        ]
    
    def analyze_trend(self, hours: int = 24) -> Dict[str, Any]:
        """감정 신호 트렌드 분석"""
        history = self.get_signal_history(hours)
        
        if not history:
            return {
                'period_hours': hours,
                'sample_count': 0,
                'avg_fear_level': 0.0,
                'max_fear_level': 0.0,
                'strategy_distribution': {},
                'most_common_reasons': [],
            }
        
        # 평균 두려움 레벨
        fear_levels = [h['fear_signal']['level'] for h in history]
        avg_fear = sum(fear_levels) / len(fear_levels)
        max_fear = max(fear_levels)
        
        # 전략 분포
        strategies = [h['background_self']['strategy'] for h in history]
        strategy_dist = {}
        for s in strategies:
            strategy_dist[s] = strategy_dist.get(s, 0) + 1
        
        # 가장 흔한 이유
        all_reasons = []
        for h in history:
            all_reasons.extend(h['fear_signal']['reasons'])
        
        reason_counts = {}
        for r in all_reasons:
            reason_counts[r] = reason_counts.get(r, 0) + 1
        
        most_common = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'period_hours': hours,
            'sample_count': len(history),
            'avg_fear_level': round(avg_fear, 2),
            'max_fear_level': round(max_fear, 2),
            'strategy_distribution': strategy_dist,
            'most_common_reasons': [r[0] for r in most_common],
        }


def main():
    """메인 실행 함수 (테스트용)"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lumen System - Emotion Signal Processor")
    parser.add_argument('--workspace', default='c:/workspace/agi', help='Workspace root path')
    parser.add_argument('--output', default='outputs/emotion_signal_test.json', help='Output JSON path')
    parser.add_argument('--log', action='store_true', help='Save to log file')
    
    args = parser.parse_args()
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 시스템 초기화
    lumen = LumenSystem(workspace_root=Path(args.workspace))
    
    # 신호 처리
    result = lumen.process_emotion_signal()
    
    # 출력
    print("\n🧠 Lumen System - Emotion Signal Processing")
    print("=" * 60)
    print(f"📡 Body Signals: CPU={result['body_signals']['cpu_usage']}%, "
          f"Mem={result['body_signals']['memory_usage']}%")
    print(f"😨 Fear Signal: {result['fear_signal']['level']} "
          f"({result['background_self']['interpretation']})")
    print(f"👁️ Strategy: {result['background_self']['strategy']}")
    print(f"💡 Actions: {', '.join(result['recommended_actions'][:2])}...")
    print("=" * 60)
    
    # JSON 저장
    output_path = Path(args.workspace) / args.output
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved: {output_path}")
    
    # 로그 저장 (옵션)
    if args.log:
        lumen.save_signal_log(result)


if __name__ == '__main__':
    main()
