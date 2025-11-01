#!/usr/bin/env python3
import os
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

WORKSPACE = Path(__file__).resolve().parents[1]
OUTPUTS = WORKSPACE / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

INCLUDE_EXT = {"md", "json", "ps1", "py", "csv", "txt", "ipynb", "yml", "yaml"}
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".idea", ".vscode"}


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def should_skip_dir(p: Path) -> bool:
    name = p.name
    if name in EXCLUDE_DIRS:
        return True
    # skip hidden
    if name.startswith("."):
        return True
    return False


def main() -> int:
    items: List[Dict] = []

    for root, dirs, files in os.walk(WORKSPACE):
        # mutate dirs in-place to prune
        dirs[:] = [d for d in dirs if not should_skip_dir(Path(root) / d)]
        for fn in files:
            ext = Path(fn).suffix.lstrip(".").lower()
            if ext not in INCLUDE_EXT:
                continue
            full = Path(root) / fn
            rel = str(full.relative_to(WORKSPACE))
            try:
                st = full.stat()
            except FileNotFoundError:
                continue
            items.append({
                "relative_path": rel.replace("\\", "/"),
                "name": full.stem,
                "ext": ext,
                "size": st.st_size,
                "mtime_iso": iso(datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)),
                "tags": [ext] + [p.name for p in full.parents if p != WORKSPACE][-3:][::-1],
            })

    items.sort(key=lambda e: (e.get("ext", ""), e.get("relative_path", "")))
    out_json = OUTPUTS / "original_data_index.json"
    out_md = OUTPUTS / "original_data_index.md"

    with out_json.open("w", encoding="utf-8") as f:
        json.dump({"count": len(items), "items": items}, f, ensure_ascii=False, indent=2)

    with out_md.open("w", encoding="utf-8") as f:
        f.write(f"# Original Data Index (auto)\n\nTotal: {len(items)} files\n\n")
        cur_ext = None
        for e in items:
            ext = e.get("ext", "")
            if ext != cur_ext:
                cur_ext = ext
                f.write(f"\n## .{ext}\n\n")
            rel = e.get("relative_path", "")
            name = e.get("name", os.path.basename(rel))
            f.write(f"- [{name}]({rel}) ({ext})\n")

    print(f"Wrote {out_json} and {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
