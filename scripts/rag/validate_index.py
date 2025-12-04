from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence


@dataclass
class ValidationIssue:
    level: str
    message: str
    record_source: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate evidence index JSON structure and embeddings."
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("knowledge_base/evidence_index.json"),
        help="Path to evidence index JSON (default: knowledge_base/evidence_index.json)",
    )
    parser.add_argument(
        "--expected-dim",
        type=int,
        default=128,
        help="Expected embedding dimension (default: 128)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (non-zero exit code).",
    )
    return parser.parse_args()


def load_records(path: Path) -> Sequence[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Index not found: {path}") from exc

    if isinstance(data, dict):
        documents = data.get("documents") or []
        embeddings = data.get("embeddings") or []
        records: List[dict] = []
        for doc, emb in zip(documents, embeddings):
            record = dict(doc)
            metadata = record.get("metadata") or {}
            record["source"] = metadata.get("source", record.get("source", "unknown"))
            if "preview" not in record:
                text = record.get("text", "")
                record["preview"] = text[:200]
            record["embedding"] = emb
            record.setdefault("url", metadata.get("url"))
            records.append(record)
        return records

    if not isinstance(data, list):
        raise SystemExit("Index JSON must be a list of records or a dict with 'documents'.")
    return data


def validate_records(records: Sequence[dict], expected_dim: int) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    for record in records:
        source = str(record.get("source") or "").strip() or None
        if not source:
            issues.append(ValidationIssue("error", "Missing 'source' value"))
        preview = record.get("preview")
        if not isinstance(preview, str) or not preview.strip():
            issues.append(
                ValidationIssue(
                    "warning",
                    "Empty or missing 'preview' field",
                    record_source=source,
                )
            )
        embedding = record.get("embedding")
        if embedding is None:
            issues.append(
                ValidationIssue("error", "Missing 'embedding'", record_source=source)
            )
            continue
        if not isinstance(embedding, list) or not all(
            isinstance(value, (int, float)) for value in embedding
        ):
            issues.append(
                ValidationIssue(
                    "error",
                    "Embedding must be a list of numbers",
                    record_source=source,
                )
            )
            continue
        if expected_dim and len(embedding) != expected_dim:
            issues.append(
                ValidationIssue(
                    "warning",
                    f"Embedding dimension {len(embedding)} != expected {expected_dim}",
                    record_source=source,
                )
            )
        url = record.get("url")
        if url and not isinstance(url, str):
            issues.append(
                ValidationIssue("warning", "URL is not a string", record_source=source)
            )
    return issues


def main() -> None:
    args = parse_args()
    records = load_records(args.index)
    issues = validate_records(records, expected_dim=args.expected_dim)

    errors = [issue for issue in issues if issue.level == "error"]
    warnings = [issue for issue in issues if issue.level == "warning"]

    if not issues:
        print(f"Validation passed ({len(records)} records).")
        return

    for collection, label in ((errors, "ERROR"), (warnings, "WARNING")):
        for issue in collection:
            prefix = f"[{label}]"
            source = f" ({issue.record_source})" if issue.record_source else ""
            print(f"{prefix}{source} {issue.message}")

    if errors or (args.strict and warnings):
        raise SystemExit(
            f"Validation failed with {len(errors)} errors and {len(warnings)} warnings."
        )
    print(f"Validation completed: {len(errors)} errors, {len(warnings)} warnings.")


if __name__ == "__main__":
    main()
