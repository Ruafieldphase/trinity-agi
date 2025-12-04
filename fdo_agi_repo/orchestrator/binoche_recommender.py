"""
Binoche Decision Recommender

Phase 6f 학습 결과를 활용하여 BQI 패턴 기반 자동 의사결정을 제공합니다.

작성자: GitHub Copilot (Gitco)
날짜: 2025-10-28
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Binoche Persona 모델 경로
BINOCHE_MODEL_PATH = Path(__file__).parent.parent / "outputs" / "binoche_persona.json"

class BinocheRecommender:
    """
    Phase 6f BQI 학습 결과 기반 자동 의사결정 추천
    
    8개 BQI 패턴에서 학습된 확률로 approve/revise/reject 결정을 추천합니다.
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Args:
            model_path: binoche_persona.json 경로 (기본값: outputs/binoche_persona.json)
        """
        self.model_path = model_path or BINOCHE_MODEL_PATH
        self.model = self._load_model()
        self.bqi_patterns = self.model.get("bqi_probabilities", {})
        
    def _load_model(self) -> Dict[str, Any]:
        """Binoche Persona 모델 로드"""
        if not self.model_path.exists():
            return {}
        
        with open(self.model_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_decision_recommendation(
        self, 
        bqi_coord: Dict[str, Any],
        quality: float = 0.0
    ) -> Tuple[str, float, str]:
        """
        BQI 좌표 기반 의사결정 추천
        
        Args:
            bqi_coord: BQI 좌표 dict {"priority": 1, "emotion": {"keywords": [...]}, "rhythm_phase": "exploration"}
            current_quality: 현재 quality 점수 (0.0-1.0)
        
        Returns:
            (decision, confidence, reason)
            - decision: "approve", "revise", "reject" 중 하나
            - confidence: 결정 신뢰도 (0.0-1.0)
            - reason: 결정 이유 설명
        """
        if not self.bqi_patterns:
            return "revise", 0.5, "Binoche model not loaded (fallback to revise)"
        
        # BQI 패턴 키 생성
        pattern_key = self._build_pattern_key(bqi_coord)
        
        # 패턴 매칭
        pattern_stats = self.bqi_patterns.get(pattern_key)
        
        if not pattern_stats:
            # 패턴이 없으면 기본 결정 (revise)
            return "revise", 0.3, f"No learned pattern for {pattern_key} (fallback)"
        
        # 확률 기반 결정
        approve_prob = pattern_stats.get("approve_prob", 0.0)
        revise_prob = pattern_stats.get("revise_prob", 0.0)
        reject_prob = pattern_stats.get("reject_prob", 0.0)
        samples = pattern_stats.get("sample_count", 0)
        
        # 최대 확률 결정
        max_prob = max(approve_prob, revise_prob, reject_prob)
        
        if max_prob == approve_prob:
            decision = "approve"
        elif max_prob == revise_prob:
            decision = "revise"
        else:
            decision = "reject"
        
        # Quality 기반 오버라이드 (Phase 6f 학습: quality > 0.8 → approve 강화)
        if quality >= 0.8 and approve_prob > 0.5:
            decision = "approve"
            reason = f"Pattern {pattern_key}: {approve_prob:.0%} approve (n={samples}), quality {quality:.2f} ≥ 0.8 → APPROVE"
        elif quality < 0.4 and reject_prob > 0.3:
            decision = "reject"
            reason = f"Pattern {pattern_key}: {reject_prob:.0%} reject (n={samples}), quality {quality:.2f} < 0.4 → REJECT"
        else:
            # 표준 패턴 기반 결정
            reason = f"Pattern {pattern_key}: approve={approve_prob:.0%} revise={revise_prob:.0%} reject={reject_prob:.0%} (n={samples}) → {decision.upper()}"
        
        # 신뢰도 계산: max_prob × log10(samples+1) / 3 (샘플 수 고려)
        import math
        confidence = min(1.0, max_prob * math.log10(samples + 1) / 3.0)
        
        return decision, confidence, reason
    
    def _build_pattern_key(self, bqi_coord: Dict[str, Any]) -> str:
        """
        BQI 좌표에서 패턴 키 생성 (binoche_persona_learner.py와 동일 로직)
        
        Args:
            bqi_coord: {"priority": 1, "emotion": {"keywords": [...]}, "rhythm_phase": "exploration"}
        
        Returns:
            Pattern key (예: "p1_e:neutral_r:exploration")
        """
        priority = bqi_coord.get("priority", 1)
        rhythm = bqi_coord.get("rhythm_phase", "unknown")
        emotions = bqi_coord.get("emotion", {"keywords": ["neutral"]})
        
        # Handle emotion dict structure
        if isinstance(emotions, dict):
            emotion_keywords = emotions.get("keywords", ["neutral"])
        else:
            emotion_keywords = emotions if isinstance(emotions, list) else ["neutral"]
        
        emotion_str = "keywords" if emotion_keywords != ["neutral"] else "neutral"
        
        return f"p{priority}_e:{emotion_str}_r:{rhythm}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        if not self.model:
            return {"loaded": False}
        
        info_theory = self.model.get("information_theory", {})
        bqi_power = info_theory.get("bqi_predictive_power", {})
        
        return {
            "loaded": True,
            "version": self.model.get("version", "unknown"),
            "total_decisions": self.model.get("stats", {}).get("total_decisions", 0),
            "bqi_patterns": len(self.bqi_patterns),
            "bqi_mutual_info": bqi_power.get("mutual_info", 0.0),
            "bqi_reduction_percent": bqi_power.get("reduction_percent", 0.0),
            "bqi_interpretation": bqi_power.get("interpretation", "unknown"),
            "patterns": list(self.bqi_patterns.keys())
        }
    
    def explain_pattern(self, pattern_key: str) -> Optional[Dict[str, Any]]:
        """특정 패턴 설명"""
        return self.bqi_patterns.get(pattern_key)


def get_binoche_recommendation(
    bqi_coord: Dict[str, Any],
    quality: float = 0.0
) -> Tuple[str, float, str]:
    """
    편의 함수: Binoche 추천 가져오기
    
    Args:
        bqi_coord: BQI 좌표
        quality: 현재 quality 점수
    
    Returns:
        (decision, confidence, reason)
    """
    recommender = BinocheRecommender()
    return recommender.get_decision_recommendation(bqi_coord, quality)


if __name__ == "__main__":
    # 테스트: p1_e:neutral_r:exploration (88% approve)
    recommender = BinocheRecommender()
    
    print("🧬 Binoche Recommender Test\n")
    print(f"Model Info: {json.dumps(recommender.get_model_info(), indent=2)}\n")
    
    # Test case 1: exploration (should approve)
    bqi_exploration = {
        "priority": 1,
        "emotion": {"keywords": ["neutral"]},
        "rhythm_phase": "exploration"
    }
    decision, conf, reason = recommender.get_decision_recommendation(bqi_exploration, quality=0.75)
    print(f"Test 1 - Exploration:")
    print(f"  BQI: {bqi_exploration}")
    print(f"  Decision: {decision} (confidence: {conf:.2f})")
    print(f"  Reason: {reason}\n")
    
    # Test case 2: planning (should revise)
    bqi_planning = {
        "priority": 1,
        "emotion": {"keywords": ["neutral"]},
        "rhythm_phase": "planning"
    }
    decision, conf, reason = recommender.get_decision_recommendation(bqi_planning, quality=0.65)
    print(f"Test 2 - Planning:")
    print(f"  BQI: {bqi_planning}")
    print(f"  Decision: {decision} (confidence: {conf:.2f})")
    print(f"  Reason: {reason}\n")
    
    # Test case 3: p3 exploration (should approve 100%)
    bqi_urgent = {
        "priority": 3,
        "emotion": {"keywords": ["neutral"]},
        "rhythm_phase": "exploration"
    }
    decision, conf, reason = recommender.get_decision_recommendation(bqi_urgent, quality=0.70)
    print(f"Test 3 - Urgent Exploration:")
    print(f"  BQI: {bqi_urgent}")
    print(f"  Decision: {decision} (confidence: {conf:.2f})")
    print(f"  Reason: {reason}\n")
    
    # Pattern 설명
    print("Pattern Details:")
    for pattern_key in ["p1_e:neutral_r:exploration", "p1_e:neutral_r:planning", "p3_e:neutral_r:exploration"]:
        details = recommender.explain_pattern(pattern_key)
        if details:
            print(f"  {pattern_key}: approve={details.get('approve_prob', 0):.0%}, revise={details.get('revise_prob', 0):.0%}, n={details.get('sample_count', 0)}")
