import os
import json
import time
import logging
from typing import List, Optional, Dict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pathlib import Path

# Add project root to path for imports
import sys
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.slack_event_queue import SlackEventQueue

logger = logging.getLogger("SlackGateway")

class SlackGateway:
    def __init__(self):
        self.bot_token = os.environ.get("SLACK_BOT_TOKEN")
        self.channel_id = os.environ.get("SLACK_ALERT_CHANNEL")
        
        # Fallback to manual environment if needed (for user's environment)
        if not self.bot_token:
            # Attempt to get from common location or environment variables
            import subprocess
            try:
                self.bot_token = subprocess.check_output(
                    ['powershell', '-Command', '[Environment]::GetEnvironmentVariable("SLACK_BOT_TOKEN", "User")'],
                    text=True
                ).strip()
                self.channel_id = subprocess.check_output(
                    ['powershell', '-Command', '[Environment]::GetEnvironmentVariable("SLACK_ALERT_CHANNEL", "User")'],
                    text=True
                ).strip()
            except:
                pass

        if not self.bot_token:
            logger.error("SLACK_BOT_TOKEN not found in environment")
            self.client = None
        else:
            self.client = WebClient(token=self.bot_token)
            
        self.queue = SlackEventQueue()

    def send_question(self, text: str, choices: List[str]) -> Optional[str]:
        """
        인간(Tuner)에게 선택형 질문 전송
        """
        if not self.client:
            logger.warning("Slack client not initialized. Cannot send question.")
            return None

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📍 *AGI Boundary Detection*\n{text}"
                }
            },
            {
                "type": "actions",
                "block_id": "tuner_decision",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": choice},
                        "value": choice,
                        "action_id": f"btn_{i}"
                    } for i, choice in enumerate(choices)
                ]
            }
        ]

        try:
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=text,
                blocks=blocks
            )
            return response["ts"]
        except SlackApiError as e:
            logger.error(f"Failed to send Slack message: {e.response['error']}")
            return None

    async def wait_for_response(self, question_ts: str, timeout: int = 300) -> Optional[str]:
        """
        슬랙 대기열을 폴링하여 인간의 응답(한 단어 또는 버튼 선택)을 대기
        """
        import asyncio
        start_time = time.time()
        logger.info(f"Waiting for response to question {question_ts} (timeout: {timeout}s)")
        
        while time.time() - start_time < timeout:
            pending = self.queue.get_pending_events()
            for event in pending:
                event_ts = event.get("ts")
                event_text = event.get("text", "").strip()
                thread_ts = event.get("thread_ts")
                
                # 버튼 클릭 응답 처리 (Bolt/Listener가 action_id 등을 텍스트로 넣어주거나, 직접 입력한 경우)
                if float(event_ts) > float(question_ts):
                    # 만약 thread_ts가 있다면 현재 질문의 ts와 맞는지 확인
                    if thread_ts and thread_ts != question_ts:
                        continue
                    
                    logger.info(f"Received human tuner response: {event_text}")
                    self.queue.mark_processed(event.get("id"), "success")
                    return event_text
            
            await asyncio.sleep(2)
            
        logger.warning(f"Timeout waiting for Slack response ({timeout}s)")
        return None

# 전역 게이트웨이 인스턴스
_gateway = None
def get_slack_gateway() -> SlackGateway:
    global _gateway
    if _gateway is None:
        _gateway = SlackGateway()
    return _gateway
