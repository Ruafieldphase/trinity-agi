#!/usr/bin/env python3
"""
Pipeline Integration Wrapper for BinocheDecisionEngine

기존 파이프라인의 복잡한 Binoche 시스템과 새로운 BinocheDecisionEngine을 통합

Phase 6b Enhancement:
- 단순화된 의사결정 로직
- 8가지 학습된 규칙 적용
- 70-80% 자동화 목표
"""

from typing import Dict, Any, Literal
import sys
from pathlib import Path

# Add parent to path for direct execution
if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

try:
    from .binoche_integration import BinocheDecisionEngine, BinocheDecision
except ImportError:
    from orchestrator.binoche_integration import BinocheDecisionEngine, BinocheDecision


class PipelineBinocheAdapter:
    """파이프라인용 Binoche 어댑터"""
    
    def __init__(self):
        self.engine = BinocheDecisionEngine()
    
    def make_decision(
        self,
        task_goal: str,
        eval_report: Dict[str, Any],
        bqi_coord: Dict[str, Any],
        meta_confidence: float = None
    ) -> Dict[str, Any]:
        """
        파이프라인에서 호출할 의사결정 함수
        
        Returns:
            {
                "action": "approve" | "revise" | "reject" | "ask_user",
                "confidence": float,
                "auto_approved": bool,
                "auto_revised": bool,
                "should_continue_pipeline": bool,
                "reason": str
            }
        """
        quality = float(eval_report.get("quality", 0.0))
        evidence_ok = bool(eval_report.get("evidence_ok", True))
        
        # Meta-cognition 확신도 사용 (있으면)
        confidence = meta_confidence if meta_confidence is not None else quality
        
        # BinocheDecisionEngine으로 의사결정
        decision: BinocheDecision = self.engine.review_task(
            task_goal=task_goal,
            quality=quality,
            bqi_coord=bqi_coord,
            evidence_ok=evidence_ok,
            confidence=confidence
        )
        
        # 파이프라인 형식으로 변환
        return {
            "action": decision.action,
            "confidence": decision.confidence,
            "auto_approved": decision.action == "approve",
            "auto_revised": decision.action == "revise",
            "should_continue_pipeline": decision.action in ["revise", "reject"],
            "reason": decision.reasoning,
            "rule_applied": decision.rule_applied,
            "bqi_pattern": decision.bqi_pattern,
            "quality_score": decision.quality_score
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        return self.engine.get_stats()
    
    def print_stats(self):
        """통계 출력"""
        self.engine.print_stats()


# 전역 인스턴스 (파이프라인에서 사용)
_pipeline_binoche = None

def get_pipeline_binoche() -> PipelineBinocheAdapter:
    """싱글톤 패턴으로 Binoche 어댑터 생성"""
    global _pipeline_binoche
    if _pipeline_binoche is None:
        _pipeline_binoche = PipelineBinocheAdapter()
    return _pipeline_binoche


def enhanced_binoche_decision(
    task_goal: str,
    eval_report: Dict[str, Any],
    bqi_coord: Dict[str, Any],
    meta_confidence: float = None
) -> Dict[str, Any]:
    """
    파이프라인에서 호출할 간소화된 Binoche 의사결정 함수
    
    기존 복잡한 get_binoche_recommendation + get_ensemble_decision을 대체
    
    Example:
        decision = enhanced_binoche_decision(
            task_goal="Implement new feature",
            eval_report={"quality": 0.85, "evidence_ok": True},
            bqi_coord={"priority": 1, "emotion": "neutral", "rhythm": "exploration"}
        )
        
        if decision["auto_approved"]:
            return early_success(...)
    """
    adapter = get_pipeline_binoche()
    return adapter.make_decision(task_goal, eval_report, bqi_coord, meta_confidence)


def print_session_stats():
    """세션 통계 출력 (디버깅용)"""
    adapter = get_pipeline_binoche()
    adapter.print_stats()


if __name__ == "__main__":
    # Test integration
    print("=== Pipeline Binoche Adapter Test ===\n")
    
    # Test 1: High quality exploration
    decision1 = enhanced_binoche_decision(
        task_goal="Implement monitoring dashboard",
        eval_report={"quality": 0.85, "evidence_ok": True},
        bqi_coord={"priority": 1, "emotion": "neutral", "rhythm": "exploration"}
    )
    print(f"Test 1: {decision1['action']} (auto_approved={decision1['auto_approved']})")
    print(f"  Reason: {decision1['reason']}\n")
    
    # Test 2: Planning task
    decision2 = enhanced_binoche_decision(
        task_goal="Plan deployment strategy",
        eval_report={"quality": 0.75, "evidence_ok": True},
        bqi_coord={"priority": 1, "emotion": "neutral", "rhythm": "planning"}
    )
    print(f"Test 2: {decision2['action']} (auto_revised={decision2['auto_revised']})")
    print(f"  Reason: {decision2['reason']}\n")
    
    print_session_stats()
