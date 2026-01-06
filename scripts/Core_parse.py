#!/usr/bin/env python3
"""Flatten ChatGPT Core conversations.json into JSONL/CSV rows.

The Core export stores each conversation as a mapping tree. This script walks
the nodes in deterministic order and emits one record per message, capturing
metadata required by downstream analytics (stats, dashboards, RAG prep).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional


MessageNode = Dict[str, object]


def _format_ts(value: Optional[object]) -> Optional[str]:
    """Return ISO8601 string (UTC) when value is a numeric epoch."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    if isinstance(value, str) and value:
        return value
    return None


def _serialize_metadata(meta: Optional[dict]) -> str:
    return json.dumps(meta or {}, ensure_ascii=False, separators=(",", ":"))


def _stringify_content(content: Optional[object]) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if not isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)

    ctype = content.get("content_type")
    parts = content.get("parts")
    if ctype == "text" and isinstance(parts, list):
        rendered: List[str] = []
        for part in parts:
            if isinstance(part, str):
                rendered.append(part)
            else:
                rendered.append(json.dumps(part, ensure_ascii=False))
        return "\n\n".join(rendered)

    # Preserve rich structures (e.g., user_editable_context, multimodal_text) as JSON
    return json.dumps(content, ensure_ascii=False)


def _walk_nodes(mapping: Dict[str, dict]) -> Iterator[dict]:
    """Yield node dicts in deterministic order (pre-order traversal)."""

    visited = set()

    roots: List[str] = []
    if "client-created-root" in mapping:
        roots.append("client-created-root")
    else:
        for node_id, node in mapping.items():
            if node.get("parent") is None:
                roots.append(node_id)

    if not roots:
        roots = list(mapping.keys())

    for root in roots:
        stack: List[str] = [root]
        while stack:
            node_id = stack.pop()
            if node_id in visited:
                continue
            node = mapping.get(node_id)
            if not node:
                continue
            visited.add(node_id)
            yield node

            children = node.get("children", []) or []
            if isinstance(children, list) and children:
                for child_id in reversed(children):
                    if isinstance(child_id, str):
                        stack.append(child_id)


def flatten_conversation(conv: dict) -> Iterable[dict]:
    mapping = conv.get("mapping", {})
    if not isinstance(mapping, dict):
        return []

    convo_id = conv.get("conversation_id") or conv.get("id") or ""
    title = conv.get("title") or ""

    records = []
    order = 1
    for node in _walk_nodes(mapping):
        message = node.get("message")
        if not isinstance(message, dict):
            continue

        role = (message.get("author") or {}).get("role")
        if role not in {"user", "assistant", "tool"}:
            continue

        record = {
            "source": "Core",
            "conversation_id": convo_id,
            "conversation_title": title,
            "message_order": order,
            "message_id": message.get("id") or "",
            "parent_id": node.get("parent"),
            "author_role": role,
            "content": _stringify_content(message.get("content")),
            "create_time": _format_ts(message.get("create_time")),
            "update_time": _format_ts(message.get("update_time")),
            "status": message.get("status"),
            "metadata_json": _serialize_metadata(message.get("metadata")),
        }
        records.append(record)
        order += 1

    return records


def load_conversations(path: Path) -> List[dict]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Input not found: {path}") from None
    if not isinstance(raw, list):
        raise SystemExit("Unexpected conversations.json format (expected list)")
    return raw


def write_jsonl(records: Iterable[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False))
            fh.write("\n")


def write_csv(records: Iterable[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source",
        "conversation_id",
        "conversation_title",
        "message_order",
        "author_role",
        "content",
        "create_time",
    ]

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for rec in records:
            row = {k: rec.get(k, "") for k in fields}
            writer.writerow(row)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="ai_binoche_conversation_origin/Core/origin/conversations.json",
        help="Path to conversations.json export",
    )
    parser.add_argument(
        "--out-jsonl",
        default="outputs/Core/core_conversations_flat.jsonl",
        help="Output JSONL file",
    )
    parser.add_argument(
        "--out-csv",
        help="Optional CSV output mirroring the JSONL",
    )

    args = parser.parse_args(argv)
    input_path = Path(args.input)
    out_jsonl = Path(args.out_jsonl)
    out_csv = Path(args.out_csv) if args.out_csv else None

    conversations = load_conversations(input_path)

    all_records: List[dict] = []
    for conv in conversations:
        all_records.extend(flatten_conversation(conv))

    write_jsonl(all_records, out_jsonl)
    if out_csv:
        write_csv(all_records, out_csv)

    print(f"Wrote {len(all_records)} records to {out_jsonl}")
    if out_csv:
        print(f"CSV mirror: {out_csv}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
