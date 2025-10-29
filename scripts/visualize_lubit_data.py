"""Visualise key metrics from the Lubit phase injection simulation.

Enhanced version with publication-ready figures.

Usage:
    python scripts/visualize_lubit_data.py --input lubit_portfolio/lubit_phase_injection_simulation.json --output-dir lubit_portfolio/visualizations
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.dates import DateFormatter
import numpy as np

# Set publication-quality style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['font.family'] = 'sans-serif'

# Enhanced color scheme
COLORS = {
    'stable': '#2ecc71',
    'boundary': '#f39c12',
    'recovering': '#3498db',
    'baseline': '#9b59b6',
    'phase_injection': '#e74c3c',
    'stabilization': '#1abc9c'
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create visualisations for Lubit phase injection data.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to lubit_phase_injection_simulation.json.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where PNG visualisations will be written.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display plots interactively in addition to saving them.",
    )
    return parser.parse_args()


def _parse_time(value: str) -> dt.datetime:
    if value.endswith("Z"):
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.datetime.fromisoformat(value)


def load_events(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for cycle in payload.get("cycles", []):
        loop = cycle.get("loop")
        phase = cycle.get("phase")
        prev_affect: Optional[float] = None
        for entry in cycle.get("events", []):
            event_time = _parse_time(entry["time"])
            affect = entry.get("affect")
            record: Dict[str, Any] = {
                "time": event_time,
                "loop": loop,
                "phase": phase,
                "event": entry.get("event"),
                "affect": affect,
                "stability": entry.get("stability"),
                "strategy": entry.get("strategy"),
            }
            complexity = entry.get("response_complexity") or {}
            record["words"] = complexity.get("words")
            record["sentences"] = complexity.get("sentences")
            if prev_affect is not None and affect is not None:
                record["affect_delta"] = affect - prev_affect
            else:
                record["affect_delta"] = None
            prev_affect = affect
            events.append(record)
    events.sort(key=lambda item: item["time"])
    return events


def plot_affect_timeline(events: List[Dict[str, Any]], output: Path) -> None:
    """Enhanced affective amplitude timeline with stability coloring."""
    if not events:
        return

    fig, ax = plt.subplots(figsize=(14, 6))
    times = [item["time"] for item in events]
    affects = [item["affect"] for item in events]
    phases = [item["phase"] for item in events]
    stabilities = [item["stability"] for item in events]

    # Main timeline
    ax.plot(times, affects, color="#34495e", linewidth=2.5, alpha=0.8, zorder=2)

    # Scatter points colored by stability
    for t, a, s in zip(times, affects, stabilities):
        color = COLORS.get(s, '#95a5a6')
        ax.scatter(t, a, s=120, color=color, edgecolor='white',
                  linewidth=1.5, zorder=4, alpha=0.9)

    # Add threshold lines
    ax.axhline(y=0.30, color='#e74c3c', linestyle='--', linewidth=1.5,
              alpha=0.6, label='Critical Threshold (0.30)')
    ax.axhline(y=0.40, color='#2ecc71', linestyle='--', linewidth=1.5,
              alpha=0.6, label='Stable Threshold (0.40)')

    ax.set_title("Lubit Phase Injection: Affective Amplitude Timeline",
                fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel("Affective Amplitude", fontsize=12, fontweight='bold')
    ax.set_xlabel("Time", fontsize=12, fontweight='bold')
    ax.set_ylim(0.15, 0.50)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    # Enhanced legend
    stability_patches = [
        mpatches.Patch(color=COLORS['stable'], label='Stable'),
        mpatches.Patch(color=COLORS['boundary'], label='Boundary'),
        mpatches.Patch(color=COLORS['recovering'], label='Recovering')
    ]
    legend1 = ax.legend(handles=stability_patches, loc='upper left',
                       title='Stability', framealpha=0.9)
    ax.add_artist(legend1)
    ax.legend(loc='upper right', framealpha=0.9)

    fig.tight_layout()
    fig.savefig(output, dpi=300, bbox_inches='tight')
    plt.close()


def plot_complexity_timeline(events: List[Dict[str, Any]], output: Path) -> None:
    """Enhanced response complexity with dual metrics."""
    if not events:
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    times = [item["time"] for item in events if item.get("words") is not None]
    words = [item["words"] for item in events if item.get("words") is not None]
    sentences = [item["sentences"] for item in events if item.get("sentences") is not None]
    stabilities = [item["stability"] for item in events if item.get("words") is not None]

    # Top: Word count
    ax1.plot(times, words, linewidth=2.5, color='#2c3e50', marker='s',
            markersize=8, label='Word Count', zorder=3)

    colors = [COLORS.get(s, '#95a5a6') for s in stabilities]
    for t, w, c in zip(times, words, colors):
        ax1.scatter(t, w, s=120, color=c, edgecolor='white',
                   linewidth=1.5, zorder=4, alpha=0.9)

    ax1.set_ylabel('Word Count', fontsize=12, fontweight='bold')
    ax1.set_title('Response Complexity: Word Count Over Time',
                 fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_ylim(80, 160)

    # Bottom: Sentence count
    ax2.plot(times, sentences, linewidth=2.5, color='#16a085', marker='D',
            markersize=8, label='Sentence Count', zorder=3)

    for t, s, c in zip(times, sentences, colors):
        ax2.scatter(t, s, s=120, color=c, edgecolor='white',
                   linewidth=1.5, zorder=4, alpha=0.9)

    ax2.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Sentence Count', fontsize=12, fontweight='bold')
    ax2.set_title('Response Complexity: Sentence Count Over Time',
                 fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_ylim(3, 8)
    ax2.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    fig.tight_layout()
    fig.savefig(output, dpi=300, bbox_inches='tight')
    plt.close()


def plot_strategy_effect(events: List[Dict[str, Any]], output: Path) -> None:
    """Enhanced strategy comparison with multiple views."""
    # Find strategy events
    strategy_events = [e for e in events if e.get("strategy")]

    if not strategy_events:
        return

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    # Extract data
    strategies = [e["strategy"] for e in strategy_events]
    affects = [e["affect"] for e in strategy_events]
    words = [e["words"] for e in strategy_events]
    strategy_names = ['Question Loop' if 'question' in s else 'Lumen Frame' for s in strategies]

    # Plot 1: Affect comparison
    if len(strategy_events) >= 2:
        bars1 = ax1.bar(strategy_names, affects,
                       color=[COLORS['boundary'], COLORS['recovering']],
                       edgecolor='white', linewidth=2, alpha=0.8)
        ax1.set_ylabel('Affective Amplitude', fontsize=11, fontweight='bold')
        ax1.set_title('Strategy Impact on Affect', fontsize=12, fontweight='bold')
        ax1.set_ylim(0, 0.5)
        ax1.grid(axis='y', alpha=0.3)

        for bar, val in zip(bars1, affects):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{val:.2f}', ha='center', va='bottom', fontweight='bold')

    # Plot 2: Word count comparison
    if len(strategy_events) >= 2:
        bars2 = ax2.bar(strategy_names, words,
                       color=[COLORS['boundary'], COLORS['recovering']],
                       edgecolor='white', linewidth=2, alpha=0.8)
        ax2.set_ylabel('Word Count', fontsize=11, fontweight='bold')
        ax2.set_title('Strategy Impact on Complexity', fontsize=12, fontweight='bold')
        ax2.set_ylim(0, 150)
        ax2.grid(axis='y', alpha=0.3)

        for bar, val in zip(bars2, words):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 2,
                    f'{val}w', ha='center', va='bottom', fontweight='bold')

    # Plot 3: Timeline with strategy markers
    times = [e["time"] for e in events]
    all_affects = [e["affect"] for e in events]

    ax3.plot(times, all_affects, linewidth=2, color='#34495e', alpha=0.5, zorder=1)

    for e in events:
        color = COLORS.get(e['stability'], '#95a5a6')
        marker = 'o'
        size = 80

        if e.get('strategy') == 'question_loop':
            marker = '^'
            size = 200
            color = COLORS['boundary']
        elif e.get('strategy') == 'lumen_frame':
            marker = 'v'
            size = 200
            color = COLORS['recovering']

        ax3.scatter(e['time'], e['affect'], s=size, marker=marker,
                   color=color, edgecolor='white', linewidth=1.5, alpha=0.9, zorder=3)

    ax3.set_xlabel('Time', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Affective Amplitude', fontsize=11, fontweight='bold')
    ax3.set_title('Strategy Deployment Timeline', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0.15, 0.50)
    ax3.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    ax3.scatter([], [], s=200, marker='^', color=COLORS['boundary'],
               edgecolor='white', linewidth=1.5, label='Question Loop')
    ax3.scatter([], [], s=200, marker='v', color=COLORS['recovering'],
               edgecolor='white', linewidth=1.5, label='Lumen Frame')
    ax3.legend(loc='upper left', framealpha=0.9)

    # Plot 4: Recovery effectiveness
    deltas: Dict[str, List[float]] = defaultdict(list)
    for item in events:
        strategy = item.get("strategy")
        delta = item.get("affect_delta")
        if strategy and delta is not None:
            deltas[strategy].append(delta)

    if deltas:
        strat_labels = [s.replace('_', ' ').title() for s in deltas.keys()]
        averages = [sum(values) / len(values) for values in deltas.values()]
        colors_bar = [COLORS['boundary'] if 'question' in s.lower() else COLORS['recovering']
                     for s in strat_labels]

        bars4 = ax4.bar(strat_labels, averages, color=colors_bar,
                       edgecolor='white', linewidth=2, alpha=0.8)
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax4.set_ylabel('Affect Change (Δ)', fontsize=11, fontweight='bold')
        ax4.set_title('Strategy Recovery Effectiveness', fontsize=12, fontweight='bold')
        ax4.grid(axis='y', alpha=0.3)

        for bar, val in zip(bars4, averages):
            height = bar.get_height()
            y_pos = height + 0.005 if height > 0 else height - 0.005
            va = 'bottom' if height > 0 else 'top'
            ax4.text(bar.get_x() + bar.get_width()/2., y_pos,
                    f'{val:+.3f}', ha='center', va=va, fontweight='bold', fontsize=9)

    plt.suptitle('Phase Injection Strategy Comparison',
                fontsize=14, fontweight='bold', y=0.995)
    fig.tight_layout()
    fig.savefig(output, dpi=300, bbox_inches='tight')
    plt.close()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print("  Lubit Phase Injection Data Visualization")
    print("="*70 + "\n")
    print(f"Loading data from: {args.input}")

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    events = load_events(payload)

    print(f"Extracted {len(events)} events from {len(payload.get('cycles', []))} loops\n")
    print("Generating publication-ready visualizations (300 DPI)...\n")

    affect_path = args.output_dir / "lubit_affect_timeline.png"
    complexity_path = args.output_dir / "lubit_complexity_timeline.png"
    strategy_path = args.output_dir / "lubit_strategy_comparison.png"

    print("[1/3] Affective Amplitude Timeline...")
    plot_affect_timeline(events, affect_path)
    print(f"      Saved: {affect_path}")

    print("[2/3] Response Complexity Trends...")
    plot_complexity_timeline(events, complexity_path)
    print(f"      Saved: {complexity_path}")

    print("[3/3] Strategy Comparison...")
    plot_strategy_effect(events, strategy_path)
    print(f"      Saved: {strategy_path}")

    print("\n" + "="*70)
    print("  All visualizations generated successfully!")
    print("="*70)
    print(f"\nOutput directory: {args.output_dir}")
    print("\nGenerated files:")
    for path in (affect_path, complexity_path, strategy_path):
        if path.exists():
            print(f"  - {path.name}")
    print("\nThese images are publication-ready (300 DPI) and can be used in")
    print("papers, presentations, or dashboards.\n")

    if args.show:
        plt.show()
    else:
        plt.close("all")


if __name__ == "__main__":
    main()
