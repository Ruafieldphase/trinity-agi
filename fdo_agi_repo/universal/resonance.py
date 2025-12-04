from __future__ import annotations
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from pathlib import Path
import json

from .task_schema import UniversalTask, AbstractIntent


class ResonanceEvent(BaseModel):
    """단일 실행 또는 평가에서의 공통 메트릭 스냅샷."""

    task_id: str
    resonance_key: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: Dict[str, float] = Field(default_factory=dict)
    tags: Dict[str, Any] = Field(default_factory=dict)


def derive_resonance_key(task: UniversalTask) -> str:
    """도메인 불가지론적 공통 키.

    기본 규칙: "{domain_id}:{intent}" (예: "software_engineering:analyze")
    필요 시 subdomain/ontology 신호를 붙일 수 있도록 확장.
    """
    parts: List[str] = [task.domain.domain_id, task.intent.value]
    if task.domain.subdomain:
        parts.append(task.domain.subdomain)
    return ":".join(parts)


class ResonanceStore:
    """간단한 JSONL 파일 기반 저장소."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: ResonanceEvent):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json())
            f.write("\n")

    def latest(self) -> Optional[ResonanceEvent]:
        if not self.path.exists():
            return None
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                last_line = None
                for line in f:
                    if line.strip():
                        last_line = line
                if not last_line:
                    return None
                data = json.loads(last_line)
                return ResonanceEvent(**data)
        except Exception:
            return None
    
    def read_all(self) -> List[ResonanceEvent]:
        """Read all events from the store"""
        if not self.path.exists():
            return []
        
        events = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        events.append(ResonanceEvent(**data))
        except Exception:
            pass
        
        return events

