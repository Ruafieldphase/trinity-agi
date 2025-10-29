from __future__ import annotations
import os
import json
import time
import uuid
from typing import Any, Dict, List, Tuple, Optional
import argparse

# Ensure we can import orchestrator modules when run as a script
HERE = os.path.dirname(__file__)
REPO = os.path.dirname(HERE)
import sys
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from orchestrator.pipeline import run_task
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


def _event_ts(records: List[Dict[str, Any]], task_id: str, event: str) -> float | None:
    for r in records:
        if r.get("event") == event and r.get("task_id") == task_id:
            return float(r.get("ts", 0))
    return None


def _eval_quality(records: List[Dict[str, Any]], task_id: str) -> float | None:
    for r in records:
        if r.get("event") == "eval" and r.get("task_id") == task_id:
            val = (r.get("eval") or {}).get("quality")
            if val is None:
                return None
            try:
                return float(val)
            except Exception:
                return None
    return None


def _pearson_corr(xs: List[float], ys: List[float]) -> Optional[float]:
    n = len(xs)
    if n < 2 or len(ys) != n:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x <= 0 or var_y <= 0:
        return None
    cov = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    try:
        return cov / (var_x ** 0.5 * var_y ** 0.5)
    except ZeroDivisionError:
        return None


def _agg_stats(durations: List[float], user_chars: List[float], oks: List[bool]) -> Dict[str, Any]:
    cnt = len(durations)
    if cnt == 0:
        return {
            "count": 0,
            "ok_count": 0,
            "success_rate": None,
            "total_duration_sec": 0.0,
            "avg_duration_sec": None,
            "max_duration_sec": None,
            "avg_user_chars": None,
            "max_user_chars": None,
            "corr_userchars_duration": None,
        }
    ok_count = sum(1 for b in oks if b)
    total = float(sum(durations))
    avg_d = total / cnt
    max_d = max(durations)
    avg_u = (sum(user_chars) / cnt) if user_chars else None
    max_u = max(user_chars) if user_chars else None
    corr = _pearson_corr([float(x) for x in user_chars], [float(d) for d in durations]) if user_chars else None
    return {
        "count": cnt,
        "ok_count": ok_count,
        "success_rate": (ok_count / cnt) if cnt else None,
        "total_duration_sec": round(total, 6),
        "avg_duration_sec": round(avg_d, 6),
        "max_duration_sec": round(max_d, 6),
        "avg_user_chars": round(avg_u, 2) if avg_u is not None else None,
        "max_user_chars": max_u,
        "corr_userchars_duration": None if corr is None else round(corr, 4),
    }


def _persona_llm_aggregate(records: List[Dict[str, Any]], task_id: str) -> Dict[str, Any]:
    # Collect persona_llm_end events for this task_id
    events: List[Dict[str, Any]] = [
        r for r in records
        if r.get("event") == "persona_llm_end" and r.get("task_id") == task_id
    ]
    if not events:
        return {"has_events": False}

    per_persona: Dict[str, Dict[str, Any]] = {}
    per_pass: Dict[str, Dict[str, Any]] = {}
    all_durations: List[float] = []
    all_user_chars: List[float] = []
    all_oks: List[bool] = []

    def ensure_bucket(d: Dict[str, Any], key: str) -> Dict[str, Any]:
        if key not in d:
            d[key] = {"durations": [], "user_chars": [], "oks": [], "attempts": [], "errors": []}
        return d[key]

    for r in events:
        persona = r.get("persona") or r.get("role") or "unknown"
        dur = float(r.get("duration_sec") or 0.0)
        ok = bool(r.get("ok"))
        user_chars = 0.0
        pc = r.get("prompt_chars") or {}
        try:
            user_chars = float(pc.get("user") or 0)
        except Exception:
            try:
                user_chars = float(r.get("prompt_user_chars") or 0)
            except Exception:
                user_chars = 0.0
        pass_key = str(r.get("pass")) if r.get("pass") is not None else None
        aval = r.get("attempt")
        try:
            attempt_idx = int(str(aval)) if aval is not None else 0
        except Exception:
            attempt_idx = 0
        err_txt = r.get("error")

        # overall accumulators
        all_durations.append(dur)
        all_user_chars.append(user_chars)
        all_oks.append(ok)

        # persona bucket
        b = ensure_bucket(per_persona, persona)
        b["durations"].append(dur)
        b["user_chars"].append(user_chars)
        b["oks"].append(ok)
        b["attempts"].append(attempt_idx)
        if err_txt:
            b["errors"].append(str(err_txt))

        # pass bucket
        if pass_key is not None:
            pb = ensure_bucket(per_pass, pass_key)
            pb["durations"].append(dur)
            pb["user_chars"].append(user_chars)
            pb["oks"].append(ok)

    # summarize
    def _hist(ints: List[int]) -> Dict[str, int]:
        h: Dict[str, int] = {}
        for i in ints:
            key = str(i)
            h[key] = h.get(key, 0) + 1
        return dict(sorted(h.items(), key=lambda kv: int(kv[0])))

    def _top_errors(errs: List[str], topn: int = 5) -> List[Tuple[str, int]]:
        # bucket by error token before ':' if present
        counts: Dict[str, int] = {}
        for e in errs:
            token = e.split(":", 1)[0].strip() if ":" in e else e.strip()
            token = token or "(unknown)"
            counts[token] = counts.get(token, 0) + 1
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:topn]

    summary_per_persona: Dict[str, Any] = {}
    for k, v in per_persona.items():
        base = _agg_stats(v["durations"], v["user_chars"], v["oks"])
        base["attempt_hist"] = _hist(v["attempts"]) if v.get("attempts") else {}
        # success attempt histogram: only attempts where ok True
        succ_attempts = [v["attempts"][i] for i in range(len(v["attempts"])) if v["oks"][i]] if v.get("attempts") else []
        base["success_attempt_hist"] = _hist(succ_attempts) if succ_attempts else {}
        base["error_top"] = _top_errors(v.get("errors", []))
        summary_per_persona[k] = base
    summary_per_pass: Dict[str, Any] = {
        k: _agg_stats(v["durations"], v["user_chars"], v["oks"]) for k, v in per_pass.items()
    } if per_pass else {}

    overall = _agg_stats(all_durations, all_user_chars, all_oks)

    return {
        "has_events": True,
        "overall": overall,
        "by_persona": summary_per_persona,
        "by_pass": summary_per_pass,
    }


