#!/usr/bin/env python3
"""
Slack 알림 시스템 통합 테스트
PowerShell 인코딩 문제를 우회하여 직접 Python으로 테스트
"""

import os
#!/usr/bin/env python3
"""
Slack 알림 시스템 통합 테스트 (직접 실행 전용)

주의: pytest 수집 시 실행되지 않도록 모든 실행 로직은 main() 내부로 옮겼습니다.
"""

import os
import sys
import time
from datetime import datetime
import requests


def main() -> int:
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    slack_channel = os.environ.get("SLACK_ALERT_CHANNEL")

    if not slack_token:
        print("❌ SLACK_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
        return 1

    if not slack_channel:
        print("❌ SLACK_ALERT_CHANNEL 환경 변수가 설정되지 않았습니다.")
        return 1

    print("=" * 60)
    print("🧪 Slack 알림 시스템 통합 테스트")
    print("=" * 60)
    print()
    print(f"📡 Token: {slack_token[:15]}...")
    print(f"📢 Channel: {slack_channel}")
    print()

    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json; charset=utf-8",
    }

    test_count = 0
    success_count = 0
    fail_count = 0

    def send_slack_message(blocks, text="Deployment Alert"):
        payload = {
            "channel": slack_channel,
            "text": text,
            "blocks": blocks,
        }
        try:
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json=payload,
                timeout=15,
            )
            result = response.json()
            return result.get("ok", False), result.get("error", "Unknown error")
        except Exception as e:
            return False, str(e)

    def test_notification(name, blocks, text="Test"):
        nonlocal test_count, success_count, fail_count
        test_count += 1
        print(f"[{test_count}] 테스트: {name}")
        try:
            success, error = send_slack_message(blocks, text)
            if success:
                success_count += 1
                print("  ✅ 성공")
            else:
                fail_count += 1
                print(f"  ❌ 실패: {error}")
        except Exception as e:
            fail_count += 1
            print(f"  ❌ 예외: {e}")
        print()
        time.sleep(1)

    # 1. 배포 시작 알림
    print("═══ 배포 알림 테스트 ═══")
    print()
    test_notification(
        "배포 시작 알림 (5%)",
        [
            {"type": "header", "text": {"type": "plain_text", "text": "🚀 카나리 배포 시작"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": "*배포 비율:*\n5%"},
                {"type": "mrkdwn", "text": "*버전:*\ntest-v1.0.0"},
                {"type": "mrkdwn", "text": "*시작 시간:*\n" + datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            ]},
        ],
        "카나리 5% 배포를 시작합니다...",
    )

    # 2. 배포 진행 알림 - Deploying
    test_notification(
        "배포 진행 알림 (deploying)",
        [
            {"type": "header", "text": {"type": "plain_text", "text": "🔄 배포 진행 중"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": "*진행률:*\n25%"},
                {"type": "mrkdwn", "text": "*단계:*\nDeploying"},
                {"type": "mrkdwn", "text": "*상세:*\nDocker 이미지 빌드 중..."},
            ]},
        ],
        "카나리 25% 배포 진행 중...",
    )

    # 3. 배포 진행 알림 - Validating
    test_notification(
        "배포 진행 알림 (validating)",
        [
            {"type": "header", "text": {"type": "plain_text", "text": "✔️ 검증 중"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": "*진행률:*\n50%"},
                {"type": "mrkdwn", "text": "*단계:*\nValidating"},
                {"type": "mrkdwn", "text": "*상세:*\n헬스 체크 진행 중..."},
            ]},
        ],
        "카나리 50% 검증 중...",
    )

    # 4. 배포 진행 알림 - Monitoring
    test_notification(
        "배포 진행 알림 (monitoring)",
        [
            {"type": "header", "text": {"type": "plain_text", "text": "👀 모니터링 중"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": "*진행률:*\n75%"},
                {"type": "mrkdwn", "text": "*단계:*\nMonitoring"},
                {"type": "mrkdwn", "text": "*상세:*\n트래픽 모니터링 중..."},
            ]},
        ],
        "카나리 75% 모니터링 중...",
    )

    # 5. 배포 완료 알림
    test_notification(
        "배포 완료 알림",
        [
            {"type": "header", "text": {"type": "plain_text", "text": "✅ 배포 완료"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": "*배포 비율:*\n100%"},
                {"type": "mrkdwn", "text": "*소요 시간:*\n15분 30초"},
                {"type": "mrkdwn", "text": "*완료 시간:*\n" + datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            ]},
            {"type": "context", "elements": [
                {"type": "mrkdwn", "text": "🎉 배포가 성공적으로 완료되었습니다!"},
            ]},
        ],
        "카나리 100% 배포 완료!",
    )

    # 6. 배포 실패 알림
    test_notification(
        "배포 실패 알림",
        [
            {"type": "header", "text": {"type": "plain_text", "text": "❌ 배포 실패"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": "*배포 비율:*\n50%"},
                {"type": "mrkdwn", "text": "*실패 시간:*\n" + datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            ]},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*오류 메시지:*\\n```\\n헬스 체크 실패 - 타임아웃 (30초)\\n```"}},
            {"type": "context", "elements": [
                {"type": "mrkdwn", "text": "⚠️ 즉시 확인이 필요합니다!"},
            ]},
        ],
        "카나리 50% 배포 실패!",
    )

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
        print("✅ 모든 배포 알림 테스트가 성공했습니다!")
        print()
        print(f"이제 Slack 채널 ({slack_channel})에서 6개의 테스트 메시지를 확인하세요.")
        print()
        return 0
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
