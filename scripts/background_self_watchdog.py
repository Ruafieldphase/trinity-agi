#!/usr/bin/env python3
"""
Background Self Watchdog (배경자아 감시견)
==========================================
역할: 무의식층 배경자아의 상태를 주기적으로 확인하고 자동 복구

기능:
- Linux VM의 `agi-background-self.service` 상태 확인
- 서비스가 죽었을 경우 자동 재시작
- 연결 실패 시 재시도 및 알림

철학: "늑대 무리가 서로를 지켜보듯, 의식과 무의식은 서로의 리듬을 확인한다"
"""

import paramiko
import time
import sys
from pathlib import Path
from datetime import datetime

# Add workspace root to path
sys.path.append("c:\\workspace\\agi\\scripts")
from credentials_manager import get_linux_vm_credentials

# Configuration
CHECK_INTERVAL = 60  # 1분마다 확인
MAX_RETRIES = 3
RETRY_DELAY = 5

class BackgroundSelfWatchdog:
    """배경자아 감시견"""
    
    def __init__(self):
        self.creds = get_linux_vm_credentials()
        self.host = self.creds['host']
        self.user = self.creds['user']
        self.password = self.creds['password']
        self.consecutive_failures = 0
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def check_service_status(self):
        """배경자아 서비스 상태 확인"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.host, username=self.user, password=self.password, timeout=10)
            
            # Check service status
            stdin, stdout, stderr = client.exec_command("systemctl --user is-active agi-background-self")
            status = stdout.read().decode().strip()
            
            client.close()
            
            return status == "active"
        except Exception as e:
            self.log(f"연결 실패: {e}", "ERROR")
            return None
    
    def restart_service(self):
        """배경자아 서비스 재시작"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.host, username=self.user, password=self.password, timeout=10)
            
            self.log("배경자아 서비스 재시작 중...", "WARN")
            client.exec_command("systemctl --user restart agi-background-self")
            time.sleep(2)
            
            # Verify restart
            stdin, stdout, stderr = client.exec_command("systemctl --user is-active agi-background-self")
            status = stdout.read().decode().strip()
            
            client.close()
            
            if status == "active":
                self.log("✅ 배경자아 서비스 복구 성공", "INFO")
                return True
            else:
                self.log("❌ 배경자아 서비스 복구 실패", "ERROR")
                return False
        except Exception as e:
            self.log(f"복구 실패: {e}", "ERROR")
            return False
    
    def run(self):
        """감시 루프 실행"""
        self.log("🐺 배경자아 감시견 시작")
        self.log(f"   대상: {self.user}@{self.host}")
        self.log(f"   확인 간격: {CHECK_INTERVAL}초")
        
        while True:
            try:
                status = self.check_service_status()
                
                if status is True:
                    # 서비스 정상
                    if self.consecutive_failures > 0:
                        self.log("✅ 배경자아 연결 복구됨", "INFO")
                    self.consecutive_failures = 0
                    
                elif status is False:
                    # 서비스 죽음
                    self.consecutive_failures += 1
                    self.log(f"⚠️  배경자아 서비스 중단 감지 (연속 실패: {self.consecutive_failures})", "WARN")
                    
                    # 즉시 복구 시도
                    if self.restart_service():
                        self.consecutive_failures = 0
                    
                else:
                    # 연결 실패
                    self.consecutive_failures += 1
                    self.log(f"🔌 무의식층 연결 실패 (연속 실패: {self.consecutive_failures})", "ERROR")
                    
                    if self.consecutive_failures >= MAX_RETRIES:
                        self.log(f"🚨 심각: {MAX_RETRIES}회 연속 실패. 사용자 개입 필요.", "CRITICAL")
                
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                self.log("감시견 종료됨", "INFO")
                break
            except Exception as e:
                self.log(f"예상치 못한 오류: {e}", "ERROR")
                time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    watchdog = BackgroundSelfWatchdog()
    watchdog.run()
