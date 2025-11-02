#!/usr/bin/env python
"""
레이턴시 트렌드 분석 및 대시보드 생성
- 24시간 레이턴시 분포
- Persona별 duration 분해
- 경고 임계값 초과 이벤트
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import sys

def analyze_latency_trends(hours=24):
    ledger_path = Path("fdo_agi_repo/memory/resonance_ledger.jsonl")
    if not ledger_path.exists():
        print(f"❌ Ledger not found: {ledger_path}")
        return None
    
    cutoff = datetime.now() - timedelta(hours=hours)
    
    # 데이터 수집
    tasks = defaultdict(dict)  # task_id -> {thesis: duration, antithesis: duration, ...}
    latency_warnings = []
    
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry.get("timestamp", "2000-01-01T00:00:00"))
                if ts < cutoff:
                    continue
                
                event = entry.get("event", "")
                task_id = entry.get("task_id", "")
                
                # Persona duration 수집
                if event in ["thesis_end", "antithesis_end", "synthesis_end"]:
                    persona = event.replace("_end", "")
                    duration = entry.get("duration_sec", 0)
                    tasks[task_id][persona] = duration
                
                # Latency 경고 수집
                if event == "latency_warning":
                    latency_warnings.append({
                        "task_id": task_id,
                        "latency_ms": entry.get("latency_ms", 0),
                        "max_latency_ms": entry.get("max_latency_ms", 0),
                        "timestamp": ts
                    })
            except Exception as e:
                continue
    
    # 통계 계산
    total_durations = []
    thesis_durations = []
    antithesis_durations = []
    synthesis_durations = []
    
    for task_id, durations in tasks.items():
        if all(k in durations for k in ["thesis", "antithesis", "synthesis"]):
            total = sum(durations.values())
            total_durations.append(total)
            thesis_durations.append(durations["thesis"])
            antithesis_durations.append(durations["antithesis"])
            synthesis_durations.append(durations["synthesis"])
    
    if not total_durations:
        print(f"⚠️ No complete task data in last {hours}h")
        return None
    
    stats = {
        "period_hours": hours,
        "total_tasks": len(total_durations),
        "latency_warnings": len(latency_warnings),
        "total_latency": {
            "avg_sec": sum(total_durations) / len(total_durations),
            "min_sec": min(total_durations),
            "max_sec": max(total_durations),
            "p50_sec": sorted(total_durations)[len(total_durations) // 2],
            "p95_sec": sorted(total_durations)[int(len(total_durations) * 0.95)]
        },
        "persona_breakdown": {
            "thesis": {
                "avg_sec": sum(thesis_durations) / len(thesis_durations),
                "min_sec": min(thesis_durations),
                "max_sec": max(thesis_durations)
            },
            "antithesis": {
                "avg_sec": sum(antithesis_durations) / len(antithesis_durations),
                "min_sec": min(antithesis_durations),
                "max_sec": max(antithesis_durations)
            },
            "synthesis": {
                "avg_sec": sum(synthesis_durations) / len(synthesis_durations),
                "min_sec": min(synthesis_durations),
                "max_sec": max(synthesis_durations)
            }
        },
        "warnings": latency_warnings[:10]  # 최근 10건
    }
    
    return stats

def generate_html_dashboard(stats):
    if not stats:
        return "<html><body><h1>No data available</h1></body></html>"
    
    total = stats["total_latency"]
    thesis = stats["persona_breakdown"]["thesis"]
    antithesis = stats["persona_breakdown"]["antithesis"]
    synthesis = stats["persona_breakdown"]["synthesis"]
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Latency Performance Dashboard</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; color: white; }}
        .metric-card.warning {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .metric-card.success {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
        .metric-value {{ font-size: 2.5em; font-weight: bold; margin: 10px 0; }}
        .metric-label {{ font-size: 0.9em; opacity: 0.9; }}
        .persona-chart {{ display: flex; gap: 10px; margin: 30px 0; height: 200px; align-items: flex-end; }}
        .persona-bar {{ flex: 1; background: #3498db; border-radius: 4px 4px 0 0; position: relative; }}
        .persona-bar.thesis {{ background: #e74c3c; }}
        .persona-bar.antithesis {{ background: #f39c12; }}
        .persona-bar.synthesis {{ background: #2ecc71; }}
        .bar-label {{ position: absolute; top: -30px; width: 100%; text-align: center; font-weight: bold; color: #2c3e50; }}
        .bar-value {{ position: absolute; bottom: 5px; width: 100%; text-align: center; color: white; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #3498db; color: white; }}
        .timestamp {{ font-size: 0.85em; color: #7f8c8d; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Latency Performance Dashboard</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Period: {stats['period_hours']}h</p>
        
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Average Latency</div>
                <div class="metric-value">{total['avg_sec']:.1f}s</div>
                <div class="metric-label">P95: {total['p95_sec']:.1f}s | Max: {total['max_sec']:.1f}s</div>
            </div>
            <div class="metric-card success">
                <div class="metric-label">Total Tasks</div>
                <div class="metric-value">{stats['total_tasks']}</div>
                <div class="metric-label">Completed in {stats['period_hours']}h</div>
            </div>
            <div class="metric-card warning">
                <div class="metric-label">Latency Warnings</div>
                <div class="metric-value">{stats['latency_warnings']}</div>
                <div class="metric-label">Threshold violations</div>
            </div>
        </div>
        
        <h2>📊 Persona Breakdown</h2>
        <div class="persona-chart">
            <div class="persona-bar thesis" style="height: {thesis['avg_sec'] / total['avg_sec'] * 100}%;">
                <div class="bar-label">Thesis</div>
                <div class="bar-value">{thesis['avg_sec']:.1f}s</div>
            </div>
            <div class="persona-bar antithesis" style="height: {antithesis['avg_sec'] / total['avg_sec'] * 100}%;">
                <div class="bar-label">Antithesis</div>
                <div class="bar-value">{antithesis['avg_sec']:.1f}s</div>
            </div>
            <div class="persona-bar synthesis" style="height: {synthesis['avg_sec'] / total['avg_sec'] * 100}%;">
                <div class="bar-label">Synthesis</div>
                <div class="bar-value">{synthesis['avg_sec']:.1f}s</div>
            </div>
        </div>
        
        <h2>⚠️ Recent Warnings (Top 10)</h2>
        <table>
            <tr>
                <th>Task ID</th>
                <th>Latency</th>
                <th>Threshold</th>
                <th>Exceeded By</th>
                <th>Timestamp</th>
            </tr>
"""
    
    for w in stats["warnings"]:
        exceeded = w["latency_ms"] - w["max_latency_ms"]
        exceeded_pct = (exceeded / w["max_latency_ms"]) * 100
        html += f"""
            <tr>
                <td>{w['task_id'][:8]}...</td>
                <td>{w['latency_ms'] / 1000:.1f}s</td>
                <td>{w['max_latency_ms'] / 1000:.1f}s</td>
                <td style="color: #e74c3c; font-weight: bold;">+{exceeded / 1000:.1f}s ({exceeded_pct:.0f}%)</td>
                <td class="timestamp">{w['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
"""
    
    html += """
        </table>
        
        <h2>💡 Optimization Recommendations</h2>
        <ul>
"""
    
    if total["avg_sec"] > 20:
        html += "<li>🔴 <strong>Critical</strong>: Average latency > 20s. Consider parallel execution for Thesis/Antithesis.</li>"
    elif total["avg_sec"] > 15:
        html += "<li>🟡 <strong>Warning</strong>: Average latency > 15s. Monitor and optimize LLM calls.</li>"
    else:
        html += "<li>🟢 <strong>Good</strong>: Average latency within acceptable range.</li>"
    
    if stats["latency_warnings"] > 5:
        html += f"<li>🔴 <strong>High</strong>: {stats['latency_warnings']} warnings in {stats['period_hours']}h. Increase timeout threshold or optimize execution.</li>"
    
    if antithesis["avg_sec"] > thesis["avg_sec"] * 2:
        html += "<li>🟡 Antithesis taking 2x longer than Thesis. Investigate prompt complexity.</li>"
    
    html += """
        </ul>
    </div>
</body>
</html>
"""
    
    return html

def main():
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    
    print(f"🔍 Analyzing latency trends (last {hours}h)...")
    stats = analyze_latency_trends(hours)
    
    if not stats:
        print("❌ Analysis failed (no data or error)")
        return 1
    
    # JSON 저장
    json_path = Path("outputs/latency_performance_latest.json")
    json_path.parent.mkdir(exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, default=str)
    print(f"✅ JSON saved: {json_path}")
    
    # HTML 대시보드 생성
    html = generate_html_dashboard(stats)
    html_path = Path("outputs/latency_performance_dashboard.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ Dashboard saved: {html_path}")
    
    # 요약 출력
    print("\n📊 Summary:")
    print(f"  Total Tasks: {stats['total_tasks']}")
    print(f"  Avg Latency: {stats['total_latency']['avg_sec']:.1f}s")
    print(f"  P95 Latency: {stats['total_latency']['p95_sec']:.1f}s")
    print(f"  Warnings: {stats['latency_warnings']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
