"""
Ledger 기반 Async vs Sequential 레이턴시 분석
이미 실행된 태스크의 Ledger 데이터를 분석하여 Async Thesis의 효과 측정
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import statistics


def load_ledger(ledger_path: Path) -> List[Dict[str, Any]]:
    """Ledger 로드"""
    if not ledger_path.exists():
        return []
    
    events = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                events.append(json.loads(line))
            except Exception:
                pass
    return events


def extract_task_list(events: List[Dict[str, Any]]) -> List[str]:
    """thesis_end, antithesis_end, synthesis_end 중 하나라도 있는 태스크 목록 추출"""
    task_ids = set()
    for e in events:
        if e.get("event") in ["thesis_end", "antithesis_end", "synthesis_end"] and e.get("task_id"):
            task_ids.add(e.get("task_id"))
    return sorted(task_ids)


def get_task_metrics(events: List[Dict[str, Any]], task_id: str) -> Dict[str, Any]:
    """특정 태스크의 메트릭 추출"""
    task_events = [e for e in events if e.get("task_id") == task_id]
    
    def get_duration(event_name: str) -> float:
        matches = [e for e in task_events if e.get("event") == event_name]
        return float(matches[-1].get("duration_sec", 0.0)) if matches else 0.0
    
    def get_flag(event_name: str) -> bool:
        return any(e.get("event") == event_name for e in task_events)
    
    thesis = get_duration("thesis_end")
    anti = get_duration("antithesis_end")
    synth = get_duration("synthesis_end")
    
    # 유효한 데이터인지 확인 (최소 1개 단계는 duration이 있어야 함)
    if thesis == 0 and anti == 0 and synth == 0:
        return None
    
    async_enabled = get_flag("thesis_async_enabled")
    
    return {
        "task_id": task_id,
        "thesis": thesis,
        "antithesis": anti,
        "synthesis": synth,
        "total": thesis + anti + synth,
        "async_enabled": async_enabled,
        "second_pass": get_flag("second_pass_start"),
    }


def analyze_by_mode(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """모드별 분석"""
    async_tasks = [t for t in tasks if t["async_enabled"]]
    seq_tasks = [t for t in tasks if not t["async_enabled"]]
    
    analysis = {}
    
    for mode, data in [("async", async_tasks), ("sequential", seq_tasks)]:
        if not data:
            analysis[mode] = {
                "count": 0,
                "error": "No data",
            }
            continue
        
        analysis[mode] = {
            "count": len(data),
            "thesis": {
                "mean": statistics.mean(t["thesis"] for t in data),
                "stdev": statistics.stdev(t["thesis"] for t in data) if len(data) > 1 else 0.0,
                "min": min(t["thesis"] for t in data),
                "max": max(t["thesis"] for t in data),
            },
            "antithesis": {
                "mean": statistics.mean(t["antithesis"] for t in data),
                "stdev": statistics.stdev(t["antithesis"] for t in data) if len(data) > 1 else 0.0,
                "min": min(t["antithesis"] for t in data),
                "max": max(t["antithesis"] for t in data),
            },
            "synthesis": {
                "mean": statistics.mean(t["synthesis"] for t in data),
                "stdev": statistics.stdev(t["synthesis"] for t in data) if len(data) > 1 else 0.0,
                "min": min(t["synthesis"] for t in data),
                "max": max(t["synthesis"] for t in data),
            },
            "total": {
                "mean": statistics.mean(t["total"] for t in data),
                "stdev": statistics.stdev(t["total"] for t in data) if len(data) > 1 else 0.0,
                "min": min(t["total"] for t in data),
                "max": max(t["total"] for t in data),
            },
            "second_pass_rate": sum(1 for t in data if t["second_pass"]) / len(data),
        }
    
    # 비교
    if "async" in analysis and "sequential" in analysis and "total" in analysis["async"] and "total" in analysis["sequential"]:
        seq_total = analysis["sequential"]["total"]["mean"]
        async_total = analysis["async"]["total"]["mean"]
        
        analysis["comparison"] = {
            "latency_reduction_sec": seq_total - async_total,
            "latency_reduction_pct": ((seq_total - async_total) / seq_total * 100) if seq_total > 0 else 0.0,
            "recommendation": "async" if async_total < seq_total else "sequential",
        }
    
    return analysis


def generate_report(tasks: List[Dict[str, Any]], analysis: Dict[str, Any], output_path: Path):
    """리포트 생성"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        "# Ledger-Based Async vs Sequential Analysis",
        "",
        f"Generated: {ts}",
        f"Total tasks analyzed: {len(tasks)}",
        "",
    ]
    
    if "comparison" in analysis:
        comp = analysis["comparison"]
        lines.extend([
            "## Executive Summary",
            "",
            f"- **Latency Reduction**: {comp['latency_reduction_sec']:.2f}s ({comp['latency_reduction_pct']:.1f}%)",
            f"- **Recommendation**: {'✅ Enable Async Thesis' if comp['recommendation'] == 'async' else '⚠️ Keep Sequential'}",
            "",
        ])
    
    for mode in ["sequential", "async"]:
        if mode not in analysis or "total" not in analysis[mode]:
            continue
        
        data = analysis[mode]
        lines.extend([
            f"## {mode.upper()} Mode",
            "",
            f"- Sample Size: {data['count']}",
            f"- Thesis: {data['thesis']['mean']:.2f}s (±{data['thesis']['stdev']:.2f}) [{data['thesis']['min']:.2f}-{data['thesis']['max']:.2f}]",
            f"- Antithesis: {data['antithesis']['mean']:.2f}s (±{data['antithesis']['stdev']:.2f}) [{data['antithesis']['min']:.2f}-{data['antithesis']['max']:.2f}]",
            f"- Synthesis: {data['synthesis']['mean']:.2f}s (±{data['synthesis']['stdev']:.2f}) [{data['synthesis']['min']:.2f}-{data['synthesis']['max']:.2f}]",
            f"- **Total: {data['total']['mean']:.2f}s (±{data['total']['stdev']:.2f}) [{data['total']['min']:.2f}-{data['total']['max']:.2f}]**",
            f"- Second Pass Rate: {data['second_pass_rate']:.1%}",
            "",
        ])
    
    lines.extend([
        "## Sample Data",
        "",
    ])
    
    for t in tasks[:10]:  # 최대 10개만 표시
        mode = "ASYNC" if t["async_enabled"] else "SEQ"
        lines.append(f"- [{mode}] {t['task_id']}: {t['total']:.2f}s (T:{t['thesis']:.2f} A:{t['antithesis']:.2f} S:{t['synthesis']:.2f})")
    
    if len(tasks) > 10:
        lines.append(f"- ... ({len(tasks) - 10} more tasks)")
    
    lines.append("")
    
    report = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return report


