#!/usr/bin/env python3
"""Flatten Sena MCP exports (chat_messages) to CSV/JSONL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from conversation_utils import flatten_sena_conversation, write_records


def load_conversations(path: Path) -> list[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse {path}: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Flatten Sena conversations.json export.")
    parser.add_argument("--input", type=Path, required=True, help="Path to Sena conversations.json")
    parser.add_argument(
        "--source",
        type=str,
        default="sena",
        help="Source label (default: sena)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (defaults to outputs/<source>)",
    )
    args = parser.parse_args()

    conversations = load_conversations(args.input)
    if not conversations:
        raise SystemExit(f"No conversations found in {args.input}")

    source = args.source
    output_dir = args.output_dir or Path("outputs") / source
    stem = f"{source}_conversations_flat"

    records = []
    for conversation in conversations:
        records.extend(flatten_sena_conversation(conversation, source=source))

    if not records:
        raise SystemExit("No chat messages found in input file.")

    write_records(records, output_dir, stem)
    print(f"[flatten_sena_export] wrote {len(records)} rows to {output_dir}")


if __name__ == "__main__":
    main()

