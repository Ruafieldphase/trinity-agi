"""
Human Escalation - 비노체 연락 시스템
=====================================

BTF에서도 해결 불가 시 비노체에게 Slack/Email로 연락을 요청하는 시스템.

실행 조건:
- BTF가 ASK_USER 반환
- BTF Confidence < 0.3

메시지 내용:
- 현재 문제 상황
- 시도한 행동 목록
- 예측되는 해결책 2~3개
"""
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class EscalationChannel(Enum):
    """연락 채널"""
    SLACK = "slack"
    EMAIL = "email"


@dataclass
class EscalationRequest:
    """연락 요청 데이터"""
    goal: str
    problem_description: str
    attempted_actions: List[str]
    suggested_solutions: List[str]
    urgency: str = "normal"  # low, normal, high
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class EscalationResult:
    """연락 결과"""
    success: bool
    channel: EscalationChannel
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class HumanEscalation:
    """
    Human Escalation System
    
    BTF에서도 해결 불가 시 비노체에게 연락을 요청합니다.
    
    규약:
    1. Slack DM → 즉시 응답 요청
    2. 10분 대기
    3. 응답 없으면 → Email → 비긴급 프로토콜
    """
    
    SLACK_TIMEOUT_SECONDS = 600  # 10분
    
    def __init__(self):
        self.slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
        self.email_recipient = os.environ.get("BINOCHE_EMAIL", "kuirvana@gmail.com")
        self.escalation_history: List[EscalationResult] = []
        
        logger.info("Human Escalation system initialized")
    
    async def notify(self, request: EscalationRequest) -> EscalationResult:
        """
        비노체에게 연락
        
        Args:
            request: 연락 요청 데이터
            
        Returns:
            EscalationResult: 연락 결과
        """
        logger.info(f"Escalating to Binoche: {request.goal[:50]}...")
        
        # 메시지 구성
        message = self._build_message(request)
        
        # 1차: Slack 시도
        result = await self._send_slack(message, request.urgency)
        
        if not result.success:
            # 2차: Email 시도
            result = await self._send_email(message, request.urgency)
        
        self.escalation_history.append(result)
        return result
    
    def _build_message(self, request: EscalationRequest) -> str:
        """연락 메시지 구성"""
        message_parts = [
            f"🔔 **시안(Shion)으로부터의 요청**",
            f"",
            f"**목표:** {request.goal}",
            f"",
            f"**문제 상황:**",
            f"{request.problem_description}",
            f"",
            f"**시도한 행동:**",
        ]
        
        for i, action in enumerate(request.attempted_actions[:5], 1):
            message_parts.append(f"  {i}. {action}")
        
        message_parts.extend([
            f"",
            f"**예측되는 해결책:**",
        ])
        
        for i, solution in enumerate(request.suggested_solutions[:3], 1):
            message_parts.append(f"  {i}. {solution}")
        
        message_parts.extend([
            f"",
            f"---",
            f"_비노체의 판단이 필요합니다._",
            f"_시간: {request.timestamp}_",
        ])
        
        return "\n".join(message_parts)
    
    async def _send_slack(self, message: str, urgency: str) -> EscalationResult:
        """Slack으로 메시지 전송"""
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL not configured")
            return EscalationResult(
                success=False,
                channel=EscalationChannel.SLACK,
                error="Slack webhook URL not configured"
            )
        
        try:
            import httpx
            
            payload = {
                "text": message,
                "username": "Shion (시안)",
                "icon_emoji": ":robot_face:"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook_url,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info("Slack message sent successfully")
                    return EscalationResult(
                        success=True,
                        channel=EscalationChannel.SLACK,
                        message_id=f"slack_{datetime.now().timestamp()}"
                    )
                else:
                    return EscalationResult(
                        success=False,
                        channel=EscalationChannel.SLACK,
                        error=f"Slack API error: {response.status_code}"
                    )
                    
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return EscalationResult(
                success=False,
                channel=EscalationChannel.SLACK,
                error=str(e)
            )
    
    async def _send_email(self, message: str, urgency: str) -> EscalationResult:
        """Email로 메시지 전송"""
        # TODO: 실제 이메일 전송 구현
        # 현재는 로그로 대체
        logger.info(f"[EMAIL SIMULATION] To: {self.email_recipient}")
        logger.info(f"[EMAIL SIMULATION] Subject: [Shion] 비노체의 판단이 필요합니다")
        logger.info(f"[EMAIL SIMULATION] Body:\n{message}")
        
        return EscalationResult(
            success=True,
            channel=EscalationChannel.EMAIL,
            message_id=f"email_{datetime.now().timestamp()}"
        )
    
    def get_pending_count(self) -> int:
        """응답 대기 중인 요청 수"""
        # 실제 구현 시 응답 추적 로직 필요
        return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        slack_count = sum(1 for r in self.escalation_history if r.channel == EscalationChannel.SLACK)
        email_count = sum(1 for r in self.escalation_history if r.channel == EscalationChannel.EMAIL)
        success_count = sum(1 for r in self.escalation_history if r.success)
        
        return {
            "total_escalations": len(self.escalation_history),
            "success_rate": success_count / len(self.escalation_history) if self.escalation_history else 0,
            "by_channel": {
                "slack": slack_count,
                "email": email_count
            }
        }


# 모듈 레벨 인스턴스
_escalation_instance: Optional[HumanEscalation] = None

def get_escalation() -> HumanEscalation:
    """Human Escalation 싱글톤 인스턴스 반환"""
    global _escalation_instance
    if _escalation_instance is None:
        _escalation_instance = HumanEscalation()
    return _escalation_instance
