from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone


@dataclass
class CompressionInput:
    source: str
    payload: Any
    meta: Dict[str, Any]


class SelfCompression:
    """
    Self-Compression (자기 수축/압축) 스켈레톤
    - 정규화 → 노이즈/충돌 제거 → 리듬화/위상 전이 → 상태 파일 반영
    - 현재는 단순 직렬화/로그 용도로 동작하며, 실제 모델/리듬화 로직은 확장 지점.
    """

    def __init__(self, outputs_dir: Path, memory_dir: Path):
        self.outputs_dir = outputs_dir
        self.memory_dir = memory_dir
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.thought_path = self.outputs_dir / "thought_stream_latest.json"
        self.state_path = self.memory_dir / "agi_internal_state.json"
        self.heartbeat_path = self.outputs_dir / "unconscious_heartbeat.json"

    def _load_state_stub(self) -> Dict[str, Any]:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _load_heartbeat_count(self) -> int:
        if self.heartbeat_path.exists():
            try:
                data = json.loads(self.heartbeat_path.read_text(encoding="utf-8"))
                return int(data.get("heartbeat_count", 0))
            except Exception:
                return 0
        return 0

    def compress(self, items: List[CompressionInput]) -> Dict[str, Any]:
        """
        정규화/간이 압축 단계:
        - 빈 payload/중복 source 제거
        - 메타 정보만 남겨 thought_stream_latest.json에 "병합" 기록 (기존 필드 보존)
        - internal_state 역시 덮어쓰지 않고 self_expansion 섹션으로 병합
        """
        filtered: List[CompressionInput] = []
        seen = set()
        for it in items:
            if it.payload in (None, "", []):
                continue
            key = (it.source, json.dumps(it.meta, sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            filtered.append(it)

        summary = {
            "count": len(filtered),
            "sources": list({it.source for it in filtered}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        thought_patch = {
            "self_expansion": {
                "compression": {
                    "summary": summary,
                    "entries": [{"source": it.source, "meta": it.meta} for it in filtered],
                }
            }
        }
        try:
            existing = {}
            if self.thought_path.exists():
                existing = json.loads(self.thought_path.read_text(encoding="utf-8"))
            merged = dict(existing) if isinstance(existing, dict) else {}
            merged.setdefault("self_expansion", {})
            merged["self_expansion"]["compression"] = thought_patch["self_expansion"]["compression"]
            self.thought_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            # fallback: 최소한의 객체로 기록
            self.thought_path.write_text(json.dumps(thought_patch, ensure_ascii=False, indent=2), encoding="utf-8")

        prev_state = self._load_state_stub()
        prev_events = prev_state.get("compression_events", 0)
        hb_count = max(prev_state.get("heartbeat_count", 0), self._load_heartbeat_count())
        state_patch = {
            "heartbeat_count": hb_count,
            "self_expansion": {
                "compression_events": prev_events + summary["count"],
                "last_compression": summary["timestamp"],
                "sources": summary["sources"],
            },
        }
        try:
            existing_state = prev_state if isinstance(prev_state, dict) else {}
            merged_state = dict(existing_state)
            merged_state["heartbeat_count"] = hb_count
            merged_state.setdefault("self_expansion", {})
            merged_state["self_expansion"].update(state_patch["self_expansion"])
            self.state_path.write_text(json.dumps(merged_state, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            self.state_path.write_text(json.dumps(state_patch, ensure_ascii=False, indent=2), encoding="utf-8")

        return summary