def main(argv: List[str]) -> int:
    here = Path(__file__).resolve()
    root = here.parents[1]
    ledger_path = root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
    
    if not ledger_path.exists():
        print("Error: Ledger not found")
        return 1
    
    # Ledger 로드
    print("Loading ledger...")
    events = load_ledger(ledger_path)
    print(f"  {len(events)} events loaded")
    
    # 태스크 목록 추출
    task_ids = extract_task_list(events)
    print(f"  {len(task_ids)} completed tasks found")
    
    # 메트릭 추출
    print("Extracting metrics...")
    tasks = []
    for tid in task_ids:
        metrics = get_task_metrics(events, tid)
        if metrics:
            tasks.append(metrics)
    
    print(f"  {len(tasks)} tasks with valid metrics")
    
    if not tasks:
        print("Error: No tasks with valid duration data")
        return 1
    
    # 모드별 분석
    analysis = analyze_by_mode(tasks)
    
    # 리포트 생성
    output_md = root / "outputs" / "ledger_async_analysis_latest.md"
    report = generate_report(tasks, analysis, output_md)
    print(f"\n{report}")
    
    # JSON 저장
    output_json = root / "outputs" / "ledger_async_analysis_latest.json"
    json_data = {
        "timestamp": datetime.now().isoformat(),
        "total_tasks": len(tasks),
        "tasks": tasks,
        "analysis": analysis,
    }
    output_json.write_text(json.dumps(json_data, indent=2), encoding="utf-8")
    
    print(f"\n[✓] Analysis saved:")
    print(f"    MD:   {output_md}")
    print(f"    JSON: {output_json}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
