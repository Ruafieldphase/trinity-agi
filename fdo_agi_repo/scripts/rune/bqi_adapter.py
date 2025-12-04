from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pathlib import Path
import json

_EMOTION_KEYWORDS = {
    "hope": [
        "hope", "growth", "expand",
        "기대", "희망", "가능", "될까", "좋을", "발전", "성장", "해보", "될거", "잘"
    ],
    "concern": [
        "risk", "concern", "worry",
        "불안", "우려", "걱정", "문제", "위험", "실패", "어려", "힘들", "어렵"
    ],
    "focus": [
        "now", "focus",
        "지금", "현재", "당장", "즉시", "바로", "먼저", "우선"
    ],
    "integration": [
        "integrate",
        "합치", "통합", "조율", "연결", "조합", "묶", "통일", "합쳐"
    ],
    "curiosity": [
        "궁금", "알고", "뭐야", "뭘까", "어떻게", "왜", "어떤"
    ],
    "gratitude": [
        "고마", "감사", "좋아", "멋지", "훌륭"
    ]
}


@dataclass
class BQICoordinate:
    """Minimal coordinate structure used by META/PLAN/RUNE nodes."""

    timestamp: datetime
    rhythm_phase: str
    emotion: Dict[str, Any]
    priority: int
    raw_prompt: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat(),
            "rhythm_phase": self.rhythm_phase,
            "emotion": self.emotion,
            "priority": self.priority,
            "raw_prompt": self.raw_prompt,
        }


def analyse_question(prompt: str, *, now: Optional[datetime] = None) -> BQICoordinate:
    """Derive rhythm/emotion coordinates from the latest user prompt."""
    prompt_lower = prompt.lower()
    rhythm_phase = _infer_rhythm(prompt_lower)
    priority = _infer_priority(prompt_lower)
    emotion = _infer_emotion(prompt_lower)

    coord = BQICoordinate(
        timestamp=(now or datetime.now(timezone.utc)),
        rhythm_phase=rhythm_phase,
        emotion=emotion,
        priority=priority,
        raw_prompt=prompt,
    )

    # Phase 4: Apply learned biases from pattern model if available
    try:
        _apply_learned_biases(prompt_lower, coord)
    except Exception:
        # Never fail classification due to optional learner
        pass

    return coord


def _infer_rhythm(prompt_lower: str) -> str:
    if any(keyword in prompt_lower for keyword in ["integrate", "합", "통합"]):
        return "integration"
    if any(keyword in prompt_lower for keyword in ["why", "risk", "우려", "왜"]):
        return "reflection"
    if any(keyword in prompt_lower for keyword in ["plan", "schedule", "계획", "언제"]):
        return "planning"
    return "exploration"


def _infer_priority(prompt_lower: str) -> int:
    # Priority 4: 긴급 키워드
    if any(marker in prompt_lower for marker in [
        "urgent", "critical", "emergency",
        "위험", "즉시", "긴급", "당장", "빨리"
    ]):
        return 4
    
    # Priority 3: 확인/검토 키워드
    if any(marker in prompt_lower for marker in [
        "check", "verify", "review",
        "확인", "검토", "점검", "체크"
    ]):
        return 3
    
    # Priority 2: 가능성/고려 키워드
    if any(marker in prompt_lower for marker in [
        "maybe", "consider", "possible",
        "가능", "고려", "아마", "혹시"
    ]):
        return 2
    
    return 1


def _infer_emotion(prompt_lower: str) -> Dict[str, Any]:
    matches = []
    for label, keywords in _EMOTION_KEYWORDS.items():
        # 한글은 단어 경계 매칭 완화 (부분 문자열 포함)
        for kw in keywords:
            if kw.lower() in prompt_lower:
                matches.append(label)
                break  # 해당 감정 레이블은 한 번만 추가
    return {"keywords": matches or ["neutral"]}


def _contains_word(text: str, pattern: str) -> bool:
    """더 이상 사용 안함 - _infer_emotion에서 직접 처리"""
    return bool(re.search(rf"\b{re.escape(pattern.lower())}\b", text))


# ------------------------
# Phase 4: Pattern Learning (optional at runtime)
# ------------------------

_MODEL_CACHE: Optional[Dict[str, Any]] = None


def _candidate_model_paths() -> list[Path]:
    here = Path(__file__).resolve()
    roots = [
        # Typical repo layout: d:\nas_backup\fdo_agi_repo\outputs
        here.parents[2] / "fdo_agi_repo" / "outputs" / "bqi_pattern_model.json",
        # Fallback: sibling outputs under current repo root
        here.parents[2] / "outputs" / "bqi_pattern_model.json",
    ]
    # Uniquify while preserving order
    seen = set()
    uniq: list[Path] = []
    for p in roots:
        if str(p) not in seen:
            uniq.append(p)
            seen.add(str(p))
    return uniq


def _load_pattern_model() -> Optional[Dict[str, Any]]:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    for p in _candidate_model_paths():
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                _MODEL_CACHE = data
                return data
        except Exception:
            continue
    _MODEL_CACHE = {}
    return _MODEL_CACHE


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[A-Za-z0-9가-힣_]+", text or "") if len(t) >= 2]


def _apply_learned_biases(prompt_lower: str, coord: BQICoordinate) -> None:
    model = _load_pattern_model() or {}
    if not model:
        return

    kws = set(t.lower() for t in _tokenize(prompt_lower))
    if not kws:
        return

    # Priority adjustments: sum deltas in [-1, +1], clamp to [1, 4]
    pr_rules: Dict[str, int] = model.get("priority_rules", {}) or {}
    delta = 0
    for kw in kws:
        d = pr_rules.get(kw)
        if isinstance(d, int):
            delta += d
    if delta != 0:
        new_p = max(1, min(4, coord.priority + (1 if delta > 0 else -1)))
        coord.priority = new_p

    # Rhythm voting with weights
    rh_rules: Dict[str, Dict[str, float]] = model.get("rhythm_rules", {}) or {}
    votes: Dict[str, float] = {}
    for kw in kws:
        for rh, w in (rh_rules.get(kw) or {}).items():
            if not isinstance(w, (int, float)):
                continue
            votes[rh] = votes.get(rh, 0.0) + float(w)
    if votes:
        # pick max if sufficiently confident
        rh, w = max(votes.items(), key=lambda x: x[1])
        if w >= 0.6 and rh:
            coord.rhythm_phase = rh

    # Emotion enrichment with weights
    em_rules: Dict[str, Dict[str, float]] = model.get("emotion_rules", {}) or {}
    current = set(e.lower() for e in coord.emotion.get("keywords", []) if isinstance(e, str))
    add_scores: Dict[str, float] = {}
    for kw in kws:
        for em, w in (em_rules.get(kw) or {}).items():
            if not isinstance(w, (int, float)):
                continue
            add_scores[em] = add_scores.get(em, 0.0) + float(w)
    # Add up to 2 highest that are not already present and above threshold
    if add_scores:
        for em, w in sorted(add_scores.items(), key=lambda x: x[1], reverse=True)[:2]:
            if w >= 0.6 and em not in current:
                current.add(em)
    if current:
        coord.emotion["keywords"] = list(current)
