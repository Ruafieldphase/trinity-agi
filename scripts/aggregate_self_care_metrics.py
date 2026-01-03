"""
Self-care 텔레메트리 집계 스크립트.

`fdo_agi_repo/orchestrator/self_care.py`가 기록한 JSONL 로그를 읽어
최근 N시간(기본 24시간)의 기본 통계를 요약 출력한다.

🔄 Phase 2.5 Integration: Quantum Flow Monitor 통합
- Self-care 요약 시 Quantum Flow 상태 측정
- Flow State → Goal Generation 연결
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from workspace_root import get_workspace_root

# Quantum Flow Monitor 임포트
sys.path.insert(0, str(get_workspace_root() / "fdo_agi_repo"))
try:
    from copilot.quantum_flow_monitor import QuantumFlowMonitor
    QUANTUM_FLOW_AVAILABLE = True
except ImportError:
    QUANTUM_FLOW_AVAILABLE = False


def load_entries(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            yield data


def to_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def summarize(entries: Iterable[Dict[str, Any]], hours: int, workspace_root: Optional[Path] = None) -> Dict[str, Any]:
    cutoff = datetime.now() - timedelta(hours=hours)
    sample: List[Dict[str, Any]] = []
    for item in entries:
        ts = to_datetime(item.get("timestamp", ""))
        if ts is None or ts < cutoff:
            continue
        sample.append(item)

    if not sample:
        base_summary = {"count": 0, "hours": hours}
        # Quantum Flow 측정 (데이터 없어도 측정 시도)
        if QUANTUM_FLOW_AVAILABLE and workspace_root:
            try:
                monitor = QuantumFlowMonitor(workspace_root)
                flow_metrics = monitor.measure_flow_state()
                base_summary["quantum_flow"] = {
                    "phase_coherence": flow_metrics.phase_coherence,
                    "state": flow_metrics.state,
                    "conductivity": flow_metrics.conductivity,
                    "measured_at": datetime.now().isoformat()
                }
            except Exception:
                pass
        return base_summary

    def collect(key: str, default: float = 0.0) -> List[float]:
        collected: List[float] = []
        for entry in sample:
            state = entry.get("system_state", {})
            try:
                collected.append(float(state.get(key, default)))
            except Exception:
                pass
        return collected

    stagnations = [
        float(entry.get("stagnation", {}).get("stagnation_level", 0.0))
        for entry in sample
    ]
    queue_sizes = collect("queue_size")
    queue_thresholds = collect("queue_threshold", 1.0)
    memory_growth = collect("memory_growth_rate")
    latency = collect("latency_p99")
    throughput = collect("throughput")
    expected_throughput = collect("expected_throughput", 1.0)

    def ratio(values_a: List[float], values_b: List[float], default: float = 0.0) -> List[float]:
        ratios: List[float] = []
        for a, b in zip(values_a, values_b):
            if b == 0:
                ratios.append(default)
            else:
                ratios.append(a / b)
        return ratios

    queue_ratio = ratio(queue_sizes, queue_thresholds, default=0.0)
    throughput_ratio = ratio(throughput, expected_throughput, default=0.0)

    def avg(values: List[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    if stagnations:
        idx = max(math.ceil(0.95 * len(stagnations)) - 1, 0)
        p95 = sorted(stagnations)[idx]
    else:
        p95 = 0.0

    mean_stagnation = avg(stagnations)
    if len(stagnations) > 1:
        variance = sum((v - mean_stagnation) ** 2 for v in stagnations) / (len(stagnations) - 1)
        std = math.sqrt(max(variance, 0.0))
    else:
        std = 0.0

    result = {
        "count": len(sample),
        "hours": hours,
        "stagnation_avg": mean_stagnation,
        "stagnation_p95": p95,
        "stagnation_std": std,
        "stagnation_over_03": sum(1 for v in stagnations if v > 0.3),
        "stagnation_over_05": sum(1 for v in stagnations if v > 0.5),
        "queue_ratio_avg": avg(queue_ratio),
        "memory_growth_avg": avg(memory_growth),
        "latency_p99_avg": avg(latency),
        "throughput_ratio_avg": avg(throughput_ratio),
        "circulation_ok_rate": sum(1 for entry in sample if entry.get("circulation_ok")) / len(sample),
    }
    
    # 🔄 Quantum Flow 측정 추가
    if QUANTUM_FLOW_AVAILABLE and workspace_root:
        try:
            monitor = QuantumFlowMonitor(workspace_root)
            flow_metrics = monitor.measure_flow_state()
            result["quantum_flow"] = {
                "phase_coherence": flow_metrics.phase_coherence,
                "amplitude_sync": flow_metrics.amplitude_sync,
                "frequency_match": flow_metrics.frequency_match,
                "electron_flow_resistance": flow_metrics.electron_flow_resistance,
                "conductivity": flow_metrics.conductivity,
                "state": flow_metrics.state,
                "measured_at": datetime.now().isoformat(),
                "interpretation": _interpret_flow_state(flow_metrics.state, flow_metrics.phase_coherence)
            }
            
            # Flow 히스토리 저장
            monitor.save_measurement(flow_metrics)
            
        except Exception as e:
            result["quantum_flow"] = {
                "error": str(e),
                "available": False
            }
    
    return result


def _interpret_flow_state(state: str, coherence: float) -> str:
    """Flow 상태 해석"""
    interpretations = {
        "superconducting": f"🌟 초전도 상태 (coherence={coherence:.2f}) - 저항 없는 완벽한 흐름! Goal 생성에 최적",
        "coherent": f"✨ 결맞음 상태 (coherence={coherence:.2f}) - 좋은 흐름 상태. Goal 생성 권장",
        "resistive": f"⚡ 저항 상태 (coherence={coherence:.2f}) - 흐름에 약간의 저항. Self-care 필요",
        "chaotic": f"🌀 혼돈 상태 (coherence={coherence:.2f}) - 흐름 단절. 휴식 및 재정비 필요"
    }
    return interpretations.get(state, f"❓ 알 수 없는 상태 (coherence={coherence:.2f})")


def format_output(summary: Dict[str, Any]) -> str:
    if summary.get("count", 0) == 0:
        output = "❗ 최근 기간에 해당하는 Self-Care 텔레메트리가 없습니다."
        # Quantum Flow 정보가 있으면 추가
        if "quantum_flow" in summary and not summary["quantum_flow"].get("error"):
            qf = summary["quantum_flow"]
            output += f"\n\n🌊 Quantum Flow State:\n{qf.get('interpretation', 'N/A')}"
        return output

    lines = [
        f"Self-Care Telemetry Summary (last {summary['hours']}h)",
        f"- Samples: {summary['count']}",
        f"- Avg stagnation: {summary['stagnation_avg']:.3f}",
        f"- 95th percentile stagnation: {summary['stagnation_p95']:.3f}",
        f"- Stagnation >0.3 count: {summary['stagnation_over_03']}",
        f"- Stagnation >0.5 count: {summary['stagnation_over_05']}",
        f"- Avg queue usage ratio: {summary['queue_ratio_avg']:.2f}",
        f"- Avg memory growth rate: {summary['memory_growth_avg']:.3f}",
        f"- Avg latency_p99: {summary['latency_p99_avg']:.1f} ms",
        f"- Avg throughput ratio: {summary['throughput_ratio_avg']:.2f}",
        f"- Circulation OK rate: {summary['circulation_ok_rate']*100:.1f}%",
    ]
    
    # 🔄 Quantum Flow 정보 추가
    if "quantum_flow" in summary:
        qf = summary["quantum_flow"]
        if not qf.get("error"):
            lines.append("")
            lines.append("🌊 Quantum Flow State:")
            lines.append(f"  {qf.get('interpretation', 'N/A')}")
            lines.append(f"  - Conductivity: {qf.get('conductivity', 0):.3f} S")
            lines.append(f"  - Resistance: {qf.get('electron_flow_resistance', 0):.3f} Ω")
        else:
            lines.append("")
            lines.append(f"⚠️  Quantum Flow measurement unavailable: {qf.get('error', 'Unknown')}")
    
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Self-Care 텔레메트리 집계 + Quantum Flow 측정")
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="요약할 최근 시간(기본 24시간)",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("outputs") / "self_care_metrics.jsonl",
        help="Self-care 텔레메트리 JSONL 경로",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="요약을 JSON으로 출력",
    )
    parser.add_argument(
        "--summary-path",
        type=Path,
        help="요약 결과를 JSON 파일로 저장할 경로",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=get_workspace_root(),
        help="워크스페이스 루트 경로",
    )
    args = parser.parse_args()

    entries = load_entries(args.path)
    summary = summarize(entries, args.hours, workspace_root=args.workspace_root)

    if args.summary_path:
        payload = dict(summary)
        payload["generated_at"] = datetime.now().isoformat()
        summary_path = args.summary_path
        try:
            summary_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"✅ Summary written to {summary_path}")

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(format_output(summary))


if __name__ == "__main__":
    main()
