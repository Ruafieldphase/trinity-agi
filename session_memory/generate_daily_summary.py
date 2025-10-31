#!/usr/bin/env python3
"""
Daily Session Summary Generator
- 최근 24시간 내 세션 집계 및 Markdown 요약 자동 생성
- outputs/daily_summaries/YYYY-MM-DD.md 파일로 저장
"""
import sys
import os
import csv
from datetime import datetime, timedelta
from pathlib import Path
from session_search import SessionSearch

def main():
    # 경로 설정
    output_dir = Path("outputs/daily_summaries")
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = output_dir / f"{today}.md"

    # 세션 데이터 집계
    search = SessionSearch()
    sessions = search.get_recent_sessions(limit=100, days=1)
    stats = search.get_stats_by_persona()

    # 전체 통계 계산
    total_sessions = len(sessions)
    completed = sum(1 for s in sessions if s['status'] == 'completed')
    active = sum(1 for s in sessions if s['status'] == 'active')
    paused = sum(1 for s in sessions if s['status'] == 'paused')
    abandoned = sum(1 for s in sessions if s['status'] == 'abandoned')
    resonance_scores = [s['resonance_score'] for s in sessions if s.get('resonance_score') is not None]
    avg_resonance = sum(resonance_scores)/len(resonance_scores) if resonance_scores else None

    # Markdown 헤더
    md = [
        f"# Daily Session Summary ({today})\n",
        f"- Total sessions: **{total_sessions}**",
        f"- Completed: {completed}  Active: {active}  Paused: {paused}  Abandoned: {abandoned}",
        f"- Avg Resonance: {avg_resonance:.2f}" if avg_resonance is not None else "- Avg Resonance: N/A",
        ""
    ]

    # 퍼소나별 통계
    if stats:
        md.append("## Stats by Persona\n")
        md.append("| Persona | Sessions | Completed | Avg Resonance | Avg Hours |")
        md.append("|---------|----------|-----------|---------------|-----------|")
        for r in stats:
            md.append(f"| {r['persona']} | {r['session_count']} | {r['completed_count']} | "
                      f"{r['avg_resonance']:.2f} | {r['avg_duration_hours']:.1f} |")
        md.append("")

    # YouTube Learner 섹션
    try:
        yt_index_md = Path("outputs/youtube_learner/INDEX.md")
        yt_index_csv = Path("outputs/youtube_learner/INDEX.csv")
        md.append("## YouTube Learner\n")
        md.append("- 전체 인덱스: [INDEX.md](outputs/youtube_learner/INDEX.md)")
        if yt_index_csv.exists():
            rows = []
            with yt_index_csv.open('r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= 3:
                        break
                    rows.append(row)
            if rows:
                md.append("\n| Video ID | Title | Subs | Frames | Analyzed At | Link |")
                md.append("|---|---|---:|---:|---|---|")
                for row in rows:
                    vid = row.get('video_id', '')
                    title = (row.get('title', '') or '').replace('|', ' ')[:100]
                    subs = row.get('subtitles', '')
                    frames = row.get('frames', '')
                    ts = (row.get('analyzed_at', '') or '').replace('T', ' ')[:19]
                    path_str = row.get('path', '')
                    link = path_str
                    try:
                        p = Path(path_str)
                        md_path = p.with_suffix('.md')
                        if md_path.exists():
                            link = md_path.as_posix()
                        else:
                            link = p.as_posix()
                    except Exception:
                        pass
                    md.append(f"| {vid} | {title} | {subs} | {frames} | {ts} | [{vid}]({link}) |")
            else:
                md.append("- 최근 항목이 없습니다.")
        else:
            md.append("- 인덱스 파일을 찾을 수 없습니다.")
        md.append("")
    except Exception:
        # YouTube 섹션 오류는 리포트 생성을 막지 않음
        md.append("## YouTube Learner\n")
        md.append("- 인덱스 요약 중 오류가 발생했습니다.")
        md.append("")

    # 세션 요약 테이블
    md.append("## Session List (last 24h)\n")
    md.append("| Title | Started | Ended | Status | Persona | Resonance | Tasks | Artifacts | Tags |")
    md.append("|-------|---------|-------|--------|---------|-----------|-------|-----------|------|")
    for s in sessions:
        title = (s.get('title') or '')[:32]
        start_time = (s.get('start_time') or '')[:16]
        end_time = (s.get('end_time') or '')[:16]
        status = s.get('status', '')
        persona = s.get('persona', '')
        resonance = '' if s.get('resonance_score') is None else s.get('resonance_score')
        tasks = s.get('task_count', 0) or 0
        artifacts = s.get('artifact_count', 0) or 0
        tags = s.get('tags') or ''
        md.append(f"| {title} | {start_time} | {end_time} | {status} | {persona} | {resonance} | {tasks} | {artifacts} | {tags} |")
    md.append("")

    # 하이라이트: resonance 최고/최저, 태그/퍼소나별 분포 등
    if resonance_scores:
        max_r = max(resonance_scores)
        min_r = min(resonance_scores)
        md.append(f"- Highest Resonance: {max_r:.2f}")
        md.append(f"- Lowest Resonance: {min_r:.2f}")

    # 파일 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"✅ Daily summary written to {output_path}")

if __name__ == "__main__":
    main()
