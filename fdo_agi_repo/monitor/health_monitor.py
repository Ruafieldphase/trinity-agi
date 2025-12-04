#!/usr/bin/env python3
"""
AGI Health Monitor
헬스 상태를 주기적으로 체크하고 Slack 알림
"""

import time
import sys
from pathlib import Path
from datetime import datetime
import argparse

# 현재 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent))

from metrics_collector import MetricsCollector
from slack_notifier import SlackNotifier


class HealthMonitor:
    """헬스 상태 자동 모니터링"""

    def __init__(self, check_interval: int = 60, notify_on_recovery: bool = True):
        """
        Args:
            check_interval: 체크 간격 (초)
            notify_on_recovery: 복구 시 알림 여부
        """
        self.collector = MetricsCollector()
        self.notifier = SlackNotifier()
        self.check_interval = check_interval
        self.notify_on_recovery = notify_on_recovery

        # 상태 추적
        self.last_status = None  # True=healthy, False=unhealthy, None=unknown
        self.consecutive_failures = 0
        self.consecutive_successes = 0

    def check_and_notify(self) -> bool:
        """
        헬스 체크 및 필요 시 알림

        Returns:
            현재 헬스 상태 (True=healthy)
        """
        try:
            health = self.collector.get_health_status()
            current_status = health.get('healthy', False)

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Health Check: "
                  f"{'✅ HEALTHY' if current_status else '❌ UNHEALTHY'}")

            # 상태 변화 감지
            if self.last_status is not None and current_status != self.last_status:
                if current_status:
                    # 실패 → 성공 (복구)
                    print(f"  → Status changed: UNHEALTHY → HEALTHY")
                    if self.notify_on_recovery:
                        self.notifier.send_recovery_alert(health)
                else:
                    # 성공 → 실패
                    print(f"  → Status changed: HEALTHY → UNHEALTHY")
                    self.notifier.send_health_alert(health)

            # 첫 실행 시 실패 상태면 알림
            elif self.last_status is None and not current_status:
                print(f"  → Initial status: UNHEALTHY (sending alert)")
                self.notifier.send_health_alert(health)

            # 상태 업데이트
            self.last_status = current_status

            # 연속 실패/성공 카운트
            if current_status:
                self.consecutive_failures = 0
                self.consecutive_successes += 1
            else:
                self.consecutive_successes = 0
                self.consecutive_failures += 1

            # 연속 실패 경고 (3회 이상)
            if self.consecutive_failures >= 3:
                print(f"  ⚠️  Consecutive failures: {self.consecutive_failures}")

            return current_status

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error during health check: {e}")
            return False

    def run(self, duration: int = None):
        """
        모니터링 루프 실행

        Args:
            duration: 실행 시간 (초, None=무한)
        """
        print("=" * 60)
        print("🏥 AGI Health Monitor Started")
        print("=" * 60)
        print(f"Check interval: {self.check_interval}s")
        print(f"Notify on recovery: {self.notify_on_recovery}")
        if duration:
            print(f"Duration: {duration}s ({duration/60:.1f} minutes)")
        else:
            print(f"Duration: ♾️  Infinite (Ctrl+C to stop)")
        print("=" * 60)
        print()

        start_time = time.time()
        iteration = 0

        try:
            while True:
                iteration += 1
                print(f"\n[Iteration {iteration}]")

                # 헬스 체크
                self.check_and_notify()

                # 시간 제한 확인
                if duration and (time.time() - start_time) >= duration:
                    print(f"\n✅ Monitoring completed ({duration}s)")
                    break

                # 대기
                print(f"  → Next check in {self.check_interval}s...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped by user (Ctrl+C)")
        except Exception as e:
            print(f"\n\n❌ Monitoring error: {e}")
            raise

        # 최종 통계
        total_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("📊 Monitoring Statistics")
        print("=" * 60)
        print(f"Total time: {total_time:.0f}s ({total_time/60:.1f} minutes)")
        print(f"Total checks: {iteration}")
        print(f"Final status: {'✅ HEALTHY' if self.last_status else '❌ UNHEALTHY'}")
        print("=" * 60)


def main():
    """CLI"""
    parser = argparse.ArgumentParser(description='AGI Health Monitor')
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--duration', '-d',
        type=int,
        default=None,
        help='Total duration in seconds (default: infinite)'
    )
    parser.add_argument(
        '--no-recovery-notify',
        action='store_true',
        help='Disable recovery notifications'
    )

    args = parser.parse_args()

    monitor = HealthMonitor(
        check_interval=args.interval,
        notify_on_recovery=not args.no_recovery_notify
    )

    monitor.run(duration=args.duration)


if __name__ == '__main__':
    main()
