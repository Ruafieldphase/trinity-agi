"""
Async Thesis 24시간 모니터링 대시보드
Production 배포 후 품질/안정성 추적

Usage:
    python scripts/monitor_async_thesis_health.py
    python scripts/monitor_async_thesis_health.py --hours 24
    python scripts/monitor_async_thesis_health.py --alert
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
from workspace_root import get_workspace_root


def load_ledger(ledger_path: Path, hours: int = 24) -> List[Dict[str, Any]]:
    """Ledger에서 최근 N시간 데이터 로드"""
    if not ledger_path.exists():
        return []
    
    import time
    cutoff_unix = time.time() - (hours * 3600)
    events = []
    
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                
                # UNIX timestamp 파싱 (ts 필드 우선, 그 다음 timestamp)
                ts_unix = event.get("ts") or event.get("timestamp")
                
                if ts_unix:
                    # float 또는 ISO string
                    if isinstance(ts_unix, (int, float)):
                        if ts_unix >= cutoff_unix:
                            events.append(event)
                    elif isinstance(ts_unix, str):
                        # ISO string을 UNIX timestamp로 변환
                        try:
                            dt = datetime.fromisoformat(ts_unix.replace("Z", "+00:00"))
                            ts_float = dt.timestamp()
                            if ts_float >= cutoff_unix:
                                events.append(event)
                        except:
                            pass
            except json.JSONDecodeError:
                continue
    
    return events


def analyze_async_health(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Async Thesis 헬스 메트릭 계산"""
    
    # 태스크별로 이벤트 그룹핑
    tasks = defaultdict(list)
    for ev in events:
        tid = ev.get("task_id", "unknown")
        tasks[tid].append(ev)
    
    # 메트릭 초기화
    metrics = {
        "total_tasks": 0,
        "async_tasks": 0,
        "sequential_tasks": 0,
        "fallback_count": 0,
        "error_count": 0,
        "second_pass_count": 0,
        "avg_latency_async": 0.0,
        "avg_latency_seq": 0.0,
        "async_durations": [],
        "seq_durations": [],
    }
    
    for tid, task_events in tasks.items():
        # 완료된 태스크만 카운트
        has_end = any(e.get("event") == "synthesis_end" for e in task_events)
        if not has_end:
            continue
        
        metrics["total_tasks"] += 1
        
        # Async 여부 확인
        is_async = any(e.get("event") == "thesis_async_enabled" for e in task_events)
        has_fallback = any(e.get("event") == "thesis_async_fallback" for e in task_events)
        has_error = any("error" in e.get("event", "") for e in task_events)
        
        # Second pass 정확한 판단: symmetry phase의 second_pass 필드 확인
        has_second_pass = False
        for e in task_events:
            if e.get("event") == "autopoietic_phase" and e.get("phase") == "symmetry" and e.get("stage") == "end":
                if e.get("second_pass") is True:
                    has_second_pass = True
                    break
        
        if is_async:
            metrics["async_tasks"] += 1
        else:
            metrics["sequential_tasks"] += 1
        
        if has_fallback:
            metrics["fallback_count"] += 1
        
        if has_error:
            metrics["error_count"] += 1
        
        if has_second_pass:
            metrics["second_pass_count"] += 1
        
        # Duration 추출
        thesis_dur = None
        anti_dur = None
        synth_dur = None
        
        for ev in task_events:
            if ev.get("event") == "thesis_end":
                thesis_dur = ev.get("duration_sec", 0)
            elif ev.get("event") == "antithesis_end":
                anti_dur = ev.get("duration_sec", 0)
            elif ev.get("event") == "synthesis_end":
                synth_dur = ev.get("duration_sec", 0)
        
        if thesis_dur and anti_dur and synth_dur:
            total = thesis_dur + anti_dur + synth_dur
            if is_async:
                metrics["async_durations"].append(total)
            else:
                metrics["seq_durations"].append(total)
    
    # 평균 계산
    if metrics["async_durations"]:
        metrics["avg_latency_async"] = sum(metrics["async_durations"]) / len(metrics["async_durations"])
    
    if metrics["seq_durations"]:
        metrics["avg_latency_seq"] = sum(metrics["seq_durations"]) / len(metrics["seq_durations"])
    
    # 비율 계산
    metrics["fallback_rate"] = (metrics["fallback_count"] / metrics["async_tasks"] * 100) if metrics["async_tasks"] > 0 else 0.0
    metrics["error_rate"] = (metrics["error_count"] / metrics["total_tasks"] * 100) if metrics["total_tasks"] > 0 else 0.0
    metrics["second_pass_rate"] = (metrics["second_pass_count"] / metrics["total_tasks"] * 100) if metrics["total_tasks"] > 0 else 0.0
    
    return metrics


def check_alerts(metrics: Dict[str, Any]) -> List[str]:
    """알림 조건 확인"""
    alerts = []
    
    # Rollback 조건
    if metrics["fallback_rate"] > 10.0:
        alerts.append(f"🚨 HIGH FALLBACK RATE: {metrics['fallback_rate']:.1f}% (threshold: 10%)")
    
    if metrics["error_rate"] > 5.0:
        alerts.append(f"🚨 HIGH ERROR RATE: {metrics['error_rate']:.1f}% (threshold: 5%)")
    
    # 품질 저하 경고
    if metrics["second_pass_rate"] > 5.0:
        alerts.append(f"⚠️  QUALITY DEGRADATION: {metrics['second_pass_rate']:.1f}% second pass rate")
    
    # 성능 저하 경고
    if metrics["avg_latency_async"] > 0 and metrics["avg_latency_seq"] > 0:
        if metrics["avg_latency_async"] > metrics["avg_latency_seq"]:
            alerts.append(f"⚠️  ASYNC SLOWER: {metrics['avg_latency_async']:.1f}s vs {metrics['avg_latency_seq']:.1f}s")
    
    return alerts


