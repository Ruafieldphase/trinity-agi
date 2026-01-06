from __future__ import annotations

import argparse
import json
from pathlib import Path

from .retriever import EvidenceRetriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lightweight CLI helper that queries evidence_index.json."
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional persona config JSON to read default RAG settings.",
    )
    parser.add_argument("query", help="Sentence or keywords to search for")
    parser.add_argument(
        "--index",
        type=Path,
        default=None,
        help="Path to the evidence index JSON.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of hits to display.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Filter results below the given similarity score.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    default_index = Path("knowledge_base/evidence_index.json")
    settings = None
    if args.config:
        from .settings import load_rag_settings

        settings = load_rag_settings(args.config)

    index_path = args.index or (settings.index if settings else default_index)
    top_k = args.top_k if args.top_k is not None else (
        settings.top_k if settings else 4
    )
    min_score = (
        args.min_score
        if args.min_score is not None
        else (settings.min_score if settings else None)
    )

    retriever = EvidenceRetriever(index_path)
    hits = retriever.query(args.query, top_k=top_k, min_score=min_score)

    if args.json:
        serialized = [
            {
                "source": hit.source,
                "score": hit.score,
                "preview": hit.preview,
                "url": hit.url,
            }
            for hit in hits
        ]
        print(json.dumps(serialized, ensure_ascii=False, indent=2))
        return

    if not hits:
        print("No matches found.")
        return

    for idx, hit in enumerate(hits, start=1):
        print(f"[{idx}] {hit.source}")
        print(f"    score : {hit.score:.4f}")
        if hit.url:
            print(f"    url   : {hit.url}")
        print(f"    preview: {hit.preview}")


if __name__ == "__main__":
    main()
