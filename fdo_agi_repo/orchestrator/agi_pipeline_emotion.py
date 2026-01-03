"""
AGI Pipeline with Core System Integration
AGI 파이프라인에 Core 시스템 통합

감정 신호를 AGI 의사결정에 반영
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 상대 import 문제 해결
try:
    from .core_system import CoreSystem, EmotionStrategy
except ImportError:
    from core_system import CoreSystem, EmotionStrategy

logger = logging.getLogger(__name__)


class AGIPipelineWithEmotion:
    """
    감정 신호가 통합된 AGI 파이프라인
    
    김주환 이론 적용:
    - 두려움 신호 → 작업 우선순위 조정
    - FLOW 상태 → 창의적 작업 활성화
    - EMERGENCY → 안정화 우선
    """
    
    def __init__(self, workspace_root: Path):
        """
        Args:
            workspace_root: 워크스페이스 루트 경로
        """
        self.workspace_root = Path(workspace_root)
        self.Core = CoreSystem(workspace_root)
        
        logger.info(f"AGIPipelineWithEmotion initialized: {workspace_root}")
    
    def should_process_task(self, task_priority: str = "normal") -> Dict[str, Any]:
        """
        작업 처리 여부 결정 (감정 신호 기반)
        
        Args:
            task_priority: 작업 우선순위 ("low", "normal", "high", "critical")
        
        Returns:
            {
                'should_process': bool,
                'reason': str,
                'emotion_state': str,
                'recommended_delay_seconds': int,
            }
        """
        # 현재 감정 신호 수집
        result = self.Core.process_emotion_signal()
        strategy = EmotionStrategy(result['background_self']['strategy'])
        fear_level = result['fear_signal']['level']
        
        # 전략별 작업 처리 로직
        if strategy == EmotionStrategy.EMERGENCY:
            # 긴급 상황: critical만 처리
            should_process = (task_priority == "critical")
            reason = "🚨 긴급 상황 - critical 작업만 처리" if should_process else "⏸️ 긴급 상황 - 작업 중단"
            delay = 0 if should_process else 300  # 5분 대기
            
        elif strategy == EmotionStrategy.RECOVERY:
            # 휴식 필요: high 이상만 처리
            should_process = (task_priority in ["high", "critical"])
            reason = "🧘 휴식 권장 - 중요 작업만 처리" if should_process else "⏱️ 휴식 권장 - 작업 연기"
            delay = 0 if should_process else 60  # 1분 대기
            
        elif strategy == EmotionStrategy.STEADY:
            # 안정 유지: normal 이상 처리
            should_process = (task_priority in ["normal", "high", "critical"])
            reason = "👁️ 관찰 모드 - 정상 작업 진행" if should_process else "⏳ 관찰 모드 - low 작업 대기"
            delay = 0 if should_process else 30  # 30초 대기
            
        else:  # FLOW
            # 최적 상태: 모든 작업 처리
            should_process = True
            reason = "🚀 FLOW 상태 - 모든 작업 처리"
            delay = 0
        
        return {
            'should_process': should_process,
            'reason': reason,
            'emotion_state': strategy.value,
            'fear_level': fear_level,
            'recommended_delay_seconds': delay,
            'body_signals': result['body_signals'],
            'recommended_actions': result['recommended_actions'],
        }
    
    def adjust_task_batch_size(self) -> int:
        """
        감정 신호 기반 배치 크기 조정
        
        Returns:
            권장 배치 크기 (1 ~ 10)
        """
        result = self.Core.process_emotion_signal()
        strategy = EmotionStrategy(result['background_self']['strategy'])
        
        # 전략별 배치 크기
        batch_sizes = {
            EmotionStrategy.EMERGENCY: 1,   # 긴급: 1개씩 신중하게
            EmotionStrategy.RECOVERY: 2,    # 휴식: 2개씩
            EmotionStrategy.STEADY: 5,      # 관찰: 5개씩
            EmotionStrategy.FLOW: 10,       # 최적: 10개씩
        }
        
        batch_size = batch_sizes.get(strategy, 5)
        logger.info(f"Adjusted batch size: {batch_size} (strategy={strategy.value})")
        
        return batch_size
    
    def should_enable_creative_mode(self) -> bool:
        """
        창의 모드 활성화 여부
        
        FLOW 상태일 때만 활성화
        """
        result = self.Core.process_emotion_signal()
        strategy = EmotionStrategy(result['background_self']['strategy'])
        
        enable = (strategy == EmotionStrategy.FLOW)
        logger.info(f"Creative mode: {'ENABLED' if enable else 'DISABLED'} (strategy={strategy.value})")
        
        return enable
    
    def get_self_correction_threshold(self) -> float:
        """
        자기 교정 임계값 조정
        
        두려움이 높을수록 더 신중하게 (낮은 임계값)
        """
        result = self.Core.process_emotion_signal()
        fear_level = result['fear_signal']['level']
        
        # 두려움 역비례: 0.0 → 0.9, 1.0 → 0.5
        threshold = 0.9 - (fear_level * 0.4)
        threshold = round(threshold, 2)
        
        logger.info(f"Self-correction threshold: {threshold} (fear={fear_level})")
        
        return threshold
    
    def log_emotion_context(self, task_id: str, task_result: Dict[str, Any]):
        """
        작업 완료 시 감정 컨텍스트 로깅
        
        Args:
            task_id: 작업 ID
            task_result: 작업 실행 결과
        """
        result = self.Core.process_emotion_signal()
        
        log_entry = {
            'task_id': task_id,
            'task_success': task_result.get('success', False),
            'task_quality': task_result.get('quality', 0.0),
            'emotion_state': result['background_self']['strategy'],
            'fear_level': result['fear_signal']['level'],
            'body_signals': result['body_signals'],
            'timestamp': result['timestamp'],
        }
        
        # 로그 저장
        log_path = self.workspace_root / "outputs" / "emotion_task_correlation.jsonl"
        log_path.parent.mkdir(exist_ok=True)
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        logger.info(f"Emotion context logged: task={task_id}, state={log_entry['emotion_state']}")


def integrate_with_pipeline(workspace_root: str = "c:/workspace/agi") -> AGIPipelineWithEmotion:
    """
    파이프라인 통합 헬퍼
    
    Usage:
        pipeline = integrate_with_pipeline()
        
        # 작업 처리 전
        decision = pipeline.should_process_task(task_priority="normal")
        if decision['should_process']:
            # 작업 실행
            result = execute_task()
            
            # 감정 컨텍스트 로깅
            pipeline.log_emotion_context(task_id="task_001", task_result=result)
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    return AGIPipelineWithEmotion(workspace_root=Path(workspace_root))


if __name__ == '__main__':
    # 테스트
    pipeline = integrate_with_pipeline()
    
    print("\n🧠 AGI Pipeline with Emotion Integration")
    print("=" * 60)
    
    # 작업 처리 결정
    for priority in ["low", "normal", "high", "critical"]:
        decision = pipeline.should_process_task(task_priority=priority)
        status = "YES" if decision['should_process'] else "NO"
        print(f"Priority={priority:8s} → Process={status:5s} | {decision['reason']}")
    
    print("\n📊 Adaptive Settings:")
    print(f"  Batch Size: {pipeline.adjust_task_batch_size()}")
    print(f"  Creative Mode: {pipeline.should_enable_creative_mode()}")
    print(f"  Correction Threshold: {pipeline.get_self_correction_threshold()}")
    print("=" * 60)
