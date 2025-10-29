from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from .describe_index import compute_stats
from .settings import load_rag_settings, RagSettings
from .validate_index import load_records, validate_records
from .retriever import EvidenceRetriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a quick RAG index health check (validate, describe, sample query)."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/persona_registry_e2.json"),
        help="Persona configuration with RAG settings.",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Sample query to run after validation. Skipped if not provided.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        help="Override top_k for sample query.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        help="Override min_score for sample query.",
    )
    return parser.parse_args()


def print_issues(errors: List[str], warnings: List[str]) -> None:
    for issue in errors:
        print(issue)
    for issue in warnings:
        print(issue)


def main() -> None:
    args = parse_args()
    settings = load_rag_settings(args.config)
    records = load_records(settings.index)
    issues = validate_records(records, expected_dim=128)

    errors = [
        f"[ERROR]{' (' + issue.record_source + ')' if issue.record_source else ''} {issue.message}"
        for issue in issues
        if issue.level == "error"
    ]
    warnings = [
        f"[WARNING]{' (' + issue.record_source + ')' if issue.record_source else ''} {issue.message}"
        for issue in issues
        if issue.level == "warning"
    ]

    if errors or warnings:
        print_issues(errors, warnings)
    else:
        print("Validation passed (0 issues).")

    stats = compute_stats(records)
    print(
        f"Index stats: records={stats.record_count}, preview_avg={stats.preview_avg:.1f}, "
        f"embedding_dims={stats.embedding_dims}, missing_urls={stats.missing_urls}"
    )

    if args.query:
        top_k = args.top_k if args.top_k is not None else settings.top_k
        min_score = (
            args.min_score
            if args.min_score is not None
            else settings.min_score
        )

        retriever = EvidenceRetriever(settings.index)
        hits = retriever.query(args.query, top_k=top_k, min_score=min_score)
        if not hits:
            print("Sample query returned no matches.")
        else:
            for idx, hit in enumerate(hits, start=1):
                print(f"[{idx}] {hit.source} (score={hit.score:.4f})")
                if hit.url:
                    print(f"    url: {hit.url}")
                print(f"    preview: {hit.preview}")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
