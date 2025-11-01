"""
Async Thesis vs Sequential 비교 테스트
각 모드로 N건씩 실행하고 레이턴시, 품질, 성공률을 비교
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics


@dataclass
class TaskResult:
    task_id: str
    mode: str  # "async" or "sequential"
    success: bool
    thesis_duration: float
    antithesis_duration: float
    synthesis_duration: float
    total_duration: float
    quality_score: float
    second_pass_triggered: bool
    error: Optional[str] = None


def setup_paths():
    """경로 설정"""
    here = Path(__file__).resolve()
    root = here.parents[1]
    fdo = root / "fdo_agi_repo"
    
    for p in [str(root), str(fdo)]:
        if p not in sys.path:
            sys.path.insert(0, p)
    
    return root, fdo


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


def extract_task_metrics(events: List[Dict[str, Any]], task_id: str) -> Dict[str, Any]:
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
    
    # Quality score 추정 (synthesis의 citation 수로 대체)
    synth_events = [e for e in task_events if e.get("event") == "synthesis_end"]
    citations = synth_events[-1].get("citations", 0) if synth_events else 0
    quality = min(1.0, citations / 5.0) if citations > 0 else 0.5
    
    return {
        "thesis": thesis,
        "antithesis": anti,
        "synthesis": synth,
        "total": thesis + anti + synth,
        "quality": quality,
        "second_pass": get_flag("second_pass_start"),
        "async_enabled": get_flag("thesis_async_enabled"),
    }


def run_single_task(mode: str, sample_num: int) -> TaskResult:
    """단일 태스크 실행"""
    from fdo_agi_repo.orchestrator import pipeline
    
    # 환경변수 설정
    if mode == "async":
        os.environ["ASYNC_THESIS_ENABLED"] = "true"
    else:
        os.environ.pop("ASYNC_THESIS_ENABLED", None)
    
    task_id = f"compare-{mode}-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    spec = {
        "task_id": task_id,
        "title": f"Latency Test {mode.upper()} #{sample_num}",
        "goal": "Compare async vs sequential execution performance",
        "constraints": [],
        "inputs": {},
        "scope": "analysis",
        "permissions": ["READ"],
        "evidence_required": False,
    }
    
    start = time.time()
    try:
        result = pipeline.run_task({}, spec)
        elapsed = time.time() - start
        success = result.get("status") == "completed"
        error = None if success else result.get("error", "Unknown error")
    except Exception as e:
        elapsed = time.time() - start
        success = False
        error = str(e)
    
    # Ledger에서 메트릭 추출
    root, fdo = setup_paths()
    ledger_path = fdo / "memory" / "resonance_ledger.jsonl"
    time.sleep(0.5)  # Ledger 쓰기 대기
    events = load_ledger(ledger_path)
    metrics = extract_task_metrics(events, task_id)
    
    return TaskResult(
        task_id=task_id,
        mode=mode,
        success=success,
        thesis_duration=metrics["thesis"],
        antithesis_duration=metrics["antithesis"],
        synthesis_duration=metrics["synthesis"],
        total_duration=metrics["total"],
        quality_score=metrics["quality"],
        second_pass_triggered=metrics["second_pass"],
        error=error,
    )


def run_comparison(runs_per_mode: int = 3) -> Dict[str, Any]:
    """비교 테스트 실행"""
    print(f"\n{'='*60}")
    print(f"  Async vs Sequential Comparison Test")
    print(f"  Runs per mode: {runs_per_mode}")
    print(f"{'='*60}\n")
    
    results = {"async": [], "sequential": []}
    
    for mode in ["sequential", "async"]:
        print(f"\n[{mode.upper()}] Running {runs_per_mode} tasks...")
        for i in range(runs_per_mode):
            print(f"  #{i+1}/{runs_per_mode}... ", end="", flush=True)
            result = run_single_task(mode, i + 1)
            results[mode].append(result)
            status = "✓" if result.success else "✗"
            print(f"{status} ({result.total_duration:.1f}s)")
            time.sleep(1)  # Rate limiting
    
    return results


def analyze_results(results: Dict[str, List[TaskResult]]) -> Dict[str, Any]:
    """결과 분석"""
    analysis = {}
    
    for mode in ["sequential", "async"]:
        data = results[mode]
        successful = [r for r in data if r.success]
        
        if not successful:
            analysis[mode] = {
                "runs": len(data),
                "success_rate": 0.0,
                "error": "No successful runs",
            }
            continue
        
        analysis[mode] = {
            "runs": len(data),
            "success_rate": len(successful) / len(data),
            "thesis": {
                "mean": statistics.mean(r.thesis_duration for r in successful),
                "stdev": statistics.stdev(r.thesis_duration for r in successful) if len(successful) > 1 else 0.0,
                "min": min(r.thesis_duration for r in successful),
                "max": max(r.thesis_duration for r in successful),
            },
            "antithesis": {
                "mean": statistics.mean(r.antithesis_duration for r in successful),
                "stdev": statistics.stdev(r.antithesis_duration for r in successful) if len(successful) > 1 else 0.0,
                "min": min(r.antithesis_duration for r in successful),
                "max": max(r.antithesis_duration for r in successful),
            },
            "synthesis": {
                "mean": statistics.mean(r.synthesis_duration for r in successful),
                "stdev": statistics.stdev(r.synthesis_duration for r in successful) if len(successful) > 1 else 0.0,
                "min": min(r.synthesis_duration for r in successful),
                "max": max(r.synthesis_duration for r in successful),
            },
            "total": {
                "mean": statistics.mean(r.total_duration for r in successful),
                "stdev": statistics.stdev(r.total_duration for r in successful) if len(successful) > 1 else 0.0,
                "min": min(r.total_duration for r in successful),
                "max": max(r.total_duration for r in successful),
            },
            "quality": {
                "mean": statistics.mean(r.quality_score for r in successful),
                "stdev": statistics.stdev(r.quality_score for r in successful) if len(successful) > 1 else 0.0,
            },
            "second_pass_rate": sum(1 for r in successful if r.second_pass_triggered) / len(successful),
        }
    
    # 비교 계산
    if all(mode in analysis and "total" in analysis[mode] for mode in ["sequential", "async"]):
        seq_total = analysis["sequential"]["total"]["mean"]
        async_total = analysis["async"]["total"]["mean"]
        
        analysis["comparison"] = {
            "latency_reduction_sec": seq_total - async_total,
            "latency_reduction_pct": ((seq_total - async_total) / seq_total * 100) if seq_total > 0 else 0.0,
            "quality_delta": analysis["async"]["quality"]["mean"] - analysis["sequential"]["quality"]["mean"],
            "recommendation": "async" if async_total < seq_total and abs(analysis["async"]["quality"]["mean"] - analysis["sequential"]["quality"]["mean"]) < 0.1 else "sequential",
        }
    else:
        analysis["comparison"] = {
            "error": "Insufficient successful runs for comparison",
        }
    
    return analysis


def generate_report(results: Dict[str, List[TaskResult]], analysis: Dict[str, Any], output_path: Path):
    """리포트 생성"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        "# Async vs Sequential Comparison Report",
        "",
        f"Generated: {ts}",
        f"Runs per mode: {len(results['sequential'])}",
        "",
        "## Executive Summary",
        "",
    ]
    
    if "comparison" in analysis and "error" not in analysis["comparison"]:
        comp = analysis["comparison"]
        lines.extend([
            f"- **Latency Reduction**: {comp['latency_reduction_sec']:.2f}s ({comp['latency_reduction_pct']:.1f}%)",
            f"- **Quality Impact**: {comp['quality_delta']:+.3f}",
            f"- **Recommendation**: {'✅ Enable Async Thesis' if comp['recommendation'] == 'async' else '⚠️ Keep Sequential'}",
            "",
        ])
    elif "comparison" in analysis:
        lines.extend([
            f"- **Status**: ⚠️ {analysis['comparison'].get('error', 'Insufficient data')}",
            "",
        ])
    
    for mode in ["sequential", "async"]:
        if mode not in analysis:
            continue
        
        data = analysis[mode]
        lines.extend([
            f"## {mode.upper()} Mode",
            "",
            f"- Success Rate: {data['success_rate']:.1%}",
        ])
        
        if "total" in data:
            lines.extend([
                f"- Thesis: {data['thesis']['mean']:.2f}s (±{data['thesis']['stdev']:.2f})",
                f"- Antithesis: {data['antithesis']['mean']:.2f}s (±{data['antithesis']['stdev']:.2f})",
                f"- Synthesis: {data['synthesis']['mean']:.2f}s (±{data['synthesis']['stdev']:.2f})",
                f"- **Total: {data['total']['mean']:.2f}s (±{data['total']['stdev']:.2f})**",
                f"- Quality Score: {data['quality']['mean']:.3f} (±{data['quality']['stdev']:.3f})",
                f"- Second Pass Rate: {data['second_pass_rate']:.1%}",
            ])
        else:
            lines.append(f"- Error: {data.get('error', 'No successful runs')}")
        
        lines.append("")
    
    lines.extend([
        "## Raw Data",
        "",
        "### Sequential",
    ])
    for r in results["sequential"]:
        status = "✓" if r.success else "✗"
        lines.append(f"- {status} {r.task_id}: {r.total_duration:.2f}s (T:{r.thesis_duration:.2f} A:{r.antithesis_duration:.2f} S:{r.synthesis_duration:.2f})")
    
    lines.extend([
        "",
        "### Async",
    ])
    for r in results["async"]:
        status = "✓" if r.success else "✗"
        lines.append(f"- {status} {r.task_id}: {r.total_duration:.2f}s (T:{r.thesis_duration:.2f} A:{r.antithesis_duration:.2f} S:{r.synthesis_duration:.2f})")
    
    lines.append("")
    
    report = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return report


def main(argv: List[str]) -> int:
    root, _ = setup_paths()
    
    # 실행 횟수 파싱
    runs = 3
    if len(argv) > 1:
        try:
            runs = int(argv[1])
        except ValueError:
            print(f"Invalid runs count: {argv[1]}, using default: 3")
    
    # 비교 테스트 실행
    results = run_comparison(runs_per_mode=runs)
    
    # 분석
    analysis = analyze_results(results)
    
    # 리포트 생성
    output_md = root / "outputs" / "async_comparison_latest.md"
    report = generate_report(results, analysis, output_md)
    print(f"\n{report}")
    
    # JSON 저장
    output_json = root / "outputs" / "async_comparison_latest.json"
    json_data = {
        "timestamp": datetime.now().isoformat(),
        "runs_per_mode": runs,
        "results": {
            mode: [asdict(r) for r in data]
            for mode, data in results.items()
        },
        "analysis": analysis,
    }
    output_json.write_text(json.dumps(json_data, indent=2), encoding="utf-8")
    
    print(f"\n[✓] Report saved:")
    print(f"    MD:   {output_md}")
    print(f"    JSON: {output_json}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
