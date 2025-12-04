from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Length metrics


def calculate_length_metrics(response: str) -> Dict[str, Any]:
    sentences = re.split(r"[.!?]+", response)
    sentences = [s for s in sentences if s.strip()]
    words = response.split()
    char_count = len(response)
    word_count = len(words)
    sentence_count = len(sentences)
    avg_sentence_length = word_count / sentence_count if sentence_count else 0.0

    if word_count < 50:
        length_score = word_count / 50 * 0.5
    elif word_count <= 500:
        length_score = 0.5 + (word_count - 50) / 450 * 0.5
    else:
        length_score = max(0.7, 1.0 - (word_count - 500) / 1000)

    return {
        "char_count": char_count,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_length, 1),
        "length_score": round(length_score, 2),
    }


# ---------------------------------------------------------------------------
# Sentiment metrics

POSITIVE_EXTENDED = {
    "hope",
    "growth",
    "stability",
    "trust",
    "creative",
    "opportunity",
    "calm",
    "align",
    "care",
    "resilience",
    "insight",
    "balance",
    "support",
    "expand",
    "potential",
    "synergy",
    "harmony",
    "progress",
    "success",
    "improve",
}

NEGATIVE_EXTENDED = {
    "fear",
    "risk",
    "fail",
    "collapse",
    "danger",
    "stuck",
    "hurt",
    "doubt",
    "chaos",
    "conflict",
    "tension",
    "problem",
    "issue",
    "block",
    "weakness",
    "threat",
    "error",
    "concern",
    "limitation",
    "barrier",
}


def calculate_sentiment_metrics(response: str) -> Dict[str, Any]:
    tokens = [token.lower() for token in re.findall(r"\b[\w']+\b", response)]
    if not tokens:
        return {
            "sentiment_score": 0.0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_ratio": 1.0,
            "confidence": 0.0,
        }

    pos_count = sum(1 for t in tokens if t in POSITIVE_EXTENDED)
    neg_count = sum(1 for t in tokens if t in NEGATIVE_EXTENDED)

    if pos_count + neg_count == 0:
        sentiment_score = 0.0
        confidence = 0.0
    else:
        sentiment_score = (pos_count - neg_count) / len(tokens) * 10
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        confidence = min((pos_count + neg_count) / len(tokens), 1.0)

    neutral_ratio = 1.0 - min((pos_count + neg_count) / len(tokens), 1.0)

    return {
        "sentiment_score": round(sentiment_score, 2),
        "positive_count": pos_count,
        "negative_count": neg_count,
        "neutral_ratio": round(neutral_ratio, 2),
        "confidence": round(confidence, 2),
    }


# ---------------------------------------------------------------------------
# Completeness metrics

def calculate_completeness_metrics(
    response: str, seed_prompt: str, persona_role: str
) -> Dict[str, Any]:
    response_lower = response.lower()
    prompt_lower = seed_prompt.lower()

    reasoning_keywords = ["because", "since", "therefore", "thus", "hence", "왜냐하면", "따라서", "그러므로"]
    has_reasoning = any(kw in response_lower for kw in reasoning_keywords)

    example_keywords = ["for example", "such as", "instance", "예를 들어", "가령", "구체적으로"]
    has_concrete_example = any(kw in response_lower for kw in example_keywords)

    prompt_keywords = _extract_keywords(prompt_lower, top_n=5)
    keyword_hits = sum(1 for kw in prompt_keywords if kw in response_lower)
    keyword_coverage = keyword_hits / len(prompt_keywords) if prompt_keywords else 0.0

    role_alignment = _calculate_role_alignment(response_lower, persona_role)

    completeness_score = (
        0.3 * (1.0 if has_reasoning else 0.0)
        + 0.2 * (1.0 if has_concrete_example else 0.0)
        + 0.3 * keyword_coverage
        + 0.2 * role_alignment
    )

    return {
        "has_reasoning": has_reasoning,
        "has_concrete_example": has_concrete_example,
        "addresses_prompt": keyword_coverage >= 0.4,
        "keyword_coverage": round(keyword_coverage, 2),
        "role_alignment": round(role_alignment, 2),
        "completeness_score": round(completeness_score, 2),
    }


def _extract_keywords(text: str, top_n: int = 5) -> List[str]:
    words = [w for w in re.findall(r"\b[\w']+\b", text) if len(w) > 3]
    stopwords = {"that", "this", "with", "from", "have", "will", "what", "when", "어떻게", "무엇"}
    filtered = [w for w in words if w not in stopwords]
    counter = Counter(filtered)
    return [word for word, _ in counter.most_common(top_n)]


def _calculate_role_alignment(response: str, persona_role: str) -> float:
    role_keywords = {
        "Seed explorer": ["explore", "expand", "discover", "potential", "탐색", "확장"],
        "Critical reflector": ["challenge", "question", "concern", "risk", "반박", "문제"],
        "Integrator": ["synthesize", "reconcile", "integrate", "combine", "통합", "조화"],
        "Affect monitor": ["emotion", "feeling", "affect", "drift", "감정", "분위기"],
        "Implementation planner": ["plan", "action", "step", "implement", "계획", "실행"],
    }

    keywords = role_keywords.get(persona_role, [])
    if not keywords:
        return 0.5

    matches = sum(1 for kw in keywords if kw in response)
    return min(matches / 3, 1.0)


# ---------------------------------------------------------------------------
# Antithesis metrics

