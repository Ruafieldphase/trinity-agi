# -*- coding: utf-8 -*-
"""
Phase 4: Lightweight BQI Pattern Learner

- Mines resonance_ledger.jsonl to learn associations between goal keywords and BQI coordinates.
- Produces outputs/bqi_pattern_model.json with rules:
  {
    "meta": { ... },
    "priority_rules": { "keyword": delta[-1..+1] },
    "emotion_rules": { "keyword": { "emotion": weight[0..1], ... } },
    "rhythm_rules": { "keyword": { "rhythm": weight[0..1], ... } }
  }

No third-party dependencies required.
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Optional UTF-8 enforcement if module exists
try:
    # Try repo-local encoding helper if present
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import encoding_setup  # type: ignore # noqa: F401
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "memory" / "resonance_ledger.jsonl"
OUTPUTS_DIR = ROOT / "outputs"
MODEL_PATH = OUTPUTS_DIR / "bqi_pattern_model.json"

TOKEN_RE = re.compile(r"[A-Za-z0-9가-힣_]+", re.UNICODE)
STOPWORDS = set(
    [
        # Korean stopwords (minimal)
        "그리고", "그래서", "그러나", "하지만", "또는", "및", "좀", "매우", "보다", "수", "등", "것",
        "이번", "관련", "대해", "되는", "하는", "하기", "입니다", "입니다만", "에서", "으로", "이다",
        "어떻게", "무엇", "왜", "언제", "어디", "누가", "됨", "같은", "때문", "정도",
        # English
        "and", "or", "but", "the", "a", "an", "to", "of", "in", "on", "for", "with", "by",
        "at", "from", "as", "is", "are", "be", "this", "that", "it", "we", "you",
    ]
)

def safe_read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue

def tokenize(text: str) -> List[str]:
    tokens = [t.lower() for t in TOKEN_RE.findall(text or "")]
    return [t for t in tokens if t not in STOPWORDS and len(t) >= 2]

def collect_task_samples(ledger_iter: Iterable[Dict[str, Any]]):
    """Collect per-task info: goal text, last BQI, outcome success/failure.

    Returns dict task_id -> {
      'goal': str,
      'bqi': {'priority': int, 'emotion': [str], 'rhythm': str} | None,
      'success': bool | None
    }
    """
    tasks: Dict[str, Dict[str, Any]] = {}

    for ev in ledger_iter:
        task_id = ev.get("task_id") or ev.get("taskId") or ev.get("task")
        if not task_id:
            continue
        rec = tasks.setdefault(task_id, {"goal": None, "bqi": None, "success": None})

        # goal text capture (prefer earliest start)
        if rec["goal"] is None:
            goal = (
                ev.get("goal")
                or ev.get("question")
                or ev.get("query")
                or ev.get("message")
            )
            if isinstance(goal, str) and goal.strip():
                rec["goal"] = goal.strip()

        # bqi capture
        bqi = ev.get("bqi") or ev.get("bqi_coord") or ev.get("bqiCoordinate")
        if isinstance(bqi, dict):
            # Normalize fields
            pr = bqi.get("priority")
            em = bqi.get("emotion") or bqi.get("emotions")
            rh = bqi.get("rhythm")
            if isinstance(pr, (int, float)):
                pr = int(pr)
            if isinstance(em, str):
                em = [em]
            if rh is None:
                rh = "exploration"
            rec["bqi"] = {"priority": pr or 2, "emotion": em or [], "rhythm": rh}

        # success capture
        event = (ev.get("event") or ev.get("type") or "").lower()
        quality = ev.get("quality") or ev.get("score")
        evidence_ok = ev.get("evidence_ok") or ev.get("evidence") == "ok"
        error_flag = bool(ev.get("error") or ev.get("exception"))

        if quality is not None:
            try:
                q = float(quality)
                if q >= 0.8:
                    rec["success"] = True
                elif q < 0.4:
                    rec["success"] = False
            except Exception:
                pass
        if event in {"task_complete", "completed", "success"}:
            if rec["success"] is None:
                rec["success"] = True
        if evidence_ok:
            rec["success"] = True
        if error_flag or event in {"error", "failed", "exception"}:
            rec["success"] = False

    return tasks

def learn_rules(tasks: Dict[str, Dict[str, Any]]):
    # Use only successful tasks with goal and bqi
    samples = [r for r in tasks.values() if r.get("success") and r.get("goal") and r.get("bqi")]

    kw_priority_values: Dict[str, List[int]] = defaultdict(list)
    kw_emotions: Dict[str, Counter] = defaultdict(Counter)
    kw_rhythms: Dict[str, Counter] = defaultdict(Counter)

    for rec in samples:
        goal = rec["goal"]
        bqi = rec["bqi"] or {}
        priority = int(bqi.get("priority", 2) or 2)
        emotions = list(bqi.get("emotion", []) or [])
        rhythm = str(bqi.get("rhythm", "exploration") or "exploration")

        keywords = tokenize(goal)
        if not keywords:
            continue
        for kw in set(keywords):  # de-dup within a single goal
            kw_priority_values[kw].append(priority)
            for em in emotions:
                if isinstance(em, str) and em:
                    kw_emotions[kw][em.lower()] += 1
            kw_rhythms[kw][rhythm.lower()] += 1

    # Compute global mean priority
    all_priorities = [p for vals in kw_priority_values.values() for p in vals]
    global_mean = sum(all_priorities) / len(all_priorities) if all_priorities else 2.0

    # priority delta mapping -> -1, 0, +1
    priority_rules: Dict[str, int] = {}
    for kw, vals in kw_priority_values.items():
        if not vals:
            continue
        mean_p = sum(vals) / len(vals)
        delta = mean_p - global_mean
        if delta >= 0.5:
            priority_rules[kw] = +1
        elif delta <= -0.5:
            priority_rules[kw] = -1
        else:
            # Only include strong signals; skip zeros to keep model small
            continue

    def normalize_counter(c: Counter) -> Dict[str, float]:
        total = sum(c.values())
        if total <= 0:
            return {}
        # Keep top-3 per keyword
        top = c.most_common(3)
        return {k: round(v / float(total), 3) for k, v in top if v > 0}

    emotion_rules: Dict[str, Dict[str, float]] = {
        kw: normalize_counter(cnt)
        for kw, cnt in kw_emotions.items()
        if cnt and sum(cnt.values()) >= 2  # need at least 2 signals
    }
    rhythm_rules: Dict[str, Dict[str, float]] = {
        kw: normalize_counter(cnt)
        for kw, cnt in kw_rhythms.items()
        if cnt and sum(cnt.values()) >= 2
    }

    return {
        "priority_rules": priority_rules,
        "emotion_rules": emotion_rules,
        "rhythm_rules": rhythm_rules,
        "samples_used": len(samples),
        "global_mean_priority": round(global_mean, 3),
    }


def main():
    start = time.time()
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    if not LEDGER_PATH.exists():
        model = {
            "meta": {
                "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "duration_sec": 0,
                "note": "ledger not found; created empty model",
            },
            "priority_rules": {},
            "emotion_rules": {},
            "rhythm_rules": {},
            "samples_used": 0,
            "global_mean_priority": 2.0,
        }
        MODEL_PATH.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[Phase4] No ledger found. Wrote empty model to {MODEL_PATH}")
        return 0

    tasks = collect_task_samples(safe_read_jsonl(LEDGER_PATH))
    stats = learn_rules(tasks)

    model = {
        "meta": {
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "duration_sec": round(time.time() - start, 3),
            "ledger_path": str(LEDGER_PATH),
            "task_count": len(tasks),
        },
        **stats,
    }

    MODEL_PATH.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[Phase4] BQI pattern model generated:")
    print(f"  - tasks scanned: {len(tasks)}")
    print(f"  - samples used: {stats['samples_used']}")
    print(f"  - priority rules: {len(stats['priority_rules'])}")
    print(f"  - emotion rules: {len(stats['emotion_rules'])}")
    print(f"  - rhythm rules: {len(stats['rhythm_rules'])}")
    print(f"  -> saved: {MODEL_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
