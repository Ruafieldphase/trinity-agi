"""
Realtime Resonance Pipeline

Phase 4: Ledger/Monitoring metrics -> Seasonality check -> Scheduler windows ->
Resonance simulation -> Status export (JSON + Markdown)

Safe-by-default: tolerates missing fields, uses heuristic seeding.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Local imports (existing repo scripts)
import sys
from pathlib import Path as _PathPatch
_ROOT = _PathPatch(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.resonance_simulator import ResonanceSimulator
from scripts.seasonality_detector_smoke import SeasonalAnomalyDetector, AnomalySeverity


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _get(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def seed_from_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
    """Heuristically derive initial state seeds from monitoring metrics.

    Returns keys: info_density, coherence, ethics
    """
    # success rate in [0,1]
    success_rate = float(_get(metrics, "AGI.SuccessRate", 0.75))
    if success_rate > 1.5:  # if given as percentage 0-100
        success_rate = success_rate / 100.0

    # avg confidence across channels if available
    confidences: List[float] = []
    for ch in ("Cloud", "Local", "Gateway"):
        v = _get(metrics, f"Channels.{ch}.AvgConfidence")
        if isinstance(v, (int, float)):
            confidences.append(float(v))
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.70

    # replan rate as weak signal
    replan_rate = float(_get(metrics, "AGI.ReplanRate", 40.0))
    replan_rate01 = replan_rate / 100.0 if replan_rate > 1.0 else replan_rate

    # Compose seeds (bounded)
    info_density = (
        (success_rate - 0.5)
        + 0.5 * (avg_conf - 0.5)
        + 0.2 * (replan_rate01 - 0.5)
    )
    info_density = _clamp(info_density, -1.0, 1.0)

    coherence = _clamp(0.55 + 0.3 * (avg_conf - 0.5), 0.1, 0.9)
    ethics = _clamp(0.60 + 0.2 * (success_rate - 0.5), 0.05, 0.95)

    return {
        "info_density": float(info_density),
        "coherence": float(coherence),
        "ethics": float(ethics),
    }


def read_lumen_state(workspace: Path) -> Optional[Dict[str, Any]]:
    """Read Lumen emotion signals from lumen_state.json.
    
    Returns: {"fear": float, "joy": float, "trust": float, "timestamp": str}
    """
    lumen_path = workspace / "fdo_agi_repo/memory/lumen_state.json"
    
    if not lumen_path.exists():
        return None
    
    try:
        # Use utf-8-sig to handle BOM
        with lumen_path.open("r", encoding="utf-8-sig") as f:
            data = json.load(f)
            # Handle both flat and nested emotion structures
            emotion = data.get("emotion", {})
            if emotion:
                result = {
                    "fear": float(emotion.get("fear", 0.0)),
                    "joy": float(emotion.get("joy", 0.5)),
                    "trust": float(emotion.get("trust", 0.5)),
                    "timestamp": data.get("timestamp", ""),
                }
            else:
                result = {
                    "fear": float(data.get("fear", 0.0)),
                    "joy": float(data.get("joy", 0.5)),
                    "trust": float(data.get("trust", 0.5)),
                    "timestamp": data.get("timestamp", ""),
                }
            return result
    except Exception as e:
        print(f"[Warning] Could not read Lumen state: {e}")
        return None


def analyze_seasonality(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Feed HourlyLatency series into seasonal detector and flag latest point anomalies.

    Expects Channels.<Name>.HourlyLatency: List[float], len ~24
    """
    results: List[Dict[str, Any]] = []
    for ch in ("Cloud", "Local", "Gateway"):
        series = _get(metrics, f"Channels.{ch}.HourlyLatency")
        if not isinstance(series, list) or len(series) < 6:
            continue

        period = len(series)
        det = SeasonalAnomalyDetector(period=period)

        # Learn baseline with all but last two points to give room
        for v in series[:-1]:
            try:
                det.detect(float(v), metric_name=f"{ch}.latency")
            except Exception:
                pass

        latest_value = float(series[-1])
        alert = det.detect(latest_value, metric_name=f"{ch}.latency")
        results.append(
            {
                "channel": ch,
                "latest": latest_value,
                "period": period,
                "anomaly": bool(alert is not None),
                "severity": (alert.severity.name if alert else None),
                "deviation_sigma": (getattr(alert, "deviation", None)),
                "baseline": (getattr(alert, "baseline", None)),
                "confidence": (getattr(alert, "confidence", None)),
            }
        )

    return results


def compute_next_runs(now: datetime) -> Dict[str, str]:
    """Compute next scheduler run timestamps (string ISO)."""
    # Daily 03:10 and 03:20
    def next_daily_at(h: int, m: int) -> datetime:
        dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if dt <= now:
            dt = dt + timedelta(days=1)
        return dt

    # Hourly at :00
    def next_hourly_at(minute: int = 0) -> datetime:
        dt = now.replace(minute=minute, second=0, microsecond=0)
        if dt <= now:
            dt = dt + timedelta(hours=1)
        return dt

    return {
        "bqi_daily": next_daily_at(3, 10).isoformat(),
        "monitoring_daily": next_daily_at(3, 20).isoformat(),
        "health_hourly": next_hourly_at(0).isoformat(),
    }


