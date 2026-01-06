#!/usr/bin/env python3
"""
Show autonomous goal gate status and recent audit entries.

Usage:
  python scripts/show_autonomous_goal_gate_status.py --tail 5
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def tail_audit(path: Path, tail: int) -> List[Dict[str, Any]]:
    if not path.exists() or tail <= 0:
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    out: List[Dict[str, Any]] = []
    for line in lines[-tail:]:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Show autonomous goal gate status")
    from workspace_root import get_workspace_root
    parser.add_argument("--workspace", type=str, default=str(get_workspace_root()), help="Workspace root")
    parser.add_argument("--tail", type=int, default=5, help="Audit tail count")
    args = parser.parse_args()

    workspace = Path(args.workspace)
    outputs = workspace / "outputs"

    status_path = outputs / "autonomous_goal_gate_status.json"
    audit_path = outputs / "autonomous_goal_gate_audit.jsonl"

    status = load_json(status_path)
    audits = tail_audit(audit_path, args.tail)

    print("=== Gate Status ===")
    if status:
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        print(f"(missing) {status_path}")

    print("\n=== Gate Audit (last %d) ===" % args.tail)
    if audits:
        print(json.dumps(audits, ensure_ascii=False, indent=2))
    else:
        print(f"(no audit entries found in {audit_path})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