def generate_report(metrics: Dict[str, Any], hours: int, alerts: List[str]) -> str:
    """리포트 생성"""
    
    # 상태 판단
    if alerts:
        if any("🚨" in a for a in alerts):
            status = "🔴 CRITICAL"
            recommendation = "⚠️  ROLLBACK RECOMMENDED"
        else:
            status = "🟡 WARNING"
            recommendation = "Monitor closely"
    else:
        status = "🟢 HEALTHY"
        recommendation = "Continue monitoring"
    
    report = f"""# Async Thesis Health Monitor

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: Last {hours} hours

## Status: {status}

**Recommendation**: {recommendation}

---

## Executive Summary

- **Total Tasks**: {metrics['total_tasks']}
- **Async Tasks**: {metrics['async_tasks']} ({metrics['async_tasks']/max(metrics['total_tasks'],1)*100:.1f}%)
- **Sequential Tasks**: {metrics['sequential_tasks']} ({metrics['sequential_tasks']/max(metrics['total_tasks'],1)*100:.1f}%)

---

## Critical Metrics (Rollback Triggers)

| Metric | Current | Threshold | Status |
|--------|---------|-----------|--------|
| **Fallback Rate** | {metrics['fallback_rate']:.1f}% | <10% | {'🔴 CRITICAL' if metrics['fallback_rate'] > 10 else '🟢 OK'} |
| **Error Rate** | {metrics['error_rate']:.1f}% | <5% | {'🔴 CRITICAL' if metrics['error_rate'] > 5 else '🟢 OK'} |
| **Second Pass** | {metrics['second_pass_rate']:.1f}% | <5% | {'🟡 WARNING' if metrics['second_pass_rate'] > 5 else '🟢 OK'} |

---

## Performance Metrics

| Mode | Count | Avg Latency | Samples |
|------|-------|-------------|---------|
| **Async** | {metrics['async_tasks']} | {metrics['avg_latency_async']:.2f}s | {len(metrics['async_durations'])} |
| **Sequential** | {metrics['sequential_tasks']} | {metrics['avg_latency_seq']:.2f}s | {len(metrics['seq_durations'])} |

"""

    if metrics['avg_latency_async'] > 0 and metrics['avg_latency_seq'] > 0:
        improvement = metrics['avg_latency_seq'] - metrics['avg_latency_async']
        pct = (improvement / metrics['avg_latency_seq']) * 100
        report += f"**Improvement**: {improvement:.2f}s ({pct:.1f}%)\n\n"
    
    report += "---\n\n"
    
    # 알림
    if alerts:
        report += "## 🚨 Alerts\n\n"
        for alert in alerts:
            report += f"- {alert}\n"
        report += "\n---\n\n"
    
    # 세부 카운트
    report += f"""## Detailed Counts

- Async enabled events: {metrics['async_tasks']}
- Fallback events: {metrics['fallback_count']}
- Error events: {metrics['error_count']}
- Second pass events: {metrics['second_pass_count']}

---

## Rollback Plan

If alerts are triggered:

```bash
# Option 1: Disable via config
sed -i 's/enabled: true/enabled: false/' fdo_agi_repo/configs/app.yaml

# Option 2: Environment variable
unset ASYNC_THESIS_ENABLED

# Verify
python scripts/run_sample_task.py
grep "thesis_async" fdo_agi_repo/memory/resonance_ledger.jsonl | tail -5
```

---

**Generated by**: `scripts/monitor_async_thesis_health.py`
"""
    
    return report


def main(argv: List[str]) -> int:
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor Async Thesis health")
    parser.add_argument("--hours", type=int, default=24, help="Hours to look back")
    parser.add_argument("--alert", action="store_true", help="Exit with error if alerts present")
    parser.add_argument("--json", help="Export JSON to file")
    
    args = parser.parse_args(argv[1:])
    
    # 경로 설정
    here = Path(__file__).resolve()
    root = get_workspace_root()
    ledger_path = root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
    output_md = root / "outputs" / "async_thesis_health_latest.md"
    
    print(f"Loading ledger from: {ledger_path}")
    print(f"Looking back: {args.hours} hours")
    
    # 데이터 로드
    events = load_ledger(ledger_path, args.hours)
    print(f"Loaded {len(events)} events")
    
    # 분석
    metrics = analyze_async_health(events)
    alerts = check_alerts(metrics)
    
    # 리포트 생성
    report = generate_report(metrics, args.hours, alerts)
    
    # 저장
    output_md.write_text(report, encoding="utf-8")
    print(f"\n✓ Report saved: {output_md}")
    
    # JSON 저장
    if args.json:
        json_path = Path(args.json)
        json_data = {
            "timestamp": datetime.now().isoformat(),
            "hours": args.hours,
            "metrics": metrics,
            "alerts": alerts,
        }
        json_path.write_text(json.dumps(json_data, indent=2), encoding="utf-8")
        print(f"✓ JSON saved: {json_path}")
    
    # 콘솔 출력
    print("\n" + "="*70)
    print(report)
    print("="*70)
    
    # Alert 모드
    if args.alert and alerts:
        print(f"\n🚨 {len(alerts)} alert(s) detected!")
        return 1
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
