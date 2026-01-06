from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List


def load_session(path: Path) -> List[Dict]:
    entries: List[Dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def summarise_session(session_id: str, entries: Iterable[Dict]) -> Dict[str, any]:
    persona_counts = Counter()
    tag_counts = Counter()
    for entry in entries:
        persona = entry.get("agent", {}).get("persona_id", "unknown")
        persona_counts[persona] += 1
        tags = entry.get("metadata", {}).get("tags", [])
        tag_counts.update(tags)
    return {
        "session_id": session_id,
        "total_memories": sum(persona_counts.values()),
        "persona_counts": dict(persona_counts),
        "top_tags": tag_counts.most_common(5),
    }


def inspect_memory(base_dir: Path) -> None:
    sessions_dir = base_dir / "sessions"
    if not sessions_dir.exists():
        print(f"No sessions directory found at {sessions_dir}")
        return

    summaries = []
    for path in sorted(sessions_dir.glob("*.jsonl")):
        session_id = path.stem
        entries = load_session(path)
        summaries.append(summarise_session(session_id, entries))

    print("=== Memory Store Overview ===")
    print(f"Sessions: {len(summaries)}")
    total_memories = sum(s["total_memories"] for s in summaries)
    print(f"Total memories: {total_memories}")
    for summary in summaries[-5:]:
        print(f"- Session {summary['session_id']}: {summary['total_memories']} memories")
        print(f"  Personas: {summary['persona_counts']}")
        print(f"  Top tags: {summary['top_tags']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect stored memory coordinates.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("outputs/memory"),
        help="Base directory containing memory sessions/",
    )
    args = parser.parse_args()
    inspect_memory(args.base_dir)


if __name__ == "__main__":
    main()
