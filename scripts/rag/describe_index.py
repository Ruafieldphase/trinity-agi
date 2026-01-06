from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Sequence

from .validate_index import load_records


@dataclass
class IndexStats:
    record_count: int
    preview_min: int
    preview_max: int
    preview_avg: float
    embedding_dims: Dict[int, int]
    missing_embeddings: int
    missing_urls: int


def compute_stats(records: Sequence[dict]) -> IndexStats:
    if not records:
        return IndexStats(
            record_count=0,
            preview_min=0,
            preview_max=0,
            preview_avg=0.0,
            embedding_dims={},
            missing_embeddings=0,
            missing_urls=0,
        )

    preview_lengths = [
        len(str(record.get("preview", ""))) for record in records
    ]
    embedding_dims: Dict[int, int] = {}
    missing_embeddings = 0
    missing_urls = 0
    for record in records:
        embedding = record.get("embedding")
        if isinstance(embedding, list):
            embedding_dims[len(embedding)] = embedding_dims.get(len(embedding), 0) + 1
        else:
            missing_embeddings += 1
        if not record.get("url"):
            missing_urls += 1

    preview_min = min(preview_lengths)
    preview_max = max(preview_lengths)
    preview_avg = sum(preview_lengths) / len(preview_lengths)

    return IndexStats(
        record_count=len(records),
        preview_min=preview_min,
        preview_max=preview_max,
        preview_avg=preview_avg,
        embedding_dims=dict(sorted(embedding_dims.items())),
        missing_embeddings=missing_embeddings,
        missing_urls=missing_urls,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarise evidence index statistics."
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("knowledge_base/evidence_index.json"),
        help="Path to evidence index JSON (default: knowledge_base/evidence_index.json)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output stats as JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_records(args.index)
    stats = compute_stats(records)
    if args.json:
        print(
            json.dumps(
                {
                    "record_count": stats.record_count,
                    "preview": {
                        "min": stats.preview_min,
                        "max": stats.preview_max,
                        "avg": stats.preview_avg,
                    },
                    "embedding_dims": stats.embedding_dims,
                    "missing_embeddings": stats.missing_embeddings,
                    "missing_urls": stats.missing_urls,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    print(f"Records          : {stats.record_count}")
    print(
        "Preview length   : min {0.preview_min} / max {0.preview_max} / avg {0.preview_avg:.1f}".format(
            stats
        )
    )
    if stats.embedding_dims:
        dims = ", ".join(f"{dim}->{count}" for dim, count in stats.embedding_dims.items())
        print(f"Embedding dims   : {dims}")
    else:
        print("Embedding dims   : (none)")
    print(f"Missing embeddings: {stats.missing_embeddings}")
    print(f"Missing URLs     : {stats.missing_urls}")


if __name__ == "__main__":
    main()
