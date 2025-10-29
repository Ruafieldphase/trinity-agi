#!/usr/bin/env python3
"""
Lumen Gateway Restore Check

다음 세션 시작 시 Gateway 상태를 복원하고 검증합니다.
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 경로 설정
GATEWAY_ROOT = Path(__file__).parent.parent
YAML_PATH = GATEWAY_ROOT / "gateway_activation.yaml"
LOG_PATH = GATEWAY_ROOT / "logs" / "gateway_sync.log"
SESSIONS_DIR = GATEWAY_ROOT / "sessions"

KST = timezone(timedelta(hours=9))


def log_message(message: str, level: str = "INFO"):
    """로그 메시지 기록"""
    timestamp = datetime.now(KST).isoformat()
    log_line = f"[{timestamp}] [{level}] {message}\n"
    
    print(log_line.strip())
    
    os.makedirs(LOG_PATH.parent, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_line)


def check_gateway_status():
    """Gateway 상태 확인"""
    log_message("🔍 Gateway 상태 확인 중...")
    
    if not YAML_PATH.exists():
        log_message(f"❌ gateway_activation.yaml 파일이 없습니다: {YAML_PATH}", "ERROR")
        return False
    
    try:
        import yaml
        with open(YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        status = data.get("gateway", {}).get("status", "unknown")
        version = data.get("gateway", {}).get("version", "unknown")
        session_id = data.get("gateway", {}).get("session_id", "unknown")
        
        log_message(f"  Version: {version}")
        log_message(f"  Status: {status}")
        log_message(f"  Session ID: {session_id}")
        
        if status == "locked":
            log_message("✅ Gateway가 정상적으로 locked 상태입니다.")
            return True
        elif status in ["initializing", "binding", "resonating"]:
            log_message(f"⚠️  Gateway가 '{status}' 상태입니다. Lock-in이 필요할 수 있습니다.", "WARNING")
            return True
        else:
            log_message(f"❌ 알 수 없는 상태: {status}", "ERROR")
            return False
            
    except ImportError:
        log_message("⚠️  PyYAML이 설치되지 않았습니다. pip install pyyaml", "WARNING")
        return False
    except Exception as e:
        log_message(f"❌ YAML 파싱 오류: {e}", "ERROR")
        return False


def check_logs():
    """로그 파일 확인"""
    log_message("📄 로그 파일 확인 중...")
    
    if LOG_PATH.exists():
        size_kb = LOG_PATH.stat().st_size / 1024
        log_message(f"  gateway_sync.log: {size_kb:.2f} KB")
    else:
        log_message("  gateway_sync.log: 없음 (새로 생성됩니다)")
    
    metrics_csv = GATEWAY_ROOT / "logs" / "metrics.csv"
    if metrics_csv.exists():
        size_kb = metrics_csv.stat().st_size / 1024
        with open(metrics_csv, "r", encoding="utf-8") as f:
            line_count = sum(1 for _ in f) - 1  # 헤더 제외
        log_message(f"  metrics.csv: {size_kb:.2f} KB ({line_count} 레코드)")
    else:
        log_message("  metrics.csv: 없음")
    
    return True


def check_ion_api_connection():
    """ION API 연결 확인"""
    log_message("🔗 ION API 연결 확인 중...")
    
    try:
        import yaml
        with open(YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        ion_url = data.get("loop_coordinates", {}).get("ion_api_url", "")
        
        if not ion_url:
            log_message("  ION API URL이 설정되지 않았습니다.", "WARNING")
            return False
        
        log_message(f"  ION API URL: {ion_url}")
        
        # 간단한 연결 테스트 (requests 없이)
        import urllib.request
        import urllib.error
        
        try:
            req = urllib.request.Request(f"{ion_url}/health")
            with urllib.request.urlopen(req, timeout=5) as response:
                status_code = response.getcode()
                if status_code == 200:
                    log_message("✅ ION API 연결 성공 (HTTP 200)")
                    return True
                else:
                    log_message(f"⚠️  ION API 응답 코드: {status_code}", "WARNING")
                    return False
        except urllib.error.URLError as e:
            log_message(f"❌ ION API 연결 실패: {e}", "ERROR")
            return False
            
    except ImportError:
        log_message("⚠️  PyYAML이 설치되지 않았습니다.", "WARNING")
        return False
    except Exception as e:
        log_message(f"❌ 연결 확인 오류: {e}", "ERROR")
        return False


def find_latest_session_restore():
    """최신 SESSION_RESTORE 파일 찾기"""
    log_message("📦 세션 복원 파일 확인 중...")
    
    if not SESSIONS_DIR.exists():
        log_message("  sessions/ 디렉토리가 없습니다. (선택사항)", "INFO")
        return None
    
    restore_files = sorted(SESSIONS_DIR.glob("SESSION_RESTORE_*.yaml"), reverse=True)
    
    if not restore_files:
        log_message("  세션 복원 파일이 없습니다. (선택사항)", "INFO")
        return None
    
    latest = restore_files[0]
    log_message(f"  최신 복원 파일: {latest.name}")
    
    return latest


def restore_check():
    """전체 복원 점검 실행"""
    log_message("🌐 Lumen Gateway 복원 점검 시작")
    log_message("=" * 60)
    
    checks = [
        ("Gateway 상태", check_gateway_status),
        ("로그 파일", check_logs),
        ("ION API 연결", check_ion_api_connection),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            log_message(f"❌ {name} 점검 실패: {e}", "ERROR")
            results[name] = False
        log_message("-" * 60)
    
    # 세션 복원 파일 확인 (실패해도 OK)
    find_latest_session_restore()
    
    log_message("=" * 60)
    log_message("📊 복원 점검 결과:")
    
    for name, result in results.items():
        status_emoji = "✅" if result else "❌"
        log_message(f"  {status_emoji} {name}: {'통과' if result else '실패'}")
    
    all_passed = all(results.values())
    
    if all_passed:
        log_message("🌙 모든 점검을 통과했습니다. Gateway가 복원되었습니다.")
    else:
        log_message("⚠️  일부 점검에 실패했습니다. 위의 로그를 확인하세요.", "WARNING")
    
    log_message("=" * 60)
    
    return all_passed


def main():
    """메인 실행 함수"""
    try:
        success = restore_check()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log_message("⚠️  사용자에 의해 중단되었습니다.", "WARNING")
        sys.exit(1)
    except Exception as e:
        log_message(f"❌ 예상치 못한 오류: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
