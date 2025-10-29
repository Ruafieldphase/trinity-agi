"""
Utility Functions

Slack Bot 공통 유틸리티
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import re


def load_env_file(path: str = ".env.slack") -> Dict[str, str]:
    """
    환경 변수 파일 로드
    
    Args:
        path: .env 파일 경로
    
    Returns:
        환경 변수 딕셔너리
    """
    env_vars = {}
    
    if not os.path.exists(path):
        return env_vars
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # 빈 줄이나 주석 무시
            if not line or line.startswith("#"):
                continue
            
            # KEY=VALUE 형식 파싱
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars


def apply_env_vars(env_vars: Dict[str, str]) -> None:
    """
    환경 변수 적용
    
    Args:
        env_vars: 환경 변수 딕셔너리
    """
    for key, value in env_vars.items():
        os.environ[key] = value


def format_duration(seconds: float) -> str:
    """
    초를 사람이 읽기 쉬운 형식으로 변환
    
    Args:
        seconds: 초
    
    Returns:
        포맷된 문자열 (예: "1h 23m 45s")
    """
    if seconds < 60:
        return f"{seconds:.0f}s"
    
    minutes = seconds // 60
    seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes:.0f}m {seconds:.0f}s"
    
    hours = minutes // 60
    minutes = minutes % 60
    
    if hours < 24:
        return f"{hours:.0f}h {minutes:.0f}m"
    
    days = hours // 24
    hours = hours % 24
    
    return f"{days:.0f}d {hours:.0f}h"


def format_bytes(bytes_value: int) -> str:
    """
    바이트를 사람이 읽기 쉬운 형식으로 변환
    
    Args:
        bytes_value: 바이트 수
    
    Returns:
        포맷된 문자열 (예: "1.5 MB")
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes_value)
    unit_idx = 0
    
    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024
        unit_idx += 1
    
    return f"{size:.1f} {units[unit_idx]}"


def parse_percentage(text: str) -> Optional[int]:
    """
    퍼센트 문자열 파싱
    
    Args:
        text: 퍼센트 문자열 (예: "50%", "50", "0.5")
    
    Returns:
        정수 퍼센트 (0-100) 또는 None
    """
    # "50%" 형식
    match = re.match(r"(\d+)%", text)
    if match:
        value = int(match.group(1))
        return value if 0 <= value <= 100 else None
    
    # "50" 형식
    try:
        value = int(text)
        return value if 0 <= value <= 100 else None
    except ValueError:
        pass
    
    # "0.5" 형식 (0.0 ~ 1.0)
    try:
        value = float(text)
        if 0.0 <= value <= 1.0:
            return int(value * 100)
    except ValueError:
        pass
    
    return None


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    텍스트 잘라내기
    
    Args:
        text: 원본 텍스트
        max_length: 최대 길이
        suffix: 접미사
    
    Returns:
        잘라낸 텍스트
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    텍스트에서 JSON 추출
    
    Args:
        text: 텍스트
    
    Returns:
        JSON 딕셔너리 또는 None
    """
    # JSON 블록 찾기
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return None
    
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def format_timestamp(timestamp: Optional[float] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    타임스탬프 포맷
    
    Args:
        timestamp: Unix 타임스탬프 (None이면 현재 시간)
        format_str: 포맷 문자열
    
    Returns:
        포맷된 시간 문자열
    """
    if timestamp is None:
        dt = datetime.now()
    else:
        dt = datetime.fromtimestamp(timestamp)
    
    return dt.strftime(format_str)


def validate_slack_token(token: str) -> bool:
    """
    Slack 토큰 유효성 검증
    
    Args:
        token: Slack 토큰
    
    Returns:
        유효 여부
    """
    # Bot Token: xoxb-
    # App Token: xapp-
    # User Token: xoxp-
    return token.startswith(("xoxb-", "xapp-", "xoxp-"))


def create_quick_reply_blocks(
    text: str,
    buttons: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    빠른 답장 블록 생성
    
    Args:
        text: 메시지 텍스트
        buttons: 버튼 리스트 [{"text": "버튼명", "value": "값"}]
    
    Returns:
        Slack 블록 리스트
    """
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }
    ]
    
    # 버튼 추가
    if buttons:
        elements = []
        for btn in buttons:
            elements.append({
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": btn["text"]
                },
                "value": btn["value"]
            })
        
        blocks.append({
            "type": "actions",
            "elements": elements
        })
    
    return blocks


def parse_user_mention(text: str) -> Optional[str]:
    """
    사용자 멘션 파싱
    
    Args:
        text: 텍스트 (예: "<@U12345678>")
    
    Returns:
        사용자 ID 또는 None
    """
    match = re.match(r"<@([A-Z0-9]+)>", text)
    if match:
        return match.group(1)
    return None


def is_valid_channel(channel: str) -> bool:
    """
    채널 ID 유효성 검증
    
    Args:
        channel: 채널 ID 또는 이름
    
    Returns:
        유효 여부
    """
    # 채널 ID: C로 시작 (공개 채널) 또는 G로 시작 (비공개 그룹)
    if channel.startswith(("C", "G", "D")):
        return True
    
    # 채널 이름: #으로 시작
    if channel.startswith("#"):
        return True
    
    return False


def format_list(items: List[str], prefix: str = "•") -> str:
    """
    리스트 포맷
    
    Args:
        items: 아이템 리스트
        prefix: 접두사 (기본: 불릿)
    
    Returns:
        포맷된 문자열
    """
    return "\n".join([f"{prefix} {item}" for item in items])


def create_status_emoji(status: str) -> str:
    """
    상태에 맞는 이모지 반환
    
    Args:
        status: 상태 (healthy, degraded, down, warning, error, etc.)
    
    Returns:
        이모지
    """
    emoji_map = {
        "healthy": "✅",
        "degraded": "⚠️",
        "down": "❌",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️",
        "success": "✅",
        "failed": "❌",
        "pending": "🕐",
        "running": "🔄",
        "completed": "✅"
    }
    
    return emoji_map.get(status.lower(), "📊")


def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    안전한 중첩 딕셔너리 접근
    
    Args:
        data: 딕셔너리
        *keys: 키 체인
        default: 기본값
    
    Returns:
        값 또는 기본값
    """
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current
