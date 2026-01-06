"""
Self-care 텔레메트리 요약을 Markdown 리포트로 변환.

기본적으로 `outputs/self_care_metrics_summary.json`을 읽어
`outputs/self_care_metrics_report.md`를 생성한다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime


def load_summary(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Summary file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_markdown(summary: dict) -> str:
    generated_at = summary.get("generated_at")
    if generated_at:
        try:
            ts = datetime.fromisoformat(generated_at)
            generated_at = ts.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

    lines = [
        "# Self-Care Metrics Summary",
        "",
        f"- Generated: {generated_at or 'N/A'}",
        f"- Sample Count: {summary.get('count', 0)} (last {summary.get('hours', '?')}h)",
        "",
        "## Stagnation",
        f"- Average stagnation: {summary.get('stagnation_avg', 0.0):.3f}",
        f"- 95th percentile: {summary.get('stagnation_p95', 0.0):.3f}",
        f"- Standard deviation: {summary.get('stagnation_std', 0.0):.3f}",
        f"- >0.3 count: {summary.get('stagnation_over_03', 0)}",
        f"- >0.5 count: {summary.get('stagnation_over_05', 0)}",
        "",
        "## Flow Indicators",
        f"- Queue usage ratio (avg): {summary.get('queue_ratio_avg', 0.0):.2f}",
        f"- Memory growth rate (avg): {summary.get('memory_growth_avg', 0.0):.3f}",
        f"- Latency p99 (avg): {summary.get('latency_p99_avg', 0.0):.1f} ms",
        f"- Throughput ratio (avg): {summary.get('throughput_ratio_avg', 0.0):.2f}",
        f"- Circulation OK rate: {summary.get('circulation_ok_rate', 0.0)*100:.1f}%",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Self-care 요약 Markdown 생성")
    parser.add_argument(
        "--summary-path",
        type=Path,
        default=Path("outputs") / "self_care_metrics_summary.json",
        help="요약 JSON 경로",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs") / "self_care_metrics_report.md",
        help="생성할 Markdown 경로",
    )
    args = parser.parse_args()

    summary = load_summary(args.summary_path)
    markdown = render_markdown(summary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(markdown + "\n")
    print(f"✅ Markdown report written to {args.output}")


if __name__ == "__main__":
    main()
