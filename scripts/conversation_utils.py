from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional


@dataclass
class MessageRecord:
    source: str
    conversation_id: str
    conversation_title: Optional[str]
    message_order: int
    message_id: str
    parent_id: Optional[str]
    author_role: str
    content: str
    create_time: Optional[str]
    update_time: Optional[str]
    status: Optional[str]
    metadata_json: Optional[str]


def _to_iso(value: object) -> Optional[str]:
    """Normalise timestamps (epoch, string) into ISO-8601."""
    if value in (None, "", "null"):
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=UTC).isoformat()
        except Exception:
            return None
    if isinstance(value, str):
        return value
    return str(value)


def _serialise_metadata(metadata: object) -> Optional[str]:
    if metadata in (None, {}, []):
        return None
    try:
        return json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
    except TypeError:
        # Unserialisable objects – best effort string conversion
        return json.dumps(str(metadata), ensure_ascii=False)


def _extract_text(content: object) -> str:
    """
    Convert OpenAI style message content (dict/list/str) into plain text.

    - `{"content_type": "text", "parts": [...]}` -> concatenated parts
    - list of blocks (each with `type`) -> join textual blocks, JSON dump others
    - fallback: `str(content)`
    """
    if content is None:
        return ""

    if isinstance(content, dict):
        ctype = content.get("content_type")
        if ctype == "text" and "parts" in content:
            text = "".join(part for part in content["parts"] if isinstance(part, str))
            return text.replace("\ufffd", "?")
        return json.dumps(content, ensure_ascii=False).replace("\ufffd", "?")

    if isinstance(content, list):
        fragments: List[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and "text" in block:
                    fragments.append(str(block["text"]))
                elif block.get("type") == "tool_call":
                    fragments.append(json.dumps(block, ensure_ascii=False))
                else:
                    fragments.append(json.dumps(block, ensure_ascii=False))
            elif isinstance(block, str):
                fragments.append(block)
        return "\n".join(fragments).replace("\ufffd", "?")

    return str(content).replace("\ufffd", "?")


def _clean_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return str(value).replace("\ufffd", "?")


# ---------- OpenAI / ChatGPT export helpers ----------


def _openai_iter_messages(mapping: Dict[str, dict], start_ids: Iterable[str]) -> Iterator[dict]:
    """Iterative depth-first traversal yielding nodes with messages."""
    stack: List[str] = list(reversed(list(start_ids)))
    seen: set[str] = set()
    while stack:
        node_id = stack.pop()
        if node_id in seen or node_id not in mapping:
            continue
        seen.add(node_id)
        node = mapping[node_id]
        message = node.get("message")
        if message:
            yield node
        children = node.get("children") or []
        for child in reversed(children):
            stack.append(child)


def flatten_openai_conversation(conversation: dict, source: str) -> List[MessageRecord]:
    """Flatten a single ChatGPT conversation export (mapping/tree structure)."""
    mapping: Dict[str, dict] = conversation.get("mapping") or {}
    if not mapping:
        return []

    root_children: List[str] = []
    for node_id, node in mapping.items():
        if node.get("parent") is None:
            root_children.extend(node.get("children") or [])

    records: List[MessageRecord] = []
    order = 1
    for child_id in root_children:
        for node in _openai_iter_messages(mapping, [child_id]):
            message = node.get("message") or {}
            role = message.get("author", {}).get("role") or ""
            # skip hidden/system context
            if role == "system":
                continue
            content = _extract_text(message.get("content"))
            if not content and role == "":
                continue
            records.append(
                MessageRecord(
                    source=source,
                    conversation_id=_clean_str(conversation.get("conversation_id") or conversation.get("id") or ""),
                    conversation_title=_clean_str(conversation.get("title")),
                    message_order=order,
                    message_id=_clean_str(message.get("id") or ""),
                    parent_id=_clean_str(node.get("parent")),
                    author_role=role,
                    content=content,
                    create_time=_clean_str(_to_iso(message.get("create_time"))),
                    update_time=_clean_str(_to_iso(message.get("update_time"))),
                    status=_clean_str(message.get("status")),
                    metadata_json=_clean_str(_serialise_metadata(message.get("metadata"))),
                )
            )
            order += 1
    return records


# ---------- Sena / MCP export helpers ----------


def flatten_sena_conversation(conversation: dict, source: str = "sena") -> List[MessageRecord]:
    """Flatten Sena MCP exports (list of chat_messages)."""
    messages = conversation.get("chat_messages") or []
    if not messages:
        return []

    convo_id = _clean_str(conversation.get("uuid") or conversation.get("id") or "")
    title = _clean_str(conversation.get("name"))
    records: List[MessageRecord] = []
    for idx, message in enumerate(messages, start=1):
        sender = str(message.get("sender") or "").lower()
        if sender in {"human", "user"}:
            role = "user"
        elif sender in {"assistant", "ai"}:
            role = "assistant"
        else:
            role = sender or "unknown"

        content_text = message.get("text") or ""
        if not content_text:
            content_text = _extract_text(message.get("content"))

        records.append(
            MessageRecord(
                source=source,
                conversation_id=convo_id,
                conversation_title=title,
                message_order=idx,
                message_id=_clean_str(message.get("uuid") or ""),
                parent_id=None,
                author_role=role,
                content=content_text.replace("\ufffd", "?"),
                create_time=_clean_str(_to_iso(message.get("created_at"))),
                update_time=_clean_str(_to_iso(message.get("updated_at"))),
                status=None,
                metadata_json=_clean_str(
                    _serialise_metadata(
                    {
                        "attachments": message.get("attachments"),
                        "files": message.get("files"),
                    }
                    )
                ),
            )
        )
    return records


def write_records(records: List[MessageRecord], output_dir: Path, stem: str) -> None:
    """Write flattened records to CSV and JSONL under output_dir."""
    if not records:
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{stem}.csv"
    jsonl_path = output_dir / f"{stem}.jsonl"

    import pandas as pd  # local import to avoid hard dependency for other usages

    df = pd.DataFrame([asdict(r) for r in records])
    df = df.applymap(lambda x: x.replace("\ufffd", "?") if isinstance(x, str) else x)
    df.to_csv(csv_path, index=False)

    with jsonl_path.open("w", encoding="utf-8", newline="\n") as fp:
        for record in records:
            payload = {k: (v.replace("\ufffd", "?") if isinstance(v, str) else v) for k, v in asdict(record).items()}
            fp.write(json.dumps(payload, ensure_ascii=False))
            fp.write("\n")
