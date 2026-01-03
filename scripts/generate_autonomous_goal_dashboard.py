#!/usr/bin/env python3
"""
자율 목표 시스템 대시보드 생성기
goal_tracker.json과 autonomous_goals_latest.json을 분석하여 HTML 대시보드 생성
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import subprocess
from workspace_root import get_workspace_root

WORKSPACE = get_workspace_root()
GOAL_TRACKER = WORKSPACE / "fdo_agi_repo" / "memory" / "goal_tracker.json"
LATEST_GOALS = WORKSPACE / "outputs" / "autonomous_goals_latest.json"
LOOP_LOG = WORKSPACE / "outputs" / "autonomous_goal_loop.log"
OUTPUT_HTML = WORKSPACE / "outputs" / "autonomous_goal_dashboard_latest.html"
TEMPLATE_HTML = WORKSPACE / "scripts" / "templates" / "autonomous_goal_dashboard.html"


def load_goal_tracker() -> Dict[str, Any]:
    """goal_tracker.json 로드"""
    if not GOAL_TRACKER.exists():
        return {"goals": []}
    
    with open(GOAL_TRACKER, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def load_latest_goals() -> List[Dict[str, Any]]:
    """최신 생성된 목표 로드"""
    if not LATEST_GOALS.exists():
        return []
    
    with open(LATEST_GOALS, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("goals", [])


def check_background_loop() -> Dict[str, Any]:
    """백그라운드 루프 상태 확인"""
    try:
        # PowerShell Job 확인
        result = subprocess.run(
            ["powershell", "-Command", "Get-Job | Where-Object { $_.Name -eq 'AutoGoalLoop' } | ConvertTo-Json"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            job_info = json.loads(result.stdout)
            return {
                "status": "running",
                "state": job_info.get("State", "Unknown"),
                "id": job_info.get("Id", "Unknown")
            }
        else:
            return {"status": "stopped", "state": "NotRunning", "id": None}
    except Exception as e:
        return {"status": "unknown", "error": str(e)}


def analyze_metrics(tracker: Dict[str, Any]) -> Dict[str, Any]:
    """메트릭 분석"""
    goals = tracker.get("goals", [])
    
    if not goals:
        return {
            "total_goals": 0,
            "total_executions": 0,
            "success_count": 0,
            "failed_count": 0,
            "pending_count": 0,
            "success_rate": 0.0,
            "avg_execution_time": 0.0,
            "last_execution": None,
            "execution_history": [],
            "source_breakdown": {}
        }
    
    total_goals = len(goals)
    executions = [g for g in goals if g.get("executions")]
    total_executions = sum(len(g.get("executions", [])) for g in goals)
    
    success_count = 0
    failed_count = 0
    pending_count = 0
    execution_times = []
    execution_history = []
    source_breakdown = {}
    
    for goal in goals:
        # source 분류
        tags = goal.get("tags", [])
        source = "manual"
        for tag in tags:
            if tag.startswith("source:"):
                source = tag.split(":", 1)[1]
                break
        source_breakdown[source] = source_breakdown.get(source, 0) + 1
        
        execs = goal.get("executions", [])
        if not execs:
            pending_count += 1
            continue
        
        for ex in execs:
            status = ex.get("status", "unknown")
            if status == "success":
                success_count += 1
            elif status == "failed":
                failed_count += 1
            
            # 실행 시간
            if "duration_seconds" in ex:
                execution_times.append(ex["duration_seconds"])
            
            # 실행 이력
            execution_history.append({
                "goal_title": goal.get("title", "Unknown"),
                "timestamp": ex.get("timestamp", ""),
                "status": status,
                "duration": ex.get("duration_seconds", 0),
                "output": ex.get("output", "")[:200]  # 200자만
            })
    
    # 최신 순으로 정렬
    execution_history.sort(key=lambda x: x["timestamp"], reverse=True)
    
    success_rate = (success_count / total_executions * 100) if total_executions > 0 else 0.0
    avg_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
    
    last_execution = execution_history[0] if execution_history else None
    
    return {
        "total_goals": total_goals,
        "total_executions": total_executions,
        "success_count": success_count,
        "failed_count": failed_count,
        "pending_count": pending_count,
        "success_rate": round(success_rate, 1),
        "avg_execution_time": round(avg_time, 2),
        "last_execution": last_execution,
        "execution_history": execution_history[:20],  # 최근 20개만
        "source_breakdown": source_breakdown
    }


def get_current_goals(goals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """현재 활성 목표 (최신 생성 목표)"""
    return goals[:10] if goals else []


def generate_html(metrics: Dict[str, Any], current_goals: List[Dict[str, Any]], 
                  loop_status: Dict[str, Any]) -> str:
    """HTML 생성"""
    
    # 템플릿 없으면 기본 HTML 생성
    if not TEMPLATE_HTML.exists():
        return generate_default_html(metrics, current_goals, loop_status)
    
    with open(TEMPLATE_HTML, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 플레이스홀더 치환
    html = template
    html = html.replace("{{TOTAL_GOALS}}", str(metrics["total_goals"]))
    html = html.replace("{{TOTAL_EXECUTIONS}}", str(metrics["total_executions"]))
    html = html.replace("{{SUCCESS_COUNT}}", str(metrics["success_count"]))
    html = html.replace("{{FAILED_COUNT}}", str(metrics["failed_count"]))
    html = html.replace("{{SUCCESS_RATE}}", f"{metrics['success_rate']}%")
    html = html.replace("{{AVG_TIME}}", f"{metrics['avg_execution_time']}s")
    
    # 루프 상태
    loop_state_badge = "🟢 Running" if loop_status["status"] == "running" else "🔴 Stopped"
    html = html.replace("{{LOOP_STATUS}}", loop_state_badge)
    
    # 최근 실행 이력 (JSON)
    html = html.replace("{{EXECUTION_HISTORY_JSON}}", json.dumps(metrics["execution_history"]))
    
    # 현재 목표 (JSON)
    html = html.replace("{{CURRENT_GOALS_JSON}}", json.dumps(current_goals))
    
    # 타임스탬프
    html = html.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    return html


def generate_default_html(metrics: Dict[str, Any], current_goals: List[Dict[str, Any]], 
                          loop_status: Dict[str, Any]) -> str:
    """기본 HTML (템플릿 없을 때)"""
    
    loop_badge = "🟢 Running" if loop_status["status"] == "running" else "🔴 Stopped"
    
    # Source 분류 카드 생성
    source_counts = {}
    for g in current_goals:
        source = g.get("source", "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
    
    source_cards = ""
    source_icons = {
        "music_daemon": "🎵",
        "manual": "✋",
        "auto": "🤖",
        "rhythm": "🌊",
        "unknown": "❓"
    }
    for source, count in source_counts.items():
        icon = source_icons.get(source, "📦")
        source_cards += f"""
        <div class="metric-card">
            <div class="metric-value">{count}</div>
            <div class="metric-label">{icon} {source}</div>
        </div>
        """
    
    history_rows = ""
    for h in metrics["execution_history"][:10]:
        status_icon = "✅" if h["status"] == "success" else "❌"
        history_rows += f"""
        <tr>
            <td>{h['timestamp'][:19]}</td>
            <td>{h['goal_title']}</td>
            <td>{status_icon} {h['status']}</td>
            <td>{h['duration']}s</td>
        </tr>
        """
    
    goals_rows = ""
    for g in current_goals[:5]:
        priority_color = "red" if g.get("priority", 5) >= 8 else "orange" if g.get("priority", 5) >= 5 else "green"
        goals_rows += f"""
        <tr>
            <td>{g.get('title', 'Unknown')}</td>
            <td style="color: {priority_color};">{g.get('priority', 5)}</td>
            <td>{g.get('type', 'unknown')}</td>
        </tr>
        """
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="30">
    <title>🎯 자율 목표 대시보드</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #1e1e1e; color: #d4d4d4; }}
        h1 {{ color: #4ec9b0; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: #2d2d30; padding: 20px; border-radius: 8px; border-left: 4px solid #4ec9b0; }}
        .metric-value {{ font-size: 36px; font-weight: bold; color: #4ec9b0; }}
        .metric-label {{ color: #858585; font-size: 14px; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; background: #2d2d30; margin-bottom: 30px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #3e3e42; }}
        th {{ background: #252526; color: #4ec9b0; }}
        tr:hover {{ background: #37373d; }}
        .status-badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
        .success {{ background: #0e8a16; color: white; }}
        .failed {{ background: #d73a49; color: white; }}
        .timestamp {{ color: #858585; font-size: 12px; text-align: right; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 자율 목표 시스템 대시보드</h1>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{metrics['total_goals']}</div>
                <div class="metric-label">총 목표 수</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics['total_executions']}</div>
                <div class="metric-label">총 실행 횟수</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics['success_rate']}%</div>
                <div class="metric-label">성공률</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics['avg_execution_time']}s</div>
                <div class="metric-label">평균 실행 시간</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{loop_badge}</div>
                <div class="metric-label">백그라운드 루프</div>
            </div>
        </div>
        
        <h2>🏷️ Source 분류</h2>
        <div class="metrics">
            {source_cards}
        </div>
        
        <h2>📊 최근 실행 이력 (최근 10개)</h2>
        <table>
            <thead>
                <tr>
                    <th>시간</th>
                    <th>목표</th>
                    <th>상태</th>
                    <th>실행 시간</th>
                </tr>
            </thead>
            <tbody>
                {history_rows or '<tr><td colspan="4">실행 이력 없음</td></tr>'}
            </tbody>
        </table>
        
        <h2>🎯 현재 목표 (최근 5개)</h2>
        <table>
            <thead>
                <tr>
                    <th>목표</th>
                    <th>우선순위</th>
                    <th>타입</th>
                </tr>
            </thead>
            <tbody>
                {goals_rows or '<tr><td colspan="3">목표 없음</td></tr>'}
            </tbody>
        </table>
        
        <div class="timestamp">
            ⏰ 마지막 업데이트: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 🔄 30초마다 자동 새로고침
        </div>
    </div>
</body>
</html>
"""
    return html


def main():
    print("🎯 자율 목표 대시보드 생성 중...")
    
    # 1. 데이터 로드
    print("   📂 goal_tracker.json 로드...")
    tracker = load_goal_tracker()
    
    print("   📂 autonomous_goals_latest.json 로드...")
    latest_goals = load_latest_goals()
    
    print("   🔍 백그라운드 루프 상태 확인...")
    loop_status = check_background_loop()
    
    # 2. 메트릭 분석
    print("   📊 메트릭 분석...")
    metrics = analyze_metrics(tracker)
    
    # 3. 현재 목표
    current_goals = get_current_goals(latest_goals)
    
    # 4. HTML 생성
    print("   🎨 HTML 생성...")
    html = generate_html(metrics, current_goals, loop_status)
    
    # 5. 저장
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ 대시보드 생성 완료!")
    print(f"   📄 {OUTPUT_HTML}")
    print(f"\n📊 요약:")
    print(f"   • 총 목표: {metrics['total_goals']}")
    print(f"   • 총 실행: {metrics['total_executions']}")
    print(f"   • 성공률: {metrics['success_rate']}%")
    print(f"   • 루프 상태: {loop_status['status']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
