from __future__ import annotations

import json
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .schema import MemoryCoordinate, now_utc


@dataclass
class MemoryStoreConfig:
    base_path: Path
    max_sessions: int = 10
    max_memories_per_session: int = 500
    max_total_size_mb: int = 100
    archive_after_days: int = 30
    delete_after_days: int = 180


class MemoryStore:
    def __init__(self, config: MemoryStoreConfig) -> None:
        self.config = config
        self.config.base_path.mkdir(parents=True, exist_ok=True)
        self.sessions_path = self.config.base_path / "sessions"
        self.sessions_path.mkdir(exist_ok=True)
        self.index_path = self.config.base_path / "index.json"
        self._cache: Dict[str, List[MemoryCoordinate]] = {}

    # ------------------------------------------------------------------ add
    def add(self, memory: MemoryCoordinate) -> None:
        session_id = memory.time.get("session_id", "unknown")
        session_path = self.sessions_path / f"{session_id}.jsonl"
        session_path.parent.mkdir(parents=True, exist_ok=True)
        with session_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(memory.to_dict(), ensure_ascii=False) + "\n")
        self._cache.setdefault(session_id, []).append(memory)
        self._enforce_limits()

    # ---------------------------------------------------------------- search
    def search(
        self,
        query: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        persona_id: Optional[str] = None,
        domain: Optional[str] = None,
        min_importance: float = 0.0,
        tags: Optional[List[str]] = None,
        bqi_filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[MemoryCoordinate]:
        matches: List[MemoryCoordinate] = []
        for memory in self._iter_all():
            if persona_id and memory.agent.get("persona_id") != persona_id:
                continue
            if domain and memory.space.get("domain") != domain:
                continue
            if memory.metadata.get("importance", 0.0) < min_importance:
                continue
            if tags and not set(tags).issubset(set(memory.metadata.get("tags", []))):
                continue
            if not self._match_time(memory, time_range):
                continue
            if query and not self._contains_query(memory, query):
                continue
            if bqi_filters and not self._match_bqi(memory, bqi_filters):
                continue
            matches.append(memory)
            if len(matches) >= limit:
                break
        return matches

    def get_recent(self, n: int = 10) -> List[MemoryCoordinate]:
        all_memories = list(self._iter_all())
        all_memories.sort(key=lambda m: m.timestamp, reverse=True)
        return all_memories[:n]

    def get_by_session(self, session_id: str) -> List[MemoryCoordinate]:
        return list(self._load_session(session_id))

    def get_by_id(self, memory_id: str) -> Optional[MemoryCoordinate]:
        for memory in self._iter_all():
            if memory.memory_id == memory_id:
                return memory
        return None

    # ---------------------------------------------------------------- limits
    def _enforce_limits(self) -> None:
        sessions = sorted(self.sessions_path.glob("*.jsonl"))
        if len(sessions) > self.config.max_sessions:
            to_delete = sessions[: len(sessions) - self.config.max_sessions]
            for path in to_delete:
                path.unlink(missing_ok=True)
                self._cache.pop(path.stem, None)

    # ---------------------------------------------------------------- utils
    def _iter_all(self) -> Iterable[MemoryCoordinate]:
        for session_file in sorted(self.sessions_path.glob("*.jsonl"), reverse=True):
            yield from self._load_session(session_file.stem)

    def _load_session(self, session_id: str) -> Iterable[MemoryCoordinate]:
        if session_id in self._cache:
            yield from self._cache[session_id]
            return
        session_file = self.sessions_path / f"{session_id}.jsonl"
        entries: List[MemoryCoordinate] = []
        if session_file.exists():
            with session_file.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    entries.append(MemoryCoordinate.from_dict(data))
        self._cache[session_id] = entries
        yield from entries

    @staticmethod
    def _match_time(memory: MemoryCoordinate, time_range: Optional[Tuple[datetime, datetime]]) -> bool:
        if not time_range:
            return True
        start, end = time_range
        ts = memory.timestamp
        if start and ts < start:
            return False
        if end and ts > end:
            return False
        return True

    @staticmethod
    def _contains_query(memory: MemoryCoordinate, query: str) -> bool:
        q = query.lower()
        return q in memory.content.get("response_full", "").lower() or q in memory.metadata.get("tags", [])

    @staticmethod
    def _match_bqi(memory: MemoryCoordinate, filters: Dict[str, Any]) -> bool:
        snapshot = memory.metadata.get("bqi_snapshot") or {}
        if "rhythm_phase" in filters:
            rp = filters["rhythm_phase"]
            if rp and snapshot.get("rhythm_phase") != rp:
                return False
        if "emotion" in filters and filters["emotion"]:
            wanted = set(filters["emotion"] if isinstance(filters["emotion"], list) else [filters["emotion"]])
            have = set(snapshot.get("emotion", {}).get("keywords", []))
            if wanted and not wanted.intersection(have):
                return False
        return True
