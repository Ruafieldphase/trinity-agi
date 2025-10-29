#!/usr/bin/env python3
"""
ion-mentoring Cache Performance Dashboard
캐시 히트율 및 성능 모니터링 대시보드
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from flask import Flask, jsonify, render_template_string

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)

# 대시보드 HTML 템플릿
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ion-mentoring Cache Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #238636 0%, #1f6feb 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        h1 { font-size: 24px; font-weight: 600; }
        .subtitle { font-size: 14px; opacity: 0.8; margin-top: 5px; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
        }
        .card-title {
            font-size: 14px;
            color: #8b949e;
            margin-bottom: 10px;
        }
        .card-value {
            font-size: 32px;
            font-weight: 600;
            color: #58a6ff;
        }
        .card-subtitle {
            font-size: 12px;
            color: #8b949e;
            margin-top: 5px;
        }
        .status-good { color: #3fb950; }
        .status-warning { color: #d29922; }
        .status-bad { color: #f85149; }
        .chart-container {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .update-time {
            text-align: center;
            color: #8b949e;
            font-size: 12px;
            margin-top: 20px;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        .badge-success { background: #1a7f37; color: white; }
        .badge-warning { background: #9e6a03; color: white; }
        .badge-danger { background: #da3633; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ion-mentoring Cache Performance Dashboard</h1>
        <div class="subtitle">Real-time cache hit rate and performance monitoring</div>
    </div>

    <div class="grid">
        <div class="card">
            <div class="card-title">Cache Hit Rate</div>
            <div class="card-value" id="hitRate">-</div>
            <div class="card-subtitle" id="hitRateStatus">Loading...</div>
        </div>
        <div class="card">
            <div class="card-title">Total Requests</div>
            <div class="card-value" id="totalRequests">-</div>
            <div class="card-subtitle" id="requestsBreakdown">-</div>
        </div>
        <div class="card">
            <div class="card-title">Avg Response Time</div>
            <div class="card-value" id="avgTime">-</div>
            <div class="card-subtitle" id="timeStatus">Loading...</div>
        </div>
        <div class="card">
            <div class="card-title">Redis Status</div>
            <div class="card-value" id="redisStatus">-</div>
            <div class="card-subtitle" id="redisInfo">Checking...</div>
        </div>
    </div>

    <div class="chart-container">
        <h3 style="margin-bottom: 15px; font-size: 16px;">Cache Performance Timeline</h3>
        <canvas id="performanceChart" height="80"></canvas>
    </div>

    <div class="update-time">
        Last updated: <span id="updateTime">-</span> | Auto-refresh every 10s
    </div>

    <div style="margin-top: 30px;">
        <h3 style="margin-bottom: 15px; font-size: 18px; display: flex; justify-content: space-between; align-items: center;">
            <span>Recent Session Summaries</span>
            <span style="font-size: 14px; opacity: 0.7;" id="storageStats">-</span>
        </h3>
        <div id="sessionSummaries" style="max-height: 400px; overflow-y: auto;">
            <div style="text-align: center; padding: 40px; opacity: 0.5;">
                Loading session summaries...
            </div>
        </div>
    </div>

    <script>
        let performanceChart = null;
        const chartData = {
            labels: [],
            hitRates: [],
            avgTimes: []
        };

        function initChart() {
            const ctx = document.getElementById('performanceChart').getContext('2d');
            performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartData.labels,
                    datasets: [
                        {
                            label: 'Hit Rate (%)',
                            data: chartData.hitRates,
                            borderColor: '#3fb950',
                            backgroundColor: 'rgba(63, 185, 80, 0.1)',
                            yAxisID: 'y-hit-rate',
                            tension: 0.3
                        },
                        {
                            label: 'Avg Time (ms)',
                            data: chartData.avgTimes,
                            borderColor: '#58a6ff',
                            backgroundColor: 'rgba(88, 166, 255, 0.1)',
                            yAxisID: 'y-time',
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { labels: { color: '#c9d1d9' } }
                    },
                    scales: {
                        x: { ticks: { color: '#8b949e' }, grid: { color: '#30363d' } },
                        'y-hit-rate': {
                            type: 'linear',
                            position: 'left',
                            ticks: { color: '#3fb950' },
                            grid: { color: '#30363d' },
                            title: { display: true, text: 'Hit Rate (%)', color: '#3fb950' }
                        },
                        'y-time': {
                            type: 'linear',
                            position: 'right',
                            ticks: { color: '#58a6ff' },
                            grid: { display: false },
                            title: { display: true, text: 'Response Time (ms)', color: '#58a6ff' }
                        }
                    }
                }
            });
        }

        async function updateDashboard() {
            try {
                const response = await fetch('/api/cache_stats');
                const data = await response.json();

                // Update cards
                const hitRate = parseFloat(data.hit_rate) || 0;
                document.getElementById('hitRate').textContent = data.hit_rate;

                let hitRateClass = 'status-good';
                let hitRateText = 'Excellent';
                if (hitRate < 50) {
                    hitRateClass = 'status-bad';
                    hitRateText = 'Poor';
                } else if (hitRate < 70) {
                    hitRateClass = 'status-warning';
                    hitRateText = 'Fair';
                }
                document.getElementById('hitRateStatus').innerHTML =
                    `<span class="${hitRateClass}">${hitRateText}</span>`;

                document.getElementById('totalRequests').textContent = data.total_requests;
                document.getElementById('requestsBreakdown').textContent =
                    `Hits: ${data.cache_hits} | Misses: ${data.cache_misses}`;

                document.getElementById('avgTime').textContent = `${data.avg_time_ms}ms`;

                const avgTime = parseFloat(data.avg_time_ms) || 0;
                let timeClass = 'status-good';
                let timeText = 'Fast';
                if (avgTime > 100) {
                    timeClass = 'status-bad';
                    timeText = 'Slow';
                } else if (avgTime > 50) {
                    timeClass = 'status-warning';
                    timeText = 'Moderate';
                }
                document.getElementById('timeStatus').innerHTML =
                    `<span class="${timeClass}">${timeText}</span>`;

                // Redis status
                const redisOk = data.redis_available;
                document.getElementById('redisStatus').innerHTML = redisOk
                    ? '<span class="badge badge-success">Connected</span>'
                    : '<span class="badge badge-danger">Disconnected</span>';
                document.getElementById('redisInfo').textContent = redisOk
                    ? 'L2 cache active'
                    : 'Using local cache only';

                // Update chart
                const now = new Date().toLocaleTimeString('ko-KR');
                chartData.labels.push(now);
                chartData.hitRates.push(hitRate);
                chartData.avgTimes.push(avgTime);

                // Keep last 20 data points
                if (chartData.labels.length > 20) {
                    chartData.labels.shift();
                    chartData.hitRates.shift();
                    chartData.avgTimes.shift();
                }

                if (performanceChart) {
                    performanceChart.update();
                }

                document.getElementById('updateTime').textContent =
                    new Date().toLocaleString('ko-KR');

                // Update session summaries
                await updateSessionSummaries();

            } catch (error) {
                console.error('Failed to update dashboard:', error);
            }
        }

        async function updateSessionSummaries() {
            try {
                // Fetch storage stats
                const statsResponse = await fetch('/api/storage_stats');
                const stats = await statsResponse.json();

                document.getElementById('storageStats').textContent =
                    `Total: ${stats.total_sessions} (LLM: ${stats.llm_summaries}, Rule: ${stats.rule_based_summaries})`;

                // Fetch recent summaries
                const summariesResponse = await fetch('/api/session_summaries');
                const data = await summariesResponse.json();

                const container = document.getElementById('sessionSummaries');

                if (data.summaries && data.summaries.length > 0) {
                    container.innerHTML = data.summaries.map(summary => {
                        const createdAt = new Date(summary.created_at).toLocaleString('ko-KR');
                        const summaryTypeColor = summary.summary_type === 'llm' ? '#3fb950' : '#58a6ff';
                        const summaryTypeText = summary.summary_type === 'llm' ? 'LLM' : 'Rule';

                        return `
                            <div style="background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 15px; margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <div style="font-size: 14px; font-weight: 600;">
                                        ${summary.session_id}
                                    </div>
                                    <div style="display: flex; gap: 10px; align-items: center;">
                                        <span style="background: ${summaryTypeColor}; color: #0d1117; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">
                                            ${summaryTypeText}
                                        </span>
                                        <span style="font-size: 12px; opacity: 0.6;">
                                            ${summary.message_count} msgs
                                        </span>
                                    </div>
                                </div>
                                <div style="font-size: 13px; line-height: 1.6; margin-bottom: 8px; max-height: 100px; overflow-y: auto;">
                                    ${summary.summary}
                                </div>
                                <div style="font-size: 11px; opacity: 0.5; display: flex; justify-content: space-between;">
                                    <span>User: ${summary.user_id}</span>
                                    <span>${createdAt}</span>
                                </div>
                            </div>
                        `;
                    }).join('');
                } else {
                    container.innerHTML = '<div style="text-align: center; padding: 40px; opacity: 0.5;">No session summaries yet</div>';
                }

            } catch (error) {
                console.error('Failed to update session summaries:', error);
                document.getElementById('sessionSummaries').innerHTML =
                    '<div style="text-align: center; padding: 40px; opacity: 0.5; color: #f85149;">Error loading summaries</div>';
            }
        }

        // Initialize
        initChart();
        updateDashboard();
        setInterval(updateDashboard, 10000); // Update every 10 seconds
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """대시보드 메인 페이지"""
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/cache_stats')
def cache_stats():
    """캐시 통계 API"""
    try:
        # OptimizedPersonaPipeline 임포트
        from persona_system.pipeline_optimized import get_optimized_pipeline

        pipeline = get_optimized_pipeline()
        stats = pipeline.stats

        # 캐시 히트율 계산
        total = stats['total_requests']
        hits = stats['cache_hits']
        misses = stats['cache_misses']
        hit_rate = (hits / total * 100) if total > 0 else 0
        avg_time = (stats['total_time_ms'] / total) if total > 0 else 0

        # Redis 상태 확인
        redis_available = False
        try:
            cache = pipeline.cache
            cache_type = type(cache).__name__
            redis_available = 'Redis' in cache_type
        except Exception:
            pass

        return jsonify({
            'total_requests': total,
            'cache_hits': hits,
            'cache_misses': misses,
            'hit_rate': f'{hit_rate:.1f}%',
            'avg_time_ms': f'{avg_time:.1f}',
            'redis_available': redis_available,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'hit_rate': '0.0%',
            'avg_time_ms': '0.0',
            'redis_available': False
        }), 500


@app.route('/api/session_summaries')
def session_summaries():
    """세션 요약 목록 조회 (최근 10개)"""
    try:
        from persona_system.utils.session_summary_storage import get_session_storage

        storage = get_session_storage()
        recent_sessions = storage.list_recent(limit=10)

        summaries = []
        for session in recent_sessions:
            summaries.append({
                'session_id': session.session_id,
                'user_id': session.user_id,
                'summary': session.summary,
                'summary_type': session.summary_type,
                'created_at': session.created_at,
                'message_count': session.message_count,
                'summary_length': session.summary_length
            })

        return jsonify({
            'summaries': summaries,
            'total': len(summaries)
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'summaries': []
        }), 500


@app.route('/api/session_summary/<session_id>')
def session_summary(session_id):
    """특정 세션 요약 조회"""
    try:
        from persona_system.utils.session_summary_storage import get_session_storage

        storage = get_session_storage()
        session = storage.load(session_id)

        if session:
            return jsonify({
                'session_id': session.session_id,
                'user_id': session.user_id,
                'summary': session.summary,
                'summary_type': session.summary_type,
                'created_at': session.created_at,
                'message_count': session.message_count,
                'summary_length': session.summary_length,
                'metadata': session.metadata
            })
        else:
            return jsonify({'error': 'Session not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/storage_stats')
def storage_stats():
    """저장소 통계"""
    try:
        from persona_system.utils.session_summary_storage import get_session_storage

        storage = get_session_storage()
        stats = storage.get_stats()

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def health():
    """Health check endpoint"""
    try:
        from persona_system.pipeline_optimized import get_optimized_pipeline

        pipeline = get_optimized_pipeline()
        cache = pipeline.cache
        cache_type = type(cache).__name__

        return jsonify({
            'status': 'healthy',
            'cache_type': cache_type,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


def main():
    """Run dashboard server"""
    print("=" * 60)
    print("ion-mentoring Cache Performance Dashboard")
    print("=" * 60)
    print()
    print("Starting server on http://localhost:5001")
    print("Press Ctrl+C to stop")
    print()

    app.run(host='0.0.0.0', port=5001, debug=False)


if __name__ == '__main__':
    main()
