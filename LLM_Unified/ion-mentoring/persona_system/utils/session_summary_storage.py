#!/usr/bin/env python3
"""
Session summary storage (JSONL + lightweight embedding index).

Responsibilities
----------------
- Persist session summaries to JSONL files grouped by day
- Maintain a compact index for fast lookups and metadata
- Generate and store embedding vectors (Vertex AI if available, hash fallback)
- Provide simple filtering + similarity search APIs
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .embedding_service import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


@dataclass
class SessionSummary:
    """Structured representation of a stored session summary."""

    session_id: str
    user_id: str
    summary: str
    summary_type: str  # "llm" or "rule_based"
    created_at: str  # ISO timestamp
    message_count: int = 0
    summary_length: int = 0
    metadata: Optional[Dict[str, Any]] = None
    embedding_path: Optional[str] = None
    embedding_dims: int = 0
    embedding_model: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.summary_length:
            self.summary_length = len(self.summary or "")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionSummary":
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            summary=data.get("summary", ""),
            summary_type=data.get("summary_type", "llm"),
            created_at=data.get("created_at") or datetime.now().isoformat(),
            message_count=data.get("message_count", 0),
            summary_length=data.get("summary_length", len(data.get("summary", ""))),
            metadata=data.get("metadata") or {},
            embedding_path=data.get("embedding_path"),
            embedding_dims=data.get("embedding_dims", 0),
            embedding_model=data.get("embedding_model"),
        )


class SessionSummaryStorage:
    """File-backed long term memory for persona sessions."""

    def __init__(self, data_dir: Optional[Path] = None):
        project_root = (
            Path(__file__).parent.parent.parent if data_dir is None else None
        )
        base_dir = data_dir or (project_root / "data" / "session_summaries")

        self.data_dir = Path(base_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.data_dir / "index.json"
        self.embedding_dir = self.data_dir / "embeddings"
        self.embedding_dir.mkdir(parents=True, exist_ok=True)

        self.index: Dict[str, Dict[str, Any]] = {}
        self.embedding_service: EmbeddingService = get_embedding_service()

        self._load_index()
        logger.info("SessionSummaryStorage initialized at %s", self.data_dir)

    # ------------------------------------------------------------------ #
    # Index helpers
    # ------------------------------------------------------------------ #
    def _load_index(self):
        if not self.index_file.exists():
            self.index = {}
            return

        try:
            with open(self.index_file, "r", encoding="utf-8") as fh:
                self.index = json.load(fh)
            logger.debug("Loaded %s entries from index", len(self.index))
        except Exception as exc:  # pragma: no cover - corrupted file guard
            logger.error("Failed to load index: %s", exc)
            self.index = {}

    def _save_index(self):
        try:
            with open(self.index_file, "w", encoding="utf-8") as fh:
                json.dump(self.index, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error("Failed to persist index: %s", exc)

    # ------------------------------------------------------------------ #
    # Path helpers
    # ------------------------------------------------------------------ #
    def _get_file_path(self, date: datetime) -> Path:
        month_dir = self.data_dir / date.strftime("%Y-%m")
        month_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"session_summaries_{date.strftime('%Y%m%d')}.jsonl"
        return month_dir / file_name

    def _get_embedding_path(self, session_id: str) -> Path:
        safe_id = session_id.replace("/", "_")
        return self.embedding_dir / f"{safe_id}.json"

    # ------------------------------------------------------------------ #
    # Embedding persistence
    # ------------------------------------------------------------------ #
    def _write_embedding(
        self,
        session_id: str,
        vector: List[float],
        *,
        model_name: Optional[str],
        created_at: datetime,
    ) -> Optional[Path]:
        if not vector:
            return None

        payload = {
            "session_id": session_id,
            "model": model_name,
            "dims": len(vector),
            "created_at": created_at.isoformat(),
            "embedding": vector,
        }

        try:
            path = self._get_embedding_path(session_id)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False)
            return path
        except Exception as exc:
            logger.warning("Failed to persist embedding for %s: %s", session_id, exc)
            return None

    def _load_embedding_vector(self, entry: Dict[str, Any]) -> Optional[List[float]]:
        path = entry.get("embedding_path")
        if not path:
            return None

        try:
            target = Path(path)
            if not target.exists():
                return None
            with open(target, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data.get("embedding")
        except Exception as exc:
            logger.warning("Failed to read embedding %s: %s", path, exc)
            return None

    def _delete_embedding(self, entry: Dict[str, Any]):
        path = entry.get("embedding_path")
        if not path:
            return
        try:
            target = Path(path)
            if target.exists():
                target.unlink()
        except Exception as exc:
            logger.warning("Failed to remove embedding %s: %s", path, exc)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def save(
        self,
        session_id: str,
        user_id: str,
        summary: str,
        summary_type: str = "llm",
        message_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Persist a session summary + embedding metadata."""
        try:
            now = datetime.now()
            payload = SessionSummary(
                session_id=session_id,
                user_id=user_id,
                summary=summary,
                summary_type=summary_type,
                created_at=now.isoformat(),
                message_count=message_count,
                summary_length=len(summary or ""),
                metadata=metadata or {},
            )

            embedding_path = None
            embedding_dims = 0
            embedding_model = None
            try:
                vector = self.embedding_service.embed(summary or "")
                if vector:
                    embedding_model = getattr(self.embedding_service, "model_name", "")
                    stored_path = self._write_embedding(
                        session_id,
                        vector,
                        model_name=embedding_model,
                        created_at=now,
                    )
                    if stored_path:
                        embedding_path = str(stored_path)
                        embedding_dims = len(vector)
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning("Embedding generation failed for %s: %s", session_id, exc)

            payload.embedding_path = embedding_path
            payload.embedding_dims = embedding_dims
            payload.embedding_model = embedding_model

            file_path = self._get_file_path(now)
            with open(file_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload.to_dict(), ensure_ascii=False) + "\n")

            self.index[session_id] = {
                "user_id": user_id,
                "created_at": payload.created_at,
                "file_path": str(file_path),
                "summary_type": summary_type,
                "message_count": message_count,
                "embedding_path": embedding_path,
                "embedding_dims": embedding_dims,
                "embedding_model": embedding_model,
            }
            self._save_index()

            logger.info(
                "Saved summary session_id=%s user_id=%s length=%s dims=%s",
                session_id,
                user_id,
                payload.summary_length,
                embedding_dims,
            )
            return True
        except Exception as exc:
            logger.error("Failed to save session summary: %s", exc, exc_info=True)
            return False

    def load(self, session_id: str) -> Optional[SessionSummary]:
        """Load a single session summary from storage."""
        entry = self.index.get(session_id)
        if not entry:
            logger.debug("Session not found in index: %s", session_id)
            return None

        file_path = Path(entry["file_path"])
        if not file_path.exists():
            logger.warning("Summary file missing: %s", file_path)
            return None

        last_match: Optional[SessionSummary] = None
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    if data.get("session_id") == session_id:
                        last_match = SessionSummary.from_dict(data)
        except Exception as exc:
            logger.error("Failed to load session %s: %s", session_id, exc, exc_info=True)
            return None

        if not last_match:
            logger.warning("Session not found in file: %s", session_id)
        return last_match

    def search(
        self,
        *,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        summary_type: Optional[str] = None,
        limit: int = 100,
        query_text: Optional[str] = None,
        min_similarity: float = 0.0,
        include_embeddings: bool = False,
    ) -> List[SessionSummary]:
        """Filter summaries with optional semantic search."""
        try:
            results: List[SessionSummary] = []
            query_vector: Optional[List[float]] = None
            if query_text:
                query_vector = self.embedding_service.embed(query_text)

            ordered_entries = sorted(
                self.index.items(),
                key=lambda item: item[1].get("created_at", ""),
                reverse=True,
            )

            for session_id, entry in ordered_entries:
                if user_id and entry.get("user_id") != user_id:
                    continue
                if summary_type and entry.get("summary_type") != summary_type:
                    continue

                created_at = entry.get("created_at")
                if created_at:
                    created_dt = datetime.fromisoformat(created_at)
                    if start_date and created_dt < start_date:
                        continue
                    if end_date and created_dt > end_date:
                        continue

                summary = self.load(session_id)
                if not summary:
                    continue

                if query_vector is not None:
                    summary_vector = self._load_embedding_vector(entry)
                    similarity = (
                        self.embedding_service.cosine_similarity(query_vector, summary_vector)
                        if summary_vector
                        else 0.0
                    )
                    if similarity < min_similarity:
                        continue
                    summary.metadata = summary.metadata or {}
                    summary.metadata["similarity"] = round(similarity, 4)
                    if include_embeddings and summary_vector:
                        summary.metadata["embedding_preview"] = summary_vector[:8]

                results.append(summary)
                if len(results) >= limit:
                    break

            results.sort(key=lambda item: item.created_at, reverse=True)

            logger.info(
                "Search completed (limit=%s, query=%s) -> %s results",
                limit,
                bool(query_text),
                len(results),
            )
            return results
        except Exception as exc:
            logger.error("Failed to search session summaries: %s", exc, exc_info=True)
            return []

    def list_recent(
        self, limit: int = 10, *, include_embeddings: bool = False
    ) -> List[SessionSummary]:
        """Shortcut for latest summaries (no filters)."""
        return self.search(limit=limit, include_embeddings=include_embeddings)

    def get_stats(self) -> Dict[str, Any]:
        """Return aggregate statistics for dashboards/health checks."""
        total = len(self.index)
        llm_count = sum(1 for entry in self.index.values() if entry.get("summary_type") == "llm")
        rule_count = sum(
            1 for entry in self.index.values() if entry.get("summary_type") == "rule_based"
        )

        now = datetime.now()
        last_day = now - timedelta(days=1)
        recent = sum(
            1
            for entry in self.index.values()
            if entry.get("created_at")
            and datetime.fromisoformat(entry["created_at"]) > last_day
        )

        embeddings_available = sum(
            1 for entry in self.index.values() if entry.get("embedding_path")
        )

        return {
            "total_sessions": total,
            "llm_summaries": llm_count,
            "rule_based_summaries": rule_count,
            "recent_24h": recent,
            "storage_path": str(self.data_dir),
            "embedding_path": str(self.embedding_dir),
            "embeddings_available": embeddings_available,
        }

    def delete(self, session_id: str) -> bool:
        """Remove a session summary from the index (and optional vector)."""
        if session_id not in self.index:
            logger.warning("Session not found for delete: %s", session_id)
            return False

        try:
            entry = self.index[session_id]
            self._delete_embedding(entry)
            del self.index[session_id]
            self._save_index()
            logger.info("Deleted session %s from index", session_id)
            return True
        except Exception as exc:
            logger.error("Failed to delete session %s: %s", session_id, exc)
            return False


_session_storage: Optional[SessionSummaryStorage] = None


def get_session_storage(data_dir: Optional[Path] = None) -> SessionSummaryStorage:
    global _session_storage
    if _session_storage is None:
        _session_storage = SessionSummaryStorage(data_dir=data_dir)
    return _session_storage


def reset_session_storage():
    global _session_storage
    _session_storage = None
    logger.info("SessionSummaryStorage reset")
