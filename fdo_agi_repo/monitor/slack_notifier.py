#!/usr/bin/env python3
"""
Slack Notifier for AGI Dashboard
헬스 체크 실패 시 Slack으로 자동 알림
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import urllib.request
import urllib.error


class SlackNotifier:
    """Slack 웹훅을 통한 알림 전송"""

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Args:
            webhook_url: Slack 웹훅 URL (없으면 환경변수에서 읽음)
        """
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')

        if not self.webhook_url:
            print("Warning: SLACK_WEBHOOK_URL not set. Notifications will be skipped.")

    def send_message(self, text: str, blocks: Optional[list] = None) -> bool:
        """
        Slack 메시지 전송

        Args:
            text: 메시지 텍스트 (fallback)
            blocks: Slack Blocks API 형식

        Returns:
            성공 여부
        """
        if not self.webhook_url:
            print(f"[Slack] Skipped (no webhook): {text}")
            return False

        payload = {
            "text": text
        }

        if blocks:
            payload["blocks"] = blocks

        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    print(f"[Slack] Message sent successfully")
                    return True
                else:
                    print(f"[Slack] Failed with status {response.status}")
                    return False

        except urllib.error.URLError as e:
            print(f"[Slack] Error sending message: {e}")
            return False
        except Exception as e:
            print(f"[Slack] Unexpected error: {e}")
            return False

    def send_health_alert(self, health_status: Dict[str, Any]) -> bool:
        """
        헬스 체크 실패 알림

        Args:
            health_status: get_health_status() 결과

        Returns:
            성공 여부
        """
        if health_status.get('healthy'):
            # 정상이면 알림 안 보냄
            return True

        checks = health_status.get('checks', {})
        current = health_status.get('current_values', {})
        thresholds = health_status.get('thresholds', {})

        # 실패한 체크 항목 찾기
        failed_checks = [k for k, v in checks.items() if not v]

        # Slack Blocks 구성
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 AGI 시스템 헬스 체크 실패",
                    "emoji": true
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*시간*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n*상태*: :x: UNHEALTHY"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*실패한 체크 항목:*"
                }
            }
        ]

        # 실패 항목별 상세 정보
        for check in failed_checks:
            if check == 'confidence_ok':
                value = current.get('confidence', 0)
                threshold = thresholds.get('min_confidence', 0.6)
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":x: *Confidence*: {value:.3f} (목표: ≥{threshold})"
                    }
                })
            elif check == 'quality_ok':
                value = current.get('quality', 0)
                threshold = thresholds.get('min_quality', 0.65)
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":x: *Quality*: {value:.3f} (목표: ≥{threshold})"
                    }
                })
            elif check == 'second_pass_ok':
                value = current.get('second_pass_rate', 0)
                threshold = thresholds.get('max_second_pass_rate', 2.0)
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":x: *Second Pass Rate*: {value:.3f} (목표: ≤{threshold})"
                    }
                })

        # 액션 버튼
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "대시보드 열기",
                            "emoji": true
                        },
                        "url": "http://localhost:5000",
                        "action_id": "open_dashboard"
                    }
                ]
            }
        ])

        fallback_text = f"🚨 AGI 헬스 체크 실패: {', '.join(failed_checks)}"
        return self.send_message(fallback_text, blocks)

    def send_recovery_alert(self, health_status: Dict[str, Any]) -> bool:
        """
        헬스 체크 복구 알림

        Args:
            health_status: get_health_status() 결과

        Returns:
            성공 여부
        """
        if not health_status.get('healthy'):
            # 여전히 실패 상태면 알림 안 보냄
            return True

        current = health_status.get('current_values', {})

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ AGI 시스템 헬스 체크 복구",
                    "emoji": true
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*시간*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n*상태*: :white_check_mark: HEALTHY"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Confidence:*\n{current.get('confidence', 0):.3f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Quality:*\n{current.get('quality', 0):.3f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Second Pass Rate:*\n{current.get('second_pass_rate', 0):.3f}"
                    }
                ]
            }
        ]

        fallback_text = "✅ AGI 시스템 헬스 체크 복구됨"
        return self.send_message(fallback_text, blocks)

    def send_metrics_summary(self, metrics: Dict[str, Any]) -> bool:
        """
        일일 메트릭 요약 알림

        Args:
            metrics: get_realtime_metrics() 결과

        Returns:
            성공 여부
        """
        m = metrics.get('metrics', {})
        persona_perf = metrics.get('persona_performance', {})

        # 페르소나 성능 텍스트 생성
        persona_text = []
        for persona, stats in persona_perf.items():
            persona_text.append(
                f"• *{persona}*: {stats['success_rate']*100:.1f}% 성공률, "
                f"{stats['avg_duration']:.1f}s 평균응답"
            )

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 AGI 일일 메트릭 요약",
                    "emoji": true
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*기간*: 최근 24시간\n*생성 시간*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*평균 Confidence:*\n{m.get('avg_confidence', 0):.3f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*평균 Quality:*\n{m.get('avg_quality', 0):.3f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*총 작업:*\n{m.get('total_tasks', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*자기교정:*\n{m.get('second_pass_count', 0)}회"
                    }
                ]
            }
        ]

        if persona_text:
            blocks.extend([
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*페르소나 성능:*\n" + "\n".join(persona_text)
                    }
                }
            ])

        fallback_text = f"📊 AGI 일일 요약: Confidence={m.get('avg_confidence', 0):.3f}, Quality={m.get('avg_quality', 0):.3f}"
        return self.send_message(fallback_text, blocks)


def main():
    """테스트"""
    notifier = SlackNotifier()

    # 테스트 메시지
    print("=== Slack Notifier Test ===\n")

    test_message = "🧪 AGI Slack Notifier 테스트"
    success = notifier.send_message(test_message)

    if success:
        print("✅ 테스트 메시지 전송 성공")
    else:
        print("❌ 테스트 메시지 전송 실패")
        print("💡 SLACK_WEBHOOK_URL 환경변수를 설정하세요")


if __name__ == '__main__':
    main()
