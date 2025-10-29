from __future__ import annotations
import os, sys, time, json, uuid
from pathlib import Path

# Ensure repo root on sys.path
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from orchestrator.pipeline import run_task

LEDGER = REPO / "memory" / "resonance_ledger.jsonl"

def count_second_pass() -> int:
    if not LEDGER.exists():
        return 0
    cnt = 0
    with LEDGER.open("r", encoding="utf-8") as f:
        for line in f:
            if "\"second_pass\"" in line:
                cnt += 1
    return cnt

def do_run(corrections_enabled: bool) -> dict:
    os.environ["PYTHONPATH"] = str(REPO)
    os.environ["RAG_DISABLE"] = "1"  # force no citations
    os.environ["CORRECTIONS_ENABLED"] = "1" if corrections_enabled else "0"

    before = count_second_pass()

    spec = {
        "task_id": str(uuid.uuid4()),
        "title": "demo",
        "goal": "force replan (no citations)",
        "constraints": [],
        "inputs": {},
        "scope": "doc",
        "permissions": ["READ","WRITE"],
        "evidence_required": True,
    }
    tool_cfg = {
        "rag": {"index_path": "memory/vectorstore", "top_k": 6},
        "fileio": {"sandbox_root": "sandbox/"}
    }
    t0 = time.time()
    _ = run_task(tool_cfg, spec)
    elapsed_ms = int((time.time() - t0) * 1000)
    after = count_second_pass()

    return {
        "CorrectionsEnabled": corrections_enabled,
        "ElapsedMs": elapsed_ms,
        "SecondPassOccurred": (after - before) > 0,
        "SecondPassDelta": after - before,
    }


def main() -> int:
    r1 = do_run(False)
    r2 = do_run(True)

    print(json.dumps({"off": r1, "on": r2, "ledger": str(LEDGER)}, ensure_ascii=False, indent=2))

    # Assert: off -> no second pass, on -> second pass
    if r1["SecondPassOccurred"]:
        print("[ASSERT] FAILED: second_pass occurred with corrections disabled.")
        return 2
    if not r2["SecondPassOccurred"]:
        print("[ASSERT] FAILED: second_pass did not occur with corrections enabled.")
        return 3
    print("[ASSERT] PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
