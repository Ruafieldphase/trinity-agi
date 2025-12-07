"""
Credentials Manager
모든 인증 정보를 한곳에서 관리하는 중앙 시스템
"""
import os
from pathlib import Path
from typing import Optional

class CredentialsManager:
    """AGI 시스템의 모든 인증 정보를 관리"""
    
    def __init__(self, env_file: Optional[Path] = None):
        if env_file is None:
            env_file = Path(__file__).parent.parent / ".env_credentials"
        
        self.env_file = env_file
        self.credentials = {}
        self._load()
    
    def _load(self):
        """인증 정보 파일 로드"""
        if not self.env_file.exists():
            print(f"⚠️ Credentials file not found: {self.env_file}")
            return
        
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    self.credentials[key.strip()] = value.strip()
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """인증 정보 가져오기"""
        return self.credentials.get(key, default)
    
    @property
    def linux_vm(self) -> dict:
        """Linux VM 접속 정보"""
        return {
            'host': self.get('LINUX_VM_HOST', '192.168.119.128'),
            'user': self.get('LINUX_VM_USER', 'bino'),
            'password': self.get('LINUX_VM_PASSWORD', '0000')
        }
    
    @property
    def slack(self) -> dict:
        """Slack API 정보"""
        return {
            'bot_token': self.get('SLACK_BOT_TOKEN'),
            'app_token': self.get('SLACK_APP_TOKEN')
        }
    
    @property
    def wave_api_key(self) -> str:
        """Wave API 키"""
        return self.get('WAVE_API_KEY', 'wave_60hn6pf7-zba22qzp-tdfe9tm2-t2a8d1y1')

# 전역 인스턴스
_credentials = None

def get_credentials() -> CredentialsManager:
    """전역 Credentials Manager 인스턴스 가져오기"""
    global _credentials
    if _credentials is None:
        _credentials = CredentialsManager()
    return _credentials

# 편의 함수들
def get_linux_vm_credentials() -> dict:
    """Linux VM 접속 정보 가져오기"""
    return get_credentials().linux_vm

def get_slack_credentials() -> dict:
    """Slack API 정보 가져오기"""
    return get_credentials().slack

def get_wave_api_key() -> str:
    """Wave API 키 가져오기"""
    return get_credentials().wave_api_key

if __name__ == "__main__":
    # 테스트
    creds = get_credentials()
    print("🔐 Credentials Manager Test")
    print(f"Linux VM: {creds.linux_vm}")
    print(f"Slack: {creds.slack}")
    print(f"Wave API: {creds.wave_api_key}")
