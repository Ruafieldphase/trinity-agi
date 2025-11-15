#!/usr/bin/env python3
"""
🎵🎯 Music-Goal Live Tracker
실시간으로 음악과 목표 생성 간의 연결을 모니터링하고 리포트 생성
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root / "fdo_agi_repo"))

from utils.goal_tracker import GoalTracker


def load_music_goal_events(hours: int = 24) -> List[Dict]:
    """최근 N시간 내 music-goal 이벤트 로드"""
    event_log_path = workspace_root / "outputs" / "music_goal_events.jsonl"
    if not event_log_path.exists():
        return []
    
    cutoff = datetime.now() - timedelta(hours=hours)
    events = []
    
    with open(event_log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                timestamp = datetime.fromisoformat(event.get("timestamp", ""))
                if timestamp >= cutoff:
                    events.append(event)
            except:
                continue
    
    return events


def analyze_music_goal_correlation(hours: int = 24) -> Dict:
    """음악-목표 상관관계 분석"""
    events = load_music_goal_events(hours)
    tracker = GoalTracker()
    
    # 태그별 통계
    tempo_distribution = {"high": 0, "medium": 0, "low": 0}
    brainwave_distribution = {}
    
    # 목표 상태별 카운트
    goal_status_counts = {"proposed": 0, "in_progress": 0, "completed": 0, "failed": 0}
    
    music_tagged_goals = []
    
    # music_daemon 태그가 있는 모든 목표 찾기
    all_goals = tracker.list_goals()
    for goal in all_goals:
        tags = goal.get("tags", [])
        if any("source:music_daemon" in tag for tag in tags):
            music_tagged_goals.append(goal)
            
            # 상태 카운트
            status = goal.get("status", "proposed")
            goal_status_counts[status] = goal_status_counts.get(status, 0) + 1
            
            # Tempo 분포
            tempo_tags = [t for t in tags if t.startswith("tempo:")]
            if tempo_tags:
                tempo = int(tempo_tags[0].split(":")[1])
                if tempo >= 120:
                    tempo_distribution["high"] += 1
                elif tempo >= 80:
                    tempo_distribution["medium"] += 1
                else:
                    tempo_distribution["low"] += 1
            
            # Brainwave 분포
            brainwave_tags = [t for t in tags if t.startswith("brainwave:")]
            if brainwave_tags:
                brainwave = brainwave_tags[0].split(":")[1]
                brainwave_distribution[brainwave] = brainwave_distribution.get(brainwave, 0) + 1
    
    # 이벤트 통계
    total_events = len(events)
    unique_goals = len(set(e.get("goal_id") for e in events if e.get("goal_id")))
    
    return {
        "summary": {
            "analysis_period_hours": hours,
            "total_music_events": total_events,
            "unique_goals_created": unique_goals,
            "total_music_tagged_goals": len(music_tagged_goals),
            "goal_status": goal_status_counts
        },
        "distributions": {
            "tempo": tempo_distribution,
            "brainwave": brainwave_distribution
        },
        "recent_events": events[-10:],  # 최근 10개
        "music_goals": music_tagged_goals[:10]  # 최근 10개
    }


def generate_markdown_report(analysis: Dict) -> str:
    """Markdown 리포트 생성"""
    summary = analysis["summary"]
    distributions = analysis["distributions"]
    
    md = f"""# 🎵🎯 Music-Goal Live Tracker Report

## 📊 Summary (Last {summary['analysis_period_hours']} hours)

- **Total Music Events**: {summary['total_music_events']}
- **Unique Goals Created**: {summary['unique_goals_created']}
- **Total Music-Tagged Goals**: {summary['total_music_tagged_goals']}

### Goal Status Distribution
- Proposed: {summary['goal_status']['proposed']}
- In Progress: {summary['goal_status']['in_progress']}
- Completed: {summary['goal_status']['completed']}
- Failed: {summary['goal_status']['failed']}

## 🎼 Music Distributions

### Tempo Distribution
- High (≥120 BPM): {distributions['tempo']['high']}
- Medium (80-119 BPM): {distributions['tempo']['medium']}
- Low (<80 BPM): {distributions['tempo']['low']}

### Brainwave Distribution
"""
    
    for brainwave, count in distributions['brainwave'].items():
        md += f"- {brainwave}: {count}\n"
    
    md += "\n## 🎯 Recent Music-Tagged Goals\n\n"
    for goal in analysis['music_goals'][:5]:
        title = goal.get("title", "N/A")
        status = goal.get("status", "N/A")
        tags = ", ".join(goal.get("tags", [])[:3])
        md += f"- [{status.upper()}] **{title}**\n  - Tags: `{tags}...`\n"
    
    md += "\n## 📡 Recent Music Events\n\n"
    for event in analysis['recent_events'][-5:]:
        timestamp = event.get("timestamp", "N/A")
        tempo = event.get("tempo", "N/A")
        brainwave = event.get("brainwave", "N/A")
        goal_id = event.get("goal_id", "N/A")
        md += f"- `{timestamp}` | Tempo: {tempo} | Brainwave: {brainwave} | Goal: `{goal_id}`\n"
    
    md += f"\n---\n*Generated at {datetime.now().isoformat()}*\n"
    
    return md


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Music-Goal Live Tracker")
    parser.add_argument("--hours", type=int, default=24, help="Analysis window in hours")
    parser.add_argument("--output", type=str, default="outputs/music_goal_live_tracker_latest.md", help="Output file")
    args = parser.parse_args()
    
    print(f"🎵 Analyzing music-goal correlation (last {args.hours} hours)...")
    analysis = analyze_music_goal_correlation(args.hours)
    
    # JSON 저장
    json_path = workspace_root / "outputs" / "music_goal_live_tracker_latest.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON saved: {json_path}")
    
    # Markdown 리포트 생성
    md = generate_markdown_report(analysis)
    md_path = workspace_root / args.output
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"✅ Markdown report saved: {md_path}")
    
    # 요약 출력
    summary = analysis["summary"]
    print(f"\n📊 Summary:")
    print(f"  - Total Events: {summary['total_music_events']}")
    print(f"  - Unique Goals: {summary['unique_goals_created']}")
    print(f"  - Completed: {summary['goal_status']['completed']}")
    print(f"  - In Progress: {summary['goal_status']['in_progress']}")


if __name__ == "__main__":
    main()
