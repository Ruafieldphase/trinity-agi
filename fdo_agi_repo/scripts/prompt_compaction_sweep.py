from __future__ import annotations
import os
import json
import time
import argparse
from typing import Any, Dict, List

# Ensure imports
import sys
HERE = os.path.dirname(__file__)
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from scripts.perf_profile import profile_once  # reuse existing profiler

OUTPUT_DIR = os.path.join(REPO, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _run_with_env(env_updates: Dict[str, str]) -> Dict[str, Any]:
    # backup
    backup = {k: os.environ.get(k) for k in env_updates.keys()}
    try:
        for k, v in env_updates.items():
            os.environ[k] = str(v)
        return profile_once(force_low_quality=False, include_persona_llm=True)
    finally:
        for k, old in backup.items():
            if old is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = old


def main():
    p = argparse.ArgumentParser(description="Prompt compaction sweep")
    p.add_argument("--synth-values", type=str, default="1200,1000",
                   help="Comma-separated values for SYNTHESIS_SECTION_MAX_CHARS (default: 1200,1000)")
    p.add_argument("--thesis-values", type=str, default="1000",
                   help="Comma-separated values for THESIS_LEARNING_MAX_CHARS (default: 1000)")
    p.add_argument("--anti-values", type=str, default="1200",
                   help="Comma-separated values for ANTITHESIS_SOURCE_MAX_CHARS (default: 1200)")
    p.add_argument("--repeats", type=int, default=1, help="각 조합을 반복 실행할 횟수 (기본 1)")
    p.add_argument("--dryrun", action="store_true", help="Print planned runs without executing")
    args = p.parse_args()

    synth_vals = [v.strip() for v in args.synth_values.split(",") if v.strip()]
    thesis_vals = [v.strip() for v in args.thesis_values.split(",") if v.strip()]
    anti_vals = [v.strip() for v in args.anti_values.split(",") if v.strip()]

    plans: List[Dict[str, str]] = []
    for s in synth_vals:
        for t in thesis_vals:
            for a in anti_vals:
                plans.append({
                    "SYNTHESIS_SECTION_MAX_CHARS": s,
                    "THESIS_LEARNING_MAX_CHARS": t,
                    "ANTITHESIS_SOURCE_MAX_CHARS": a,
                })

    if args.dryrun:
        print(json.dumps({"planned": plans}, ensure_ascii=False, indent=2))
        return

    results: List[Dict[str, Any]] = []
    t0 = time.time()
    for i, envs in enumerate(plans, 1):
        for r in range(1, max(1, args.repeats) + 1):
            print(f"-- Run {i}/{len(plans)} rep {r}/{max(1, args.repeats)} with {envs} --", flush=True)
            prof = _run_with_env(envs)
            results.append({
                "env": envs,
                "rep": r,
                "profile": prof,
            })

    t1 = time.time()

    # Summarize concise view
    summary_rows: List[Dict[str, Any]] = []
    # group by env combo
    from collections import defaultdict
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    def env_key(d: Dict[str, str]) -> str:
        return json.dumps(d, sort_keys=True)
    for r in results:
        grouped[env_key(r["env"])].append(r)

    for key, rows in grouped.items():
        envs = rows[0]["env"]
        # aggregate over repeats
        ws, me, osr, ssr, sad, sau = [], [], [], [], [], []
        for r in rows:
            prof = r["profile"]
            persona = (prof.get("persona_llm") or {})
            byp = (persona.get("by_persona") or {})
            syn = byp.get("synthesis") or {}
            ws.append(prof.get("wall_clock_seconds"))
            me.append((prof.get("segments") or {}).get("meta_to_eval"))
            osr.append((persona.get("overall") or {}).get("success_rate"))
            ssr.append(syn.get("success_rate"))
            sad.append(syn.get("avg_duration_sec"))
            sau.append(syn.get("avg_user_chars"))
        def _avg(arr):
            arr2 = [x for x in arr if isinstance(x, (int, float))]
            return (sum(arr2) / len(arr2)) if arr2 else None
        row = {
            **envs,
            "repeats": len(rows),
            "wall_clock_avg": _avg(ws),
            "meta_to_eval_avg": _avg(me),
            "success_rate_overall_avg": _avg(osr),
            "synthesis_success_rate_avg": _avg(ssr),
            "synthesis_avg_duration_avg": _avg(sad),
            "synthesis_avg_user_chars_avg": _avg(sau),
        }
        summary_rows.append(row)

    out = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_runs": len(results),
        "elapsed_sec": round(t1 - t0, 3),
        "results": results,
        "summary": summary_rows,
    }

    # write files
    ts = time.strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(OUTPUT_DIR, f"prompt_compaction_sweep_{ts}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # Minimal markdown report
    md_path = os.path.join(OUTPUT_DIR, f"prompt_compaction_sweep_{ts}.md")
    lines = ["# Prompt Compaction Sweep Summary", "", f"총 실행: {len(results)} | 소요: {round(t1-t0, 1)}s", ""]
    lines.append("| SYNTHESIS | THESIS | ANTITHESIS | repeats | wall_clock_avg | meta_to_eval_avg | overall_sr_avg | synth_sr_avg | synth_avg_dur_avg | synth_avg_chars_avg |")
    lines.append("|-----------|--------|------------|--------:|---------------:|-----------------:|---------------:|-------------:|-------------------:|--------------------:|")
    for row in summary_rows:
        lines.append(
            f"| {row['SYNTHESIS_SECTION_MAX_CHARS']} | {row['THESIS_LEARNING_MAX_CHARS']} | {row['ANTITHESIS_SOURCE_MAX_CHARS']} | "
            f"{row.get('repeats', 1)} | {row.get('wall_clock_avg')} | {row.get('meta_to_eval_avg')} | {row.get('success_rate_overall_avg')} | {row.get('synthesis_success_rate_avg')} | "
            f"{row.get('synthesis_avg_duration_avg')} | {row.get('synthesis_avg_user_chars_avg')} |")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(json.dumps({"json": json_path, "md": md_path, "summary": summary_rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
