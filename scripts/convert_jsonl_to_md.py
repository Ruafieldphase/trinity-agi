"""
Utility helpers to convert conversation JSON/JSONL exports into Markdown.

Usage examples (run from repository root):
    python scripts/convert_jsonl_to_md.py perple \
        outputs/perple/perple_conversations_flat.jsonl
    python scripts/convert_jsonl_to_md.py chat \
        outputs/elro/elro_conversations_flat.jsonl
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Dict, Any


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def normalise_datetime(value: Any) -> str | None:
    if value in (None, "", "null"):
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value).isoformat()
        except (ValueError, OSError):
            return str(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
        except ValueError:
            return value
    return str(value)


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Perple export (one record per document)
# ---------------------------------------------------------------------------

def convert_perple(path: Path) -> str:
    sections: List[str] = ["# Perple Conversations\n"]
    for item in load_jsonl(path):
        title = item.get("title") or item.get("file_name") or "Untitled"
        date_iso = item.get("date_iso") or normalise_datetime(item.get("date"))
        meta_lines = [
            f"- **File**: `{item.get('file_name', '')}`",
            f"- **Relative Path**: `{item.get('relative_path', '')}`",
            f"- **Date**: {date_iso or 'N/A'}",
            f"- **URL**: {item.get('url', 'N/A')}",
            f"- **Tags**: {item.get('tags', '')}",
            f"- **UUID**: `{item.get('uuid', '')}`",
            f"- **Model/Mode**: {item.get('model', '')} / {item.get('mode', '')}",
            f"- **Word Count**: {item.get('word_count', '')}",
        ]
        sections.append(f"## {title}\n")
        sections.extend(meta_lines)
        sections.append("\n")
        content = item.get("content", "")
        sections.append(content.strip() + "\n\n")
    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Chat export (Rua, Sena, Lumen, Elo, etc.)
# ---------------------------------------------------------------------------

@dataclass
class Message:
    order: int
    role: str
    content: str
    create_time: str | None
    metadata: Dict[str, Any]


def convert_chat(path: Path, source_name: str) -> str:
    conversations: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"title": None, "messages": []}
    )

    for item in load_jsonl(path):
        conv_id = item.get("conversation_id") or "unknown"
        conv = conversations[conv_id]
        conv["title"] = item.get("conversation_title") or conv["title"] or "Untitled"
        content = item.get("content") or ""

        # Some exports double-encode JSON payloads (e.g., system messages).
        if content.strip().startswith("{") and content.strip().endswith("}"):
            try:
                parsed = json.loads(content)
                content = json.dumps(parsed, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                # keep original
                pass

        conv["messages"].append(
            Message(
                order=int(item.get("message_order") or 0),
                role=item.get("author_role", "unknown"),
                content=content.replace("\r\n", "\n"),
                create_time=normalise_datetime(item.get("create_time")),
                metadata={
                    k: v
                    for k, v in item.items()
                    if k
                    not in {
                        "conversation_id",
                        "conversation_title",
                        "message_order",
                        "author_role",
                        "content",
                    }
                },
            )
        )

    lines: List[str] = [f"# {source_name} Conversations\n"]

    for conv_id, payload in sorted(conversations.items(), key=lambda x: x[0]):
        title = payload["title"] or "Untitled"
        messages: List[Message] = sorted(
            payload["messages"], key=lambda m: (m.order, m.create_time or "")
        )
        lines.append(f"## {title}\n")
        lines.append(f"- **Conversation ID**: `{conv_id}`")
        lines.append(f"- **Message Count**: {len(messages)}\n")

        for msg in messages:
            lines.append(f"### Message {msg.order} — {msg.role}\n")
            if msg.create_time:
                lines.append(f"- Timestamp: {msg.create_time}")
            if msg.metadata:
                lines.append(f"- Metadata: `{json.dumps(msg.metadata, ensure_ascii=False)}`")
            lines.append("\n")
            if msg.content:
                lines.append(msg.content.strip() + "\n")
            else:
                lines.append("_(no content)_\n")

        lines.append("\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Convert conversation JSON/JSONL to Markdown.")
    parser.add_argument(
        "format",
        choices=["perple", "chat"],
        help="Export format type (perple = document-level, chat = message-level).",
    )
    parser.add_argument("input_path", type=Path, help="Path to JSON or JSONL file.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Destination Markdown path (default: same as input with .md suffix).",
    )
    args = parser.parse_args()

    if args.format == "perple":
        content = convert_perple(args.input_path)
    else:
        source_name = args.input_path.stem.split("_")[0].title()
        content = convert_chat(args.input_path, source_name=source_name)

    output_path = args.output or args.input_path.with_suffix(".md")
    write_markdown(output_path, content)
    print(f"Wrote Markdown to {output_path}")


if __name__ == "__main__":
    main()
