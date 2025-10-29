from __future__ import annotations

import json
import math
from pathlib import Path
import hashlib
from typing import Any, Dict, Iterable, List, Sequence


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(a: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in a))


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    denom = _norm(a) * _norm(b)
    if not denom:
        return 0.0
    return _dot(a, b) / denom


class SimpleVectorStore:
    def __init__(self, index_path: Path) -> None:
        self.index_path = index_path
        if index_path.exists():
            self._records = json.loads(index_path.read_text(encoding="utf-8"))
        else:
            self._records = []

    def search(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_embedding = self._embed(query_text)
        scored: List[Dict[str, Any]] = []
        dim = len(query_embedding)
        for record in self._records:
            embedding = record.get("embedding")
            if not embedding:
                continue
            embedding_vec = list(embedding)
            if len(embedding_vec) < dim:
                embedding_vec = embedding_vec + [0.0] * (dim - len(embedding_vec))
            elif len(embedding_vec) > dim:
                embedding_vec = embedding_vec[:dim]
            score = _cosine_similarity(query_embedding, embedding_vec)
            scored.append(
                {
                    "source": record.get("source", "unknown"),
                    "preview": record.get("preview", ""),
                    "url": record.get("url"),
                    "score": score,
                }
            )
        scored.sort(key=lambda row: row["score"], reverse=True)
        return scored[:top_k]

    def embed_text(self, text: str) -> List[float]:
        return self._embed(text)

    def records(self) -> List[Dict[str, Any]]:
        return list(self._records)

    def replace(self, records: Iterable[Dict[str, Any]]) -> None:
        self._records = [dict(record) for record in records]
        self._records.sort(key=lambda item: str(item.get("source", "")).lower())
        self._write()

    def _write(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(self._records, ensure_ascii=False, indent=2)
        self.index_path.write_text(serialized, encoding="utf-8")

    def _embed(self, text: str) -> List[float]:
        # Placeholder: deterministic bag-of-words hashing.
        tokens = text.lower().split()
        vec = [0.0] * 128
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            slot = int.from_bytes(digest[:4], "big") % len(vec)
            vec[slot] += 1.0
        return vec
