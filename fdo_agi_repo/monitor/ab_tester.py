#!/usr/bin/env python3
"""
A/B Testing Automation Tool for AGI Performance Optimization
깃코의 프롬프트 압축 최적화 A/B 테스트 자동화
"""

import subprocess
import json
import time
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent))
from metrics_collector import MetricsCollector
from slack_notifier import SlackNotifier


class ABTester:
    """A/B 테스트 자동화"""

    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent

        self.repo_root = Path(repo_root)
        self.collector = MetricsCollector(repo_root)
        self.notifier = SlackNotifier()
        self.results = []

    def run_single_test(
        self,
        test_name: str,
        env_vars: Dict[str, str],
        task_title: str = "ab_test",
        task_goal: str = "AGI 성능 테스트"
    ) -> Dict[str, Any]:
        """
        단일 테스트 실행

        Args:
            test_name: 테스트 이름
            env_vars: 환경변수 딕셔너리
            task_title: 작업 제목
            task_goal: 작업 목표

        Returns:
            테스트 결과
        """
        print(f"\n{'='*60}")
        print(f"[Test] {test_name}")
        print(f"{'='*60}")

        # 환경변수 출력
        for key, value in env_vars.items():
            print(f"  {key}={value}")

        # 시작 시간
        start_time = time.time()
        start_ts = datetime.now()

        # Ledger 이벤트 수 기록 (before)
        ledger_path = self.repo_root / "memory" / "resonance_ledger.jsonl"
        if ledger_path.exists():
            with open(ledger_path, 'r', encoding='utf-8') as f:
                events_before = sum(1 for _ in f)
        else:
            events_before = 0

        # 테스트 실행
        try:
            cmd = [
                "python", "-m", "scripts.run_task",
                "--title", task_title,
                "--goal", task_goal
            ]

            # 환경변수 설정
            import os
            env = os.environ.copy()
            env.update(env_vars)

            print(f"\n  → Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5분 타임아웃
            )

            success = result.returncode == 0
            print(f"  → Exit code: {result.returncode}")

        except subprocess.TimeoutExpired:
            print(f"  -> [ERROR] Timeout (300s)")
            success = False
        except Exception as e:
            print(f"  -> [ERROR] Error: {e}")
            success = False

        # 종료 시간
        end_time = time.time()
        duration = end_time - start_time

        # Ledger 이벤트 수 기록 (after)
        if ledger_path.exists():
            with open(ledger_path, 'r', encoding='utf-8') as f:
                events_after = sum(1 for _ in f)
        else:
            events_after = 0

        new_events = events_after - events_before

        # 메트릭 수집 (최근 생성된 이벤트만)
        print(f"\n  → Collecting metrics ({new_events} new events)...")
        time.sleep(2)  # 메모리 flush 대기

        # 최근 이벤트 기반으로 메트릭 추출
        metrics = self._extract_metrics_from_recent_events(new_events)

        result_data = {
            'test_name': test_name,
            'env_vars': env_vars,
            'timestamp': start_ts.isoformat(),
            'duration_sec': round(duration, 2),
            'success': success,
            'new_events': new_events,
            'metrics': metrics
        }

        # 결과 출력
        print(f"\n  [Metrics]:")
        print(f"    - Confidence: {metrics.get('avg_confidence', 0):.3f}")
        print(f"    - Quality: {metrics.get('avg_quality', 0):.3f}")
        print(f"    - Second Pass Rate: {metrics.get('second_pass_rate', 0):.3f}")
        print(f"    - Duration: {duration:.2f}s")

        self.results.append(result_data)
        return result_data

    def _extract_metrics_from_recent_events(self, event_count: int) -> Dict[str, float]:
        """최근 N개 이벤트에서 메트릭 추출"""
        ledger_path = self.repo_root / "memory" / "resonance_ledger.jsonl"

        if not ledger_path.exists():
            return {
                'avg_confidence': 0.0,
                'avg_quality': 0.0,
                'second_pass_rate': 0.0,
                'total_events': 0
            }

        # 최근 N개 이벤트 읽기
        events = []
        with open(ledger_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-event_count:] if event_count > 0 else []

            for line in recent_lines:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        # 메트릭 계산
        confidence_values = []
        quality_values = []
        second_pass_count = 0
        task_ids = set()

        for event in events:
            event_type = event.get('event')

            if event_type == 'meta_cognition':
                if 'confidence' in event:
                    confidence_values.append(event['confidence'])

            if event_type == 'eval':
                eval_data = event.get('eval', {})
                if 'quality' in eval_data and eval_data['quality'] is not None:
                    quality_values.append(eval_data['quality'])

            if event_type == 'second_pass':
                second_pass_count += 1

            task_id = event.get('task_id')
            if task_id:
                task_ids.add(task_id)

        return {
            'avg_confidence': round(statistics.mean(confidence_values), 3) if confidence_values else 0.0,
            'avg_quality': round(statistics.mean(quality_values), 3) if quality_values else 0.0,
            'second_pass_rate': round(second_pass_count / max(len(task_ids), 1), 3),
            'total_events': len(events),
            'total_tasks': len(task_ids)
        }

    def run_ab_test(
        self,
        config_a: Dict[str, str],
        config_b: Dict[str, str],
        iterations: int = 5,
        task_title: str = "ab_test",
        task_goal: str = "AGI 성능 테스트"
    ) -> Dict[str, Any]:
        """
        A/B 테스트 실행

        Args:
            config_a: 설정 A (환경변수)
            config_b: 설정 B (환경변수)
            iterations: 각 설정당 실행 횟수
            task_title: 작업 제목
            task_goal: 작업 목표

        Returns:
            A/B 비교 결과
        """
        print("\n" + "="*60)
        print("[A/B Testing Started]")
        print("="*60)
        print(f"Iterations: {iterations} per config")
        print(f"Total runs: {iterations * 2}")
        print()

        # Config A 실행
        print("\n[Running Config A...]")
        results_a = []
        for i in range(iterations):
            print(f"\n[A-{i+1}/{iterations}]")
            result = self.run_single_test(
                f"Config_A_Run_{i+1}",
                config_a,
                task_title,
                task_goal
            )
            results_a.append(result)
            time.sleep(5)  # 실행 간 대기

        # Config B 실행
        print("\n[Running Config B...]")
        results_b = []
        for i in range(iterations):
            print(f"\n[B-{i+1}/{iterations}]")
            result = self.run_single_test(
                f"Config_B_Run_{i+1}",
                config_b,
                task_title,
                task_goal
            )
            results_b.append(result)
            time.sleep(5)

        # 통계 분석
        comparison = self._compare_results(config_a, config_b, results_a, results_b)

        # 결과 저장
        output_file = self.repo_root / "outputs" / f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2)

        print(f"\n[Results saved: {output_file}]")

        # Slack 알림 전송
        self._send_slack_notification(comparison)

        return comparison

    def _send_slack_notification(self, comparison: Dict[str, Any]):
        """A/B 테스트 결과를 Slack으로 알림"""
        try:
            stats_a = comparison['stats_a']
            stats_b = comparison['stats_b']
            diff = comparison['difference']

            # Config 이름
            config_a_val = comparison['config_a'].get('SYNTHESIS_SECTION_MAX_CHARS', '?')
            config_b_val = comparison['config_b'].get('SYNTHESIS_SECTION_MAX_CHARS', '?')

            # 승자 결정
            winner = None
            if diff['quality']['absolute'] > 0.05:
                winner = f"Config B ({config_b_val})"
                reason = f"Quality +{diff['quality']['absolute']:.3f}"
            elif diff['quality']['absolute'] < -0.05:
                winner = f"Config A ({config_a_val})"
                reason = f"Quality {diff['quality']['absolute']:.3f}"

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔬 A/B 테스트 완료",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*설정 비교*\nConfig A: {config_a_val} vs Config B: {config_b_val}\n*반복 횟수*: {comparison['iterations']}회"
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
                            "text": f"*Quality*\nA: {stats_a['quality']['mean']:.3f} | B: {stats_b['quality']['mean']:.3f}\n차이: {diff['quality']['absolute']:+.3f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Confidence*\nA: {stats_a['confidence']['mean']:.3f} | B: {stats_b['confidence']['mean']:.3f}\n차이: {diff['confidence']['absolute']:+.3f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Duration*\nA: {stats_a['duration']['mean']:.1f}s | B: {stats_b['duration']['mean']:.1f}s\n차이: {diff['duration']['absolute']:+.1f}s"
                        }
                    ]
                }
            ]

            if winner:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🏆 *승자*: {winner}\n*이유*: {reason}"
                    }
                })

            self.notifier.send_message(
                f"A/B 테스트 완료: {config_a_val} vs {config_b_val}",
                blocks
            )
        except Exception as e:
            print(f"Slack notification failed: {e}")

    def _compare_results(
        self,
        config_a: Dict[str, str],
        config_b: Dict[str, str],
        results_a: List[Dict],
        results_b: List[Dict]
    ) -> Dict[str, Any]:
        """결과 비교 및 통계 분석"""

        def extract_metrics(results):
            confidence = [r['metrics']['avg_confidence'] for r in results]
            quality = [r['metrics']['avg_quality'] for r in results]
            second_pass = [r['metrics']['second_pass_rate'] for r in results]
            duration = [r['duration_sec'] for r in results]

            return {
                'confidence': {
                    'mean': round(statistics.mean(confidence), 3),
                    'stdev': round(statistics.stdev(confidence), 3) if len(confidence) > 1 else 0,
                    'min': round(min(confidence), 3),
                    'max': round(max(confidence), 3),
                    'values': confidence
                },
                'quality': {
                    'mean': round(statistics.mean(quality), 3),
                    'stdev': round(statistics.stdev(quality), 3) if len(quality) > 1 else 0,
                    'min': round(min(quality), 3),
                    'max': round(max(quality), 3),
                    'values': quality
                },
                'second_pass_rate': {
                    'mean': round(statistics.mean(second_pass), 3),
                    'stdev': round(statistics.stdev(second_pass), 3) if len(second_pass) > 1 else 0,
                    'min': round(min(second_pass), 3),
                    'max': round(max(second_pass), 3),
                    'values': second_pass
                },
                'duration': {
                    'mean': round(statistics.mean(duration), 2),
                    'stdev': round(statistics.stdev(duration), 2) if len(duration) > 1 else 0,
                    'min': round(min(duration), 2),
                    'max': round(max(duration), 2),
                    'values': duration
                }
            }

        stats_a = extract_metrics(results_a)
        stats_b = extract_metrics(results_b)

        # 차이 계산
        def calc_diff(a_mean, b_mean):
            diff = b_mean - a_mean
            pct = (diff / a_mean * 100) if a_mean != 0 else 0
            return {
                'absolute': round(diff, 3),
                'percentage': round(pct, 1)
            }

        comparison = {
            'timestamp': datetime.now().isoformat(),
            'config_a': config_a,
            'config_b': config_b,
            'iterations': len(results_a),
            'stats_a': stats_a,
            'stats_b': stats_b,
            'difference': {
                'confidence': calc_diff(stats_a['confidence']['mean'], stats_b['confidence']['mean']),
                'quality': calc_diff(stats_a['quality']['mean'], stats_b['quality']['mean']),
                'second_pass_rate': calc_diff(stats_a['second_pass_rate']['mean'], stats_b['second_pass_rate']['mean']),
                'duration': calc_diff(stats_a['duration']['mean'], stats_b['duration']['mean'])
            },
            'raw_results': {
                'config_a': results_a,
                'config_b': results_b
            }
        }

        # 결과 출력
        self._print_comparison(comparison)

        return comparison

    def _print_comparison(self, comparison: Dict[str, Any]):
        """비교 결과 출력"""
        print("\n" + "="*60)
        print("[A/B Test Results]")
        print("="*60)

        stats_a = comparison['stats_a']
        stats_b = comparison['stats_b']
        diff = comparison['difference']

        print("\n┌─────────────────┬──────────────┬──────────────┬──────────────┐")
        print("│ Metric          │ Config A     │ Config B     │ Difference   │")
        print("├─────────────────┼──────────────┼──────────────┼──────────────┤")

        # Confidence
        print(f"│ Confidence      │ {stats_a['confidence']['mean']:.3f} ±{stats_a['confidence']['stdev']:.3f} "
              f"│ {stats_b['confidence']['mean']:.3f} ±{stats_b['confidence']['stdev']:.3f} "
              f"│ {diff['confidence']['absolute']:+.3f} ({diff['confidence']['percentage']:+.1f}%) │")

        # Quality
        print(f"│ Quality         │ {stats_a['quality']['mean']:.3f} ±{stats_a['quality']['stdev']:.3f} "
              f"│ {stats_b['quality']['mean']:.3f} ±{stats_b['quality']['stdev']:.3f} "
              f"│ {diff['quality']['absolute']:+.3f} ({diff['quality']['percentage']:+.1f}%) │")

        # Second Pass Rate
        print(f"│ Second Pass     │ {stats_a['second_pass_rate']['mean']:.3f} ±{stats_a['second_pass_rate']['stdev']:.3f} "
              f"│ {stats_b['second_pass_rate']['mean']:.3f} ±{stats_b['second_pass_rate']['stdev']:.3f} "
              f"│ {diff['second_pass_rate']['absolute']:+.3f} ({diff['second_pass_rate']['percentage']:+.1f}%) │")

        # Duration
        print(f"│ Duration (s)    │ {stats_a['duration']['mean']:.1f} ±{stats_a['duration']['stdev']:.1f}   "
              f"│ {stats_b['duration']['mean']:.1f} ±{stats_b['duration']['stdev']:.1f}   "
              f"│ {diff['duration']['absolute']:+.1f} ({diff['duration']['percentage']:+.1f}%)  │")

        print("└─────────────────┴──────────────┴──────────────┴──────────────┘")

        # 승자 결정
        print("\n[Winner]:")
        winners = []
        if diff['quality']['absolute'] > 0:
            winners.append("Quality: Config B")
        elif diff['quality']['absolute'] < 0:
            winners.append("Quality: Config A")

        if diff['confidence']['absolute'] > 0:
            winners.append("Confidence: Config B")
        elif diff['confidence']['absolute'] < 0:
            winners.append("Confidence: Config A")

        if diff['duration']['absolute'] < 0:  # 빠른게 좋음
            winners.append("Speed: Config B")
        elif diff['duration']['absolute'] > 0:
            winners.append("Speed: Config A")

        if winners:
            for w in winners:
                print(f"  - {w}")
        else:
            print("  - No significant difference")


def main():
    """CLI"""
    import argparse

    parser = argparse.ArgumentParser(description='AGI A/B Testing Tool')
    parser.add_argument(
        '--iterations', '-n',
        type=int,
        default=5,
        help='Number of iterations per config (default: 5)'
    )

    args = parser.parse_args()

    tester = ABTester()

    # 예시: SYNTHESIS_SECTION_MAX_CHARS 900 vs 800 비교
    config_a = {
        'SYNTHESIS_SECTION_MAX_CHARS': '900'
    }

    config_b = {
        'SYNTHESIS_SECTION_MAX_CHARS': '800'
    }

    print("\n[A/B Test: SYNTHESIS_SECTION_MAX_CHARS]")
    print(f"  Config A: 900 (기본값)")
    print(f"  Config B: 800 (최적화)")
    print(f"  Iterations: {args.iterations}\n")

    result = tester.run_ab_test(
        config_a,
        config_b,
        iterations=args.iterations,
        task_title="ab_test_synthesis",
        task_goal="AGI 자기교정 루프 설명 3문장"
    )


if __name__ == '__main__':
    main()
