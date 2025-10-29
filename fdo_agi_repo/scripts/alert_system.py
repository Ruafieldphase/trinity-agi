#!/usr/bin/env python3
"""
헬스 체크 알림 시스템
임계치 위반 시 Slack/Discord/File 알림 발송
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import subprocess

# monitor 모듈 import를 위한 경로 추가
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from monitor.metrics_collector import MetricsCollector


class AlertSystem:
    """알림 시스템"""

    def __init__(self, include_default_excludes: bool = True, extra_exclude_prefixes: Optional[List[str]] = None):
        self.collector = MetricsCollector(
            include_default_excludes=include_default_excludes,
            exclude_prefixes=extra_exclude_prefixes,
        )
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        self.alert_file = repo_root / "outputs" / "alerts.jsonl"
        
        # 알림 파일 디렉토리 생성
        self.alert_file.parent.mkdir(parents=True, exist_ok=True)

    def check_and_alert(self) -> bool:
        """헬스 체크 후 문제 발견 시 알림 발송"""
        health = self.collector.get_health_status()
        
        if health['healthy']:
            print("✅ 전체 상태: HEALTHY - 알림 불필요")
            return True
        
        # 문제 상세 정보 수집
        issues = []
        checks = health['checks']
        policy = health.get('policy', {})
        notes = policy.get('notes', {})
        samples = policy.get('samples', {})
        
        # Confidence 체크 (샘플 부족 시 제외)
        if not checks['confidence_ok']:
            if 'confidence' not in notes:  # insufficient_samples가 아닌 경우만 알림
                issues.append(f"❌ Confidence: {health['current_values']['confidence']:.3f} < {health['thresholds']['min_confidence']} (samples: {samples.get('confidence', 0)})")
        
        # Quality 체크 (샘플 부족 시 제외)
        if not checks['quality_ok']:
            if 'quality' not in notes:  # insufficient_samples가 아닌 경우만 알림
                issues.append(f"❌ Quality: {health['current_values']['quality']:.3f} < {health['thresholds']['min_quality']} (samples: {samples.get('quality', 0)})")

        
        if not checks['second_pass_ok']:
            issues.append(f"❌ 2nd Pass: {health['current_values']['second_pass_rate']:.3f} > {health['thresholds']['max_second_pass_rate']}")
        
        if not checks['lumen_ok']:
            lumen = health['external_services']['lumen']
            issues.append(f"❌ Lumen Gateway: {lumen.get('error', 'unreachable')}")
        
        if not checks.get('proxy_ok', True):
            issues.append(f"⚠️ Local Proxy: not listening (선택적)")
        
        if not checks.get('system_ok', True):
            system = health['external_services']['system']
            if 'warnings' in system:
                if system['warnings']['cpu']:
                    issues.append(f"⚠️ CPU: {system['cpu_percent']}%")
                if system['warnings']['memory']:
                    issues.append(f"⚠️ Memory: {system['memory_percent']}%")
                if system['warnings']['disk']:
                    issues.append(f"⚠️ Disk: {system['disk_percent']}%")
        
        # 알림 메시지 생성
        alert_message = self._format_alert_message(issues, health)
        
        # 알림 발송
        self._send_alerts(alert_message, health)
        
        # 로그 기록
        self._log_alert(issues, health)
        
        print(f"🚨 알림 발송 완료: {len(issues)}개 이슈 발견")
        return False

    def _format_alert_message(self, issues: list, health: Dict[str, Any]) -> str:
        """알림 메시지 포맷"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        policy = health.get('policy', {})
        samples = policy.get('samples', {})
        recent_hours = policy.get('recent_hours', 1.0)
        filters = health.get('filters', {})
        filter_notes: List[str] = []
        exclude_prefixes = filters.get('exclude_prefixes') if isinstance(filters, dict) else None
        if exclude_prefixes:
            joined = ', '.join(exclude_prefixes)
            filter_notes.append(f"- 제외 접두사: {joined}")
        if isinstance(filters, dict) and not filters.get('default_excludes_applied', False):
            filter_notes.append('- ⚠ 기본 제외 미적용 (raw metrics)')
        
        message = f"""
🚨 **AGI 헬스 체크 경고** 🚨
시간: {timestamp}
분석 윈도우: 최근 {recent_hours}시간

**발견된 문제:**
{chr(10).join(issues)}

**현재 메트릭:**
• Confidence: {health['current_values']['confidence']:.3f} (samples: {samples.get('confidence', 0)})
• Quality: {health['current_values']['quality']:.3f} (samples: {samples.get('quality', 0)})
• 2nd Pass Rate: {health['current_values']['second_pass_rate']:.3f}

**조치 필요:**
1. 대시보드 확인: `ops_dashboard.py`
2. Ledger 분석: `summarize_ledger.py --last-hours 1` (기본 제외 적용). 원본 검토 시 `--no-default-excludes` 추가
3. 필요시 시스템 재시작
"""
        if filter_notes:
            message += "\n**필터 정보:**\n" + "\n".join(filter_notes) + "\n"
        return message

    def _send_alerts(self, message: str, health: Dict[str, Any]):
        """알림 발송 (여러 채널)"""
        # Slack 알림
        if self.slack_webhook:
            self._send_slack(message)
        
        # Discord 알림
        if self.discord_webhook:
            self._send_discord(message)
        
        # 파일 알림 (항상 기록)
        self._send_file(message)
        
        # 콘솔 출력
        print(message)

    def _send_slack(self, message: str):
        """Slack 웹훅 전송"""
        try:
            import requests
            payload = {
                "text": message,
                "username": "AGI Health Monitor",
                "icon_emoji": ":warning:"
            }
            response = requests.post(
                self.slack_webhook,
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Slack 알림 발송 성공")
            else:
                print(f"⚠️ Slack 알림 실패: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Slack 알림 오류: {e}")

    def _send_discord(self, message: str):
        """Discord 웹훅 전송"""
        try:
            import requests
            payload = {
                "content": message,
                "username": "AGI Health Monitor"
            }
            response = requests.post(
                self.discord_webhook,
                json=payload,
                timeout=10
            )
            if response.status_code in (200, 204):
                print("✅ Discord 알림 발송 성공")
            else:
                print(f"⚠️ Discord 알림 실패: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Discord 알림 오류: {e}")

    def _send_file(self, message: str):
        """파일에 알림 기록"""
        try:
            alert_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': message,
                'type': 'health_alert'
            }
            with open(self.alert_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(alert_entry, ensure_ascii=False) + '\n')
            print(f"✅ 알림 파일 기록: {self.alert_file}")
        except Exception as e:
            print(f"⚠️ 파일 기록 오류: {e}")

    def _log_alert(self, issues: list, health: Dict[str, Any]):
        """알림 로그 JSONL 형식으로 기록"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'healthy': health['healthy'],
            'issues': issues,
            'metrics': health['current_values'],
            'thresholds': health['thresholds']
        }
        
        log_file = repo_root / "outputs" / "health_alerts.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


def main():
    """CLI 엔트리 포인트"""
    import argparse
    import io

    # UTF-8 출력 강제 설정 (Windows cp949 인코딩 문제 해결)
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description='AGI 헬스 체크 & 알림 시스템')
    parser.add_argument('--no-alert', action='store_true', help='알림 발송 스킵 (체크만)')
    parser.add_argument('--no-default-excludes', action='store_true', help='요약 기본 제외 필터 비활성화')
    parser.add_argument('--exclude-prefix', action='append', default=[], help='추가로 제외할 task_id 접두사 (여러 번 사용 가능)')
    args = parser.parse_args()

    alert_system = AlertSystem(
        include_default_excludes=not args.no_default_excludes,
        extra_exclude_prefixes=args.exclude_prefix or None,
    )
    
    if args.no_alert:
        health = alert_system.collector.get_health_status()
        print(f"헬스 상태: {'HEALTHY' if health['healthy'] else 'UNHEALTHY'}")
        print(json.dumps(health, indent=2, ensure_ascii=False))
    else:
        is_healthy = alert_system.check_and_alert()
        sys.exit(0 if is_healthy else 1)


if __name__ == '__main__':
    main()
