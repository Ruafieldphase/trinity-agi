from __future__ import annotations

import argparse
import re
from pathlib import Path


METADATA_PREFIXES = ["- **File**", "- **Conversation ID**"]


def slugify(text: str, fallback: str, max_len: int = 60) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    if not text:
        text = fallback
    if len(text) > max_len:
        text = text[:max_len].rstrip("-")
    if not text:
        text = fallback
    return text


def _is_section_start(lines: list[str], idx: int) -> bool:
    if not lines[idx].startswith("## "):
        return False
    total = len(lines)
    j = idx + 1
    while j < total and not lines[j].strip():
        j += 1
    if j >= total:
        return False
    return any(lines[j].startswith(prefix) for prefix in METADATA_PREFIXES)


def split_markdown(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    lines = source.read_text(encoding="utf-8").splitlines()

    sections: list[tuple[str, list[str]]] = []
    current_title = None
    current_lines: list[str] = []

    total_lines = len(lines)
    idx = 0
    while idx < total_lines:
        if _is_section_start(lines, idx):
            line = lines[idx]
            if current_title is not None:
                sections.append((current_title, current_lines))
            current_title = line[3:].strip()
            current_lines = [line]
            idx += 1
            continue
        if current_title is not None:
            current_lines.append(lines[idx])
        idx += 1

    if current_title is not None:
        sections.append((current_title, current_lines))

    if not sections:
        raise ValueError(f"No sections found in {source}")

    digits = len(str(len(sections)))
    for idx, (title, content_lines) in enumerate(sections, start=1):
        slug = slugify(title, fallback=f"section-{idx}")
        filename = f"{idx:0{digits}d}_{slug}.md"
        (destination / filename).write_text("\n".join(content_lines).strip() + "\n", encoding="utf-8")

    print(f"Split {source} into {len(sections)} files under {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Split Markdown file by conversation sections.")
    parser.add_argument("source", type=Path, help="Source markdown file")
    parser.add_argument("destination", type=Path, help="Destination directory")
    args = parser.parse_args()
    split_markdown(args.source, args.destination)


if __name__ == "__main__":
    main()
