"""Command-line helper for Dialectical Pulse anomaly detection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

# Ensure root modules are importable when executed as script
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "analysis"))

from analysis.dialectical_pulse_utils import attach_somatic_labels, load_turn_csv

PULSE_WINDOW = 6


def classify_dialectic(row: pd.Series) -> str | None:
    text = str(row.get("content", ""))
    role = row.get("author_role", "")
    if not text:
        return None
    thesis_keywords = ["?", "왜", "어떻게", "무엇", "가능할까"]
    antithesis_keywords = ["하지만", "반대로", "그러나", "다만", "단지"]
    synthesis_keywords = ["정리하면", "결국", "즉", "따라서", "요약하면"]
    if role == "user":
        if any(k in text for k in thesis_keywords):
            return "thesis"
        return "thesis"
    if any(k in text for k in synthesis_keywords):
        return "synthesis"
    if any(k in text for k in antithesis_keywords):
        return "antithesis"
    if role == "assistant" and "###" in text:
        return "synthesis"
    return None


def detect_pulse_sequences(df: pd.DataFrame, window: int = PULSE_WINDOW) -> pd.DataFrame:
    results = []
    for conv_id, group in df.groupby("conversation_id"):
        tags = group["dialectic_tag"].reset_index(drop=True)
        for start in range(len(group)):
            end = min(start + window, len(group))
            seq = list(tags.iloc[start:end])
            if {"thesis", "antithesis", "synthesis"}.issubset(set(seq)):
                results.append(
                    {
                        "conversation_id": conv_id,
                        "start": start,
                        "end": end,
                        "sequence": seq,
                    }
                )
    return pd.DataFrame(results)


def find_missing_synthesis(df: pd.DataFrame, window: int = PULSE_WINDOW) -> pd.DataFrame:
    anomalies = []
    for conv_id, group in df.groupby("conversation_id"):
        tags = group["dialectic_tag"].reset_index(drop=True)
        timestamps = group["timestamp"].reset_index(drop=True)
        phases = group.get("somatic_phase")
        for start in range(len(group)):
            end = min(start + window, len(group))
            seq = list(tags.iloc[start:end])
            if "thesis" in seq and "antithesis" in seq and "synthesis" not in seq:
                anomalies.append(
                    {
                        "conversation_id": conv_id,
                        "start": start,
                        "end": end,
                        "sequence": seq,
                        "timestamp_start": timestamps.iloc[start],
                        "timestamp_end": timestamps.iloc[end - 1],
                        "somatic_phase": phases.iloc[start] if phases is not None else None,
                    }
                )
    return pd.DataFrame(anomalies)


def suggest_action(row: pd.Series) -> str:
    phase = row.get("somatic_phase")
    if phase == "Recovery":
        return "Suggest: breathing/meditation card, restore intrinsic rhythm."
    if phase == "Somatic Integration":
        return "Suggest: log multi-sensory feelings, link to affect journaling."
    if phase == "Temporal Reframing":
        return "Suggest: non-linear time routine, provide meta-summary."
    if phase == "Social Resonance":
        return "Suggest: review relational flow, persona switch or rest alert."
    return "Suggest: standard dialectical recap and next-step prompt."


def run_pipeline(turn_csv: Path, somatic_json: Path) -> pd.DataFrame:
    df = load_turn_csv(turn_csv)
    if "dialectic_tag" not in df.columns:
        df["dialectic_tag"] = df.apply(classify_dialectic, axis=1)
    df = attach_somatic_labels(df, somatic_json)
    anomalies = find_missing_synthesis(df)
    anomalies["action_suggestion"] = anomalies.apply(suggest_action, axis=1)
    return anomalies


if __name__ == "__main__":
    base = ROOT_DIR
    turn_path = base / "outputs" / "notebooklm" / "Core_turns.csv"
    somatic_path = base / "outputs" / "somatic_cycles.json"
    result = run_pipeline(turn_path, somatic_path)
    print(result.head())
