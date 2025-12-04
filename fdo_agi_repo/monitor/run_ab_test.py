#!/usr/bin/env python3
"""
A/B 테스트 실행 스크립트
Usage: python run_ab_test.py [--config-a VALUE] [--config-b VALUE] [--iterations N]
"""

import sys
import argparse
from pathlib import Path

# 경로 설정
monitor_dir = Path(__file__).parent
sys.path.insert(0, str(monitor_dir))

from ab_tester import ABTester


def main():
    parser = argparse.ArgumentParser(description='AGI A/B Testing Automation')
    parser.add_argument('--config-a', type=str, default='900',
                        help='Config A value for SYNTHESIS_SECTION_MAX_CHARS (default: 900)')
    parser.add_argument('--config-b', type=str, default='800',
                        help='Config B value for SYNTHESIS_SECTION_MAX_CHARS (default: 800)')
    parser.add_argument('--iterations', type=int, default=5,
                        help='Number of iterations per config (default: 5)')
    parser.add_argument('--task-goal', type=str, default='AGI 자기교정 루프 설명 3문장',
                        help='Task goal description')

    args = parser.parse_args()

    print("=" * 60)
    print("A/B Test Configuration")
    print("=" * 60)
    print(f"  Test Variable: SYNTHESIS_SECTION_MAX_CHARS")
    print(f"  Config A: {args.config_a}")
    print(f"  Config B: {args.config_b}")
    print(f"  Iterations: {args.iterations} (total {args.iterations * 2} runs)")
    print(f"  Task Goal: {args.task_goal}")
    print(f"  Estimated Time: {args.iterations * 2 * 2} minutes")
    print()

    # A/B 테스트 실행
    tester = ABTester()

    config_a = {'SYNTHESIS_SECTION_MAX_CHARS': args.config_a}
    config_b = {'SYNTHESIS_SECTION_MAX_CHARS': args.config_b}

    print("Starting A/B Test...")
    print()

    result = tester.run_ab_test(
        config_a,
        config_b,
        iterations=args.iterations,
        task_title='ab_test_synthesis',
        task_goal=args.task_goal
    )

    print()
    print("=" * 60)
    print("A/B Test Completed")
    print("=" * 60)
    print()
    print("Results saved to:")
    print(f"  - JSON: outputs/ab_test_*.json")
    print(f"  - Report: outputs/ab_test_*_report.md")
    print()


if __name__ == '__main__':
    main()
