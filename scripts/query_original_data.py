#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import List

from original_data_index import load_index, search_index


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Query original_data index and print results as JSON.")
    ap.add_argument("--index", default=os.path.join("outputs", "original_data_index.json"), help="Path to index JSON")
    ap.add_argument("--query", "-q", default=None, help="Keyword(s), space/comma separated")
    ap.add_argument("--tags", default=None, help="Tag filters (comma/space separated)")
    ap.add_argument("--ext", default=None, help="Extensions to include (e.g., md,py,csv). Comma/space separated")
    ap.add_argument("--since-days", type=int, default=None, help="Only include items modified within last N days")
    ap.add_argument("--top", type=int, default=20, help="Max results to return")
    ap.add_argument("--md", action="store_true", help="Print a short Markdown list instead of JSON")
    args = ap.parse_args(argv)

    tags = None
    if args.tags:
        tags = [t for t in re_split(args.tags)]
    exts = None
    if args.ext:
        exts = [t for t in re_split(args.ext)]

    try:
        items = load_index(args.index)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2

    results = search_index(items, query=args.query, tags=tags, exts=exts, since_days=args.since_days, top=args.top)

    if args.md:
        for e in results:
            rel = e.get("relative_path") or e.get("path") or e.get("file") or ""
            title = e.get("name") or os.path.basename(rel)
            ext = e.get("ext", "")
            print(f"- [{title}]({rel}) ({ext})")
        return 0

    print(json.dumps({"count": len(results), "items": results}, ensure_ascii=False, indent=2))
    return 0


def re_split(s: str):
    import re

    for p in re.split(r"[,;\s]+", s.strip()):
        if p:
            yield p


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
