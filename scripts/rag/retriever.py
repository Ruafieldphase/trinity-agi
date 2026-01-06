from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

from scripts.utils.simple_vector_store import SimpleVectorStore
from scripts.utils.text import clean_text


@dataclass
class RetrievalHit:
    source: str
    score: float
    preview: str
    url: str | None = None


class EvidenceRetriever:
    def __init__(self, index_path: Path) -> None:
        self.store = SimpleVectorStore(index_path)

    def query(
        self, text: str, top_k: int = 3, min_score: float | None = None
    ) -> List[RetrievalHit]:
        cleaned = clean_text(text)
        rows = self.store.search(cleaned, top_k=top_k)
        hits: List[RetrievalHit] = []
        for row in rows:
            score_value = float(row.get("score", 0.0))
            if min_score is not None and score_value < min_score:
                continue
            hits.append(
                RetrievalHit(
                    source=row.get("source", "unknown"),
                    score=score_value,
                    preview=row.get("preview", ""),
                    url=row.get("url"),
                )
            )
        return hits
