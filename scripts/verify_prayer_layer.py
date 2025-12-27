#!/usr/bin/env python3
"""
Verify that the prayer layer routes to rest/continue based on score/ATP.
"""

from pathlib import Path
import json
import time
import sys

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.append(str(WORKSPACE_ROOT))

from scripts.rhythm_think import RhythmThinker


def main() -> int:
    cases = [
        {
            "name": "low_score",
            "state": {"score": 10, "atp": 50},
            "expect": "Null State (Total Reset Required)",
        },
        {
            "name": "low_atp",
            "state": {"score": 50, "atp": 10},
            "expect": "Energy Restoration (Sleep)",
        },
        {
            "name": "normal",
            "state": {"score": 50, "atp": 50},
            "expect": "Flow Alignment (Continue)",
        },
    ]

    results = []
    for case in cases:
        got = RhythmThinker._prayer_response_for_state(None, case["state"])
        ok = got == case["expect"]
        results.append(
            {
                "name": case["name"],
                "state": case["state"],
                "expected": case["expect"],
                "actual": got,
                "ok": ok,
            }
        )

    ok_all = all(r["ok"] for r in results)
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ok": ok_all,
        "results": results,
    }

    workspace = Path(__file__).parent.parent
    out_path = workspace / "outputs" / "prayer_layer_check_latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Prayer layer check:", "OK" if ok_all else "FAIL")
    for r in results:
        status = "OK" if r["ok"] else "FAIL"
        print(f"- {r['name']}: {status} ({r['actual']})")

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
