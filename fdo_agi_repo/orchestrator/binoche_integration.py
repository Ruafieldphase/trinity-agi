#!/usr/bin/env python3
"""
Binoche Persona Integration for AGI Pipeline (Phase 6b)

자동 의사결정 시스템 - 학습된 BinochePersona 모델을 파이프라인에 통합하여
70-80% 작업을 자동으로 승인/수정/거절 처리

Usage:
    from orchestrator.binoche_integration import BinocheDecisionEngine
    
    engine = BinocheDecisionEngine()
    decision = engine.review_task(task_spec, eval_report, outputs)
    # decision = {"action": "approve", "confidence": 0.92, "rule": "P1_Exploration"}
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass

# BQI 좌표 생성
try:
    from scripts.rune.bqi_adapter import analyse_question
except ModuleNotFoundError:
    # Allow fallback
    def analyse_question(goal: str) -> Dict[str, Any]:
        return {"priority": 1, "emotion": "neutral", "rhythm": "exploration"}


@dataclass
class BinocheDecision:
    """자동 의사결정 결과"""
    action: Literal["approve", "revise", "reject", "ask_user"]
    confidence: float  # 0.0 ~ 1.0
    rule_applied: str
    reasoning: str
    bqi_pattern: Optional[str] = None
    quality_score: Optional[float] = None


class BinocheDecisionEngine:
    """
    BinochePersona 기반 자동 의사결정 엔진
    
    Phase 6b 목표:
    - 70-80% 작업 자동 처리
    - 낮은 확신도 시 사용자 확인 요청
    - 학습된 8가지 규칙 적용
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Args:
            model_path: BinochePersona 모델 JSON 경로
                       (기본값: fdo_agi_repo/outputs/binoche_persona.json)
        """
        if model_path is None:
            repo_root = Path(__file__).resolve().parents[1]
            model_path = repo_root / "outputs" / "binoche_persona.json"
        
        self.model_path = model_path
        self.model = self._load_model()
        self.rules = self._extract_rules()
        
        # 통계 추적
        self.stats = {
            "total": 0,
            "approved": 0,
            "revised": 0,
            "rejected": 0,
            "asked_user": 0
        }
    
    def _load_model(self) -> Dict[str, Any]:
        """학습된 BinochePersona 모델 로드"""
        if not self.model_path.exists():
            print(f"[Binoche] Model not found: {self.model_path}")
            return self._get_default_model()
        
        with open(self.model_path, 'r', encoding='utf-8') as f:
            model = json.load(f)
        
        print(f"[Binoche] Loaded model v{model.get('version', 'unknown')}")
        print(f"[Binoche] Trained on {model.get('stats', {}).get('total_tasks', 0)} tasks")
        
        return model
    
    def _get_default_model(self) -> Dict[str, Any]:
        """기본 보수적 모델 (학습 모델이 없을 경우)"""
        return {
            "version": "0.0.0",
            "stats": {"total_tasks": 0},
            "rules": [
                {
                    "name": "DefaultAskUser",
                    "condition": "always",
                    "action": "ask_user",
                    "confidence": 1.0,
                    "rationale": "No trained model available"
                }
            ],
            "bqi_probabilities": {},
            "work_style": {"quality_threshold": 0.8}
        }
    
    def _extract_rules(self) -> List[Dict[str, Any]]:
        """규칙 추출 및 우선순위 정렬"""
        rules = self.model.get("rules", [])
        
        # 우선순위: approve > revise > reject > ask_user
        priority_map = {"approve": 1, "revise": 2, "reject": 3, "ask_user": 4}
        
        return sorted(
            rules,
            key=lambda r: (priority_map.get(r.get("action", "ask_user"), 9), -r.get("confidence", 0))
        )
    
    def review_task(
        self,
        task_goal: str,
        quality: float,
        bqi_coord: Optional[Dict[str, Any]] = None,
        evidence_ok: bool = True,
        confidence: Optional[float] = None
    ) -> BinocheDecision:
        """
        작업 결과를 자동으로 리뷰하고 의사결정 수행
        
        Args:
            task_goal: 작업 목표 (BQI 생성용)
            quality: 평가 품질 점수 (0.0 ~ 1.0)
            bqi_coord: BQI 좌표 (없으면 자동 생성)
            evidence_ok: 증거 충분 여부
            confidence: 시스템 확신도 (없으면 quality 사용)
        
        Returns:
            BinocheDecision: 자동 의사결정 결과
        """
        self.stats["total"] += 1
        
        # BQI 좌표 생성 (없으면)
        if bqi_coord is None:
            bqi_coord = analyse_question(task_goal)
        
        bqi_pattern = self._format_bqi_pattern(bqi_coord)
        
        # 확신도 계산
        if confidence is None:
            confidence = quality
        
        # 규칙 적용
        decision = self._apply_rules(
            bqi_pattern=bqi_pattern,
            quality=quality,
            confidence=confidence,
            evidence_ok=evidence_ok
        )
        
        # 통계 업데이트
        if decision.action == "approve":
            self.stats["approved"] += 1
        elif decision.action == "revise":
            self.stats["revised"] += 1
        elif decision.action == "reject":
            self.stats["rejected"] += 1
        elif decision.action == "ask_user":
            self.stats["asked_user"] += 1
        
        return decision
    
    def _format_bqi_pattern(self, bqi_coord: Dict[str, Any]) -> str:
        """BQI 좌표를 패턴 문자열로 변환"""
        p = bqi_coord.get("priority", 1)
        e = bqi_coord.get("emotion", "neutral")
        r = bqi_coord.get("rhythm", "exploration")
        
        # 감정 키워드 처리
        emotion_keywords = bqi_coord.get("emotion_keywords", [])
        if emotion_keywords:
            e = "keywords"
        
        return f"p{p}_e:{e}_r:{r}"
    
    def _apply_rules(
        self,
        bqi_pattern: str,
        quality: float,
        confidence: float,
        evidence_ok: bool
    ) -> BinocheDecision:
        """규칙 기반 의사결정"""
        
        # Rule 1-6: BQI 패턴 매칭
        bqi_probs = self.model.get("bqi_probabilities", {})
        if bqi_pattern in bqi_probs:
            pattern_stats = bqi_probs[bqi_pattern]
            approve_prob = pattern_stats.get("approve", 0.0)
            revise_prob = pattern_stats.get("revise", 0.0)
            reject_prob = pattern_stats.get("reject", 0.0)
            
            # 높은 승인 확률 (>= 90%)
            if approve_prob >= 0.90 and quality >= 0.7:
                return BinocheDecision(
                    action="approve",
                    confidence=approve_prob,
                    rule_applied=f"BQI_{bqi_pattern}",
                    reasoning=f"High approval rate ({approve_prob:.1%}) for this BQI pattern",
                    bqi_pattern=bqi_pattern,
                    quality_score=quality
                )
            
            # 높은 수정 확률 (>= 80%)
            if revise_prob >= 0.80:
                return BinocheDecision(
                    action="revise",
                    confidence=revise_prob,
                    rule_applied=f"BQI_{bqi_pattern}_Revise",
                    reasoning=f"High revision rate ({revise_prob:.1%}) for this BQI pattern",
                    bqi_pattern=bqi_pattern,
                    quality_score=quality
                )
        
        # Rule 7: 낮은 품질 자동 거절
        quality_threshold = self.model.get("work_style", {}).get("quality_threshold", 0.8)
        if quality < 0.5:
            return BinocheDecision(
                action="reject",
                confidence=0.90,
                rule_applied="LowQuality",
                reasoning=f"Quality {quality:.2f} below minimum threshold 0.5",
                bqi_pattern=bqi_pattern,
                quality_score=quality
            )
        
        # Rule 8: 낮은 확신도 → 사용자 확인
        if confidence < 0.6:
            return BinocheDecision(
                action="ask_user",
                confidence=1.0,
                rule_applied="LowConfidence",
                reasoning=f"Confidence {confidence:.2f} below threshold 0.6, requires user review",
                bqi_pattern=bqi_pattern,
                quality_score=quality
            )
        
        # 중간 품질 범위 (0.7 ~ quality_threshold)
        if quality >= 0.7:
            return BinocheDecision(
                action="approve",
                confidence=quality,
                rule_applied="MediumQuality",
                reasoning=f"Quality {quality:.2f} meets approval threshold",
                bqi_pattern=bqi_pattern,
                quality_score=quality
            )
        
        # 기본: 사용자 확인 (불확실한 경우)
        return BinocheDecision(
            action="ask_user",
            confidence=confidence,
            rule_applied="Default",
            reasoning="No matching rule, requires user review",
            bqi_pattern=bqi_pattern,
            quality_score=quality
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        total = self.stats["total"]
        if total == 0:
            return {"automation_rate": 0.0, **self.stats}
        
        automated = self.stats["approved"] + self.stats["revised"] + self.stats["rejected"]
        automation_rate = automated / total
        
        return {
            "automation_rate": automation_rate,
            "automation_percent": f"{automation_rate:.1%}",
            **self.stats
        }
    
    def print_stats(self):
        """통계 출력"""
        stats = self.get_stats()
        print("\n[Binoche] Automation Statistics:")
        print(f"  Total decisions: {stats['total']}")
        print(f"  Automation rate: {stats['automation_percent']}")
        print(f"    - Approved: {stats['approved']}")
        print(f"    - Revised: {stats['revised']}")
        print(f"    - Rejected: {stats['rejected']}")
        print(f"    - Asked user: {stats['asked_user']}")


def demo():
    """데모: BinocheDecisionEngine 사용 예제"""
    print("=== Binoche Decision Engine Demo ===\n")
    
    engine = BinocheDecisionEngine()
    
    # Test case 1: High quality exploration task
    decision1 = engine.review_task(
        task_goal="Implement new feature for AGI monitoring",
        quality=0.85,
        confidence=0.90
    )
    print(f"Test 1: {decision1.action} ({decision1.confidence:.1%}) - {decision1.reasoning}")
    
    # Test case 2: Planning task (likely revision)
    decision2 = engine.review_task(
        task_goal="Plan deployment strategy",
        quality=0.75,
        bqi_coord={"priority": 1, "emotion": "neutral", "rhythm": "planning"}
    )
    print(f"Test 2: {decision2.action} ({decision2.confidence:.1%}) - {decision2.reasoning}")
    
    # Test case 3: Low quality (rejection)
    decision3 = engine.review_task(
        task_goal="Quick test",
        quality=0.45,
        confidence=0.50
    )
    print(f"Test 3: {decision3.action} ({decision3.confidence:.1%}) - {decision3.reasoning}")
    
    # Test case 4: Low confidence (ask user)
    decision4 = engine.review_task(
        task_goal="Uncertain task",
        quality=0.70,
        confidence=0.55
    )
    print(f"Test 4: {decision4.action} ({decision4.confidence:.1%}) - {decision4.reasoning}")
    
    engine.print_stats()


if __name__ == "__main__":
    demo()
