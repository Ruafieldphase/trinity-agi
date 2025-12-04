#!/usr/bin/env python3
"""
AGI Real-time Dashboard
Flask 기반 실시간 모니터링 대시보드
"""

from flask import Flask, render_template, jsonify
from pathlib import Path
import sys

# metrics_collector 임포트
sys.path.insert(0, str(Path(__file__).parent))
from metrics_collector import MetricsCollector

app = Flask(__name__)
collector = MetricsCollector()


@app.route('/')
def index():
    """대시보드 메인 페이지"""
    return render_template('index.html')


@app.route('/api/metrics/realtime')
def api_metrics_realtime():
    """실시간 메트릭 API (최근 1시간)"""
    hours = float(request.args.get('hours', 1.0))
    metrics = collector.get_realtime_metrics(hours=hours)
    return jsonify(metrics)


@app.route('/api/metrics/timeline')
def api_metrics_timeline():
    """타임라인 데이터 API"""
    hours = float(request.args.get('hours', 24.0))
    interval = int(request.args.get('interval', 30))
    timeline = collector.get_timeline_data(hours=hours, interval_minutes=interval)
    return jsonify(timeline)


@app.route('/api/health')
def api_health():
    """헬스 상태 API"""
    health = collector.get_health_status()
    return jsonify(health)


@app.route('/api/events/recent')
def api_events_recent():
    """최근 이벤트 API (raw events)"""
    hours = float(request.args.get('hours', 0.5))
    limit = int(request.args.get('limit', 50))
    events = collector.read_events(hours=hours)
    # 최근 N개만 반환
    return jsonify(events[-limit:])


if __name__ == '__main__':
    from flask import request
    print("🚀 AGI Dashboard Starting...")
    print("📊 Open http://localhost:5000 in your browser")
    app.run(host='0.0.0.0', port=5000, debug=True)
