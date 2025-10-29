import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class MessageRecord:
    conversation_id: str
    title: Optional[str]
    message_order: int
    message_id: str
    parent_id: Optional[str]
    author_role: str
    content: str
    create_time: Optional[str]
    status: Optional[str]


def extract_text(content) -> str:
    """Convert OpenAI export content payloads into a single string."""
    if content is None:
        return ""

    # Legacy dict structure with content_type / parts
    if isinstance(content, dict):
        content_type = content.get("content_type")
        if content_type == "text" and "parts" in content:
            return "".join(part for part in content["parts"] if isinstance(part, str))
        # For context blocks or other structured payloads keep the JSON
        return json.dumps(content, ensure_ascii=False)

    # Newer list-of-parts structure
    if isinstance(content, list):
        fragments: List[str] = []
        for part in content:
            if isinstance(part, dict):
                part_type = part.get("type")
                if part_type == "text":
                    fragments.append(part.get("text", ""))
                else:
                    fragments.append(json.dumps(part, ensure_ascii=False))
            elif isinstance(part, str):
                fragments.append(part)
        return "\n".join(fragments)

    return str(content)


def format_timestamp(value) -> Optional[str]:
    """Normalise timestamps to ISO-8601 strings."""
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    if isinstance(value, str):
        return value
    return str(value)


def traverse_nodes(mapping: Dict[str, dict], start_id: str) -> Iterable[dict]:
    """Depth-first (iterative) traversal of the conversation tree starting at start_id."""
    stack: List[str] = [start_id]
    while stack:
        node_id = stack.pop()
        if node_id not in mapping:
            continue
        node = mapping[node_id]
        message = node.get("message")
        if message:
            yield node
        children = node.get("children", [])
        if children:
            for child_id in reversed(children):
                stack.append(child_id)


def flatten_conversation(conversation: dict) -> Iterable[MessageRecord]:
    if "mapping" in conversation:
        mapping: Dict[str, dict] = conversation["mapping"]
        root_ids = [node_id for node_id, node in mapping.items() if node.get("parent") is None]

        message_order = 1
        for root_id in root_ids:
            for child_id in mapping.get(root_id, {}).get("children", []):
                for node in traverse_nodes(mapping, child_id):
                    message = node["message"]
                    role = message.get("author", {}).get("role")
                    if role == "system":
                        continue  # 기존 플랫 파일과 동일하게 시스템 메시지는 제외

                    yield MessageRecord(
                        conversation_id=conversation.get("conversation_id") or conversation.get("id"),
                        title=conversation.get("title"),
                        message_order=message_order,
                        message_id=message.get("id"),
                        parent_id=node.get("parent"),
                        author_role=role or "",
                        content=extract_text(message.get("content")),
                        create_time=format_timestamp(message.get("create_time")),
                        status=message.get("status"),
                    )
                    message_order += 1
        return

    if "chat_messages" in conversation:
        messages: List[dict] = conversation.get("chat_messages") or []
        for idx, message in enumerate(messages, start=1):
            text = message.get("text")
            if not text:
                text = extract_text(message.get("content"))

            yield MessageRecord(
                conversation_id=conversation.get("uuid") or conversation.get("id"),
                title=conversation.get("name"),
                message_order=idx,
                message_id=message.get("uuid"),
                parent_id=None,
                author_role=message.get("sender") or "",
                content=text or "",
                create_time=format_timestamp(message.get("created_at")),
                status=None,
            )


def rebuild_agent(agent_dir: Path, output_dir: Path) -> None:
    conversations_path = agent_dir / "conversations.json"
    if not conversations_path.exists():
        return

    with conversations_path.open("r", encoding="utf-8") as fp:
        conversations = json.load(fp)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{agent_dir.name}_conversations_flat.jsonl"
    backup_path = output_path.with_suffix(".jsonl.bak")
    if output_path.exists():
        output_path.replace(backup_path)

    with output_path.open("w", encoding="utf-8", newline="\n") as out_fp:
        for conversation in conversations:
            for record in flatten_conversation(conversation):
                out_fp.write(json.dumps(record.__dict__, ensure_ascii=False))
                out_fp.write("\n")


def main():
    root = Path("ai_binoche_conversation_origin")
    output_root = Path("outputs")

    for agent_dir in sorted(root.iterdir()):
        if not agent_dir.is_dir():
            continue
        conversations_path = agent_dir / "conversations.json"
        if not conversations_path.exists():
            continue

        target_dir = output_root / agent_dir.name
        rebuild_agent(agent_dir, target_dir)
        print(f"Rebuilt JSONL for {agent_dir.name}")


if __name__ == "__main__":
    main()
