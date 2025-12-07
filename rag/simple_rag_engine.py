#!/usr/bin/env python3
"""
Simple RAG Engine for E3

- Hash-based embeddings (512-dim)
- In-memory L2 distance search
- Minimal dependencies

This module is primarily used by the E3 configuration:
- Builds an evidence index from `knowledge_base/corpus.jsonl`
- Supports simple search over the built index

Index format (JSON):
{
  "documents": [...],   # each: { "id", "text", "metadata" }
  "embeddings": [...]   # list of float[512] lists, same order as documents
}
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np


DEFAULT_INDEX_PATH = Path("knowledge_base/evidence_index.json")
DEFAULT_CORPUS_PATH = Path("knowledge_base/corpus.jsonl")


@dataclass
class RAGResult:
    doc_id: str
    text: str
    metadata: Dict[str, Any]
    score: float


class SimpleRAGEngine:
    """Hash-based, file-backed RAG engine."""

    def __init__(self, index_path: Path | str = DEFAULT_INDEX_PATH, dim: int = 512) -> None:
        self.index_path = Path(index_path)
        self.dim = dim
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: List[np.ndarray] = []

        if self.index_path.exists():
            self.load_index()

    # ---- Embedding helpers -------------------------------------------------

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer (A-Z, 가-힣, 0-9)."""
        import re

        tokens = re.findall(r"[a-z0-9가-힣]+", text.lower())
        return [t for t in tokens if len(t) > 2]

    def embed_text(self, text: str) -> np.ndarray:
        """Hash-based embedding (MD5 → fixed-dim vector)."""
        tokens = self._tokenize(text)

        vec = np.zeros(self.dim, dtype=np.float32)
        for token in tokens:
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            bucket = h % self.dim
            vec[bucket] += 1.0

        # Log-TF
        vec = np.log1p(vec)

        # L2 normalize
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec

    # ---- Index management --------------------------------------------------

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] | None = None) -> None:
        emb = self.embed_text(text)
        self.documents.append({"id": doc_id, "text": text, "metadata": metadata or {}})
        self.embeddings.append(emb)

    def save_index(self) -> None:
        """Persist documents + embeddings in a JSON structure."""
        data = {
            "documents": self.documents,
            "embeddings": [emb.astype(float).tolist() for emb in self.embeddings],
        }
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_index(self) -> None:
        """Load documents + embeddings from JSON."""
        raw = json.loads(self.index_path.read_text(encoding="utf-8"))
        docs = raw.get("documents") or []
        embs = raw.get("embeddings") or []

        self.documents = list(docs)
        self.embeddings = [np.array(emb, dtype=np.float32) for emb in embs]

    # ---- Query -------------------------------------------------------------

    def search(self, query: str, top_k: int = 3) -> List[RAGResult]:
        """Search documents by L2 distance to the query embedding."""
        if not self.embeddings or not self.documents:
            return []

        query_emb = self.embed_text(query)
        matrix = np.stack(self.embeddings, axis=0)
        # L2 distances
        diffs = matrix - query_emb
        distances = np.linalg.norm(diffs, axis=1)

        # smaller distance → higher score
        order = np.argsort(distances)[: max(top_k, 0)]
        results: List[RAGResult] = []
        for idx in order:
            d = float(distances[int(idx)])
            score = 1.0 / (1.0 + d)
            doc = self.documents[int(idx)]
            results.append(
                RAGResult(
                    doc_id=str(doc.get("id", "")),
                    text=str(doc.get("text", "")),
                    metadata=dict(doc.get("metadata") or {}),
                    score=score,
                )
            )
        return results


def _build_from_corpus(engine: SimpleRAGEngine, corpus_path: Path) -> None:
    if not corpus_path.exists():
        raise SystemExit(f"Corpus file not found: {corpus_path}")
    count = 0
    with corpus_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue
            doc_id = str(doc.get("id", f"doc_{count}"))
            text = str(doc.get("text", ""))
            if not text.strip():
                continue
            metadata = doc.get("metadata") or {}
            engine.add_document(doc_id=doc_id, text=text, metadata=metadata)
            count += 1
    engine.save_index()
    print(f"Index saved: {count} documents -> {engine.index_path}")


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple hash-based RAG engine for E3.")
    parser.add_argument("--build", action="store_true", help="Build index from corpus JSONL.")
    parser.add_argument(
        "--corpus",
        default=str(DEFAULT_CORPUS_PATH),
        help=f"Corpus JSONL path (default: {DEFAULT_CORPUS_PATH})",
    )
    parser.add_argument(
        "--index",
        default=str(DEFAULT_INDEX_PATH),
        help=f"Index JSON path (default: {DEFAULT_INDEX_PATH})",
    )
    parser.add_argument("--search", help="Free-text query to search for.")
    parser.add_argument("--top_k", type=int, default=3, help="Number of results to return (default: 3).")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    index_path = Path(args.index)
    engine = SimpleRAGEngine(index_path=index_path)

    if args.build:
        print(f"Building index from corpus: {args.corpus}")
        _build_from_corpus(engine, Path(args.corpus))

    if args.search:
        if not engine.documents or not engine.embeddings:
            if not index_path.exists():
                raise SystemExit(
                    f"Index not found at {index_path}. "
                    "Run with --build first or provide a valid --index path."
                )
            # Ensure index is loaded if we didn't build in this invocation
            engine.load_index()
        results = engine.search(args.search, top_k=args.top_k)
        print(f"\nTop {args.top_k} results for '{args.search}':\n")
        for i, r in enumerate(results, start=1):
            preview = r.text[:200] + ("..." if len(r.text) > 200 else "")
            print(f"{i}. [{r.doc_id}] (score: {r.score:.3f})")
            print(f"   {preview}\n")


if __name__ == "__main__":
    main()

