#!/usr/bin/env python3
"""
Lumen Gateway Prometheus Health Exporter

Prometheus text format으로 Gateway 상태와 ION API 메트릭을 expose합니다.
"""

import csv
import os
import sys
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# 경로 설정
GATEWAY_ROOT = Path(__file__).parent.parent
YAML_PATH = GATEWAY_ROOT / "gateway_activation.yaml"
METRICS_CSV = GATEWAY_ROOT / "logs" / "metrics.csv"
LOG_PATH = GATEWAY_ROOT / "logs" / "gateway_sync.log"

KST = timezone(timedelta(hours=9))

# Prometheus 메트릭 정의
METRICS_HELP = """
# HELP lumen_gateway_status Gateway 상태 (0=initializing, 1=locked, 2=binding, 3=resonating)
# TYPE lumen_gateway_status gauge
# HELP lumen_ion_health ION API 헬스 상태 (0=down, 1=up)
# TYPE lumen_ion_health gauge
# HELP lumen_ion_response_time_ms ION API 응답 시간 (ms)
# TYPE lumen_ion_response_time_ms gauge
# HELP lumen_ion_mock_mode ION API Mock 모드 (0=real, 1=mock)
# TYPE lumen_ion_mock_mode gauge
# HELP lumen_ion_confidence ION API 응답 confidence
# TYPE lumen_ion_confidence gauge
# HELP lumen_phase_diff 페이즈 차이 메트릭 (0..1)
# TYPE lumen_phase_diff gauge
# HELP lumen_entropy_rate 엔트로피 비율 (0..1)
# TYPE lumen_entropy_rate gauge
# HELP lumen_creative_band 창의성 대역 (0..1)
# TYPE lumen_creative_band gauge
# HELP lumen_risk_band 리스크 대역 (0..1)
# TYPE lumen_risk_band gauge
""".strip()


def log_message(message: str, level: str = "INFO"):
    """로그 메시지 기록"""
    timestamp = datetime.now(KST).isoformat()
    log_line = f"[{timestamp}] [{level}] {message}\n"
    
    print(log_line.strip())
    
    os.makedirs(LOG_PATH.parent, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_line)


def get_gateway_status():
    """gateway_activation.yaml에서 status 읽기"""
    try:
        import yaml
        with open(YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        status_str = data.get("gateway", {}).get("status", "initializing")
        status_map = {
            "initializing": 0,
            "locked": 1,
            "binding": 2,
            "resonating": 3
        }
        return status_map.get(status_str, 0)
    except Exception:
        return 0


def get_latest_metrics():
    """metrics.csv에서 최신 메트릭 읽기"""
    default = {
        "ion_health": 0,
        "ion_response_time_ms": 0,
        "ion_mock_mode": 0,
        "ion_confidence": 0.0,
        "phase_diff": 0.0,
        "entropy_rate": 0.0,
        "creative_band": 0.0,
        "risk_band": 0.0,
    }
    
    if not METRICS_CSV.exists():
        return default
    
    try:
        with open(METRICS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if not rows:
                return default
            
            last_row = rows[-1]
            
            return {
                "ion_health": int(last_row.get("ion_health", 0)),
                "ion_response_time_ms": float(last_row.get("ion_response_time_ms", 0)),
                "ion_mock_mode": int(last_row.get("ion_mock_mode", 0)),
                "ion_confidence": float(last_row.get("ion_confidence", 0.0)),
                "phase_diff": float(last_row.get("phase_diff", 0.0)),
                "entropy_rate": float(last_row.get("entropy_rate", 0.0)),
                "creative_band": float(last_row.get("creative_band", 0.0)),
                "risk_band": float(last_row.get("risk_band", 0.0)),
            }
    except Exception as e:
        log_message(f"❌ metrics.csv 읽기 오류: {e}", "ERROR")
        return default


def generate_metrics():
    """Prometheus text format 메트릭 생성"""
    gateway_status = get_gateway_status()
    metrics = get_latest_metrics()
    
    lines = [
        METRICS_HELP,
        f'lumen_gateway_status {gateway_status}',
        f'lumen_ion_health {metrics["ion_health"]}',
        f'lumen_ion_response_time_ms {metrics["ion_response_time_ms"]}',
        f'lumen_ion_mock_mode {metrics["ion_mock_mode"]}',
        f'lumen_ion_confidence {metrics["ion_confidence"]}',
        f'lumen_phase_diff {metrics["phase_diff"]}',
        f'lumen_entropy_rate {metrics["entropy_rate"]}',
        f'lumen_creative_band {metrics["creative_band"]}',
        f'lumen_risk_band {metrics["risk_band"]}',
    ]
    
    return "\n".join(lines) + "\n"


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP 요청 핸들러"""
    
    def do_GET(self):
        """GET 요청 처리"""
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            
            metrics_text = generate_metrics()
            self.wfile.write(metrics_text.encode("utf-8"))
            
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK\n")
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """HTTP 로그 메시지"""
        pass  # 조용하게


def main():
    """메인 실행 함수"""
    port = int(os.environ.get("LUMEN_EXPORTER_PORT", "9108"))
    
    log_message(f"🌐 Lumen Gateway Prometheus Exporter 시작")
    log_message(f"포트: {port}")
    log_message(f"엔드포인트: http://localhost:{port}/metrics")
    log_message(f"헬스체크: http://localhost:{port}/health")
    log_message("=" * 60)
    
    try:
        server = HTTPServer(("0.0.0.0", port), MetricsHandler)
        log_message("✅ Exporter 준비 완료")
        server.serve_forever()
    except KeyboardInterrupt:
        log_message("⚠️  사용자에 의해 중단되었습니다.", "WARNING")
        sys.exit(0)
    except Exception as e:
        log_message(f"❌ Exporter 오류: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
