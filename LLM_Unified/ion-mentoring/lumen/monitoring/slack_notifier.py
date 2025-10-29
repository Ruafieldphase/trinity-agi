#!/usr/bin/env python3
"""
Slack Notifier - Cost Rhythm 알림

Cost Rhythm Loop 상태 변화를 Slack으로 알림하고,
승인 요청 시 HMAC 서명 링크를 전송합니다.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  requests 미설치: pip install requests")

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Slack 설정
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#ion-cost-alerts")

# Base URL (승인 링크용)
APPROVAL_BASE_URL = os.getenv("APPROVAL_BASE_URL", "http://localhost:8080")


@dataclass
class SlackMessage:
    """Slack 메시지"""
    text: str
    blocks: Optional[List[Dict]] = None
    channel: Optional[str] = None


class SlackNotifier:
    """
    Slack Notifier for Cost Rhythm Loop
    
    Cost rhythm 상태 변화 및 승인 요청을 Slack으로 전송합니다.
    """
    
    def __init__(self, webhook_url: str = SLACK_WEBHOOK_URL, channel: str = SLACK_CHANNEL):
        """
        Args:
            webhook_url: Slack Webhook URL
            channel: Slack 채널명
        """
        self.webhook_url = webhook_url
        self.channel = channel
        
        if not webhook_url:
            print("⚠️  SLACK_WEBHOOK_URL 환경변수 미설정")
    
    def send_message(self, message: SlackMessage) -> bool:
        """
        Slack 메시지 전송
        
        Args:
            message: SlackMessage 객체
            
        Returns:
            전송 성공 여부
        """
        if not self.webhook_url or not REQUESTS_AVAILABLE:
            print(f"📤 [DRY-RUN] Slack: {message.text}")
            return False
        
        payload = {
            "text": message.text,
            "channel": message.channel or self.channel,
        }
        
        if message.blocks:
            payload["blocks"] = message.blocks
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            
            if response.status_code == 200:
                print(f"✅ Slack 전송 성공: {message.text[:50]}...")
                return True
            else:
                print(f"❌ Slack 전송 실패 ({response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Slack 전송 오류: {e}")
            return False
    
    def send_cost_rhythm_alert(
        self,
        rhythm_status: str,
        current_spend: float,
        forecasted_spend: float,
        budget: float,
        coherence: float,
        phase: float,
        entropy: float,
    ) -> bool:
        """
        Cost Rhythm 상태 알림
        
        Args:
            rhythm_status: 리듬 상태 (RESONANT/DISSONANT/CHAOTIC)
            current_spend: 현재 비용
            forecasted_spend: 예측 비용
            budget: 예산
            coherence: 일관성
            phase: 위상
            entropy: 엔트로피
            
        Returns:
            전송 성공 여부
        """
        # 아이콘 선택
        icon_map = {
            "RESONANT": "🟢",
            "DISSONANT": "🟡",
            "CHAOTIC": "🔴",
        }
        icon = icon_map.get(rhythm_status, "⚪")
        
        # 예산 사용률
        budget_usage = (forecasted_spend / budget * 100) if budget > 0 else 0
        
        # 색상 선택
        color_map = {
            "RESONANT": "good",      # 초록
            "DISSONANT": "warning",  # 노랑
            "CHAOTIC": "danger",     # 빨강
        }
        color = color_map.get(rhythm_status, "#808080")
        
        # Slack Blocks 구성
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{icon} Cost Rhythm Alert: {rhythm_status}",
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Current Spend:*\n${current_spend:.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Forecasted:*\n${forecasted_spend:.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Budget:*\n${budget:.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Usage:*\n{budget_usage:.1f}%"
                    },
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Coherence:*\n{coherence:.3f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Phase:*\n{phase:.3f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Entropy:*\n{entropy:.3f}"
                    },
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    }
                ]
            },
        ]
        
        message = SlackMessage(
            text=f"{icon} Cost Rhythm: {rhythm_status} (Budget: {budget_usage:.1f}%)",
            blocks=blocks,
        )
        
        return self.send_message(message)
    
    def send_approval_request(
        self,
        request_id: str,
        action_type: str,
        reason: str,
        details: Dict,
        approve_url: str,
        reject_url: str,
        expires_at: str,
    ) -> bool:
        """
        승인 요청 메시지 전송
        
        Args:
            request_id: 요청 ID
            action_type: 행동 유형 (SCALE_DOWN/ROLLBACK/EMERGENCY_STOP)
            reason: 사유
            details: 상세 정보
            approve_url: 승인 URL
            reject_url: 거부 URL
            expires_at: 만료 시각
            
        Returns:
            전송 성공 여부
        """
        # 아이콘 선택
        icon_map = {
            "SCALE_DOWN": "⚠️",
            "ROLLBACK": "🚨",
            "EMERGENCY_STOP": "❌",
        }
        icon = icon_map.get(action_type, "🔔")
        
        # Slack Blocks 구성
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{icon} Approval Required: {action_type}",
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Request ID:* `{request_id}`\n*Reason:* {reason}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n{value}"
                    }
                    for key, value in list(details.items())[:6]  # 최대 6개 필드
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Approve",
                        },
                        "style": "primary",
                        "url": approve_url,
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ Reject",
                        },
                        "style": "danger",
                        "url": reject_url,
                    },
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏰ Expires at {expires_at} UTC (5 minutes)"
                    }
                ]
            },
        ]
        
        message = SlackMessage(
            text=f"{icon} Approval Required: {action_type} ({request_id})",
            blocks=blocks,
        )
        
        return self.send_message(message)
    
    def send_action_confirmation(
        self,
        request_id: str,
        action_type: str,
        status: str,
        approved_by: Optional[str] = None,
    ) -> bool:
        """
        행동 실행 확인 메시지
        
        Args:
            request_id: 요청 ID
            action_type: 행동 유형
            status: 상태 (APPROVED/REJECTED/EXPIRED/EXECUTED)
            approved_by: 승인자
            
        Returns:
            전송 성공 여부
        """
        # 아이콘 선택
        icon_map = {
            "APPROVED": "✅",
            "REJECTED": "❌",
            "EXPIRED": "⏰",
            "EXECUTED": "🎯",
        }
        icon = icon_map.get(status, "🔔")
        
        text = f"{icon} {action_type} {status}"
        if approved_by:
            text += f" by {approved_by}"
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Request ID:* `{request_id}`\n*Status:* {text}"
                }
            },
        ]
        
        message = SlackMessage(text=text, blocks=blocks)
        
        return self.send_message(message)


def main():
    """테스트 함수"""
    print("=" * 70)
    print("Slack Notifier 테스트")
    print("=" * 70)
    print()
    
    notifier = SlackNotifier()
    
    # 1. Cost Rhythm Alert
    print("1️⃣ Cost Rhythm Alert 전송")
    notifier.send_cost_rhythm_alert(
        rhythm_status="DISSONANT",
        current_spend=25.5,
        forecasted_spend=220.0,
        budget=200.0,
        coherence=0.65,
        phase=0.72,
        entropy=0.58,
    )
    print()
    
    # 2. Approval Request
    print("2️⃣ Approval Request 전송")
    notifier.send_approval_request(
        request_id="scale_down_1729876543",
        action_type="SCALE_DOWN",
        reason="Forecasted spend > budget + dissonant rhythm",
        details={
            "Current Spend": "$25.50",
            "Forecasted": "$220.00",
            "Budget": "$200.00",
            "Coherence": "0.65",
            "Phase": "0.72",
            "Entropy": "0.58",
        },
        approve_url=f"{APPROVAL_BASE_URL}/api/approve?request_id=scale_down_1729876543&token=abc123",
        reject_url=f"{APPROVAL_BASE_URL}/api/reject?request_id=scale_down_1729876543&token=abc123",
        expires_at="2025-10-25T12:35:00",
    )
    print()
    
    # 3. Action Confirmation
    print("3️⃣ Action Confirmation 전송")
    notifier.send_action_confirmation(
        request_id="scale_down_1729876543",
        action_type="SCALE_DOWN",
        status="APPROVED",
        approved_by="admin@example.com",
    )
    print()
    
    print("=" * 70)
    print("✅ Slack Notifier 테스트 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()