def profile_once(force_low_quality: bool = False, include_persona_llm: bool = True) -> Dict[str, Any]:
    task_id = str(uuid.uuid4())
    spec = {
        "task_id": task_id,
        "title": "AGI 성능 프로파일링",
        "goal": "로컬 자료를 근거로 간단한 제안서를 작성하라",
        "constraints": ["요약은 5줄 이내"],
        "inputs": {},
        "scope": "doc",
        "permissions": ["READ"],
        "evidence_required": True,
    }

    # Toggle environment to influence behavior
    old_rag = os.environ.get("RAG_DISABLE")
    old_corr = os.environ.get("CORRECTIONS_ENABLED")
    try:
        if force_low_quality:
            os.environ["RAG_DISABLE"] = "1"
            os.environ["CORRECTIONS_ENABLED"] = "true"
        t0 = time.perf_counter()
        result = run_task(tool_cfg={}, spec=spec)
        t1 = time.perf_counter()
    finally:
        # restore env
        if old_rag is None:
            os.environ.pop("RAG_DISABLE", None)
        else:
            os.environ["RAG_DISABLE"] = old_rag
        if old_corr is None:
            os.environ.pop("CORRECTIONS_ENABLED", None)
        else:
            os.environ["CORRECTIONS_ENABLED"] = old_corr

    ledger = _read_jsonl(LEDGER_PATH)
    coord = _read_jsonl(COORD_PATH)

    ts_start = None
    for r in coord:
        if r.get("event") == "task_start" and (r.get("task") or {}).get("task_id") == task_id:
            ts_start = float(r.get("ts", 0))
            break

    ts_run_config = _event_ts(ledger, task_id, "run_config")
    ts_meta = _event_ts(ledger, task_id, "meta_cognition")
    ts_eval = _event_ts(ledger, task_id, "eval")
    ts_second = _event_ts(ledger, task_id, "second_pass")

    ts_end = None
    for r in coord[::-1]:
        if r.get("event") == "task_end" and r.get("task_id") == task_id:
            ts_end = float(r.get("ts", 0))
            break

    quality = _eval_quality(ledger, task_id)

    profile = {
        "task_id": task_id,
        "force_low_quality": force_low_quality,
        "wall_clock_seconds": round(t1 - t0, 6),
        "segments": {}
    }

    def add_seg(name: str, t_a: float | None, t_b: float | None):
        if t_a is None or t_b is None:
            profile["segments"][name] = None
        else:
            profile["segments"][name] = max(0.0, float(t_b - t_a))

    add_seg("start_to_run_config", ts_start, ts_run_config)
    add_seg("run_config_to_meta", ts_run_config, ts_meta)
    add_seg("meta_to_eval", ts_meta, ts_eval)
    add_seg("eval_to_second_pass", ts_eval, ts_second)
    add_seg("eval_to_end" if ts_second is None else "second_pass_to_end", ts_eval if ts_second is None else ts_second, ts_end)

    profile["second_pass"] = bool(ts_second)
    profile["quality"] = quality

    # persona LLM aggregation (if requested and events exist)
    if include_persona_llm:
        persona_agg = _persona_llm_aggregate(ledger, task_id)
        if persona_agg.get("has_events"):
            profile["persona_llm"] = persona_agg

    out_path = os.path.join(OUTPUT_DIR, f"perf_profile_{task_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    print(json.dumps(profile, ensure_ascii=False))
    return profile


def main():
    parser = argparse.ArgumentParser(description="AGI 성능 프로파일러")
    parser.add_argument("--single-run", action="store_true", help="한 번만 실행합니다 (기본: 일반+저품질 2회)")
    parser.add_argument("--force-low-quality", action="store_true", help="저품질(학습/세컨드패스 유도) 한 번 실행")
    parser.add_argument("--no-persona-llm", action="store_true", help="퍼소나 LLM 집계를 비활성화")
    args = parser.parse_args()

    include_persona_llm = not args.no_persona_llm

    if args.single_run:
        mode = "forced low-quality" if args.force_low_quality else "normal"
        print(f"-- Profiling {mode} run --")
        profile_once(force_low_quality=args.force_low_quality, include_persona_llm=include_persona_llm)
        return

    # default: run both
    print("-- Profiling normal run --")
    profile_once(force_low_quality=False, include_persona_llm=include_persona_llm)
    print("-- Profiling forced low-quality (replan) run --")
    profile_once(force_low_quality=True, include_persona_llm=include_persona_llm)


if __name__ == "__main__":
    main()
