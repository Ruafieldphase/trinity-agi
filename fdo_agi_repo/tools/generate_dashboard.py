#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Generator for Phase 7

HTML/Markdown 대시보드 생성
- 실시간 성능 지표
- 그래프 및 차트 (ASCII)
- 세션 상세 내역
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)


class DashboardGenerator:
    """Phase 7 대시보드 생성기"""

    def __init__(self, log_dir: str = "logs/phase7"):
        """
        Args:
            log_dir: 로그 디렉토리 경로
        """
        self.log_dir = Path(log_dir)
        self.analysis_dir = self.log_dir / "analysis"
        self.reports_dir = Path("reports")

        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def load_latest_analysis(self) -> Dict[str, Any]:
        """최신 분석 데이터 로드"""
        if not self.analysis_dir.exists():
            return {}

        analysis_files = sorted(self.analysis_dir.glob("full_analysis_*.json"), reverse=True)
        if not analysis_files:
            return {}

        with open(analysis_files[0], 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_html_dashboard(self, analysis: Dict[str, Any]) -> str:
        """HTML 대시보드 생성"""
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hey Sena Phase 7 - Performance Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        h2 {{
            color: #555;
            margin: 30px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .meta {{
            color: #777;
            font-size: 0.9em;
            margin-bottom: 30px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}
        .card h3 {{
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        .card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }}
        .card .label {{
            color: #777;
            font-size: 0.9em;
        }}
        .progress {{
            background: #e9ecef;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-bar {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.3s ease;
        }}
        .status-good {{ border-left-color: #28a745; }}
        .status-warning {{ border-left-color: #ffc107; }}
        .status-bad {{ border-left-color: #dc3545; }}
        .goal-check {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .goal-check.achieved {{
            border-left: 4px solid #28a745;
            background: #d4edda;
        }}
        .goal-check.in-progress {{
            border-left: 4px solid #ffc107;
            background: #fff3cd;
        }}
        .goal-check.not-achieved {{
            border-left: 4px solid #dc3545;
            background: #f8d7da;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #777;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Hey Sena v4.1 - Phase 7 Dashboard</h1>
        <div class="meta">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
            Total Sessions: {analysis['metadata']['total_sessions']}
        </div>

        <h2>📊 Overall Statistics</h2>
        <div class="grid">
            <div class="card">
                <h3>Total Sessions</h3>
                <div class="value">{analysis['metadata']['total_sessions']}</div>
                <div class="label">of 50 target</div>
            </div>
            <div class="card">
                <h3>Total Turns</h3>
                <div class="value">{analysis['overall']['total_turns']}</div>
                <div class="label">{analysis['overall']['avg_turns_per_session']:.1f} avg/session</div>
            </div>
            <div class="card">
                <h3>Total Duration</h3>
                <div class="value">{analysis['overall']['total_duration_seconds']:.1f}s</div>
                <div class="label">{analysis['overall']['avg_session_duration']:.1f}s avg</div>
            </div>
            <div class="card">
                <h3>LLM Tokens</h3>
                <div class="value">{analysis['overall']['total_llm_tokens']}</div>
                <div class="label">{analysis['overall']['avg_tokens_per_session']:.0f} avg</div>
            </div>
        </div>

        <h2>💚 Cache Performance</h2>
        <div class="grid">
            <div class="card {self._get_status_class(analysis['cache']['overall_cache_hit_rate'], 60, 70)}">
                <h3>Overall Cache Hit Rate</h3>
                <div class="value">{analysis['cache']['overall_cache_hit_rate']:.1f}%</div>
                <div class="progress">
                    <div class="progress-bar" style="width: {min(analysis['cache']['overall_cache_hit_rate'], 100)}%">
                        {analysis['cache']['overall_cache_hit_rate']:.1f}%
                    </div>
                </div>
                <div class="label">Target: ≥ 60%</div>
            </div>
            <div class="card">
                <h3>Cache Hits/Misses</h3>
                <div class="value">{analysis['cache']['total_cache_hits']} / {analysis['cache']['total_cache_misses']}</div>
                <div class="label">Min: {analysis['cache']['min_cache_hit_rate']:.1f}%, Max: {analysis['cache']['max_cache_hit_rate']:.1f}%</div>
            </div>
        </div>

        <h2>⚡ Response Time Performance</h2>
        <div class="grid">
            <div class="card {self._get_status_class(1500 - analysis['performance']['overall_avg_response_time'], 0, 500)}">
                <h3>Average Response Time</h3>
                <div class="value">{analysis['performance']['overall_avg_response_time']:.0f}ms</div>
                <div class="label">Target: &lt; 1500ms | Median: {analysis['performance']['overall_median_response_time']:.0f}ms</div>
            </div>
            <div class="card">
                <h3>Min / Max</h3>
                <div class="value">{analysis['performance']['min_response_time']:.0f} / {analysis['performance']['max_response_time']:.0f}ms</div>
                <div class="label">P95: {analysis['performance']['p95_response_time']:.0f}ms | P99: {analysis['performance']['p99_response_time']:.0f}ms</div>
            </div>
        </div>

        <h2>🎯 Phase 7 Goals</h2>
        {self._generate_goals_html(analysis)}

        <h2>⭐ User Ratings</h2>
        {self._generate_ratings_html(analysis)}

        <h2>❌ Error Analysis</h2>
        <div class="card {self._get_status_class(5 - analysis['errors']['overall_error_rate'], 0, 2)}">
            <div class="value">{analysis['errors']['overall_error_rate']:.2f}%</div>
            <div class="label">Error Rate (Target: &lt; 5%) | Total Errors: {analysis['errors']['total_errors']}</div>
            <div class="label">Error-Free Sessions: {analysis['errors']['error_free_sessions']} / {analysis['metadata']['total_sessions']}</div>
        </div>

        <h2>📝 Top Topics</h2>
        {self._generate_topics_html(analysis)}

        {self._generate_trends_html(analysis)}

        <div class="footer">
            Generated by Hey Sena Phase 7 Dashboard Generator<br>
            Data collected from {analysis['metadata']['date_range']['start']} to {analysis['metadata']['date_range']['end']}
        </div>
    </div>
</body>
</html>
"""
        return html

    def _get_status_class(self, value: float, warning_threshold: float, good_threshold: float) -> str:
        """값에 따른 상태 클래스 반환"""
        if value >= good_threshold:
            return "status-good"
        elif value >= warning_threshold:
            return "status-warning"
        else:
            return "status-bad"

    def _generate_goals_html(self, analysis: Dict[str, Any]) -> str:
        """목표 달성 HTML 생성"""
        goals = [
            {
                "name": "Minimum 50 sessions",
                "achieved": analysis['metadata']['total_sessions'] >= 50,
                "in_progress": 0 < analysis['metadata']['total_sessions'] < 50,
                "value": f"{analysis['metadata']['total_sessions']}/50"
            },
            {
                "name": "Cache hit rate ≥ 60%",
                "achieved": analysis['cache']['overall_cache_hit_rate'] >= 60,
                "in_progress": False,
                "value": f"{analysis['cache']['overall_cache_hit_rate']:.1f}%"
            },
            {
                "name": "Avg response &lt; 1.5s",
                "achieved": analysis['performance']['overall_avg_response_time'] <= 1500,
                "in_progress": False,
                "value": f"{analysis['performance']['overall_avg_response_time']:.0f}ms"
            },
            {
                "name": "Error rate &lt; 5%",
                "achieved": analysis['errors']['overall_error_rate'] < 5,
                "in_progress": False,
                "value": f"{analysis['errors']['overall_error_rate']:.2f}%"
            }
        ]

        if analysis['ratings']['total_rated_sessions'] > 0:
            goals.append({
                "name": "User rating ≥ 4.0",
                "achieved": analysis['ratings']['avg_rating'] >= 4.0,
                "in_progress": False,
                "value": f"{analysis['ratings']['avg_rating']:.2f}/5.0"
            })

        html = ""
        for goal in goals:
            if goal['achieved']:
                css_class = "achieved"
                icon = "✅"
            elif goal['in_progress']:
                css_class = "in-progress"
                icon = "⏳"
            else:
                css_class = "not-achieved"
                icon = "❌"

            html += f"""
        <div class="goal-check {css_class}">
            <span style="font-size: 1.5em;">{icon}</span>
            <div style="flex-grow: 1;">
                <strong>{goal['name']}</strong><br>
                <span style="color: #666;">{goal['value']}</span>
            </div>
        </div>
"""
        return html

    def _generate_ratings_html(self, analysis: Dict[str, Any]) -> str:
        """평점 HTML 생성"""
        ratings = analysis['ratings']

        if ratings['total_rated_sessions'] == 0:
            return "<div class='card'><div class='label'>No ratings collected yet</div></div>"

        html = "<div class='grid'>"
        html += f"""
            <div class="card">
                <h3>Average Rating</h3>
                <div class="value">{'⭐' * int(ratings['avg_rating'])} {ratings['avg_rating']:.2f}</div>
                <div class="label">Based on {ratings['total_rated_sessions']} rated sessions</div>
            </div>
"""

        html += "<div class='card'><h3>Rating Distribution</h3>"
        for i in range(5, 0, -1):
            count = ratings['rating_distribution'][str(i)]
            percentage = (count / ratings['total_rated_sessions'] * 100) if ratings['total_rated_sessions'] > 0 else 0
            html += f"""
                <div style="margin: 5px 0;">
                    {i}⭐:
                    <div class="progress" style="display: inline-block; width: 200px; height: 20px; margin: 0 10px; vertical-align: middle;">
                        <div class="progress-bar" style="width: {percentage}%">{count}</div>
                    </div>
                    {percentage:.0f}%
                </div>
"""
        html += "</div></div>"

        return html

    def _generate_topics_html(self, analysis: Dict[str, Any]) -> str:
        """주제 HTML 생성"""
        topics = analysis['topics']

        if not topics['top_topics']:
            return "<div class='card'><div class='label'>No topics recorded yet</div></div>"

        html = "<table>"
        html += "<tr><th>Rank</th><th>Topic</th><th>Mentions</th></tr>"
        for i, topic_data in enumerate(topics['top_topics'][:10], 1):
            html += f"<tr><td>#{i}</td><td>{topic_data['topic']}</td><td>{topic_data['count']}</td></tr>"
        html += "</table>"

        return html

    def _generate_trends_html(self, analysis: Dict[str, Any]) -> str:
        """트렌드 HTML 생성"""
        trends = analysis['trends']

        if trends.get("trend") == "insufficient_data":
            return ""

        html = "<h2>📈 Trends (First Half vs Second Half)</h2>"
        html += "<div class='grid'>"

        # Cache hit rate trend
        improvement = trends['cache_hit_rate_improvement']
        icon = "↗️" if improvement > 0 else ("↘️" if improvement < 0 else "→")
        html += f"""
            <div class="card">
                <h3>Cache Hit Rate {icon}</h3>
                <div class="value">{improvement:+.1f}%</div>
                <div class="label">First: {trends['first_half_cache_rate']:.1f}% → Second: {trends['second_half_cache_rate']:.1f}%</div>
            </div>
"""

        # Response time trend
        improvement = trends['response_time_improvement']
        icon = "↗️" if improvement > 0 else ("↘️" if improvement < 0 else "→")
        html += f"""
            <div class="card">
                <h3>Response Time {icon}</h3>
                <div class="value">{improvement:+.0f}ms</div>
                <div class="label">First: {trends['first_half_response_time']:.0f}ms → Second: {trends['second_half_response_time']:.0f}ms</div>
            </div>
"""

        html += "</div>"
        return html

    def generate_markdown_dashboard(self, analysis: Dict[str, Any]) -> str:
        """Markdown 대시보드 생성"""
        md = f"""# Hey Sena Phase 7 - Performance Dashboard

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Sessions**: {analysis['metadata']['total_sessions']}

---

## 📊 Overall Statistics

| Metric | Value |
|--------|-------|
| Total Sessions | {analysis['metadata']['total_sessions']} |
| Total Turns | {analysis['overall']['total_turns']} |
| Total Duration | {analysis['overall']['total_duration_seconds']:.1f}s |
| Avg Turns/Session | {analysis['overall']['avg_turns_per_session']:.1f} |
| Avg Session Duration | {analysis['overall']['avg_session_duration']:.1f}s |
| Total LLM Tokens | {analysis['overall']['total_llm_tokens']} |
| Avg Tokens/Session | {analysis['overall']['avg_tokens_per_session']:.0f} |

---

## 💚 Cache Performance

| Metric | Value |
|--------|-------|
| **Overall Cache Hit Rate** | **{analysis['cache']['overall_cache_hit_rate']:.1f}%** |
| Target | ≥ 60% |
| Cache Hits | {analysis['cache']['total_cache_hits']} |
| Cache Misses | {analysis['cache']['total_cache_misses']} |
| Min Hit Rate | {analysis['cache']['min_cache_hit_rate']:.1f}% |
| Max Hit Rate | {analysis['cache']['max_cache_hit_rate']:.1f}% |
| Median Hit Rate | {analysis['cache']['median_cache_hit_rate']:.1f}% |

---

## ⚡ Response Time Performance

| Metric | Value |
|--------|-------|
| **Overall Avg Response** | **{analysis['performance']['overall_avg_response_time']:.0f}ms** |
| Target | < 1500ms |
| Median Response | {analysis['performance']['overall_median_response_time']:.0f}ms |
| Min Response | {analysis['performance']['min_response_time']:.0f}ms |
| Max Response | {analysis['performance']['max_response_time']:.0f}ms |
| P95 | {analysis['performance']['p95_response_time']:.0f}ms |
| P99 | {analysis['performance']['p99_response_time']:.0f}ms |

---

## 🎯 Phase 7 Goals

| Goal | Status | Value |
|------|--------|-------|
| Minimum 50 sessions | {'✅' if analysis['metadata']['total_sessions'] >= 50 else '⏳' if analysis['metadata']['total_sessions'] > 0 else '❌'} | {analysis['metadata']['total_sessions']}/50 |
| Cache hit rate ≥ 60% | {'✅' if analysis['cache']['overall_cache_hit_rate'] >= 60 else '❌'} | {analysis['cache']['overall_cache_hit_rate']:.1f}% |
| Avg response < 1.5s | {'✅' if analysis['performance']['overall_avg_response_time'] <= 1500 else '❌'} | {analysis['performance']['overall_avg_response_time']:.0f}ms |
| Error rate < 5% | {'✅' if analysis['errors']['overall_error_rate'] < 5 else '❌'} | {analysis['errors']['overall_error_rate']:.2f}% |
"""

        if analysis['ratings']['total_rated_sessions'] > 0:
            md += f"| User rating ≥ 4.0 | {'✅' if analysis['ratings']['avg_rating'] >= 4.0 else '❌'} | {analysis['ratings']['avg_rating']:.2f}/5.0 |\n"

        md += f"""
---

## ⭐ User Ratings

"""
        if analysis['ratings']['total_rated_sessions'] > 0:
            md += f"""
- **Average Rating**: {'⭐' * int(analysis['ratings']['avg_rating'])} {analysis['ratings']['avg_rating']:.2f}/5.0
- **Total Rated Sessions**: {analysis['ratings']['total_rated_sessions']}

**Distribution**:
"""
            for i in range(5, 0, -1):
                count = analysis['ratings']['rating_distribution'][str(i)]
                md += f"- {i}⭐: {count}\n"
        else:
            md += "No ratings collected yet.\n"

        md += f"""
---

## ❌ Error Analysis

- **Overall Error Rate**: {analysis['errors']['overall_error_rate']:.2f}% (Target: < 5%)
- **Total Errors**: {analysis['errors']['total_errors']}
- **Sessions with Errors**: {analysis['errors']['sessions_with_errors']}
- **Error-Free Sessions**: {analysis['errors']['error_free_sessions']}

---

## 📝 Top Topics

"""
        if analysis['topics']['top_topics']:
            md += "| Rank | Topic | Mentions |\n"
            md += "|------|-------|----------|\n"
            for i, topic_data in enumerate(analysis['topics']['top_topics'][:10], 1):
                md += f"| #{i} | {topic_data['topic']} | {topic_data['count']} |\n"
        else:
            md += "No topics recorded yet.\n"

        # Trends
        if analysis['trends'].get("trend") != "insufficient_data":
            md += f"""
---

## 📈 Trends (First Half vs Second Half)

**Cache Hit Rate**:
- First Half: {analysis['trends']['first_half_cache_rate']:.1f}%
- Second Half: {analysis['trends']['second_half_cache_rate']:.1f}%
- Improvement: {analysis['trends']['cache_hit_rate_improvement']:+.1f}%

**Response Time**:
- First Half: {analysis['trends']['first_half_response_time']:.0f}ms
- Second Half: {analysis['trends']['second_half_response_time']:.0f}ms
- Improvement: {analysis['trends']['response_time_improvement']:+.0f}ms
"""

        md += f"""
---

**Dashboard generated by Hey Sena Phase 7 Tools**
**Data range**: {analysis['metadata']['date_range']['start']} to {analysis['metadata']['date_range']['end']}
"""

        return md

    def generate_all(self) -> tuple:
        """모든 대시보드 생성"""
        print("\n📊 Generating dashboards...")

        analysis = self.load_latest_analysis()
        if not analysis:
            print("⚠️  No analysis data found. Run analyze_phase7_data.py first.")
            return None, None

        # HTML 대시보드
        html = self.generate_html_dashboard(analysis)
        html_file = self.reports_dir / f"PHASE_7_DASHBOARD_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ HTML dashboard: {html_file}")

        # Markdown 대시보드
        md = self.generate_markdown_dashboard(analysis)
        md_file = self.reports_dir / f"PHASE_7_DASHBOARD_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"✅ Markdown dashboard: {md_file}")

        return html_file, md_file


def main():
    """메인 함수"""
    print("="*70)
    print("📊 Phase 7 Dashboard Generator")
    print("="*70)

    generator = DashboardGenerator()
    html_file, md_file = generator.generate_all()

    if html_file and md_file:
        print(f"\n✅ Dashboards generated successfully!")
        print(f"\nOpen in browser: {html_file.absolute()}")


if __name__ == "__main__":
    main()
