#!/usr/bin/env python3
"""
Analyze Autopoietic Loop markers (folding/unfolding/integration/symmetry) from resonance_ledger.jsonl
and produce a concise report. Outputs both Markdown and JSON.

Usage (optional):
  python analyze_autopoietic_loop.py --hours 24 --out-md ../../outputs/autopoietic_loop_report_latest.md --out-json ../../outputs/autopoietic_loop_report_latest.json

Defaults:
  hours=24
  out-md=../../outputs/autopoietic_loop_report_latest.md
  out-json=../../outputs/autopoietic_loop_report_latest.json
"""
import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

LEDGER_PATH = Path(__file__).parent.parent / "memory" / "resonance_ledger_v2.jsonl"
DEFAULT_MD = Path(__file__).parents[2] / "outputs" / "autopoietic_loop_report_latest.md"
DEFAULT_JSON = Path(__file__).parents[2] / "outputs" / "autopoietic_loop_report_latest.json"


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--out-md", type=str, default=str(DEFAULT_MD))
    ap.add_argument("--out-json", type=str, default=str(DEFAULT_JSON))
    return ap.parse_args()


def load_events(ledger_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    path = ledger_path if ledger_path is not None else LEDGER_PATH
    if not path.exists():
        return events
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                pass
    return events


def within_window(ev: Dict[str, Any], since_dt: datetime) -> bool:
    # Try 'timestamp' first, then 'ts' (unix timestamp)
    ts = ev.get("timestamp") or ev.get("ts")
    if not ts:
        return True
    try:
        if isinstance(ts, (int, float)):
            # Unix timestamp
            dt = datetime.fromtimestamp(ts)
        else:
            # ISO string
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt >= since_dt
    except Exception:
        return True


@dataclass
class PhaseDurations:
    folding: Optional[float] = None
    unfolding: Optional[float] = None
    integration: Optional[float] = None
    symmetry: Optional[float] = None


@dataclass
class TaskLoop:
    task_id: str
    phases: PhaseDurations
    context_count: int = 0
    citations_thesis: Optional[int] = None
    citations_synthesis: Optional[int] = None
    evidence_gate_triggered: bool = False
    second_pass: bool = False
    final_quality: Optional[float] = None
    final_evidence_ok: Optional[bool] = None

    def is_complete(self) -> bool:
        p = self.phases
        return all(
            getattr(p, nm) is not None for nm in ("folding", "unfolding", "integration", "symmetry")
        )


def summarize(events: List[Dict[str, Any]], hours: int) -> Dict[str, Any]:
    now = datetime.now()
    since = now - timedelta(hours=hours)

    tasks: Dict[str, TaskLoop] = {}
    # Track timestamps for backfill estimation
    task_timestamps: Dict[str, Dict[str, Any]] = {}

    # Aggregates: policy + closed-loop snapshot
    policy_counts = {"allow": 0, "warn": 0, "block": 0}
    last_policy: Dict[str, Any] = {}
    last_closed_loop: Optional[Dict[str, Any]] = None

    for ev in events:
        if not within_window(ev, since):
            continue
        tid = ev.get("task_id")
        # Some events (e.g., policy/snapshot) may not have task_id; handle below

        # Track policy and closed-loop snapshot
        et = ev.get("event")
        if et == "resonance_policy":
            act = str(ev.get("action") or "").lower()
            if act in policy_counts:
                policy_counts[act] += 1
            last_policy = {
                "mode": ev.get("mode"),
                "policy": ev.get("policy"),
                "reasons": ev.get("reasons"),
            }
        elif et == "closed_loop_snapshot":
            snap = ev.get("snapshot")
            if isinstance(snap, dict):
                last_closed_loop = snap

        if not tid:
            continue

        # ensure record
        if tid not in tasks:
            tasks[tid] = TaskLoop(task_id=tid, phases=PhaseDurations())
        rec = tasks[tid]
        
        # Track timestamps for phase estimation
        if tid not in task_timestamps:
            task_timestamps[tid] = {}

        # Support both 'timestamp' (ISO) and 'ts' (unix timestamp)
        ts = ev.get("timestamp") or ev.get("ts")
        
        # Primary: autopoietic_phase markers (new instrumentation)
        if et == "autopoietic_phase":
            phase = ev.get("phase")
            stage = ev.get("stage")
            if phase == "folding" and stage == "start":
                rec.context_count = int(ev.get("context_count") or 0)
            if stage == "end" and isinstance(ev.get("duration_sec"), (int, float)):
                dur = float(ev["duration_sec"])
                if phase == "folding":
                    rec.phases.folding = dur
                elif phase == "unfolding":
                    rec.phases.unfolding = dur
                elif phase == "integration":
                    rec.phases.integration = dur
                elif phase == "symmetry":
                    rec.phases.symmetry = dur
                    rec.evidence_gate_triggered = bool(ev.get("evidence_gate_triggered") or False)
                    rec.second_pass = bool(ev.get("second_pass") or False)
                    rec.final_quality = ev.get("final_quality")
                    rec.final_evidence_ok = ev.get("final_evidence_ok")
        
        # Secondary: collect thesis/antithesis/synthesis timestamps for backfill
        elif et == "thesis_start":
            task_timestamps[tid]["thesis_start"] = ts
            rec.context_count = int(ev.get("context_count") or 0)
        elif et == "thesis_end":
            task_timestamps[tid]["thesis_end"] = ts
            if "citations" in ev:
                rec.citations_thesis = int(ev.get("citations") or 0)
        elif et == "antithesis_start":
            task_timestamps[tid]["antithesis_start"] = ts
        elif et == "antithesis_end":
            task_timestamps[tid]["antithesis_end"] = ts
        elif et == "synthesis_start":
            # Store all synthesis_start timestamps for second pass scenarios
            if "synthesis_starts" not in task_timestamps[tid]:
                task_timestamps[tid]["synthesis_starts"] = []
            task_timestamps[tid]["synthesis_starts"].append(ts)
        elif et == "synthesis_end":
            # Store all synthesis_end timestamps for second pass scenarios
            if "synthesis_ends" not in task_timestamps[tid]:
                task_timestamps[tid]["synthesis_ends"] = []
            task_timestamps[tid]["synthesis_ends"].append(ts)
            if "citations" in ev:
                rec.citations_synthesis = int(ev.get("citations") or 0)
        elif et in ("evidence_gate_triggered", "evidence_gate"):
            task_timestamps[tid]["evidence_gate"] = ts
            rec.evidence_gate_triggered = True
        elif et == "second_pass":
            rec.second_pass = True
        elif et == "task_complete":
            rec.final_quality = ev.get("quality")
            rec.final_evidence_ok = ev.get("evidence_ok")
    
    # Backfill: estimate phases from thesis/antithesis/synthesis events
    def parse_timestamp(ts_val: Any) -> Optional[datetime]:
        if not ts_val:
            return None
        try:
            if isinstance(ts_val, (int, float)):
                return datetime.fromtimestamp(ts_val)
            else:
                return datetime.fromisoformat(str(ts_val).replace("Z", "+00:00"))
        except Exception:
            return None
    
    for tid, rec in tasks.items():
        ts_map = task_timestamps.get(tid, {})
        phases = rec.phases
        
        # Only backfill if autopoietic phases are missing
        if phases.folding is None:
            t_start = parse_timestamp(ts_map.get("thesis_start"))
            t_end = parse_timestamp(ts_map.get("thesis_end"))
            if t_start and t_end:
                phases.folding = (t_end - t_start).total_seconds()
        
        if phases.unfolding is None:
            a_start = parse_timestamp(ts_map.get("antithesis_start"))
            a_end = parse_timestamp(ts_map.get("antithesis_end"))
            if a_start and a_end:
                phases.unfolding = (a_end - a_start).total_seconds()
        
        if phases.integration is None:
            # Use first synthesis_start and first synthesis_end for integration
            synthesis_starts = ts_map.get("synthesis_starts", [])
            synthesis_ends = ts_map.get("synthesis_ends", [])
            if synthesis_starts and synthesis_ends:
                s_start = parse_timestamp(synthesis_starts[0])  # First synthesis_start
                s_end = parse_timestamp(synthesis_ends[0])      # First synthesis_end
                if s_start and s_end:
                    phases.integration = (s_end - s_start).total_seconds()
        
        if phases.symmetry is None:
            # Estimate symmetry as time from synthesis_end to evidence_gate
            # Use the synthesis_end that occurred BEFORE evidence_gate
            eg_time_raw = ts_map.get("evidence_gate")
            eg_time = parse_timestamp(eg_time_raw)
            synthesis_ends = ts_map.get("synthesis_ends", [])
            
            if eg_time and synthesis_ends:
                # Find the last synthesis_end before evidence_gate
                valid_s_ends = [ts for ts in synthesis_ends if ts < eg_time_raw]
                if valid_s_ends:
                    s_end = parse_timestamp(valid_s_ends[-1])
                    if s_end:
                        duration = (eg_time - s_end).total_seconds()
                        if duration >= 0:
                            phases.symmetry = duration

    complete = [r for r in tasks.values() if r.is_complete()]
    incomplete = [r for r in tasks.values() if not r.is_complete()]

    def avg(vals: List[Optional[float]]) -> float:
        xs = [float(v) for v in vals if isinstance(v, (int, float))]
        return sum(xs) / len(xs) if xs else 0.0

    def p95(vals: List[Optional[float]]) -> float:
        xs = sorted(float(v) for v in vals if isinstance(v, (int, float)))
        if not xs:
            return 0.0
        # nearest-rank method
        k = max(1, int(round(0.95 * len(xs)))) - 1
        k = min(k, len(xs) - 1)
        return xs[k]

    complete_loops = len(complete)
    tasks_total = len(tasks)
    summary = {
        "window_hours": hours,
        "generated_at": now.isoformat(),
        "counts": {
            "tasks_total": tasks_total,
            "complete_loops": complete_loops,
            "incomplete_loops": len(incomplete),
            "evidence_gate_triggered": sum(1 for r in complete if r.evidence_gate_triggered),
            "second_pass": sum(1 for r in complete if r.second_pass),
        },
        "durations_avg_sec": {
            "folding": avg([r.phases.folding for r in complete]),
            "unfolding": avg([r.phases.unfolding for r in complete]),
            "integration": avg([r.phases.integration for r in complete]),
            "symmetry": avg([r.phases.symmetry for r in complete]),
        },
        "durations_p95_sec": {
            "folding": p95([r.phases.folding for r in complete]),
            "unfolding": p95([r.phases.unfolding for r in complete]),
            "integration": p95([r.phases.integration for r in complete]),
            "symmetry": p95([r.phases.symmetry for r in complete]),
        },
        "rates_pct": {
            "loop_complete_rate": (complete_loops / tasks_total * 100.0) if tasks_total else 0.0,
            "evidence_gate_trigger_rate": (sum(1 for r in complete if r.evidence_gate_triggered) / complete_loops * 100.0) if complete_loops else 0.0,
            "second_pass_rate": (sum(1 for r in complete if r.second_pass) / complete_loops * 100.0) if complete_loops else 0.0,
        },
        "quality": {
            "final_quality_avg": avg([r.final_quality for r in complete]),
            "final_evidence_ok_rate": (
                sum(1 for r in complete if r.final_evidence_ok) / len(complete) * 100.0
            ) if complete else 0.0,
        },
        "samples": [asdict(r) for r in list(complete)[:5]],
        "policy": {
            "counts": policy_counts,
            "last": last_policy,
        },
        "closed_loop": last_closed_loop or {},
    }
    return summary


def to_markdown(summary: Dict[str, Any]) -> str:
    counts = summary.get("counts", {})
    durs = summary.get("durations_avg_sec", {})
    durs_p95 = summary.get("durations_p95_sec", {})
    rates = summary.get("rates_pct", {})
    quality = summary.get("quality", {})
    lines: List[str] = []

    # ASCII-safe digest header
    gen = summary.get("generated_at", "")
    gen_short = gen[:19] if isinstance(gen, str) else str(gen)
    tasks_total = int(counts.get("tasks_total", 0) or 0)
    complete_loops = int(counts.get("complete_loops", 0) or 0)
    incomplete_loops = int(counts.get("incomplete_loops", 0) or 0)
    loop_rate = float(rates.get("loop_complete_rate", 0.0) or 0.0)
    eg = int(counts.get("evidence_gate_triggered", 0) or 0)
    sp = int(counts.get("second_pass", 0) or 0)

    lines.append("[AUTOPOIETIC LOOP DIGEST - ASCII SAFE]")
    lines.append("")
    lines.append(f"- Generated: {gen_short}")
    lines.append(f"- Tasks seen: {tasks_total}")
    lines.append(f"- Complete loops: {complete_loops} ({loop_rate:.1f}%)")
    lines.append(f"- Incomplete loops: {incomplete_loops}")
    lines.append(f"- Evidence gate: {eg}, Second pass: {sp}")
    # Build At-a-glance line including policy warns/blocks if present
    pol_counts = (summary.get("policy", {}) or {}).get("counts", {}) or {}
    pol_warn = int(pol_counts.get("warn", 0) or 0)
    pol_block = int(pol_counts.get("block", 0) or 0)
    glance_bits: list[str] = []
    if eg == 0 and sp == 0:
        glance_bits.append("Stable loop flow")
    else:
        glance_bits.append("Loops active; gates/second pass present")
    if pol_block > 0:
        glance_bits.append(f"Policy blocks: {pol_block}")
    elif pol_warn > 0:
        glance_bits.append(f"Policy warns: {pol_warn}")
    lines.append("- At-a-glance: " + "; ".join(glance_bits))
    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed section
    lines.append(f"# Autopoietic Loop Report (last {summary.get('window_hours')}h)\n")
    lines.append(f"Generated at: {summary.get('generated_at')}\n")
    lines.append("\n## Counts\n")
    lines.append(f"- Tasks Seen: {counts.get('tasks_total', 0)}")
    lines.append(f"- Complete Loops: {counts.get('complete_loops', 0)}")
    lines.append(f"- Incomplete Loops: {counts.get('incomplete_loops', 0)}")
    lines.append(f"- Evidence Gate Triggered: {counts.get('evidence_gate_triggered', 0)}")
    lines.append(f"- Second Pass Executed: {counts.get('second_pass', 0)}\n")

    lines.append("## Rates (%)\n")
    lines.append(f"- Loop Complete Rate: {rates.get('loop_complete_rate', 0.0):.1f}%")
    lines.append(f"- Evidence Gate Trigger Rate: {rates.get('evidence_gate_trigger_rate', 0.0):.1f}%")
    lines.append(f"- Second Pass Rate: {rates.get('second_pass_rate', 0.0):.1f}%\n")

    lines.append("## Avg Durations (sec)\n")
    lines.append(f"- Folding (Thesis): {durs.get('folding', 0.0):.3f}")
    lines.append(f"- Unfolding (Antithesis): {durs.get('unfolding', 0.0):.3f}")
    lines.append(f"- Integration (Synthesis): {durs.get('integration', 0.0):.3f}")
    lines.append(f"- Symmetry (Decision+Correction): {durs.get('symmetry', 0.0):.3f}\n")

    lines.append("## P95 Durations (sec)\n")
    lines.append(f"- Folding (Thesis) P95: {durs_p95.get('folding', 0.0):.3f}")
    lines.append(f"- Unfolding (Antithesis) P95: {durs_p95.get('unfolding', 0.0):.3f}")
    lines.append(f"- Integration (Synthesis) P95: {durs_p95.get('integration', 0.0):.3f}")
    lines.append(f"- Symmetry (Decision+Correction) P95: {durs_p95.get('symmetry', 0.0):.3f}\n")

    lines.append("## Quality\n")
    lines.append(f"- Final Quality Avg: {quality.get('final_quality_avg', 0.0):.3f}")
    lines.append(f"- Final Evidence OK Rate: {quality.get('final_evidence_ok_rate', 0.0):.1f}%\n")

    # Resonance Policy (ASCII-safe)
    pol = summary.get("policy", {}) or {}
    pol_counts = pol.get("counts", {}) or {}
    pol_last = pol.get("last", {}) or {}
    lines.append("## Resonance Policy (counts)\n")
    lines.append(f"- allow: {int(pol_counts.get('allow', 0) or 0)} | warn: {int(pol_counts.get('warn', 0) or 0)} | block: {int(pol_counts.get('block', 0) or 0)}")
    last_mode = pol_last.get("mode") or "--"
    last_policy = pol_last.get("policy") or "--"
    reasons = pol_last.get("reasons")
    if isinstance(reasons, list):
        reasons_str = "; ".join(str(r) for r in reasons)
    else:
        reasons_str = str(reasons or "--")
    lines.append(f"- last: mode={last_mode} policy={last_policy}")
    lines.append(f"- reasons: {reasons_str}\n")

    # Closed-loop Snapshot (ASCII-safe)
    cls = summary.get("closed_loop", {}) or {}
    if cls:
        lines.append("## Closed-loop Snapshot\n")
        rt = cls.get("realtime", {}) or {}
        sim = cls.get("resonance_simulator", cls.get("simulator", {})) or {}
        lines.append(f"- realtime: strength={rt.get('strength', '--')} coherence={rt.get('coherence', '--')} phase={rt.get('phase', '--')}")
        lines.append(f"- simulator: last_resonance={sim.get('last_resonance', '--')} last_entropy={sim.get('last_entropy', '--')}\n")

    samples = summary.get("samples", [])
    if samples:
        lines.append("## Samples (first 5)\n")
        for s in samples:
            tid = s.get("task_id")
            phases = s.get("phases", {})
            lines.append(f"- {tid}: F={phases.get('folding')} U={phases.get('unfolding')} I={phases.get('integration')} S={phases.get('symmetry')} | ctx={s.get('context_count')} | eg={s.get('evidence_gate_triggered')} | sp={s.get('second_pass')} | q={s.get('final_quality')} | evo={s.get('final_evidence_ok')}")

    return "\n".join(lines) + "\n"



def main(ledger_path: Optional[str] = None):
    args = parse_args()
    if ledger_path:
        events = load_events(Path(ledger_path))
    else:
        events = load_events()
    summary = summarize(events, args.hours)

    md = to_markdown(summary)

    out_md = Path(args["out_md"]) if isinstance(args, dict) else Path(args.out_md)
    out_json = Path(args["out_json"]) if isinstance(args, dict) else Path(args.out_json)

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(md)

__all__ = ["summarize", "to_markdown", "load_events"]


if __name__ == "__main__":
    main()
