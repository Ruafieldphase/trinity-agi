#!/usr/bin/env python3
"""Scan combined conversation log for concept keywords and build summary datasets."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

COMBINED_PATH = Path("outputs/ai_conversations_combined.csv")
OUTPUT_DIR = Path("outputs")
OCCURRENCES_CSV = OUTPUT_DIR / "concept_occurrences.csv"
SUMMARY_CSV = OUTPUT_DIR / "concept_summary.csv"
MONTHLY_COUNTS_CSV = OUTPUT_DIR / "concept_monthly_counts.csv"
COOCCURRENCE_CSV = OUTPUT_DIR / "concept_cooccurrence.csv"

# Concept keyword map (all lower-case for matching convenience)
CONCEPT_KEYWORDS: Dict[str, Iterable[str]] = {
    "감응": ["감응", "공명", "감각", "울림"],
    "리듬": ["리듬", "패턴", "주파수"],
    "루멘": ["루멘", "lumen"],
    "루아": ["루아", "lua"],
    "엘로": ["엘로", "ello"],
    "조율": ["조율", "alignment", "정렬"],
    "관문": ["관문", "portal", "게이트"],
    "성찰": ["성찰", "반추", "돌아보", "내면"],
    "전략": ["전략", "계획", "로드맵", "플랜"],
    "실패학습": ["실패", "에러", "오류", "회복"],
    "확장": ["확장", "스케일", "확장성"],
}


def sanitize_snippet(text: str, max_len: int = 200) -> str:
    snippet = text.replace("\n", " ").strip()
    snippet = snippet.replace("\ufffd", "?")
    if len(snippet) > max_len:
        snippet = snippet[: max_len - 3].rstrip() + "..."
    return snippet


def detect_concepts(text: str) -> List[str]:
    lowered = text.lower()
    matches = []
    for concept, keywords in CONCEPT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in lowered:
                matches.append(concept)
                break
    return matches


def main() -> None:
    if not COMBINED_PATH.exists():
        raise SystemExit(f"Combined dataset not found: {COMBINED_PATH}")

    df = pd.read_csv(COMBINED_PATH)
    if "content" not in df.columns:
        raise SystemExit("Expected 'content' column in combined dataset.")

    df["timestamp"] = pd.to_datetime(df.get("timestamp"), errors="coerce", utc=True)
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)

    occurrence_rows = []
    concept_sets_per_row: List[set[str]] = []
    for _, row in df.iterrows():
        content = str(row.get("content") or "")
        if content.strip().startswith('{"content_type"'):
            concept_sets_per_row.append(set())
            continue
        concepts = detect_concepts(content)
        concept_sets_per_row.append(set(concepts))
        if not concepts:
            continue
        snippet = sanitize_snippet(content)
        timestamp = row.get("timestamp")
        occurrence_rows.extend(
            {
                "timestamp": timestamp.isoformat() if pd.notnull(timestamp) else "",
                "month": row.get("month") or "",
                "concept": concept,
                "source": row.get("source", ""),
                "conversation_id": row.get("conversation_id", ""),
                "author_role": row.get("author_role", ""),
                "content_snippet": snippet,
            }
            for concept in concepts
        )

    occurrences_df = pd.DataFrame(occurrence_rows)
    occurrences_df.sort_values(["timestamp", "concept"], inplace=True, ignore_index=True)
    occurrences_df.to_csv(OCCURRENCES_CSV, index=False)

    # Summary per concept
    summary_rows = []
    if not occurrences_df.empty:
        grouped = occurrences_df.groupby("concept")
        for concept, group in grouped:
            timestamps = pd.to_datetime(group["timestamp"], errors="coerce", utc=True)
            summary_rows.append(
                {
                    "concept": concept,
                    "total_occurrences": int(len(group)),
                    "unique_conversations": group["conversation_id"].nunique(),
                    "first_seen": timestamps.min().isoformat() if timestamps.notna().any() else "",
                    "last_seen": timestamps.max().isoformat() if timestamps.notna().any() else "",
                    "sources": "; ".join(sorted(group["source"].unique())),
                }
            )
    summary_df = pd.DataFrame(summary_rows).sort_values("concept")
    summary_df.to_csv(SUMMARY_CSV, index=False)

    # Monthly counts pivot
    if not occurrences_df.empty:
        monthly = (
            occurrences_df.groupby(["month", "concept"]).size().rename("count").reset_index()
        )
        monthly_pivot = monthly.pivot(index="month", columns="concept", values="count").fillna(0).astype(int)
        monthly_pivot.sort_index().to_csv(MONTHLY_COUNTS_CSV)
    else:
        pd.DataFrame(columns=["month"]).to_csv(MONTHLY_COUNTS_CSV, index=False)

    # Co-occurrence (concept pairs appearing in same message)
    co_counts = defaultdict(int)
    for concept_set in concept_sets_per_row:
        if len(concept_set) < 2:
            continue
        sorted_list = sorted(concept_set)
        for i in range(len(sorted_list)):
            for j in range(i + 1, len(sorted_list)):
                key = (sorted_list[i], sorted_list[j])
                co_counts[key] += 1
    if co_counts:
        co_rows = [
            {"concept_a": a, "concept_b": b, "cooccurrences": count}
            for (a, b), count in sorted(co_counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))
        ]
        pd.DataFrame(co_rows).to_csv(COOCCURRENCE_CSV, index=False)
    else:
        pd.DataFrame(columns=["concept_a", "concept_b", "cooccurrences"]).to_csv(COOCCURRENCE_CSV, index=False)

    print(f"[build_concept_datasets] occurrences: {len(occurrences_df)} rows")
    print(f"[build_concept_datasets] summary concepts: {len(summary_df)}")


if __name__ == "__main__":
    main()
