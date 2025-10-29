from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple


@dataclass
class ResonanceLedgerEvent:
    """Structured representation of a single ledger entry."""

    timestamp: datetime
    session_id: str
    event_type: str
    persona_id: Optional[str]
    payload: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResonanceLedgerEvent":
        ts = data.get("timestamp")
        timestamp = (
            datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if isinstance(ts, str)
            else datetime.now(timezone.utc)
        )
        return cls(
            timestamp=timestamp,
            session_id=data.get("session_id", ""),
            event_type=data.get("event_type", ""),
            persona_id=data.get("persona_id"),
            payload={k: v for k, v in data.items() if k not in {"timestamp", "session_id", "event_type", "persona_id"}},
        )

    def to_dict(self) -> Dict[str, Any]:
        base = {
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "event_type": self.event_type,
        }
        if self.persona_id is not None:
            base["persona_id"] = self.persona_id
        base.update(self.payload)
        return base


class ResonanceLedger:
    """Append-only JSONL log of safety/evaluation/rune events."""

    def __init__(self, base_path: Path) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._current_file = self._file_for(datetime.now(timezone.utc))

    # ---------------------------------------------------------------------
    # helpers
    def _file_for(self, dt: datetime) -> Path:
        return self.base_path / f"ledger-{dt.strftime('%Y%m%d')}.jsonl"

    def _ensure_current(self) -> None:
        now = datetime.now(timezone.utc)
        expected = self._file_for(now)
        if expected != self._current_file:
            self._current_file = expected
        self._current_file.parent.mkdir(parents=True, exist_ok=True)
        if not self._current_file.exists():
            self._current_file.touch()

    # ------------------------------------------------------------------ API
    def log_event(
        self,
        session_id: str,
        event_type: str,
        persona_id: Optional[str],
        bqi_coordinate: Optional[Dict[str, Any]],
        evaluation: Optional[Dict[str, Any]],
        plan_adjustment: Optional[Dict[str, Any]],
        memory_id: Optional[str] = None,
    ) -> None:
        """Append a resonance-aware event to the ledger."""
        self._ensure_current()
        entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "event_type": event_type,
        }
        if persona_id:
            entry["persona_id"] = persona_id
        if memory_id:
            entry["memory_id"] = memory_id
        if bqi_coordinate:
            entry["bqi_coordinate"] = bqi_coordinate
        if evaluation:
            entry["evaluation"] = evaluation
        if plan_adjustment:
            entry["plan_adjustment"] = plan_adjustment
        with self._current_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ---------------------------------------------------------------- fetch
    def fetch(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        event_types: Optional[Iterable[str]] = None,
    ) -> Iterator[ResonanceLedgerEvent]:
        """Yield ledger events filtered by time range and/or event type."""
        available_files = sorted(self.base_path.glob("ledger-*.jsonl"))
        if not available_files:
            return iter(())

        event_types_set = set(event_types or [])
        start, end = self._normalise_range(time_range)

        def _reader() -> Iterator[ResonanceLedgerEvent]:
            for path in available_files:
                with path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        data = json.loads(line)
                        event = ResonanceLedgerEvent.from_dict(data)
                        if start and event.timestamp < start:
                            continue
                        if end and event.timestamp > end:
                            continue
                        if event_types_set and event.event_type not in event_types_set:
                            continue
                        yield event

        return _reader()

    @staticmethod
    def _normalise_range(
        time_range: Optional[Tuple[datetime, datetime]]
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        if not time_range:
            return (None, None)
        start, end = time_range
        if start and start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end and end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return start, end
