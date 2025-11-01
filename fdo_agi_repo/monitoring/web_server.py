"""
Web Dashboard Server for RPA Monitoring System

FastAPI 기반 웹 대시보드 백엔드
- 메트릭 히스토리 조회
- 실시간 알림 조회
- WebSocket 스트리밍
- 정적 파일 서빙 (HTML/CSS/JS)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import asyncio
import logging
from fdo_agi_repo.orchestrator.resonance_bridge import (
    load_resonance_config,
    get_active_mode,
    get_active_policy_name,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RPA Monitoring Dashboard", version="1.0.0")

# CORS 설정 (브라우저 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 경로 설정
MONITORING_DIR = Path(__file__).parent
OUTPUTS_DIR = MONITORING_DIR.parent / "outputs"
STATIC_DIR = MONITORING_DIR / "static"

# 정적 파일 경로
METRICS_FILE = OUTPUTS_DIR / "rpa_monitoring_metrics.jsonl"
ALERTS_FILE = OUTPUTS_DIR / "rpa_monitoring_alerts.jsonl"


def read_jsonl(file_path: Path, max_lines: Optional[int] = None) -> List[Dict[str, Any]]:
    """JSONL 파일 읽기"""
    if not file_path.exists():
        return []
    
    lines = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        lines.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        # 최신순 정렬 (timestamp 기준)
        lines.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        if max_lines:
            lines = lines[:max_lines]
        
        return lines
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return []


def filter_by_time_window(data: List[Dict], minutes: int) -> List[Dict]:
    """시간 윈도우로 필터링"""
    if not data:
        return []
    
    cutoff = datetime.now() - timedelta(minutes=minutes)
    
    filtered = []
    for item in data:
        timestamp_str = item.get('timestamp', '')
        if not timestamp_str:
            continue
        
        try:
            # float (Unix timestamp) 또는 ISO 8601 형식 파싱
            if isinstance(timestamp_str, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp_str)
            elif isinstance(timestamp_str, str):
                # ISO 8601 형식 파싱
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                # naive datetime으로 변환 (timezone 제거)
                timestamp = timestamp.replace(tzinfo=None)
            else:
                continue
            
            if timestamp >= cutoff:
                filtered.append(item)
        except Exception as e:
            # 경고 없이 조용히 건너뛰기 (로그 스팸 방지)
            continue
    
    return filtered


@app.get("/")
async def read_root():
    """메인 페이지 (정적 HTML)"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(
            content="<h1>RPA Monitoring Dashboard</h1><p>index.html not found. Please create static/index.html</p>",
            status_code=404
        )


@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "metrics_file_exists": METRICS_FILE.exists(),
        "alerts_file_exists": ALERTS_FILE.exists(),
    }


@app.get("/api/metrics/latest")
async def get_latest_metrics():
    """최신 메트릭 (1개)"""
    metrics = read_jsonl(METRICS_FILE, max_lines=1)
    if not metrics:
        return JSONResponse(
            content={"error": "No metrics available"},
            status_code=404
        )
    
    return metrics[0]


@app.get("/api/metrics/history")
async def get_metrics_history(minutes: int = 30):
    """메트릭 히스토리 (시간 윈도우)"""
    all_metrics = read_jsonl(METRICS_FILE)
    filtered_metrics = filter_by_time_window(all_metrics, minutes)
    
    # 시간순 정렬 (오래된 것부터 - 차트용)
    filtered_metrics.sort(key=lambda x: x.get('timestamp', ''))
    
    return {
        "count": len(filtered_metrics),
        "window_minutes": minutes,
        "metrics": filtered_metrics
    }


@app.get("/api/alerts/recent")
async def get_recent_alerts(count: int = 20, severity: Optional[str] = None):
    """최근 알림 조회"""
    all_alerts = read_jsonl(ALERTS_FILE, max_lines=count * 2)  # 여유있게 읽기
    
    # 심각도 필터링
    if severity:
        all_alerts = [a for a in all_alerts if a.get('severity', '').upper() == severity.upper()]
    
    return {
        "count": len(all_alerts[:count]),
        "severity_filter": severity,
        "alerts": all_alerts[:count]
    }


