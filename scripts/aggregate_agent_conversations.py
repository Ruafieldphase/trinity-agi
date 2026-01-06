#!/usr/bin/env python3
"""
Aggregate multi-agent conversation logs (JSONL) into a machine-readable summary.

The script scans the original conversation archive (default:
`original_data/ai_binoche_conversation_origin`) and produces a consolidated
summary with per-file and per-agent metadata.  Results are written to
`outputs/agent_conversation_summary.json`.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# Candidate base directories searched in order when --base-dir is omitted.
DEFAULT_BASE_DIR_CANDIDATES = [
    Path("original_data/ai_binoche_conversation_origin"),
    Path("../original_data/ai_binoche_conversation_origin"),
]
SUMMARY_PATH = Path("outputs/agent_conversation_summary.json")


def iter_jsonl(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    """Yield (line_no, payload) tuples from a JSONL file."""
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                yield line_no, json.loads(stripped)
            except json.JSONDecodeError:
                yield line_no, {"__parse_error__": stripped}


def summarise_file(path: Path) -> Dict[str, Any]:
    """Collect metadata for a single JSONL conversation log."""
    total_entries = 0
    parse_errors = 0
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    user_messages = 0
    assistant_messages = 0
    tool_uses = 0

    for _, payload in iter_jsonl(path):
        if "__parse_error__" in payload:
            parse_errors += 1
            continue

        total_entries += 1
        agent_id = payload.get("agentId") or agent_id
        session_id = payload.get("sessionId") or session_id

        timestamp = payload.get("timestamp")
        if timestamp:
            if first_timestamp is None:
                first_timestamp = timestamp
            last_timestamp = timestamp

        message = payload.get("message", {})
        role = message.get("role")
        if role == "user":
            user_messages += 1
        elif role == "assistant":
            assistant_messages += 1

        content = message.get("content")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "tool_use":
                    tool_uses += 1

    return {
        "path": str(path.resolve()),
        "relative_path": str(path),
        "agent_id": agent_id,
        "session_id": session_id,
        "entries": total_entries,
        "user_messages": user_messages,
        "assistant_messages": assistant_messages,
        "tool_uses": tool_uses,
        "parse_errors": parse_errors,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
    }


def aggregate(base_dir: Path) -> Dict[str, Any]:
    """Aggregate summaries for every JSONL file under base_dir."""
    jsonl_files = sorted(base_dir.rglob("*.jsonl"))
    file_summaries: List[Dict[str, Any]] = []
    agent_totals: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"files": 0, "entries": 0, "tool_uses": 0}
    )
    total_parse_errors = 0

    for file_path in jsonl_files:
        summary = summarise_file(file_path)
        file_summaries.append(summary)

        agent_id = summary.get("agent_id") or "unknown"
        totals = agent_totals[agent_id]
        totals["files"] += 1
        totals["entries"] += summary.get("entries", 0)
        totals["tool_uses"] += summary.get("tool_uses", 0)
        total_parse_errors += summary.get("parse_errors", 0)

    agents = [
        {
            "agent_id": agent_id,
            "files": data["files"],
            "entries": data["entries"],
            "tool_uses": data["tool_uses"],
        }
        for agent_id, data in sorted(agent_totals.items())
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_directory": str(base_dir.resolve()),
        "file_count": len(file_summaries),
        "total_parse_errors": total_parse_errors,
        "agents": agents,
        "files": file_summaries,
    }


def resolve_default_base_dir() -> Path:
    """Return the first existing base directory from the candidate list."""
    for candidate in DEFAULT_BASE_DIR_CANDIDATES:
        if candidate.exists():
            return candidate
    return DEFAULT_BASE_DIR_CANDIDATES[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate agent conversation JSONL logs into a summary."
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help=(
            "루트 대화 로그 디렉터리 (기본값: original_data/ai_binoche_conversation_origin)"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=SUMMARY_PATH,
        help="요약 결과를 저장할 경로 (기본값: outputs/agent_conversation_summary.json)",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=None,
        help="요약 결과 요약본을 Markdown 파일로 저장",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Markdown 표에 포함할 상위 에이전트 수 (기본값: 10)",
    )
    return parser.parse_args()


def render_markdown(summary: Dict[str, Any], top_n: int) -> str:
    """Generate a Markdown digest of the aggregated summary."""
    agents = sorted(summary["agents"], key=lambda a: a["entries"], reverse=True)
    total_entries = sum(agent["entries"] for agent in agents)
    total_tool_uses = sum(agent["tool_uses"] for agent in agents)

    lines = [
        "# Agent Conversation Summary",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Source directory: `{summary['base_directory']}`",
        f"- Total files: {summary['file_count']}",
        f"- Total entries: {total_entries}",
        f"- Total tool calls: {total_tool_uses}",
        f"- Parse errors: {summary['total_parse_errors']}",
        "",
        f"## Top {min(top_n, len(agents))} Agents by Entries",
        "",
        "| Agent ID | Files | Entries | Tool Uses |",
        "|----------|-------|---------|-----------|",
    ]

    for agent in agents[:top_n]:
        lines.append(
            f"| {agent['agent_id']} | {agent['files']} | {agent['entries']} | {agent['tool_uses']} |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    base_dir: Path
    if args.base_dir is not None:
        base_dir = args.base_dir
    else:
        base_dir = resolve_default_base_dir()

    if not base_dir.exists():
        raise SystemExit(f"Base directory not found: {base_dir}")

    summary = aggregate(base_dir)

    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    print(f"✅ Summary written to {output_path.resolve()}")
    print(f"   Files processed: {summary['file_count']}")
    print(f"   Total parse errors: {summary['total_parse_errors']}")

    if args.markdown is not None:
        markdown_path: Path = args.markdown
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown = render_markdown(summary, args.top_n)
        with markdown_path.open("w", encoding="utf-8") as handle:
            handle.write(markdown)
        print(f"   Markdown digest written to {markdown_path.resolve()}")


if __name__ == "__main__":
    main()
