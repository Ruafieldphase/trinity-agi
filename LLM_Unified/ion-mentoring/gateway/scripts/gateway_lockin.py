#!/usr/bin/env python3
"""
Lumen Gateway Lock-in Script

Gateway 서명 해시를 검증하고 status를 'locked'로 전환합니다.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 경로 설정
GATEWAY_ROOT = Path(__file__).parent.parent
YAML_PATH = GATEWAY_ROOT / "gateway_activation.yaml"
LOG_PATH = GATEWAY_ROOT / "logs" / "gateway_sync.log"

KST = timezone(timedelta(hours=9))


def log_message(message: str, level: str = "INFO"):
    """로그 메시지 기록"""
    timestamp = datetime.now(KST).isoformat()
    log_line = f"[{timestamp}] [{level}] {message}\n"
    
    # 콘솔 출력
    print(log_line.strip())
    
    # 파일 기록
    os.makedirs(LOG_PATH.parent, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_line)


def calculate_signature(yaml_content: str) -> str:
    """YAML 내용의 SHA256 서명 생성"""
    return hashlib.sha256(yaml_content.encode("utf-8")).hexdigest()


def lock_gateway():
    """Gateway를 locked 상태로 전환"""
    
    log_message("🌐 Lumen Gateway Lock-in 시작")
    
    # YAML 파일 존재 확인
    if not YAML_PATH.exists():
        log_message(f"❌ gateway_activation.yaml 파일을 찾을 수 없습니다: {YAML_PATH}", "ERROR")
        return False
    
    # YAML 파일 읽기
    try:
        import yaml
    except ImportError:
        log_message("⚠️  PyYAML이 설치되지 않았습니다. pip install pyyaml", "WARNING")
        log_message("   YAML 파싱 없이 텍스트 모드로 진행합니다.", "INFO")
        yaml = None
    
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 서명 생성
    signature = calculate_signature(content)
    log_message(f"📝 Gateway 서명: {signature[:16]}...")
    
    # YAML 파싱 및 상태 확인
    if yaml:
        try:
            data = yaml.safe_load(content)
            current_status = data.get("gateway", {}).get("status", "unknown")
            log_message(f"현재 상태: {current_status}")
            
            if current_status == "locked":
                log_message("✅ Gateway가 이미 locked 상태입니다.")
                return True
            
            # status를 locked로 변경
            data["gateway"]["status"] = "locked"
            data["gateway"]["timestamp"] = datetime.now(KST).isoformat()
            data["gateway"]["signature"] = signature
            
            # restore_points 업데이트
            data.setdefault("restore_points", {})
            data["restore_points"]["last_locked_at"] = datetime.now(KST).isoformat()
            
            # metadata 업데이트
            data.setdefault("metadata", {})
            data["metadata"]["last_updated"] = datetime.now(KST).isoformat()
            
            # YAML 파일 저장
            with open(YAML_PATH, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            log_message("✅ Gateway 상태를 'locked'로 전환했습니다.")
            log_message(f"🔒 서명이 gateway_activation.yaml에 기록되었습니다.")
            
        except Exception as e:
            log_message(f"❌ YAML 파싱 오류: {e}", "ERROR")
            return False
    else:
        # YAML 라이브러리 없이 텍스트 기반 처리
        log_message("⚠️  텍스트 모드: status를 수동으로 'locked'로 변경하세요", "WARNING")
        log_message(f"   서명: {signature}", "INFO")
    
    log_message("🌙 Lumen Gateway Lock-in 완료")
    return True


def main():
    """메인 실행 함수"""
    try:
        success = lock_gateway()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log_message("⚠️  사용자에 의해 중단되었습니다.", "WARNING")
        sys.exit(1)
    except Exception as e:
        log_message(f"❌ 예상치 못한 오류: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
