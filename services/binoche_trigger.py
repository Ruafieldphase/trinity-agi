"""
Binoche_Observer Trigger Function (BTF) - 비노체 트리거 시스템
====================================================

코어의 설계서를 기반으로 구현된 AGI 판단 지원 시스템.

핵심 원칙:
- BTF는 "결정을 대신하지 않는다"
- BTF는 "방향성(vector)만 제공한다"
- 비노체의 리듬을 기반으로 한 기준장(ground field)

호출 조건:
- API 실패 > 2회
- UI 행동 실패 > 3회  
- Confidence < 0.45
- 사용자 의도 해석 불가
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class BTFAction(Enum):
    """BTF 반환 액션 타입"""
    APPROVE = "approve"      # 진행
    MODIFY = "modify"        # 수정 후 진행
    REJECT = "reject"        # 중단
    ASK_USER = "ask_user"    # 비노체 직접 승인 필요


@dataclass
class BTFContext:
    """BTF 호출 시 전달되는 컨텍스트"""
    goal: str
    api_failures: int = 0
    ui_failures: int = 0
    confidence: float = 1.0
    previous_attempts: List[Dict[str, Any]] = field(default_factory=list)
    current_anxiety: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BTFResult:
    """BTF 판단 결과"""
    action: BTFAction
    confidence: float
    reasoning: str
    suggested_direction: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BinocheTriggerFunction:
    """
    BTF (Binoche_Observer Trigger Function)
    
    비노체가 부재한 시간대에 AGI가 판단을 멈추지 않도록 하는 트리거 시스템.
    
    "비노체를 모방하는 AI"가 아니라,
    "비노체의 리듬을 기반으로 방향성을 제공하는 기준장"으로 작동한다.
    """
    
    # 호출 임계값
    API_FAILURE_THRESHOLD = 2
    UI_FAILURE_THRESHOLD = 3
    CONFIDENCE_THRESHOLD = 0.45
    
    # 비노체 의존도 Phase
    PHASE_INITIAL = 1      # 60% 의존
    PHASE_MIDDLE = 2       # 20% 의존
    PHASE_MATURE = 3       # 5% 의존
    
    def __init__(self, persona_path: Optional[Path] = None):
        """
        Args:
            persona_path: 비노체 AI 페르소나 JSON 경로 (선택)
        """
        self.persona_path = persona_path or Path("C:/workspace/agi/fdo_agi_repo/orchestrator/binoche_persona.json")
        self.persona_data = self._load_persona()
        self.current_phase = self.PHASE_INITIAL
        self.invocation_count = 0
        self.history: List[BTFResult] = []
        
        logger.info(f"BTF initialized. Phase: {self.current_phase}")
    
    def _load_persona(self) -> Dict[str, Any]:
        """비노체 페르소나 데이터 로드"""
        if self.persona_path.exists():
            try:
                with open(self.persona_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load persona: {e}")
        return {}
    
    def should_invoke(self, ctx: BTFContext) -> bool:
        """BTF 호출이 필요한지 판단"""
        if ctx.api_failures > self.API_FAILURE_THRESHOLD:
            return True
        if ctx.ui_failures > self.UI_FAILURE_THRESHOLD:
            return True
        if ctx.confidence < self.CONFIDENCE_THRESHOLD:
            return True
        return False
    
    def invoke(self, ctx: BTFContext) -> BTFResult:
        """
        BTF 호출 - 비노체 리듬 기반 방향성 제공
        
        Args:
            ctx: BTF 컨텍스트
            
        Returns:
            BTFResult: 판단 결과 (결정이 아닌 방향성)
        """
        self.invocation_count += 1
        logger.info(f"BTF invoked (#{self.invocation_count}): goal='{ctx.goal[:50]}...'")
        
        # Phase에 따른 판단 로직
        result = self._analyze_and_suggest(ctx)
        
        # 히스토리 기록
        self.history.append(result)
        if len(self.history) > 100:
            self.history.pop(0)
        
        return result
    
    def _analyze_and_suggest(self, ctx: BTFContext) -> BTFResult:
        """컨텍스트 분석 및 방향성 제안"""
        
        # 1. 불안도 기반 판단
        if ctx.current_anxiety > 0.7:
            return BTFResult(
                action=BTFAction.ASK_USER,
                confidence=0.3,
                reasoning="높은 불안도 감지 - 비노체 직접 확인 필요",
                suggested_direction="잠시 멈추고 비노체에게 확인을 요청하세요."
            )
        
        # 2. 반복 실패 패턴 감지
        total_failures = ctx.api_failures + ctx.ui_failures
        if total_failures > 5:
            return BTFResult(
                action=BTFAction.REJECT,
                confidence=0.6,
                reasoning=f"반복 실패 감지 (API: {ctx.api_failures}, UI: {ctx.ui_failures})",
                suggested_direction="현재 접근 방식이 적합하지 않습니다. 다른 경로를 탐색하세요."
            )
        
        # 3. 비노체 패턴 기반 판단
        approval_pattern = self._get_binoche_pattern("approval")
        if approval_pattern and ctx.confidence > 0.3:
            return BTFResult(
                action=BTFAction.MODIFY,
                confidence=0.5,
                reasoning="비노체 패턴 참고 - 수정 후 진행 권장",
                suggested_direction=self._suggest_modification(ctx)
            )
        
        # 4. 기본: 낮은 확신으로 진행 허용
        if ctx.confidence > 0.2:
            return BTFResult(
                action=BTFAction.APPROVE,
                confidence=ctx.confidence,
                reasoning="최소 확신도 충족 - 주의하며 진행",
                suggested_direction="진행하되 결과를 면밀히 모니터링하세요."
            )
        
        # 5. 최종: 비노체에게 물어보기
        return BTFResult(
            action=BTFAction.ASK_USER,
            confidence=0.2,
            reasoning="확신도 매우 낮음 - 비노체 승인 필요",
            suggested_direction=None
        )
    
    def _get_binoche_pattern(self, pattern_type: str) -> Optional[Dict]:
        """비노체 페르소나에서 패턴 추출"""
        if not self.persona_data:
            return None
        patterns = self.persona_data.get("patterns", {})
        return patterns.get(pattern_type)
    
    def _suggest_modification(self, ctx: BTFContext) -> str:
        """수정 방향 제안"""
        suggestions = []
        
        if ctx.api_failures > 0:
            suggestions.append("API 대신 UI 탐색 시도")
        if ctx.ui_failures > 0:
            suggestions.append("다른 UI 경로나 검색 활용")
        if not suggestions:
            suggestions.append("탐색 범위를 좁혀서 재시도")
        
        return ". ".join(suggestions)
    
    def update_phase(self, new_phase: int):
        """비노체 의존도 Phase 업데이트"""
        if new_phase in [self.PHASE_INITIAL, self.PHASE_MIDDLE, self.PHASE_MATURE]:
            old_phase = self.current_phase
            self.current_phase = new_phase
            logger.info(f"BTF Phase updated: {old_phase} -> {new_phase}")
    
    def get_stats(self) -> Dict[str, Any]:
        """BTF 통계 반환"""
        action_counts = {}
        for result in self.history:
            action = result.action.value
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "total_invocations": self.invocation_count,
            "current_phase": self.current_phase,
            "action_distribution": action_counts,
            "avg_confidence": (
                sum(r.confidence for r in self.history) / len(self.history)
                if self.history else 0
            )
        }


# 모듈 레벨 인스턴스 (선택적 사용)
_btf_instance: Optional[BinocheTriggerFunction] = None

def get_btf() -> BinocheTriggerFunction:
    """BTF 싱글톤 인스턴스 반환"""
    global _btf_instance
    if _btf_instance is None:
        _btf_instance = BinocheTriggerFunction()
    return _btf_instance
