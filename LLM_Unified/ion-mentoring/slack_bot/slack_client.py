"""
Slack Client

Slack API와의 기본 통신을 담당하는 클라이언트 모듈
"""

import os
import time
from typing import Dict, List, Optional, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

logger = logging.getLogger(__name__)


class SlackClient:
    """Slack API 클라이언트"""
    
    def __init__(self, token: Optional[str] = None):
        """
        초기화
        
        Args:
            token: Slack Bot Token (기본값: 환경변수 SLACK_BOT_TOKEN)
        """
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError("SLACK_BOT_TOKEN이 설정되지 않았습니다")
        
        self.client = WebClient(token=self.token)
        self.retry_max = 3
        self.retry_delay = 1.0
    
    def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None,
        thread_ts: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        메시지 전송
        
        Args:
            channel: 채널 ID 또는 이름 (#으로 시작)
            text: 메시지 텍스트
            blocks: Block Kit 블록 (선택)
            attachments: 첨부 파일 (선택)
            thread_ts: 스레드 타임스탬프 (선택)
        
        Returns:
            API 응답
        """
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
                attachments=attachments,
                thread_ts=thread_ts
            )
            
            if response.get("ok"):
                logger.info(f"메시지 전송 성공: {channel}")
                return response
            else:
                logger.error(f"메시지 전송 실패: {response.get('error')}")
                return response
        
        except SlackApiError as e:
            logger.error(f"Slack API 오류: {e.response['error']}")
            raise
    
    def send_interactive_message(
        self,
        channel: str,
        text: str,
        buttons: List[Dict[str, str]],
        header: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        인터랙티브 메시지 (버튼 포함) 전송
        
        Args:
            channel: 채널 ID 또는 이름
            text: 메시지 텍스트
            buttons: 버튼 리스트 [{"text": "버튼명", "value": "값", "style": "primary|danger"}]
            header: 헤더 텍스트 (선택)
        
        Returns:
            API 응답
        """
        blocks = []
        
        # 헤더 추가
        if header:
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header
                }
            })
        
        # 본문 추가
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        })
        
        # 버튼 추가
        button_elements = []
        for btn in buttons:
            element = {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": btn["text"]
                },
                "value": btn["value"]
            }
            if "style" in btn:
                element["style"] = btn["style"]
            button_elements.append(element)
        
        blocks.append({
            "type": "actions",
            "elements": button_elements
        })
        
        return self.send_message(channel=channel, text=text, blocks=blocks)
    
    def send_alert(
        self,
        channel: str,
        severity: str,
        title: str,
        message: str,
        details: Optional[Dict[str, str]] = None,
        actions: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        알림 메시지 전송
        
        Args:
            channel: 채널 ID 또는 이름
            severity: critical, warning, info
            title: 알림 제목
            message: 알림 본문
            details: 추가 세부 정보 딕셔너리
            actions: 액션 버튼 리스트
        
        Returns:
            API 응답
        """
        # 색상 및 아이콘 결정
        color_map = {
            "critical": "#ff0000",
            "warning": "#ffcc00",
            "info": "#0099ff"
        }
        icon_map = {
            "critical": "🚨",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        
        color = color_map.get(severity, "#666666")
        icon = icon_map.get(severity, "📢")
        
        # 블록 생성
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{icon} {title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
        
        # 세부 정보 추가
        if details:
            fields = []
            for key, value in details.items():
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:*\n{value}"
                })
            blocks.append({
                "type": "section",
                "fields": fields
            })
        
        # 액션 버튼 추가
        if actions:
            elements = []
            for action in actions:
                elements.append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": action["text"]
                    },
                    "url": action.get("url"),
                    "value": action.get("value")
                })
            blocks.append({
                "type": "actions",
                "elements": elements
            })
        
        # 첨부 파일로 감싸서 색상 적용
        attachments = [
            {
                "color": color,
                "blocks": blocks
            }
        ]
        
        return self.send_message(
            channel=channel,
            text=f"{icon} {title}",
            attachments=attachments
        )
    
    def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        메시지 업데이트
        
        Args:
            channel: 채널 ID 또는 이름
            ts: 메시지 타임스탬프
            text: 새 메시지 텍스트
            blocks: 새 블록 (선택)
        
        Returns:
            API 응답
        """
        try:
            response = self.client.chat_update(
                channel=channel,
                ts=ts,
                text=text,
                blocks=blocks
            )
            
            if response.get("ok"):
                logger.info(f"메시지 업데이트 성공: {channel}")
            else:
                logger.error(f"메시지 업데이트 실패: {response.get('error')}")
            
            return response
        
        except SlackApiError as e:
            logger.error(f"Slack API 오류: {e.response['error']}")
            raise
    
    def add_reaction(self, channel: str, timestamp: str, emoji: str) -> bool:
        """
        메시지에 리액션 추가
        
        Args:
            channel: 채널 ID
            timestamp: 메시지 타임스탬프
            emoji: 이모지 이름 (콜론 제외)
        
        Returns:
            성공 여부
        """
        try:
            response = self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=emoji
            )
            return response.get("ok", False)
        
        except SlackApiError as e:
            logger.error(f"리액션 추가 실패: {e.response['error']}")
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        사용자 정보 조회
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            사용자 정보 딕셔너리
        """
        try:
            response = self.client.users_info(user=user_id)
            if response.get("ok"):
                return response.get("user")
            return None
        
        except SlackApiError as e:
            logger.error(f"사용자 조회 실패: {e.response['error']}")
            return None
    
    def send_ephemeral(
        self,
        channel: str,
        user: str,
        text: str,
        blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        임시 메시지 전송 (특정 사용자만 볼 수 있음)
        
        Args:
            channel: 채널 ID
            user: 사용자 ID
            text: 메시지 텍스트
            blocks: 블록 (선택)
        
        Returns:
            API 응답
        """
        try:
            response = self.client.chat_postEphemeral(
                channel=channel,
                user=user,
                text=text,
                blocks=blocks
            )
            
            if response.get("ok"):
                logger.info(f"임시 메시지 전송 성공: {channel} -> {user}")
            else:
                logger.error(f"임시 메시지 전송 실패: {response.get('error')}")
            
            return response
        
        except SlackApiError as e:
            logger.error(f"Slack API 오류: {e.response['error']}")
            raise


def format_fields(data: Dict[str, str]) -> List[Dict[str, str]]:
    """
    딕셔너리를 Slack 필드 포맷으로 변환
    
    Args:
        data: 변환할 데이터 {"key": "value"}
    
    Returns:
        Slack 필드 리스트
    """
    fields = []
    for key, value in data.items():
        fields.append({
            "type": "mrkdwn",
            "text": f"*{key}:*\n{value}"
        })
    return fields


def format_code_block(code: str, language: str = "") -> str:
    """
    코드 블록 포맷
    
    Args:
        code: 코드 텍스트
        language: 언어 (선택)
    
    Returns:
        Markdown 코드 블록
    """
    return f"```{language}\n{code}\n```"
