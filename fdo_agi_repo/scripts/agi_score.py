from __future__ import annotations
import os
import json
from typing import Any, Dict, List, Tuple, Set
from datetime import datetime

HERE = os.path.dirname(__file__)
REPO = os.path.dirname(HERE)

import sys
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from orchestrator.memory_bus import LEDGER_PATH, COORD_PATH

OUTPUT_DIR = os.path.join(REPO, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def _recent_task_ids(coord: List[Dict[str, Any]], limit: int = 50) -> List[str]:
    ids: List[str] = []
    for r in reversed(coord):
        if r.get("event") == "task_end":
            tid = r.get("task_id")
            if tid and tid not in ids:
                ids.append(tid)
            if len(ids) >= limit:
                break
    return list(reversed(ids))


def _collect(ledger: List[Dict[str, Any]], tids: Set[str]) -> Dict[str, Dict[str, Any]]:
    info: Dict[str, Dict[str, Any]] = {t: {"learning": False, "second_pass": False, "evidence_ok": None, "should_delegate": None} for t in tids}
    for r in ledger:
        t = r.get("task_id")
        if t not in tids:
            continue
        ev = r.get("event")
        if ev == "learning":
            info[t]["learning"] = True
        elif ev == "second_pass":
            info[t]["second_pass"] = True
        elif ev == "eval":
            try:
                info[t]["evidence_ok"] = bool((r.get("eval") or {}).get("evidence_ok"))
            except Exception:
                pass
        elif ev == "meta_cognition":
            try:
                info[t]["should_delegate"] = bool(r.get("should_delegate"))
            except Exception:
                pass
    return info


def compute_scores(info: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    n = max(1, len(info))
    learning_rate = sum(1 for v in info.values() if v["learning"]) / n
    adaptation_rate = sum(1 for v in info.values() if v["second_pass"]) / n
    evidence_rate = sum(1 for v in info.values() if v.get("evidence_ok") is True) / n
    # autonomy: 위임 권고가 없을수록 높음 (없음=True)
    no_delegate = sum(1 for v in info.values() if v.get("should_delegate") in (False, None)) / n
    autonomy = no_delegate

    # 가중 합산 (단순 휴리스틱)
    overall = 0.35 * autonomy + 0.35 * learning_rate + 0.20 * adaptation_rate + 0.10 * evidence_rate

    return {
        "tasks_considered": n,
        "autonomy": round(autonomy, 4),
        "learning_rate": round(learning_rate, 4),
        "adaptation_rate": round(adaptation_rate, 4),
        "evidence_rate": round(evidence_rate, 4),
        "agi_score": round(overall, 4),
    }


def main():
    coord = _read_jsonl(COORD_PATH)
    ledger = _read_jsonl(LEDGER_PATH)
    tids = set(_recent_task_ids(coord, limit=50))
    info = _collect(ledger, tids)
    scores = compute_scores(info)

    out_json = os.path.join(OUTPUT_DIR, "agi_score_summary.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

    # Write markdown report
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md = [
        f"# AGI Score Report ({ts})",
        "",
        f"- Tasks considered: {scores['tasks_considered']}",
        f"- Autonomy: {scores['autonomy']}",
        f"- Learning rate: {scores['learning_rate']}",
        f"- Adaptation rate: {scores['adaptation_rate']}",
        f"- Evidence rate: {scores['evidence_rate']}",
        f"- Overall AGI Score: {scores['agi_score']}",
        "",
    ]
    out_md = os.path.join(OUTPUT_DIR, "agi_score_report.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(json.dumps(scores, ensure_ascii=False))


if __name__ == "__main__":
    main()
