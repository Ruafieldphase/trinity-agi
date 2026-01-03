#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a concise context snapshot for this workspace.
- Scans the workspace for files modified within a given time window (default: 24h)
- Groups by categories: code (fdo_agi_repo/**/*.py), scripts (scripts/**/*.py|ps1), docs (docs/**/*.md), outputs (outputs/**/*.{json,md,csv,html}), configs (root and subpaths with .json/.yaml/.yml/.toml)
- Excludes noisy dirs: .venv, node_modules, .pytest_tmp, __pycache__
- Writes:
  - outputs/context_snapshot.json (machine-readable)
  - outputs/context_snapshot.md (human-readable)

Usage:
  python scripts/generate_context_snapshot.py --hours 24
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Tuple
from workspace_root import get_workspace_root

WORKSPACE = get_workspace_root()
OUTPUTS_DIR = WORKSPACE / "outputs"

EXCLUDE_DIR_NAMES = {".venv", "node_modules", ".pytest_tmp", "__pycache__", ".git"}

CATEGORIES = [
    ("code", [
        ("fdo_agi_repo", (".py",)),
    ]),
    ("scripts", [
        ("scripts", (".py", ".ps1")),
    ]),
    ("docs", [
        ("docs", (".md",)),
    ]),
    ("outputs", [
        ("outputs", (".json", ".md", ".csv", ".html")),
    ]),
    ("configs", [
        ("", (".json", ".yaml", ".yml", ".toml")),
    ]),
]

@dataclass
class FileInfo:
    path: str
    size: int
    mtime: float
    rel: str
    category: str

    def mtime_iso(self) -> str:
        import datetime as dt
        return dt.datetime.fromtimestamp(self.mtime).isoformat(sep=" ", timespec="seconds")


def within_hours(p: Path, cutoff_epoch: float) -> bool:
    try:
        return p.stat().st_mtime >= cutoff_epoch
    except OSError:
        return False


def should_exclude_dir(dirpath: Path) -> bool:
    name = dirpath.name.lower()
    return name in EXCLUDE_DIR_NAMES


def collect_files(hours: int) -> List[FileInfo]:
    cutoff = time.time() - hours * 3600

    results: List[FileInfo] = []

    # Build search specs
    specs: List[Tuple[str, Tuple[str, ...], str]] = []  # (root_subdir, exts, category)
    for category, groups in CATEGORIES:
        for root_sub, exts in groups:
            specs.append((root_sub, exts, category))

    for root_sub, exts, category in specs:
        base = WORKSPACE / root_sub
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            # prune excluded dirs
            dirnames[:] = [d for d in dirnames if not should_exclude_dir(Path(dirpath) / d)]

            for fname in filenames:
                p = Path(dirpath) / fname
                if exts and p.suffix.lower() not in exts:
                    continue
                if not within_hours(p, cutoff):
                    continue
                try:
                    st = p.stat()
                except OSError:
                    continue
                rel = str(p.relative_to(WORKSPACE))
                results.append(FileInfo(
                    path=str(p),
                    size=st.st_size,
                    mtime=st.st_mtime,
                    rel=rel,
                    category=category,
                ))

    # Sort by mtime desc
    results.sort(key=lambda x: x.mtime, reverse=True)
    return results


def group_by_category(files: List[FileInfo]) -> Dict[str, List[FileInfo]]:
    out: Dict[str, List[FileInfo]] = {}
    for f in files:
        out.setdefault(f.category, []).append(f)
    return out


def write_json(files: List[FileInfo]) -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "workspace": str(WORKSPACE),
        "generated_at": time.time(),
        "files": [asdict(f) for f in files],
        "by_category": {
            cat: [asdict(f) for f in group]
            for cat, group in group_by_category(files).items()
        }
    }
    out = OUTPUTS_DIR / "context_snapshot.json"
    with out.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    return out


def write_md(files: List[FileInfo], hours: int) -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUTS_DIR / "context_snapshot.md"
    lines: List[str] = []
    lines.append(f"# Context Snapshot (last {hours}h)\n")
    lines.append(f"Workspace: `{WORKSPACE}`\n")
    lines.append(f"Total files: {len(files)}\n")

    grouped = group_by_category(files)
    order = ["code", "scripts", "docs", "outputs", "configs"]

    for cat in order:
        group = grouped.get(cat, [])
        if not group:
            continue
        lines.append(f"## {cat} ({len(group)})\n")
        # Limit list size per section to keep it readable
        for f in group[:50]:
            size_kb = max(1, f.size // 1024)
            lines.append(f"- `{f.rel}`  (📦 {size_kb} KB, 🕒 {f.mtime_iso()})")
        if len(group) > 50:
            lines.append(f"- ... and {len(group) - 50} more")
        lines.append("")

    with out.open("w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))
    return out


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    args = ap.parse_args(argv)

    files = collect_files(args.hours)
    json_path = write_json(files)
    md_path = write_md(files, args.hours)

    print(json_path)
    print(md_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
