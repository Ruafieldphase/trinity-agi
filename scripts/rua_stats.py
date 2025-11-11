#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compute RUA dataset statistics from JSONL and emit rua_statistics.json.
Inputs: JSONL with fields: conversation_id, conversation_title, create_time
Outputs: JSON matching structure used by the dashboard and README.

Usage:
  python scripts/rua_stats.py --input outputs/rua/rua_conversations_flat.jsonl \
                              --out outputs/rua/rua_statistics.json
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
import re


def parse_time(ts: str):
    # Try multiple formats; fall back gracefully
    fmts = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]
    for f in fmts:
        try:
            return datetime.strptime(ts, f)
        except Exception:
            pass
    # As a last resort, try fromisoformat
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


STOPWORDS = set(
    [
        "의", "를", "은", "는", "이", "가", "에", "과", "와", "로", "에서", "및", "또는",
        "the", "and", "for", "with", "of", "to", "in", "on", "a", "an",
    ]
)


def tokenize(text: str):
    # Split on non-letters/digits; keep Korean/Latin/Numbers
    tokens = re.split(r"[^\w가-힣]+", text or "")
    return [t for t in tokens if t and len(t) >= 2 and t.lower() not in STOPWORDS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="outputs/rua/rua_conversations_flat.jsonl")
    ap.add_argument("--out", default="outputs/rua/rua_statistics.json")
    args = ap.parse_args()

    path = args.input
    try:
        lines = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    lines.append(obj)
                except Exception:
                    # Skip malformed lines gracefully
                    continue
    except FileNotFoundError:
        print(f"Input JSONL not found: {path}", file=sys.stderr)
        sys.exit(2)

    total = len(lines)
    conv_turns = Counter()
    conv_titles = {}
    hours = Counter()
    keywords = Counter()
    earliest = None
    latest = None

    for obj in lines:
        cid = obj.get("conversation_id")
        title = obj.get("conversation_title") or ""
        conv_turns[cid] += 1
        conv_titles[cid] = title

        ts = obj.get("create_time")
        dt = parse_time(ts) if isinstance(ts, str) else None
        if dt:
            if earliest is None or dt < earliest:
                earliest = dt
            if latest is None or dt > latest:
                latest = dt
            hours[dt.hour] += 1

        # rudimentary keyword extraction from title
        for tok in tokenize(title):
            keywords[tok] += 1

    unique_conversations = len(conv_turns)
    turn_values = list(conv_turns.values())
    avg_turns = round(sum(turn_values) / unique_conversations, 1) if unique_conversations else 0.0
    max_turns = max(turn_values) if turn_values else 0
    min_turns = min(turn_values) if turn_values else 0

    duration_days = 0.0
    earliest_s = latest_s = None
    if earliest and latest:
        duration_days = round((latest - earliest).total_seconds() / 86400.0, 1)
        earliest_s = earliest.strftime("%Y-%m-%d %H:%M:%S")
        latest_s = latest.strftime("%Y-%m-%d %H:%M:%S")

    hourly_distribution = [
        {"hour": h, "count": int(hours.get(h, 0))} for h in range(24)
    ]

    top_conversations = [
        {
            "conversation_id": cid or "",
            "title": conv_titles.get(cid, ""),
            "turn_count": count,
        }
        for cid, count in conv_turns.most_common(10)
    ]

    top_keywords = [
        {"keyword": k, "count": int(c)} for k, c in keywords.most_common(10)
    ]

    out = {
        "metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analyst": "Binoche",
            "data_source": path.split("/")[-1].split("\\")[-1],
        },
        "statistics": {
            "total_messages": total,
            "unique_conversations": unique_conversations,
            "average_turns": avg_turns,
            "max_turns": max_turns,
            "min_turns": min_turns,
            "time_range": {
                "earliest": earliest_s,
                "latest": latest_s,
                "duration_days": duration_days,
            },
        },
        "hourly_distribution": hourly_distribution,
        "top_conversations": top_conversations,
        "top_keywords": top_keywords,
    }

    # Ensure output directory exists
    import os

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=4)

    print(args.out)


if __name__ == "__main__":
    main()
