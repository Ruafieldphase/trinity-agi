from __future__ import annotations
import json
import os
import sys
from typing import Any, Dict

HERE = os.path.dirname(__file__)
REPO = os.path.dirname(HERE)
OUTPUTS = os.path.join(REPO, "outputs")
LATEST_JSON = os.path.join(OUTPUTS, "ledger_summary_latest.json")

DEFAULTS = {
    "MIN_AVG_CONFIDENCE": 0.60,
    "MIN_AVG_QUALITY": 0.65,
    "MAX_SECOND_PASS_PER_TASK": 2.0,   # 평균 2회 이내 재시도 권장
    "MIN_COMPLETION_RATE": 0.90,
}


def _get_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception:
        return default


def load_latest() -> Dict[str, Any]:
    if not os.path.exists(LATEST_JSON):
        raise FileNotFoundError(f"Latest summary not found: {LATEST_JSON}")
    with open(LATEST_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    cfg = {
        "MIN_AVG_CONFIDENCE": _get_float("MIN_AVG_CONFIDENCE", DEFAULTS["MIN_AVG_CONFIDENCE"]),
        "MIN_AVG_QUALITY": _get_float("MIN_AVG_QUALITY", DEFAULTS["MIN_AVG_QUALITY"]),
        "MAX_SECOND_PASS_PER_TASK": _get_float("MAX_SECOND_PASS_PER_TASK", DEFAULTS["MAX_SECOND_PASS_PER_TASK"]),
        "MIN_COMPLETION_RATE": _get_float("MIN_COMPLETION_RATE", DEFAULTS["MIN_COMPLETION_RATE"]),
    }

    data = load_latest()
    metrics = data.get("metrics", {})
    notes = data.get("notes", {})
    default_applied = bool(notes.get("default_excludes_applied", False))
    exclude_prefixes = notes.get("exclude_prefixes", [])

    avg_conf = metrics.get("avg_confidence")
    avg_qual = metrics.get("avg_quality")
    sp_rate = metrics.get("second_pass_rate_per_task")
    comp_rate = metrics.get("completion_rate")

    failures = []
    if isinstance(avg_conf, (int, float)):
        if avg_conf < cfg["MIN_AVG_CONFIDENCE"]:
            failures.append(f"avg_confidence {avg_conf} < {cfg['MIN_AVG_CONFIDENCE']}")
    else:
        failures.append("avg_confidence missing")

    if avg_qual is None:
        failures.append("avg_quality missing")
    elif avg_qual < cfg["MIN_AVG_QUALITY"]:
        failures.append(f"avg_quality {avg_qual} < {cfg['MIN_AVG_QUALITY']}")

    if isinstance(sp_rate, (int, float)):
        if sp_rate > cfg["MAX_SECOND_PASS_PER_TASK"]:
            failures.append(f"second_pass_rate_per_task {sp_rate} > {cfg['MAX_SECOND_PASS_PER_TASK']}")
    else:
        failures.append("second_pass_rate_per_task missing")

    if isinstance(comp_rate, (int, float)):
        if comp_rate < cfg["MIN_COMPLETION_RATE"]:
            failures.append(f"completion_rate {comp_rate} < {cfg['MIN_COMPLETION_RATE']}")
    # completion_rate가 없을 수도 있으나, 스키마 보강 이후에는 보존됨

    if failures:
        print("HEALTH: FAIL")
        print(" - " + "\n - ".join(failures))
        if not default_applied:
            print("NOTE: ledger summary generated without default excludes (--no-default-excludes).")
        return 1

    print("HEALTH: PASS")
    print(
        json.dumps(
            {
                "avg_confidence": avg_conf,
                "avg_quality": avg_qual,
                "second_pass_rate_per_task": sp_rate,
                "completion_rate": comp_rate,
                "thresholds": cfg,
                "default_excludes_applied": default_applied,
                "exclude_prefixes": exclude_prefixes,
            },
            ensure_ascii=False,
        )
    )
    if not default_applied:
        print("NOTE: ledger summary generated without default excludes (--no-default-excludes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