@app.get("/api/system/status")
async def get_system_status():
    """시스템 상태 요약"""
    latest_metrics = read_jsonl(METRICS_FILE, max_lines=1)
    recent_alerts = read_jsonl(ALERTS_FILE, max_lines=10)
    
    if not latest_metrics:
        return JSONResponse(
            content={"error": "No metrics available"},
            status_code=404
        )
    
    latest = latest_metrics[0]

    # Derive success_rate when not persisted in snapshot JSON
    if 'success_rate' in latest and isinstance(latest.get('success_rate'), (int, float)):
        success_rate = float(latest.get('success_rate') or 0)
    else:
        total_tasks = int(latest.get('total_tasks', 0) or 0)
        successful_tasks = int(latest.get('successful_tasks', 0) or 0)
        success_rate = (successful_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0
    
    # 알림 심각도별 카운트
    alert_counts = {"critical": 0, "warning": 0, "info": 0}
    for alert in recent_alerts:
        severity = alert.get('severity', '').lower()
        if severity in alert_counts:
            alert_counts[severity] += 1
    
    return {
        "timestamp": latest.get('timestamp'),
        "success_rate": success_rate,
        "error_rate": latest.get('error_rate', 0),
        "avg_response_time_ms": latest.get('avg_response_time_ms', 0),
        "active_workers": latest.get('active_workers', 0),
        "queue_size": latest.get('queue_size', 0),
        "total_tasks": latest.get('total_tasks', 0),
        "successful_tasks": latest.get('successful_tasks', 0),
        "failed_tasks": latest.get('failed_tasks', 0),
        "memory_mb": latest.get('memory_mb', 0),
        "cpu_percent": latest.get('cpu_percent', 0),
        "alerts": alert_counts,
        "health_status": "healthy" if success_rate >= 80 else "degraded",
        "resonance": {
            "mode": get_active_mode(),
            "policy_name": get_active_policy_name(),
        },
    }


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket 실시간 메트릭 스트리밍"""
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    try:
        while True:
            # 최신 메트릭 전송
            latest_metrics = read_jsonl(METRICS_FILE, max_lines=1)
            if latest_metrics:
                await websocket.send_json(latest_metrics[0])
            
            # 3초 대기
            await asyncio.sleep(3)
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


# 정적 파일 서빙 (HTML, CSS, JS)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/api/resonance/config")
async def api_resonance_config():
    """Expose current resonance configuration (active mode/policy + policies)."""
    try:
        cfg = load_resonance_config()
        return cfg
    except Exception:
        return JSONResponse(content={"error": "config_unavailable"}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    
    # static 디렉토리 생성 (없으면)
    STATIC_DIR.mkdir(exist_ok=True, parents=True)
    
    logger.info("=" * 60)
    logger.info("🚀 RPA Monitoring Web Dashboard Server")
    logger.info("=" * 60)
    logger.info(f"  Metrics file: {METRICS_FILE}")
    logger.info(f"  Alerts file:  {ALERTS_FILE}")
    logger.info(f"  Static dir:   {STATIC_DIR}")
    logger.info("")
    logger.info("  API Endpoints:")
    logger.info("    - GET  /api/health")
    logger.info("    - GET  /api/metrics/latest")
    logger.info("    - GET  /api/metrics/history?minutes=30")
    logger.info("    - GET  /api/alerts/recent?count=20&severity=CRITICAL")
    logger.info("    - GET  /api/system/status")
    logger.info("    - WS   /ws/metrics")
    logger.info("")
    logger.info("  Dashboard URL: http://127.0.0.1:8000")
    logger.info("=" * 60)
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
