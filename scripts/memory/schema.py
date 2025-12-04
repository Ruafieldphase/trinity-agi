from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class MemoryCoordinate:
    memory_id: str
    timestamp: datetime
    time: Dict[str, Any]
    space: Dict[str, Any]
    agent: Dict[str, Any]
    emotion: Dict[str, Any]
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    relations: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "memory_id": self.memory_id,
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat(),
            "time": self.time,
            "space": self.space,
            "agent": self.agent,
            "emotion": self.emotion,
            "content": self.content,
            "metadata": self.metadata,
            "relations": self.relations,
        }
        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryCoordinate":
        timestamp = data.get("timestamp")
        ts = (
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if isinstance(timestamp, str)
            else datetime.now(timezone.utc)
        )
        return cls(
            memory_id=data["memory_id"],
            timestamp=ts,
            time=data.get("time", {}),
            space=data.get("space", {}),
            agent=data.get("agent", {}),
            emotion=data.get("emotion", {}),
            content=data.get("content", {}),
            metadata=data.get("metadata", {}),
            relations=data.get("relations", {}),
        )


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