def calculate_critical_intensity(response: str, persona_id: str) -> Optional[Dict[str, Any]]:
    if persona_id != "antithesis":
        return None

    response_lower = response.lower()
    critical_keywords = [
        "however",
        "but",
        "concern",
        "problem",
        "overlook",
        "ignore",
        "risk",
        "fail",
        "weakness",
        "limitation",
        "flaw",
        "하지만",
        "그러나",
        "문제",
        "우려",
        "간과",
        "위험",
        "한계",
    ]
    critical_count = sum(1 for kw in critical_keywords if kw in response_lower)

    question_count = response.count("?") + response.count("？")

    sentiment = calculate_sentiment_metrics(response)
    disagreement_level = abs(min(sentiment["sentiment_score"], 0.0))

    intensity_score = (
        0.4 * min(critical_count / 5, 1.0)
        + 0.3 * min(question_count / 3, 1.0)
        + 0.3 * disagreement_level
    )

    return {
        "critical_keywords_count": critical_count,
        "question_count": question_count,
        "disagreement_level": round(disagreement_level, 2),
        "intensity_score": round(intensity_score, 2),
    }


# ---------------------------------------------------------------------------
# Resonance metrics (RUNE)

def calculate_resonance_metrics(
    response: str,
    tools_used: List[str],
    facts_verified: int,
    facts_total: int,
    reproducible: bool,
    external_references: List[str],
) -> Dict[str, Any]:
    impact_score = min(len(response) / 1000 + len(tools_used) * 0.05, 1.0)
    transparency = min(len(tools_used) * 0.1 + 0.5, 1.0)
    reproducibility = 0.85 if reproducible else 0.5
    verifiability = facts_verified / facts_total if facts_total else 0.7

    return {
        "impact_score": round(impact_score, 2),
        "transparency": round(transparency, 2),
        "reproducibility": round(reproducibility, 2),
        "verifiability": round(verifiability, 2),
        "notes": f"{facts_verified}/{facts_total} facts checked; {len(external_references)} references",
    }


# ---------------------------------------------------------------------------
# Aggregate Scores

def calculate_overall_score(
    length_metrics: Dict[str, Any],
    sentiment_metrics: Dict[str, Any],
    completeness_metrics: Dict[str, Any],
    critical_metrics: Optional[Dict[str, Any]],
    persona_id: str,
) -> float:
    weights = {
        "thesis": {"length": 0.2, "sentiment": 0.2, "completeness": 0.6},
        "antithesis": {
            "length": 0.2,
            "sentiment": 0.1,
            "completeness": 0.4,
            "critical_intensity": 0.3,
        },
        "synthesis": {"length": 0.2, "sentiment": 0.1, "completeness": 0.7},
    }

    w = weights.get(persona_id, weights["thesis"])
    score = (
        w.get("length", 0) * length_metrics["length_score"]
        + w.get("sentiment", 0) * abs(sentiment_metrics["sentiment_score"])
        + w.get("completeness", 0) * completeness_metrics["completeness_score"]
        + w.get("critical_intensity", 0) * ((critical_metrics or {}).get("intensity_score") or 0)
    )
    return round(score, 2)


def calculate_session_summary(log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    persona_scores = defaultdict(list)
    affect_trajectory: List[float] = []
    all_overall_scores: List[float] = []
    resonance_totals = {
        "impact_score": 0.0,
        "transparency": 0.0,
        "reproducibility": 0.0,
        "verifiability": 0.0,
        "count": 0,
    }

    for entry in log_entries:
        persona_id = entry["persona"]["id"]
        metrics = entry.get("evaluation_metrics", {})
        if not metrics:
            continue
        overall_score = metrics.get("overall_score", 0.0)

        persona_scores[persona_id].append(overall_score)
        all_overall_scores.append(overall_score)
        affect = entry.get("state_after", {}).get("affect_amplitude")
        if affect is not None:
            affect_trajectory.append(affect)
        resonance_metrics = metrics.get("resonance")
        if resonance_metrics:
            resonance_totals["impact_score"] += resonance_metrics.get("impact_score", 0)
            resonance_totals["transparency"] += resonance_metrics.get("transparency", 0)
            resonance_totals["reproducibility"] += resonance_metrics.get("reproducibility", 0)
            resonance_totals["verifiability"] += resonance_metrics.get("verifiability", 0)
            resonance_totals["count"] += 1

    persona_breakdown = {}
    for pid, scores in persona_scores.items():
        persona_breakdown[pid] = {
            "count": len(scores),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        }

    avg_overall = sum(all_overall_scores) / len(all_overall_scores) if all_overall_scores else 0.0
    if avg_overall >= 0.8:
        quality_rating = "Excellent"
    elif avg_overall >= 0.65:
        quality_rating = "Good"
    elif avg_overall >= 0.5:
        quality_rating = "Fair"
    else:
        quality_rating = "Poor"

    resonance_average = None
    if resonance_totals["count"]:
        c = resonance_totals["count"]
        resonance_average = {
            "impact_score": round(resonance_totals["impact_score"] / c, 2),
            "transparency": round(resonance_totals["transparency"] / c, 2),
            "reproducibility": round(resonance_totals["reproducibility"] / c, 2),
            "verifiability": round(resonance_totals["verifiability"] / c, 2),
        }

    return {
        "total_turns": len(all_overall_scores),
        "avg_overall_score": round(avg_overall, 2),
        "persona_breakdown": persona_breakdown,
        "affect_trajectory": [round(a, 2) for a in affect_trajectory],
        "quality_rating": quality_rating,
        "avg_resonance_metrics": resonance_average,
    }
