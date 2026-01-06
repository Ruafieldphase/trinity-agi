#!/usr/bin/env python3
"""Generate Lubit phase-injection visualizations from the canonical JSON dataset."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

PHASE_COLORS = {
    "baseline": "#64dfdf",
    "phase_injection": "#ff4d6d",
    "stabilization": "#80ffdb",
}

plt.style.use("dark_background")


@dataclass
class EventPoint:
    time: datetime
    loop: int
    phase: str
    label: str
    affect: Optional[float]
    words: Optional[int]
    stability: Optional[str]
    strategy: Optional[str]
    affect_delta: Optional[float]


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    default_data = root / "lubit_phase_injection_simulation.json"
    default_out = root / "visualizations"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=default_data, help="Path to lubit_phase_injection_simulation.json")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_out,
        help="Directory where PNG files will be written",
    )
    parser.add_argument("--dpi", type=int, default=220, help="Matplotlib DPI for saved figures")
    return parser.parse_args()


def load_events(json_path: Path) -> List[EventPoint]:
    if not json_path.exists():
        raise FileNotFoundError(f"Cannot find data file: {json_path}")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    events: List[EventPoint] = []

    for cycle in payload.get("cycles", []):
        loop = cycle.get("loop")
        phase = cycle.get("phase", "unknown")
        prev_affect: Optional[float] = None
        for entry in cycle.get("events", []):
            time_str = entry.get("time")
            dt_value = parse_iso_ts(time_str) if time_str else None
            affect = entry.get("affect")
            words = (entry.get("response_complexity") or {}).get("words")
            affect_delta = affect - prev_affect if (affect is not None and prev_affect is not None) else None
            prev_affect = affect if affect is not None else prev_affect

            events.append(
                EventPoint(
                    time=dt_value if dt_value else datetime.min,
                    loop=loop,
                    phase=phase,
                    label=entry.get("event", "event"),
                    affect=affect,
                    words=words,
                    stability=entry.get("stability"),
                    strategy=entry.get("strategy"),
                    affect_delta=affect_delta,
                )
            )

    events.sort(key=lambda e: e.time)
    return events


def parse_iso_ts(value: str) -> datetime:
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def plot_affect_timeline(events: List[EventPoint], output_path: Path, dpi: int) -> Path:
    fig, ax = plt.subplots(figsize=(10, 4.5))

    times = [e.time for e in events if e.affect is not None]
    values = [e.affect for e in events if e.affect is not None]
    colors = [PHASE_COLORS.get(e.phase, "#94a3b8") for e in events if e.affect is not None]

    ax.plot(times, values, color="#7f5af0", linewidth=2, alpha=0.75)
    ax.scatter(times, values, c=colors, s=55, edgecolors="#0f172a", linewidths=0.6)

    for e in events:
        if e.affect is None:
            continue
        ax.text(
            e.time,
            e.affect + 0.02,
            f"Loop {e.loop}\n{e.phase}",
            fontsize=8,
            color=PHASE_COLORS.get(e.phase, "#cbd5f5"),
            ha="center",
        )

    ax.set_title("Affect amplitude across the 280-second loops")
    ax.set_ylabel("Affect score")
    ax.set_ylim(0, 1)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return output_path


def plot_complexity_timeline(events: List[EventPoint], output_path: Path, dpi: int) -> Path:
    fig, ax = plt.subplots(figsize=(10, 4.2))
    points = [e for e in events if e.words is not None]
    times = [e.time for e in points]
    values = [e.words for e in points]

    ax.plot(times, values, color="#ff79c6", linewidth=2.2, marker="o", alpha=0.85)
    ax.fill_between(times, values, color="#ff79c6", alpha=0.12)

    ax.set_title("Response complexity (word count)")
    ax.set_ylabel("Words per response")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return output_path


def plot_strategy_effect(events: List[EventPoint], output_path: Path, dpi: int) -> Path:
    deltas = {}
    for e in events:
        if e.strategy and e.affect_delta is not None:
            deltas.setdefault(e.strategy, []).append(e.affect_delta)

    averages = sorted(((strategy, sum(vals) / len(vals)) for strategy, vals in deltas.items()), key=lambda x: x[0])
    if not averages:
        raise ValueError("No strategy events with affect_delta were found.")

    fig, ax = plt.subplots(figsize=(8, 4))
    strategies = [s for s, _ in averages]
    values = [v for _, v in averages]

    bars = ax.bar(strategies, values, color="#50fa7b", alpha=0.85)
    ax.axhline(0, color="#94a3b8", linewidth=1, linestyle="--")
    ax.set_ylabel("Δ Affect")
    ax.set_title("Average affect delta per intervention strategy")
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.005, f"{value:.3f}", ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return output_path


def main() -> None:
    args = parse_args()
    events = load_events(args.data)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = [
        plot_affect_timeline(events, output_dir / "lubit_affect_timeline.png", args.dpi),
        plot_complexity_timeline(events, output_dir / "lubit_complexity_timeline.png", args.dpi),
        plot_strategy_effect(events, output_dir / "lubit_strategy_comparison.png", args.dpi),
    ]

    print("Generated:")
    cwd = Path.cwd()
    for path in outputs:
        try:
            display = path.relative_to(cwd)
        except ValueError:
            display = path
        print(f" - {display}")


if __name__ == "__main__":
    main()
