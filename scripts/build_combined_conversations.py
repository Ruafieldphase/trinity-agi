#!/usr/bin/env python3
"""Combine flattened conversation datasets (Rua/Sena/others) and build summary outputs."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_SOURCES = ["rua", "sena", "elro", "lumen"]
OUTPUT_DIR = Path("outputs")
COMBINED_CSV = OUTPUT_DIR / "ai_conversations_combined.csv"
SUMMARY_TXT = OUTPUT_DIR / "ai_conversations_summary.txt"
WEEKDAY_SVG = OUTPUT_DIR / "ai_conversations_weekday.svg"


def find_source_paths(sources: Iterable[str]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for source in sources:
        csv_path = OUTPUT_DIR / source / f"{source}_conversations_flat.csv"
        if csv_path.exists():
            paths[source] = csv_path
    return paths


def load_and_prepare(source: str, path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["source"] = source
    if "content" not in df.columns:
        df["content"] = ""
    # unify title column
    if "conversation_title" not in df.columns and "title" in df.columns:
        df["conversation_title"] = df["title"]
    # parse timestamps
    timestamp_cols = [col for col in ("create_time", "update_time") if col in df.columns]
    df["timestamp"] = pd.NaT
    for col in timestamp_cols:
        parsed = pd.to_datetime(df[col], errors="coerce", utc=True)
        df["timestamp"] = df["timestamp"].fillna(parsed)
    if df["timestamp"].notna().any():
        df["timestamp"] = df["timestamp"].dt.tz_convert(None)
        df["date"] = df["timestamp"].dt.date
        df["weekday"] = df["timestamp"].dt.day_name()
        df["month"] = df["timestamp"].dt.to_period("M").astype(str)
        df["year"] = df["timestamp"].dt.year
    else:
        df["date"] = pd.NaT
        df["weekday"] = None
        df["month"] = None
        df["year"] = None
    df["content_length"] = df["content"].fillna("").astype(str).str.len()
    return df


def write_summary(df: pd.DataFrame) -> None:
    lines: list[str] = []
    for source, subset in df.groupby("source"):
        messages = len(subset)
        conversations = subset["conversation_id"].nunique() if "conversation_id" in subset.columns else 0
        lines.append(f"=== Source: {source} ===")
        lines.append(f"Messages: {messages}")
        lines.append(f"Unique conversations: {conversations}")
        if subset["timestamp"].notna().any():
            ts = subset.dropna(subset=["timestamp"])["timestamp"]
            lines.append(f"First timestamp: {ts.min()}")
            lines.append(f"Last timestamp: {ts.max()}")
            weekday_counts = (
                subset.dropna(subset=["weekday"])
                .groupby("weekday")
                .size()
                .reindex(_weekday_order(), fill_value=0)
            )
            counts_str = ", ".join(f"{day}={count}" for day, count in weekday_counts.items())
            lines.append(f"Weekday counts: {counts_str}")
        avg_len = subset["content_length"].mean()
        lines.append(f"Avg message length: {avg_len:.1f}")
        lines.append("")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_TXT.write_text("\n".join(lines), encoding="utf-8")


def _weekday_order() -> list[str]:
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def render_weekday_chart(df: pd.DataFrame) -> None:
    plt.style.use("ggplot")
    subset = df.dropna(subset=["weekday"])
    if subset.empty:
        WEEKDAY_SVG.unlink(missing_ok=True)
        return

    pivot = (
        subset.groupby(["weekday", "source"])
        .size()
        .unstack(fill_value=0)
        .reindex(_weekday_order(), fill_value=0)
    )

    ax = pivot.plot(kind="bar", stacked=False, figsize=(8, 4.5))
    ax.set_title("Messages by Weekday and Source")
    ax.set_xlabel("Weekday")
    ax.set_ylabel("Messages")
    ax.legend(title="Source")
    for container in ax.containers:
        ax.bar_label(container, label_type="edge", fontsize=8)

    plt.tight_layout()
    plt.savefig(WEEKDAY_SVG, dpi=300)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Combine flattened conversation datasets.")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=DEFAULT_SOURCES,
        help="List of sources to include (default: %(default)s)",
    )
    args = parser.parse_args()

    path_map = find_source_paths(args.sources)
    if not path_map:
        raise SystemExit("No source CSV files found. Run flatten scripts first.")

    frames = [load_and_prepare(source, path) for source, path in path_map.items()]
    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined.sort_values(["timestamp", "source", "message_order"], inplace=True, na_position="last")
    COMBINED_CSV.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(COMBINED_CSV, index=False)

    write_summary(combined)
    render_weekday_chart(combined)
    print(f"[build_combined_conversations] wrote {len(combined)} rows to {COMBINED_CSV}")
    print(f"Summary: {SUMMARY_TXT}")
    print(f"Weekday chart: {WEEKDAY_SVG}")


if __name__ == "__main__":
    main()

