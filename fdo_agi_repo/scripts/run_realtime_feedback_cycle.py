#!/usr/bin/env python3
"""
Execute a single realtime feedback loop cycle to generate monitoring artifacts.

This helper pulls the latest gateway optimization metrics, triggers a learning
cycle (with threshold lowered to 1 for testing), and appends a summary entry to
`outputs/realtime_feedback_loop.jsonl`.  It is intended to support Phase 9 E2E
verification.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "fdo_agi_repo"))

from orchestrator.realtime_feedback_loop import RealtimeFeedbackLoop


def main() -> None:
    workspace_root = PROJECT_ROOT.resolve()
    log_path = workspace_root / "outputs" / "realtime_feedback_loop.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    loop = RealtimeFeedbackLoop(
        workspace_root=workspace_root,
        collection_interval=60,
        learning_threshold=1,
    )

    entry = {"timestamp": datetime.now().isoformat()}
    metrics = loop.collect_metrics()

    if metrics:
        entry["status"] = "metrics_collected"
        entry["metrics"] = metrics

        loop.add_to_buffer(metrics)
        learning_result = loop.learn_from_metrics()
        entry["learning_result"] = learning_result
        entry["learning_triggered"] = learning_result.get("status") != "no_data"
    else:
        entry["status"] = "no_metrics_available"
        entry["learning_triggered"] = False

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"✅ Feedback loop cycle recorded to {log_path}")


if __name__ == "__main__":
    main()
