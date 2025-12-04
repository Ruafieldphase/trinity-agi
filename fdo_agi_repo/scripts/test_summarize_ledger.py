from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterable, Dict, Any

HERE = Path(__file__).parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from scripts import summarize_ledger  # type: ignore  # noqa: E402


def _write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def scenario_default_excludes() -> bool:
    now = time.time()
    ledger_records = [
        {"event": "meta_cognition", "task_id": "integration_test_demo", "confidence": 0.15, "ts": now},
        {"event": "meta_cognition", "task_id": "prod_task_alpha", "confidence": 0.92, "ts": now},
        {"event": "eval", "task_id": "integration_test_demo", "quality": 0.25, "ts": now, "eval": {"quality": 0.25}},
        {"event": "eval", "task_id": "prod_task_alpha", "quality": 0.88, "ts": now, "eval": {"quality": 0.88}},
    ]
    coord_records = [
        {"event": "task_start", "task_id": "integration_test_demo", "ts": now},
        {"event": "task_start", "task_id": "prod_task_alpha", "ts": now},
        {"event": "task_end", "task_id": "prod_task_alpha", "ts": now},
    ]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        ledger_path = tmp_path / "resonance_ledger.jsonl"
        coord_path = tmp_path / "coordinate.jsonl"
        _write_jsonl(ledger_path, ledger_records)
        _write_jsonl(coord_path, coord_records)

        original_ledger = summarize_ledger.LEDGER_PATH
        original_coord = summarize_ledger.COORD_PATH
        try:
            summarize_ledger.LEDGER_PATH = str(ledger_path)
            summarize_ledger.COORD_PATH = str(coord_path)

            filtered = summarize_ledger.summarize(last_hours=2.0)
            raw = summarize_ledger.summarize(last_hours=2.0, include_default_excludes=False)

        finally:
            summarize_ledger.LEDGER_PATH = original_ledger
            summarize_ledger.COORD_PATH = original_coord

    def _event_count(summary: Dict[str, Any], event_name: str) -> int:
        return int(summary["counts"]["events"].get(event_name, 0))

    filtered_count = _event_count(filtered, "meta_cognition")
    raw_count = _event_count(raw, "meta_cognition")

    checks = [
        ("filtered_meta_count", filtered_count == 1),
        ("raw_meta_count", raw_count == 2),
        ("filtered_confidence", abs(filtered["metrics"]["avg_confidence"] - 0.92) < 1e-6),
        ("raw_confidence", abs(raw["metrics"]["avg_confidence"] - ((0.15 + 0.92) / 2)) < 1e-6),
        ("exclude_prefixes_present", "integration_test_" in filtered["notes"]["exclude_prefixes"]),
        ("default_flag_filtered", filtered["notes"]["default_excludes_applied"] is True),
        ("default_flag_raw", filtered["notes"]["default_excludes_applied"] is True and raw["notes"]["default_excludes_applied"] is False),
    ]

    failures = [name for name, ok in checks if not ok]
    if failures:
        print("[summarize_ledger] FAIL:", ", ".join(failures))
        print("filtered:", json.dumps(filtered, ensure_ascii=False, indent=2))
        print("raw:", json.dumps(raw, ensure_ascii=False, indent=2))
        return False

    print("[summarize_ledger] default excludes scenario passed")
    return True


def main() -> None:
    results = [
        ("default_excludes", scenario_default_excludes()),
    ]
    failed = [name for name, ok in results if not ok]
    if failed:
        print("Summarize ledger tests FAILED:", ", ".join(failed))
        sys.exit(1)
    print("Summarize ledger tests PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
