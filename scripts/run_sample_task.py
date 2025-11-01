import uuid
import time
from pathlib import Path


def main():
    from fdo_agi_repo.orchestrator import pipeline

    task_id = f"runtime-test-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    spec = {
        "task_id": task_id,
        "title": "Sample Orchestrator Run",
        "goal": "Run a lightweight task to exercise policy and closed-loop logging.",
        "constraints": [],
        "inputs": {},
        "scope": "analysis",
        "permissions": ["READ"],
        "evidence_required": False,
    }

    print(f"[sample] starting task: {task_id}")
    result = pipeline.run_task({}, spec)
    print(f"[sample] status: {result.get('status')}\n")

    # Hints for the operator
    repo_root = Path(__file__).resolve().parents[1]
    ledger = repo_root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
    if ledger.exists():
        print(f"[sample] ledger updated: {ledger}")
    else:
        print("[sample] ledger not found (first run?).")


if __name__ == "__main__":
    main()

