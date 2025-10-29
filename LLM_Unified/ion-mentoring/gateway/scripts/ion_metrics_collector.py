#!/usr/bin/env python3
"""
ION API Metrics Collector

ION API의 상태를 주기적으로 수집하여 metrics.csv에 기록합니다.
"""

import csv
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 경로 설정
GATEWAY_ROOT = Path(__file__).parent.parent
YAML_PATH = GATEWAY_ROOT / "gateway_activation.yaml"
METRICS_CSV = GATEWAY_ROOT / "logs" / "metrics.csv"
LOG_PATH = GATEWAY_ROOT / "logs" / "gateway_sync.log"

KST = timezone(timedelta(hours=9))

# CSV 헤더
FIELDNAMES = [
    "ts",  # ISO8601 timestamp
    "ion_health",  # 0=down, 1=up
    "ion_response_time_ms",  # 응답 시간 (ms)
    "ion_mock_mode",  # 0=real, 1=mock
    "ion_confidence",  # 마지막 응답 confidence
    "ion_persona",  # 사용된 페르소나
    "phase_diff",  # [0..1]
    "entropy_rate",  # [0..1]
    "creative_band",  # [0..1]
    "risk_band",  # [0..1]
]


def log_message(message: str, level: str = "INFO"):
    """로그 메시지 기록"""
    timestamp = datetime.now(KST).isoformat()
    log_line = f"[{timestamp}] [{level}] {message}\n"
    
    print(log_line.strip())
    
    os.makedirs(LOG_PATH.parent, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_line)


def get_ion_api_url():
    """gateway_activation.yaml에서 ION API URL 가져오기"""
    try:
        import yaml
        with open(YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("loop_coordinates", {}).get("ion_api_url", "")
    except Exception as e:
        log_message(f"❌ YAML 파싱 오류: {e}", "ERROR")
        return "https://ion-api-64076350717.us-central1.run.app"


def check_ion_health(url: str, timeout: int = 10):
    """ION API 헬스 체크"""
    start_time = time.time()
    
    try:
        req = urllib.request.Request(f"{url}/health")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            elapsed_ms = (time.time() - start_time) * 1000
            status_code = response.getcode()
            
            return {
                "health": 1 if status_code == 200 else 0,
                "response_time_ms": round(elapsed_ms, 2),
                "error": None
            }
    except urllib.error.URLError as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "health": 0,
            "response_time_ms": round(elapsed_ms, 2),
            "error": str(e)
        }


def test_ion_chat(url: str, timeout: int = 10):
    """ION API 채팅 테스트 (Mock 모드 감지)"""
    start_time = time.time()
    
    test_message = {"message": "시스템 상태를 알려주세요"}
    
    try:
        req = urllib.request.Request(
            f"{url}/chat",
            data=json.dumps(test_message).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            elapsed_ms = (time.time() - start_time) * 1000
            data = json.loads(response.read().decode("utf-8"))
            
            # Mock 모드 감지
            content = data.get("content", "")
            is_mock = 1 if "Mock response for development" in content else 0
            
            return {
                "mock_mode": is_mock,
                "confidence": data.get("confidence", 0.0),
                "persona": data.get("persona_used", "unknown"),
                "response_time_ms": round(elapsed_ms, 2),
                "error": None
            }
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "mock_mode": -1,  # unknown
            "confidence": 0.0,
            "persona": "error",
            "response_time_ms": round(elapsed_ms, 2),
            "error": str(e)
        }


def calculate_resonance_metrics():
    """감응 메트릭 계산 (시뮬레이션)"""
    import random
    import math
    
    # 간단한 시뮬레이션 (실제로는 시스템 메트릭 기반 계산)
    t = time.time() % 300  # 5분 주기
    
    phase_diff = 0.5 * (1 + math.sin(2 * math.pi * t / 300)) * 0.8 + random.uniform(-0.05, 0.05)
    entropy_rate = 0.2 + 0.1 * math.exp(-t / 180) + random.uniform(-0.02, 0.02)
    creative_band = 0.3 + 0.2 * (1 - math.exp(-t / 240)) + random.uniform(-0.03, 0.03)
    risk_band = 0.3 * math.exp(-t / 200) + random.uniform(-0.02, 0.02)
    
    return {
        "phase_diff": max(0.0, min(1.0, round(phase_diff, 3))),
        "entropy_rate": max(0.0, min(1.0, round(entropy_rate, 3))),
        "creative_band": max(0.0, min(1.0, round(creative_band, 3))),
        "risk_band": max(0.0, min(1.0, round(risk_band, 3))),
    }


def collect_metrics(ion_url: str):
    """메트릭 수집 및 CSV 기록"""
    
    # ION API 헬스 체크
    health_result = check_ion_health(ion_url)
    
    # ION API 채팅 테스트 (Mock 감지)
    chat_result = test_ion_chat(ion_url)
    
    # 감응 메트릭 계산
    resonance = calculate_resonance_metrics()
    
    # CSV 레코드 생성
    row = {
        "ts": datetime.now(KST).isoformat(),
        "ion_health": health_result["health"],
        "ion_response_time_ms": health_result["response_time_ms"],
        "ion_mock_mode": chat_result["mock_mode"],
        "ion_confidence": chat_result["confidence"],
        "ion_persona": chat_result["persona"],
        "phase_diff": resonance["phase_diff"],
        "entropy_rate": resonance["entropy_rate"],
        "creative_band": resonance["creative_band"],
        "risk_band": resonance["risk_band"],
    }
    
    # CSV에 추가
    os.makedirs(METRICS_CSV.parent, exist_ok=True)
    
    file_exists = METRICS_CSV.exists()
    with open(METRICS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    
    # 로그 출력
    status = "✅" if health_result["health"] == 1 else "❌"
    mock_status = "🔴 MOCK" if chat_result["mock_mode"] == 1 else "🟢 REAL"
    
    log_message(
        f"{status} ION API {mock_status} | "
        f"Confidence: {chat_result['confidence']:.2f} | "
        f"Persona: {chat_result['persona']} | "
        f"Latency: {health_result['response_time_ms']:.0f}ms"
    )
    
    if chat_result["error"]:
        log_message(f"   Error: {chat_result['error']}", "ERROR")
    
    return row


def main():
    """메인 실행 함수"""
    log_message("🌐 ION API Metrics Collector 시작")
    
    ion_url = get_ion_api_url()
    log_message(f"ION API URL: {ion_url}")
    
    # 수집 간격 (초)
    interval = int(os.environ.get("LUMEN_COLLECT_INTERVAL", "30"))
    log_message(f"수집 간격: {interval}초")
    log_message("Ctrl+C로 중지")
    log_message("=" * 60)
    
    try:
        while True:
            try:
                collect_metrics(ion_url)
            except Exception as e:
                log_message(f"❌ 메트릭 수집 오류: {e}", "ERROR")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        log_message("⚠️  사용자에 의해 중단되었습니다.", "WARNING")
        sys.exit(0)


if __name__ == "__main__":
    main()