def simulate_resonance(seeds: Dict[str, float], cycles: int = 1, steps_per_phase: int = 8) -> Dict[str, Any]:
    sim = ResonanceSimulator()
    # Apply seeds
    sim.state.info_density = seeds["info_density"]
    sim.state.logical_coherence = seeds["coherence"]
    sim.state.ethical_alignment = seeds["ethics"]

    history = sim.run_simulation(cycles=cycles, steps_per_phase=steps_per_phase)
    final = sim.state.get_current_metrics()

    # Extract small series for MD (resonance projected)
    resonance_series = [round(rec["resonance"], 4) for rec in history[-min(28, len(history)):]]

    return {
        "final_state": final,
        "horizon_crossings": int(sim.state.horizon_crossings),
        "history_count": len(history),
        "resonance_series": resonance_series,
    }


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_md(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    seeds = data.get("seeds", {})
    seasonality = data.get("seasonality", [])
    sim = data.get("simulation", {})
    next_runs = data.get("next_runs", {})
    lumen = data.get("lumen_state")

    lines: List[str] = []
    lines.append("# Real-time Resonance Pipeline\n")
    lines.append(f"Generated: {datetime.now().isoformat()}\n")

    # Lumen Emotion Signals
    if lumen:
        lines.append("\n## 🎭 Lumen Emotion Signals\n")
        fear = lumen.get("fear", 0.0)
        joy = lumen.get("joy", 0.5)
        trust = lumen.get("trust", 0.5)
        
        # Status indicators
        fear_status = "🔴 HIGH" if fear >= 0.7 else ("🟡 ELEVATED" if fear >= 0.5 else "🟢 NORMAL")
        joy_status = "🟢 HIGH" if joy >= 0.7 else ("🟡 MODERATE" if joy >= 0.5 else "⚪ LOW")
        trust_status = "🟢 HIGH" if trust >= 0.7 else ("🟡 MODERATE" if trust >= 0.5 else "🔴 LOW")
        
        lines.append(f"- **Fear**: {fear:.3f} {fear_status}\n")
        lines.append(f"- **Joy**: {joy:.3f} {joy_status}\n")
        lines.append(f"- **Trust**: {trust:.3f} {trust_status}\n")
        lines.append(f"- Last Updated: {lumen.get('timestamp', 'N/A')}\n")
        
        # Recommendations based on fear level
        if fear >= 0.9:
            lines.append("\n⚠️ **Alert**: Fear level critical - Deep Maintenance recommended\n")
        elif fear >= 0.7:
            lines.append("\n⚠️ **Warning**: Fear elevated - Active Cooldown suggested\n")
        elif fear >= 0.5:
            lines.append("\n💡 **Info**: Fear moderate - Micro-Reset available\n")
    else:
        lines.append("\n## 🎭 Lumen Emotion Signals\n")
        lines.append("- No emotion state data available\n")

    lines.append("\n## Seeds\n")
    lines.append(f"- info_density: {seeds.get('info_density'):.3f}\n")
    lines.append(f"- coherence: {seeds.get('coherence'):.3f}\n")
    lines.append(f"- ethics: {seeds.get('ethics'):.3f}\n")

    lines.append("\n## Seasonality (HourlyLatency)\n")
    if seasonality:
        for r in seasonality:
            sev = r.get("severity") or "NONE"
            flag = "ALERT" if r.get("anomaly") else "OK"
            dev = r.get("deviation_sigma")
            dev_s = f" ({dev:.2f}σ)" if isinstance(dev, (int, float)) else ""
            lines.append(f"- {r['channel']}: {flag} • latest={r['latest']}{dev_s} • severity={sev}\n")
    else:
        lines.append("- No hourly latency series found in metrics (expected Channels.<Name>.HourlyLatency).\n")

    lines.append("\n## Simulation\n")
    fs = sim.get("final_state", {})
    lines.append(f"- resonance: {fs.get('resonance', 0):.3f}\n")
    lines.append(f"- info_density: {fs.get('info_density', 0):.3f}\n")
    lines.append(f"- entropy: {fs.get('entropy', 0):.3f}\n")
    lines.append(f"- coherence: {fs.get('coherence', 0):.3f}\n")
    lines.append(f"- ethics: {fs.get('ethics', 0):.3f}\n")
    lines.append(f"- horizon_crossings: {sim.get('horizon_crossings', 0)}\n")

    series = sim.get("resonance_series", [])
    if series:
        lines.append("\n### Resonance (projection, last steps)\n")
        lines.append("```")
        lines.append(", ".join(f"{x:.3f}" for x in series))
        lines.append("```\n")

    if next_runs:
        lines.append("\n## Scheduler (next runs)\n")
        for k, v in next_runs.items():
            lines.append(f"- {k}: {v}\n")

    with path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--metrics", default="outputs/monitoring_metrics_latest.json", help="Metrics JSON input")
    p.add_argument("--hours", type=int, default=24, help="Window hours (informational)")
    p.add_argument("--output-json", default="outputs/realtime_pipeline_status.json")
    p.add_argument("--output-md", default="outputs/realtime_pipeline_status.md")
    args = p.parse_args()

    metrics_path = Path(args.metrics).resolve()
    metrics = _read_json(metrics_path) or {}
    
    # Read Lumen emotion state (use absolute path)
    workspace = metrics_path.parent.parent  # outputs/ -> workspace/
    lumen_state = read_lumen_state(workspace)

    seeds = seed_from_metrics(metrics)
    seasonality = analyze_seasonality(metrics)
    simulation = simulate_resonance(seeds, cycles=1, steps_per_phase=8)
    next_runs = compute_next_runs(datetime.now())

    out = {
        "generated_at": datetime.now().isoformat(),
        "metrics_path": str(metrics_path),
        "window_hours": args.hours,
        "lumen_state": lumen_state,
        "seeds": seeds,
        "seasonality": seasonality,
        "simulation": simulation,
        "next_runs": next_runs,
    }

    write_json(Path(args.output_json), out)
    write_md(Path(args.output_md), out)

    print(f"OK: wrote {args.output_json} and {args.output_md}")


if __name__ == "__main__":
    main()
