from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
import sys
from statistics import mean
from workspace_root import get_workspace_root


def load_json(p: Path):
    # Use utf-8-sig to be resilient to BOM in generated files
    with p.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def main():
    ws = get_workspace_root()
    metrics_path = ws / "outputs" / "monitoring_metrics_latest.json"
    history_path = ws / "outputs" / "replan_rate_history.jsonl"

    if not metrics_path.exists():
        print(json.dumps({
            "ok": False,
            "reason": f"metrics_not_found: {str(metrics_path)}",
        }, ensure_ascii=False))
        sys.exit(0)

    metrics = load_json(metrics_path)

    # Try a few plausible locations for the rate and timestamp
    replan_rate = None
    ts = None
    try:
        replan_rate = float(metrics["AGI"]["ReplanRate"])  # percent
    except Exception:
        pass
    if replan_rate is None:
        # Some builds might use snake_case
        try:
            replan_rate = float(metrics["agi"]["replan_rate"])  # type: ignore[index]
        except Exception:
            pass

    ts = (
        metrics.get("Generated")
        or (metrics.get("AGI", {}).get("CollectionTime"))
        or now_iso()
    )

    if replan_rate is None:
        print(json.dumps({
            "ok": False,
            "reason": "replan_rate_missing",
        }, ensure_ascii=False))
        sys.exit(0)

    # Append to history (ensure directory)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": ts, "replan_rate": replan_rate}
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Load recent window for simple trend check
    window = []
    try:
        with history_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    window.append(float(obj.get("replan_rate")))
                except Exception:
                    continue
    except Exception:
        pass

    last_n = 6
    recent = window[-last_n:]
    trend = "unknown"
    delta = None
    if len(recent) >= 2:
        prev_mean = mean(recent[:-1]) if len(recent) > 2 else recent[0]
        delta = recent[-1] - prev_mean
        # Simple thresholds to avoid flapping on tiny noise
        if abs(delta) < 0.5:
            trend = "flat"
        elif delta < 0:
            trend = "down"
        else:
            trend = "up"

    print(json.dumps({
        "ok": True,
        "timestamp": ts,
        "replan_rate": replan_rate,
        "trend": trend,
        "delta_vs_prev_mean": delta,
        "window_size": len(recent),
        "history_file": str(history_path),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
