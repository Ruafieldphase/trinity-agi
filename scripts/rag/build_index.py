from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, List

from ..utils.simple_vector_store import SimpleVectorStore
from ..utils.text import clean_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or refresh the evidence index JSON file."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("knowledge_base/evidence_index.json"),
        help="Destination path for the generated index (default: knowledge_base/evidence_index.json)",
    )
    parser.add_argument(
        "--input-json",
        type=Path,
        help="Load records from a JSON/JSONL file (expects keys: source, preview, url, content)",
    )
    parser.add_argument(
        "--markdown-dir",
        type=Path,
        help="Scan a directory of Markdown/TXT files to build records",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with the current index (records sharing the same source will be replaced)",
    )
    parser.add_argument(
        "--preview-chars",
        type=int,
        default=220,
        help="Maximum length for preview text (default: 220)",
    )
    return parser.parse_args()


def load_from_json(path: Path) -> Iterator[Dict[str, str]]:
    content = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)
        return

    data = json.loads(content)
    if isinstance(data, dict) and "records" in data:
        data = data["records"]
    if not isinstance(data, list):
        raise ValueError("JSON input must be a list or a dict containing a 'records' key.")
    for item in data:
        yield item


def load_from_markdown(directory: Path) -> Iterator[Dict[str, str]]:
    pattern = ("*.md", "*.markdown", "*.txt")
    files: List[Path] = []
    for glob in pattern:
        files.extend(directory.glob(f"**/{glob}"))
    for path in sorted({file.resolve() for file in files}):
        raw_text = path.read_text(encoding="utf-8", errors="ignore")
        cleaned = clean_text(raw_text)
        if not cleaned:
            continue
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        title = next(
            (
                line.lstrip("#").strip()
                for line in lines
                if line.startswith("#")
            ),
            path.stem,
        )
        preview = cleaned[:200]
        yield {
            "source": title,
            "preview": preview,
            "url": "",
            "content": raw_text,
        }


def build_records(
    store: SimpleVectorStore, raw_records: Iterable[Dict[str, str]], preview_chars: int
) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    for raw in raw_records:
        source = raw.get("source") or "unknown"
        preview_source = raw.get("preview") or raw.get("content") or ""
        preview = clean_text(preview_source)[:preview_chars]
        url = raw.get("url")
        content = raw.get("content")
        embedding_input = clean_text(content) if content else preview
        if not embedding_input:
            embedding_input = source
        embedding = store.embed_text(embedding_input)
        record: Dict[str, object] = {
            "source": source,
            "preview": preview,
            "url": url,
            "embedding": embedding,
        }
        if content:
            record["content"] = content
        records.append(record)
    return records


def merge_records(
    existing: Iterable[Dict[str, object]], updates: Iterable[Dict[str, object]]
) -> List[Dict[str, object]]:
    merged: Dict[str, Dict[str, object]] = {}
    for item in existing:
        key = str(item.get("source"))
        merged[key] = dict(item)
    for item in updates:
        key = str(item.get("source"))
        merged[key] = dict(item)
    return list(merged.values())


def main() -> None:
    args = parse_args()
    if not args.input_json and not args.markdown_dir:
        raise SystemExit("Provide at least one data source (--input-json or --markdown-dir).")

    store = SimpleVectorStore(args.output)
    new_records: List[Dict[str, object]] = []
    if args.input_json:
        new_records.extend(
            build_records(
                store,
                load_from_json(args.input_json),
                preview_chars=args.preview_chars,
            )
        )
    if args.markdown_dir:
        new_records.extend(
            build_records(
                store,
                load_from_markdown(args.markdown_dir),
                preview_chars=args.preview_chars,
            )
        )

    if args.merge:
        combined = merge_records(store.records(), new_records)
    else:
        combined = new_records

    store.replace(combined)
    print(f"Index written to {args.output} (total records: {len(combined)})")


if __name__ == "__main__":
    main()
