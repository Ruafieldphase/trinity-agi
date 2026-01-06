# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import sys
from workspace_root import get_workspace_root
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# Canonical emotion keyword buckets (English + Hangul)
_EMOTION_KEYWORDS: Dict[str, list[str]] = {
    "hope": [
        "hope", "growth", "expand",
        "기대", "희망", "가능", "될까", "좋을", "발전", "성장", "미래", "전진",
    ],
    "concern": [
        "risk", "concern", "worry",
        "불안", "위험", "걱정", "문제", "실패", "두려움", "염려",
    ],
    "focus": [
        "now", "focus",
        "지금", "현재", "집중", "즉시", "바로", "먼저", "우선",
    ],
    "integration": [
        "integrate",
        "통합", "조율", "해결", "조합", "연결", "정리", "합쳐",
    ],
    "curiosity": [
        "궁금", "왜", "뭐야", "뭘까", "어떻게", "무엇", "어떤", "호기심", "why",
    ],
    "gratitude": [
        "감사", "고마워", "좋아", "멋져", "행복", "thanks", "appreciate",
    ],
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
    prompt_lower = (prompt or "").lower()
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

    try:
        _apply_learned_biases(prompt_lower, coord)
    except Exception:
        # The learner is optional; never break routing because of it.
        pass

    return coord


def _infer_rhythm(prompt_lower: str) -> str:
    integration_markers = ["integrate", "integration", "통합", "조율", "해결", "합쳐"]
    if any(keyword in prompt_lower for keyword in integration_markers):
        return "integration"

    reflection_markers = ["why", "risk", "concern", "위험", "왜", "걱정", "불안"]
    if any(keyword in prompt_lower for keyword in reflection_markers):
        return "reflection"

    planning_markers = ["plan", "schedule", "roadmap", "계획", "일정", "준비"]
    if any(keyword in prompt_lower for keyword in planning_markers):
        return "planning"

    return "exploration"


def _infer_priority(prompt_lower: str) -> int:
    urgent_markers = ["urgent", "critical", "emergency", "위험", "즉시", "긴급", "빠르게"]
    if any(marker in prompt_lower for marker in urgent_markers):
        return 4

    verify_markers = ["check", "verify", "review", "확인", "검토", "체크"]
    if any(marker in prompt_lower for marker in verify_markers):
        return 3

    consider_markers = ["maybe", "consider", "possible", "가능", "고려", "아마", "시도"]
    if any(marker in prompt_lower for marker in consider_markers):
        return 2

    return 1


def _infer_emotion(prompt_lower: str) -> Dict[str, Any]:
    matches = []
    for label, keywords in _EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in prompt_lower:
                matches.append(label)
                break
    return {"keywords": matches or ["neutral"]}


def _contains_word(text: str, pattern: str) -> bool:
    """Helper kept for compatibility; currently unused."""
    return bool(re.search(rf"\b{re.escape(pattern.lower())}\b", text))


# ------------------------
# Phase 4: Pattern Learning (optional at runtime)
# ------------------------

_MODEL_CACHE: Optional[Dict[str, Any]] = None


def _candidate_model_paths() -> list[Path]:
    here = Path(__file__).resolve()
    roots = [
        get_workspace_root() / "fdo_agi_repo" / "outputs" / "bqi_pattern_model.json",
        get_workspace_root() / "outputs" / "bqi_pattern_model.json",
    ]
    uniq: list[Path] = []
    seen: set[str] = set()
    for path in roots:
        key = str(path)
        if key not in seen:
            uniq.append(path)
            seen.add(key)
    return uniq


def _load_pattern_model() -> Optional[Dict[str, Any]]:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    for candidate in _candidate_model_paths():
        try:
            if candidate.exists():
                data = json.loads(candidate.read_text(encoding="utf-8"))
                _MODEL_CACHE = data
                return data
        except Exception:
            continue

    _MODEL_CACHE = {}
    return _MODEL_CACHE


def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    tokens = re.findall(r"[A-Za-z0-9\uac00-\ud7a3]+", text)
    return [tok for tok in tokens if len(tok) >= 2]


def _apply_learned_biases(prompt_lower: str, coord: BQICoordinate) -> None:
    model = _load_pattern_model() or {}
    if not model:
        return

    keywords = {token.lower() for token in _tokenize(prompt_lower)}
    if not keywords:
        return

    priority_rules: Dict[str, int] = model.get("priority_rules", {}) or {}
    delta = 0
    for kw in keywords:
        value = priority_rules.get(kw)
        if isinstance(value, int):
            delta += value
    if delta:
        coord.priority = max(1, min(4, coord.priority + (1 if delta > 0 else -1)))

    rhythm_rules: Dict[str, Dict[str, float]] = model.get("rhythm_rules", {}) or {}
    votes: Dict[str, float] = {}
    for kw in keywords:
        for rhythm, weight in (rhythm_rules.get(kw) or {}).items():
            if isinstance(weight, (int, float)):
                votes[rhythm] = votes.get(rhythm, 0.0) + float(weight)
    if votes:
        rhythm, weight = max(votes.items(), key=lambda item: item[1])
        if weight >= 0.6 and rhythm:
            coord.rhythm_phase = rhythm

    emotion_rules: Dict[str, Dict[str, float]] = model.get("emotion_rules", {}) or {}
    current = {str(e).lower() for e in coord.emotion.get("keywords", [])}
    additions: Dict[str, float] = {}
    for kw in keywords:
        for emotion, weight in (emotion_rules.get(kw) or {}).items():
            if isinstance(weight, (int, float)):
                additions[emotion] = additions.get(emotion, 0.0) + float(weight)
    if additions:
        for emotion, weight in sorted(additions.items(), key=lambda item: item[1], reverse=True)[:2]:
            if weight >= 0.6 and emotion.lower() not in current:
                current.add(emotion.lower())
    if current:
        coord.emotion["keywords"] = sorted(current)
