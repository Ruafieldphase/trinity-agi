from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional, Tuple

from .describe_index import compute_stats
from .retriever import EvidenceRetriever
from .settings import RagSettings, load_rag_settings
from .validate_index import ValidationIssue, load_records, validate_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Markdown report summarising RAG index health."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/persona_registry_e2.json"),
        help="Persona configuration that includes RAG settings (default: configs/persona_registry_e2.json).",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Optional sample query to include in the report.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        help="Override top_k for the sample query.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        help="Override min_score for the sample query.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write report to the given file path instead of stdout.",
    )
    parser.add_argument(
        "--json-summary",
        action="store_true",
        help="Emit summary metrics as JSON to stdout (after Markdown output).",
    )
    return parser.parse_args()


def _expected_dimension(records: List[dict]) -> int:
    for record in records:
        embedding = record.get("embedding")
        if isinstance(embedding, list) and embedding:
            return len(embedding)
    return 128


def format_validation(issues: List[ValidationIssue]) -> Tuple[str, int]:
    if not issues:
        return "- Validation passed (0 issues).", 0

    lines: List[str] = []
    error_count = 0
    for issue in issues:
        level = issue.level.upper()
        if issue.level == "error":
            error_count += 1
        source = f" ({issue.record_source})" if issue.record_source else ""
        lines.append(f"- **{level}**{source} {issue.message}")
    return "\n".join(lines), error_count


def format_stats_section(settings: RagSettings, stats) -> List[str]:
    dims = (
        ", ".join(f"{dim}->{count}" for dim, count in stats.embedding_dims.items())
        if stats.embedding_dims
        else "(none)"
    )
    return [
        f"- Records: {stats.record_count}",
        f"- Preview length avg: {stats.preview_avg:.1f} (min {stats.preview_min}, max {stats.preview_max})",
        f"- Embedding dimensions: {dims}",
        f"- Missing embeddings: {stats.missing_embeddings}",
        f"- Missing URLs: {stats.missing_urls}",
    ]


def format_query_section(
    query: str,
    hits,
    top_k: int,
    min_score: Optional[float],
) -> List[str]:
    lines = [
        f"- Query: `{query}`",
        f"- Parameters: top_k={top_k}, min_score={min_score if min_score is not None else 'None'}",
    ]
    if not hits:
        lines.append("- No matches found.")
        return lines

    lines.append("- Results:")
    for idx, hit in enumerate(hits, start=1):
        lines.append(f"  {idx}. **{hit.source}** (score={hit.score:.4f})")
        if hit.url:
            lines.append(f"     - url: {hit.url}")
        lines.append(f"     - preview: {hit.preview}")
    return lines


def generate_report(
    config_path: Path,
    settings: RagSettings,
    query: Optional[str],
    top_k_override: Optional[int],
    min_score_override: Optional[float],
) -> Tuple[str, int]:
    records = load_records(settings.index)
    expected_dim = _expected_dimension(records)
    issues = validate_records(records, expected_dim=expected_dim)
    stats = compute_stats(records)

    top_k = top_k_override if top_k_override is not None else settings.top_k
    min_score = (
        min_score_override
        if min_score_override is not None
        else settings.min_score
    )

    lines: List[str] = []
    lines.append("# RAG Index Report")
    lines.append("")
    lines.append(f"- Config: `{config_path}`")
    lines.append(f"- Index: `{settings.index}`")
    lines.append(
        f"- Defaults: top_k={settings.top_k}, min_score={settings.min_score if settings.min_score is not None else 'None'}"
    )
    lines.append("")
    lines.append("## Validation")
    validation_block, error_count = format_validation(issues)
    lines.append(validation_block)
    lines.append("")
    lines.append("## Index Stats")
    lines.extend(format_stats_section(settings, stats))

    if query is not None:
        lines.append("")
        lines.append("## Sample Query")
        retriever = EvidenceRetriever(settings.index)
        hits = retriever.query(query, top_k=top_k, min_score=min_score)
        lines.extend(format_query_section(query, hits, top_k, min_score))

    report_text = "\n".join(lines).rstrip() + "\n"
    summary = {
        "config": str(config_path),
        "index": str(settings.index),
        "top_k": settings.top_k,
        "min_score": settings.min_score,
        "record_count": stats.record_count,
        "preview_avg": stats.preview_avg,
        "preview_min": stats.preview_min,
        "preview_max": stats.preview_max,
        "embedding_dims": stats.embedding_dims,
        "missing_embeddings": stats.missing_embeddings,
        "missing_urls": stats.missing_urls,
    }
    return report_text, error_count, summary


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    settings = load_rag_settings(config_path)
    report, error_count, summary = generate_report(
        config_path=config_path,
        settings=settings,
        query=args.query,
        top_k_override=args.top_k,
        min_score_override=args.min_score,
    )

    if args.output:
        output_path = args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(f"RAG report written to {output_path}")
    else:
        print(report)

    summary_line = (
        f"Summary: records={summary['record_count']}, "
        f"avg preview={summary['preview_avg']:.1f}, "
        f"embedding_dims={summary['embedding_dims']}"
    )
    print(summary_line)

    if args.json_summary:
        import json

        print(json.dumps(summary, ensure_ascii=False, indent=2))

    if error_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
