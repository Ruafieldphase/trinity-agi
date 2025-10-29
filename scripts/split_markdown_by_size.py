from __future__ import annotations

import argparse
from pathlib import Path

CHUNK_LIMIT = 1_048_576  # 1 MiB


def split_file(source: Path, destination_dir: Path, prefix: str | None = None, limit: int = CHUNK_LIMIT) -> None:
    destination_dir.mkdir(parents=True, exist_ok=True)
    prefix = prefix or source.stem

    with source.open('r', encoding='utf-8') as f:
        part = 1
        buffer_chars: list[str] = []
        current_size = 0

        def flush() -> None:
            nonlocal buffer_chars, current_size, part
            if not buffer_chars:
                return
            filename = f"{prefix}_part{part:03d}.md"
            target = destination_dir / filename
            with target.open('w', encoding='utf-8', newline='') as out:
                out.write(''.join(buffer_chars))
            buffer_chars = []
            current_size = 0
            part += 1

        def append_char(ch: str) -> None:
            nonlocal current_size
            encoded = ch.encode('utf-8')
            if current_size + len(encoded) > limit and buffer_chars:
                flush()
            buffer_chars.append(ch)
            current_size += len(encoded)

        for line in f:
            for ch in line:
                append_char(ch)
        flush()

    print(f"Split {source} into parts under {destination_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description='Split Markdown file by size (approx 1 MiB).')
    parser.add_argument('source', type=Path, help='Source markdown file')
    parser.add_argument('destination_dir', type=Path, help='Output directory')
    parser.add_argument('--prefix', type=str, help='Filename prefix for chunks')
    parser.add_argument('--limit', type=int, default=CHUNK_LIMIT, help='Max bytes per chunk (default 1 MiB)')
    args = parser.parse_args()

    split_file(args.source, args.destination_dir, prefix=args.prefix, limit=args.limit)


if __name__ == '__main__':
    main()
