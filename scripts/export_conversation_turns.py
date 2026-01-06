from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable


def load_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def normalise_timestamp(value: Any) -> str:
    if value in (None, "", "null"):
        return ""
    return str(value)


def export_chat(input_path: Path, output_path: Path) -> None:
    rows = []
    for item in load_jsonl(input_path):
        content = item.get("content") or ""
        if content and content.strip().startswith("{") and content.strip().endswith("}"):
            try:
                parsed = json.loads(content)
                content = json.dumps(parsed, ensure_ascii=False)
            except json.JSONDecodeError:
                pass
        rows.append(
            {
                "conversation_id": item.get("conversation_id", ""),
                "conversation_title": item.get("conversation_title", ""),
                "message_order": item.get("message_order", ""),
                "author_role": item.get("author_role", ""),
                "content": content.replace("\r\n", "\n"),
                "timestamp": normalise_timestamp(item.get("create_time")),
                "metadata_json": item.get("metadata_json", ""),
            }
        )
    write_csv(output_path, rows)


def export_perple(input_path: Path, output_path: Path) -> None:
    rows = []
    for item in load_jsonl(input_path):
        rows.append(
            {
                "file_name": item.get("file_name", ""),
                "title": item.get("title", ""),
                "date": item.get("date_iso", item.get("date_raw", "")),
                "tags": item.get("tags", ""),
                "word_count": item.get("word_count", ""),
                "content": item.get("content", "").replace("\r\n", "\n"),
            }
        )
    write_csv(output_path, rows)


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError("No rows to write")
    fieldnames = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert conversation JSONL to a turn-level CSV.")
    parser.add_argument("format", choices=["chat", "perple"], help="Export format")
    parser.add_argument("input", type=Path, help="Input JSONL path")
    parser.add_argument("output", type=Path, help="Output CSV path")
    args = parser.parse_args()

    if args.format == "chat":
        export_chat(args.input, args.output)
    else:
        export_perple(args.input, args.output)
    print(f"Wrote CSV to {args.output}")


if __name__ == "__main__":
    main()
