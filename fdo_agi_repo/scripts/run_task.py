from __future__ import annotations
import argparse, uuid, json, os
import os, sys
HERE = os.path.dirname(__file__)
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from orchestrator.pipeline import run_task

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--title", required=True)
    p.add_argument("--goal", required=True)
    p.add_argument("--scope", default="doc")
    args = p.parse_args()

    spec = {
        "task_id": str(uuid.uuid4()),
        "title": args.title,
        "goal": args.goal,
        "constraints": [],
        "inputs": {},
        "scope": args.scope,
        "permissions": ["READ","WRITE"],
        "evidence_required": True,
    }
    tool_cfg = {
        "rag": {"index_path": "memory/vectorstore", "top_k": 6},
        "fileio": {"sandbox_root": "sandbox/"}
    }
    result = run_task(tool_cfg, spec)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
