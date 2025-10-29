#!/usr/bin/env python3
"""Flatten ChatGPT/OpenAI conversation exports (conversations.json) to CSV/JSONL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from conversation_utils import MessageRecord, flatten_openai_conversation, write_records


def load_conversations(path: Path) -> list[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse {path}: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Flatten OpenAI conversations.json export.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to conversations.json",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Label for the source (defaults to parent directory name).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (defaults to outputs/<source>).",
    )
    args = parser.parse_args()

    conversations = load_conversations(args.input)
    if not conversations:
        raise SystemExit(f"No conversations found in {args.input}")

    source = args.source or args.input.parent.name
    output_dir = args.output_dir or Path("outputs") / source
    stem = f"{source}_conversations_flat"

    all_records: list[MessageRecord] = []
    for conversation in conversations:
        records = flatten_openai_conversation(conversation, source=source)
        all_records.extend(records)

    if not all_records:
        raise SystemExit("No messages found after flattening (check source data).")

    write_records(all_records, output_dir, stem)
    print(f"[flatten_chatgpt_export] wrote {len(all_records)} rows to {output_dir}")


if __name__ == "__main__":
    main()

