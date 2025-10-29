#!/usr/bin/env python3
"""
Slack 대시보드 및 모니터링 알림 테스트 (스모크 테스트 스크립트)

주의: 이 파일명은 test_*.py 패턴이지만, pytest 수집 시 자동 실행되지 않도록
모든 실행 로직은 main() 내부로 옮겼습니다. 직접 실행할 때만 동작합니다.
"""

import os
import sys
import time
from datetime import datetime
import requests


def create_progress_bar(percentage: int) -> str:
    """진행률 바 생성 (0-100)."""
    percentage = max(0, min(100, int(percentage)))
    filled = int(percentage / 10)
    empty = 10 - filled
    return "█" * filled + "░" * empty


def main() -> int:
    """Standalone smoke-test runner for Slack dashboard notifications.

    - 환경 변수 SLACK_BOT_TOKEN, SLACK_ALERT_CHANNEL 필요
    - 성공 시 0, 실패 시 1 반환
    """
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    slack_channel = os.environ.get("SLACK_ALERT_CHANNEL")

    if not slack_token or not slack_channel:
        print("❌ 환경 변수가 설정되지 않았습니다. (SLACK_BOT_TOKEN, SLACK_ALERT_CHANNEL)")
        return 1

    print("=" * 60)
    print("🧪 Slack 대시보드 & 모니터링 테스트")
    print("=" * 60)
    print()
    print(f"📡 Token: {slack_token[:15]}...")
    print(f"📢 Channel: {slack_channel}")
    print()

    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json; charset=utf-8",
    }

    def send_slack_message(blocks, text="Alert") -> bool:
        payload = {
            "channel": slack_channel,
            "text": text,
            "blocks": blocks,
        }
        try:
            resp = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json=payload,
                timeout=15,
            )
            data = resp.json()
            if data.get("ok"):
                print("  ✅ 성공")
                return True
            else:
                print(f"  ❌ 실패: {data.get('error', 'unknown')}")
                return False
        except Exception as e:
            print(f"  ❌ 예외: {e}")
            return False

    test_count = 0
    success_count = 0
    fail_count = 0

    # 대시보드 테스트 (5개)
    print("═══ 대시보드 테스트 (5개) ═══")
    print()

    # 1) 25%
    test_count += 1
    print(f"[{test_count}] 테스트: 대시보드 - 배포 중 (25%)")
    if send_slack_message([
        {"type": "header", "text": {"type": "plain_text", "text": "🚀 ION API 카나리 배포 대시보드"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": "*배포 단계:*\n🔄 배포 중"},
            {"type": "mrkdwn", "text": "*진행률:*\n25%"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*진행률:*\n`{create_progress_bar(25)}` 25%"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*시작 시간:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
        ]},
    ], "배포 대시보드 - 25% 배포 중"):
        success_count += 1
    else:
        fail_count += 1
    print()
    time.sleep(1)

    # 2) 50%
    test_count += 1
    print(f"[{test_count}] 테스트: 대시보드 - 검증 중 (50%)")
    if send_slack_message([
        {"type": "header", "text": {"type": "plain_text", "text": "🚀 ION API 카나리 배포 대시보드"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": "*배포 단계:*\n✔️ 검증 중"},
            {"type": "mrkdwn", "text": "*진행률:*\n50%"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*진행률:*\n`{create_progress_bar(50)}` 50%"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": "*응답 시간:*\n45ms"},
            {"type": "mrkdwn", "text": "*상태 코드:*\n200"},
        ]},
    ], "배포 대시보드 - 50% 검증 중"):
        success_count += 1
    else:
        fail_count += 1
    print()
    time.sleep(1)

    # 3) 75%
    test_count += 1
    print(f"[{test_count}] 테스트: 대시보드 - 모니터링 중 (75%)")
    if send_slack_message([
        {"type": "header", "text": {"type": "plain_text", "text": "🚀 ION API 카나리 배포 대시보드"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": "*배포 단계:*\n👀 모니터링 중"},
            {"type": "mrkdwn", "text": "*진행률:*\n75%"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*진행률:*\n`{create_progress_bar(75)}` 75%"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": "*응답 시간:*\n42ms"},
            {"type": "mrkdwn", "text": "*에러율:*\n0.1%"},
            {"type": "mrkdwn", "text": "*성공률:*\n99.9%"},
            {"type": "mrkdwn", "text": "*활성 사용자:*\n1,234"},
        ]},
    ], "배포 대시보드 - 75% 모니터링 중"):
        success_count += 1
    else:
        fail_count += 1
    print()
    time.sleep(1)

    # 4) 100%
    test_count += 1
    print(f"[{test_count}] 테스트: 대시보드 - 완료 (100%)")
    if send_slack_message([
        {"type": "header", "text": {"type": "plain_text", "text": "🚀 ION API 카나리 배포 대시보드"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": "*배포 단계:*\n✅ 완료"},
            {"type": "mrkdwn", "text": "*진행률:*\n100%"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*진행률:*\n`{create_progress_bar(100)}` 100%"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": "*배포 시간:*\n15분 30초"},
            {"type": "mrkdwn", "text": "*Gateway URL:*\nhttps://ion-gateway.run.app"},
            {"type": "mrkdwn", "text": "*트래픽 분할:*\nLegacy 0% / Canary 100%"},
        ]},
        {"type": "context", "elements": [
            {"type": "mrkdwn", "text": "🎉 배포가 성공적으로 완료되었습니다!"},
        ]},
    ], "배포 대시보드 - 100% 완료"):
        success_count += 1
    else:
        fail_count += 1
    print()
    time.sleep(1)

    # 5) 실패 예시
    test_count += 1
    print(f"[{test_count}] 테스트: 대시보드 - 실패")
    if send_slack_message([
        {"type": "header", "text": {"type": "plain_text", "text": "🚀 ION API 카나리 배포 대시보드"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": "*배포 단계:*\n❌ 실패"},
            {"type": "mrkdwn", "text": "*진행률:*\n50%"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*진행률:*\n`{create_progress_bar(50)}` 50%"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": "*에러:*\n헬스 체크 타임아웃"},
            {"type": "mrkdwn", "text": "*응답 코드:*\n0"},
        ]},
        {"type": "context", "elements": [
            {"type": "mrkdwn", "text": "⚠️ 즉시 확인이 필요합니다!"},
        ]},
    ], "배포 대시보드 - 실패"):
        success_count += 1
    else:
        fail_count += 1
    print()
    time.sleep(1)

    # 모니터링 알림 테스트 (4개)
    print("═══ 모니터링 알림 테스트 (4개) ═══")
    print()
    severities = [
        ("INFO", "ℹ️", "#36a64f", "시스템 정상", "모든 서비스가 정상 작동 중입니다."),
        ("WARNING", "⚠️", "#ff9800", "레이턴시 증가 감지", "P95 레이턴시가 10% 증가했습니다. 모니터링을 계속합니다."),
        ("ERROR", "🔴", "#f44336", "에러율 임계값 초과", "에러율이 0.5%를 초과했습니다 (현재: 0.8%). 롤백을 고려하세요."),
        ("CRITICAL", "🚨", "#b71c1c", "서비스 다운 감지", "Canary 서비스가 응답하지 않습니다. 즉시 확인 필요!"),
    ]

    for severity, emoji, color, title, message in severities:
        test_count += 1
        print(f"[{test_count}] 테스트: 모니터링 알림 - {severity}")
        if send_slack_message([
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {title}"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*심각도:*\n{severity}"},
                {"type": "mrkdwn", "text": f"*시간:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
            ]},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*메시지:*\n{message}"}},
        ], f"{severity}: {title}"):
            success_count += 1
        else:
            fail_count += 1
        print()
        time.sleep(1)

    # 결과 요약
    print("=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print()
    print(f"총 테스트: {test_count}")
    print(f"✅ 성공: {success_count}")
    if fail_count > 0:
        print(f"❌ 실패: {fail_count}")
    print()

    if fail_count == 0:
        print("✅ 모든 대시보드 및 모니터링 알림 테스트가 성공했습니다!")
        print()
        print(f"Slack 채널 ({slack_channel})에서 9개의 추가 메시지를 확인하세요:")
        print("  - 대시보드 5개 (25%, 50%, 75%, 100%, 실패)")
        print("  - 모니터링 4개 (INFO, WARNING, ERROR, CRITICAL)")
        print()
        return 0
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
