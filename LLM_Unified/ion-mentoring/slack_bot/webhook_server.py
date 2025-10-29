"""
Webhook Server

Slack 이벤트 및 Alertmanager 웹훅 수신
"""

import os
import json
import hmac
import hashlib
import time
from typing import Dict, Any
from flask import Flask, request, jsonify
import logging

from .slack_client import SlackClient
from .slack_commands import CommandHandler
from .slack_notifications import NotificationHandler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Flask 앱 생성
app = Flask(__name__)

# 클라이언트 초기화
slack_client = SlackClient()
command_handler = CommandHandler(slack_client)
notification_handler = NotificationHandler(slack_client)

# 환경 변수
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")


def verify_slack_signature(request_body: bytes, timestamp: str, signature: str) -> bool:
    """
    Slack 요청 서명 검증
    
    Args:
        request_body: 요청 본문
        timestamp: X-Slack-Request-Timestamp 헤더
        signature: X-Slack-Signature 헤더
    
    Returns:
        검증 성공 여부
    """
    # 타임스탬프 검증 (5분 이내)
    try:
        request_time = int(timestamp)
        current_time = int(time.time())
        if abs(current_time - request_time) > 60 * 5:
            logger.warning("요청 타임스탬프가 너무 오래되었습니다")
            return False
    except ValueError:
        logger.error("잘못된 타임스탬프 형식")
        return False
    
    # 서명 생성
    sig_basestring = f"v0:{timestamp}:{request_body.decode('utf-8')}"
    my_signature = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # 서명 비교
    if hmac.compare_digest(my_signature, signature):
        return True
    else:
        logger.warning("서명 검증 실패")
        return False


@app.route("/health", methods=["GET"])
def health():
    """헬스체크 엔드포인트"""
    return jsonify({"status": "ok", "service": "ion-slack-bot"}), 200


@app.route("/slack/events", methods=["POST"])
def slack_events():
    """
    Slack 이벤트 수신
    
    URL Challenge 및 이벤트 처리
    """
    data = request.json
    
    # URL Verification (앱 설정 시 한 번만 발생)
    if data.get("type") == "url_verification":
        logger.info("URL 검증 요청 수신")
        return jsonify({"challenge": data.get("challenge")}), 200
    
    # 이벤트 처리
    event = data.get("event", {})
    event_type = event.get("type")
    
    logger.info(f"이벤트 수신: {event_type}")
    
    # 봇 자신의 메시지는 무시
    if event.get("bot_id"):
        return jsonify({"status": "ignored"}), 200
    
    # 이벤트 타입별 처리
    if event_type == "app_mention":
        handle_app_mention(event)
    elif event_type == "message":
        handle_message(event)
    
    return jsonify({"status": "ok"}), 200


@app.route("/slack/commands", methods=["POST"])
def slack_commands():
    """
    Slash Commands 처리
    """
    # 서명 검증
    if SLACK_SIGNING_SECRET:
        signature = request.headers.get("X-Slack-Signature", "")
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        
        if not verify_slack_signature(request.get_data(), timestamp, signature):
            return jsonify({"error": "Invalid signature"}), 403
    
    # 파라미터 파싱
    command = request.form.get("command", "")
    text = request.form.get("text", "")
    channel_id = request.form.get("channel_id", "")
    user_id = request.form.get("user_id", "")
    
    logger.info(f"명령어 수신: {command} {text} from {user_id}")
    
    # /ion 명령어 처리
    if command == "/ion":
        response = command_handler.handle_command(text, channel_id, user_id)
        return jsonify(response), 200
    
    return jsonify({"text": f"알 수 없는 명령어: {command}"}), 200


@app.route("/slack/interactive", methods=["POST"])
def slack_interactive():
    """
    인터랙티브 컴포넌트 (버튼 클릭 등) 처리
    """
    # 서명 검증
    if SLACK_SIGNING_SECRET:
        signature = request.headers.get("X-Slack-Signature", "")
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        
        if not verify_slack_signature(request.get_data(), timestamp, signature):
            return jsonify({"error": "Invalid signature"}), 403
    
    # 페이로드 파싱
    payload = json.loads(request.form.get("payload", "{}"))
    
    action_type = payload.get("type")
    user = payload.get("user", {})
    actions = payload.get("actions", [])
    
    logger.info(f"인터랙티브 이벤트: {action_type} from {user.get('id')}")
    
    # 버튼 클릭 처리
    if action_type == "block_actions" and actions:
        action = actions[0]
        action_value = action.get("value", "")
        channel_id = payload.get("container", {}).get("channel_id", "")
        
        # 배포 승인/거부
        if action_value.startswith("approve_deploy_"):
            parts = action_value.split("_")
            service = parts[2]
            percentage = int(parts[3])
            
            # 배포 실행
            slack_client.send_message(
                channel=channel_id,
                text=f"✅ 배포 승인됨: `ion-api-{service}` → {percentage}%"
            )
            
            # 백그라운드에서 배포 실행
            command_handler.execute_deploy(service, percentage, channel_id)
        
        elif action_value == "deny_deploy":
            slack_client.send_message(
                channel=channel_id,
                text="❌ 배포 요청이 거부되었습니다."
            )
        
        # 롤백 승인/거부
        elif action_value.startswith("approve_rollback_"):
            service = action_value.split("_")[2]
            
            slack_client.send_message(
                channel=channel_id,
                text=f"🔙 롤백 실행: `ion-api-{service}`"
            )
            
            # TODO: 롤백 스크립트 실행
        
        elif action_value == "deny_rollback":
            slack_client.send_message(
                channel=channel_id,
                text="❌ 롤백 요청이 취소되었습니다."
            )
    
    return jsonify({"response_action": "clear"}), 200


@app.route("/alertmanager", methods=["POST"])
def alertmanager_webhook():
    """
    Alertmanager 웹훅 수신
    """
    try:
        payload = request.json
        logger.info(f"Alertmanager 알림 수신: {len(payload.get('alerts', []))}개")
        
        # 알림 처리
        notification_handler.handle_alertmanager_webhook(payload)
        
        return jsonify({"status": "ok"}), 200
    
    except Exception as e:
        logger.error(f"Alertmanager 웹훅 처리 오류: {e}")
        return jsonify({"error": str(e)}), 500


def handle_app_mention(event: Dict[str, Any]) -> None:
    """
    앱 멘션 처리
    
    Args:
        event: 이벤트 데이터
    """
    channel = event.get("channel")
    user = event.get("user")
    text = event.get("text", "")
    
    # 봇 멘션 제거
    text = text.split(">", 1)[-1].strip()
    
    # 명령어로 처리
    response = command_handler.handle_command(text, channel, user)
    
    if response.get("text"):
        slack_client.send_message(
            channel=channel,
            text=response["text"]
        )


def handle_message(event: Dict[str, Any]) -> None:
    """
    메시지 처리
    
    Args:
        event: 이벤트 데이터
    """
    # 현재는 DM만 처리
    channel_type = event.get("channel_type")
    
    if channel_type == "im":
        channel = event.get("channel")
        user = event.get("user")
        text = event.get("text", "")
        
        # 명령어로 처리
        response = command_handler.handle_command(text, channel, user)
        
        if response.get("text"):
            slack_client.send_message(
                channel=channel,
                text=response["text"]
            )


def run_server(host: str = "0.0.0.0", port: int = 3000, debug: bool = False) -> None:
    """
    서버 실행
    
    Args:
        host: 호스트 주소
        port: 포트 번호
        debug: 디버그 모드
    """
    logger.info(f"Slack Bot 서버 시작: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server(debug=True)
