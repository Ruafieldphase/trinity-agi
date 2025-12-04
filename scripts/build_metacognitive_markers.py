#!/usr/bin/env python3
"""Derive simple metacognitive markers from combined conversation log."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Set

import pandas as pd

COMBINED_PATH = Path("outputs/ai_conversations_combined.csv")
OUTPUT_DIR = Path("outputs")
MARKERS_CSV = OUTPUT_DIR / "metacognitive_markers.csv"
CATEGORY_COUNTS_CSV = OUTPUT_DIR / "metacognitive_category_counts.csv"

CATEGORY_PATTERNS: Dict[str, Iterable[str]] = {
    "cross_persona": [
        "루멘",
        "루아",
        "엘로",
        "세나",
        "루빛",
        "rio",
        "ari",
        "perple",
        "[agent",
        "코멧",
        "코플",
    ],
    "self_reflection": ["나는", "내가", "스스로", "느낌", "느껴", "생각해", "성찰", "돌아보", "감정"],
    "alignment": ["정렬", "조율", "alignment", "공명", "합의", "동기화"],
    "action_plan": ["계획", "다음", "해야", "step", "실행", "준비", "로드맵", "todo"],
    "uncertainty": ["모르겠", "불확실", "걱정", "어떡", "혼란", "의문", "?", "긴장"],
    "signal_check": ["신호", "패턴", "리듬", "데이터", "지표", "분석", "로그"],
}


def normalize_text(value: str) -> str:
    return value.replace("\n", " ").replace("\ufffd", "?").strip()


def detect_categories(text: str) -> List[str]:
    lowered = text.lower()
    categories: List[str] = []
    for category, keywords in CATEGORY_PATTERNS.items():
        for keyword in keywords:
            if keyword.lower() in lowered:
                categories.append(category)
                break
    return categories


def main() -> None:
    if not COMBINED_PATH.exists():
        raise SystemExit("Combined dataset not found. Run build_combined_conversations first.")

    df = pd.read_csv(COMBINED_PATH)
    df["timestamp"] = pd.to_datetime(df.get("timestamp"), errors="coerce", utc=True)

    marker_rows = []
    for _, row in df.iterrows():
        content = str(row.get("content") or "")
        categories = detect_categories(content)
        if not categories:
            continue
        snippet = normalize_text(content)
        marker_rows.append(
            {
                "timestamp": row["timestamp"].isoformat() if pd.notnull(row["timestamp"]) else "",
                "source": row.get("source", ""),
                "conversation_id": row.get("conversation_id", ""),
                "author_role": row.get("author_role", ""),
                "categories": "; ".join(categories),
                "content": snippet,
            }
        )

    markers_df = pd.DataFrame(marker_rows)
    markers_df.sort_values("timestamp", inplace=True, ignore_index=True)
    markers_df.to_csv(MARKERS_CSV, index=False)

    category_counts: Dict[str, int] = {}
    for categories in markers_df.get("categories", []):
        if not categories:
            continue
        for category in {c.strip() for c in categories.split(";")}:
            category_counts[category] = category_counts.get(category, 0) + 1
    pd.DataFrame(
        sorted(category_counts.items(), key=lambda item: (-item[1], item[0])),
        columns=["category", "count"],
    ).to_csv(CATEGORY_COUNTS_CSV, index=False)

    print(f"[build_metacognitive_markers] markers: {len(markers_df)} rows")


if __name__ == "__main__":
    main()

