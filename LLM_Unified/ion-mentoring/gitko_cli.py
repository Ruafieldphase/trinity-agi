#!/usr/bin/env python3
"""
Gitko CLI - 명령줄에서 AI 에이전트 오케스트레이션 테스트

사용법:
    python gitko_cli.py "배포 스크립트를 리뷰하고 개선해주세요"
"""

import asyncio
import sys
from pathlib import Path

# 현재 디렉터리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from gitko_integrated_orchestrator import (
    GitkoIntegratedOrchestrator,
    IntegratedConversationAnalyzer,
)


async def main():
    if len(sys.argv) < 2:
        print('사용법: python gitko_cli.py "<작업 설명>"')
        print("\n예시:")
        print('  python gitko_cli.py "배포 스크립트를 리뷰해주세요"')
        print('  python gitko_cli.py "코드를 개선해주세요"')
        print('  python gitko_cli.py "리뷰하고 개선 제안해주세요"')
        sys.exit(1)

    user_message = " ".join(sys.argv[1:])

    print("=" * 70)
    print("🤖 Gitko AI Agent Orchestrator")
    print("=" * 70)
    print(f"\n📝 사용자 요청: {user_message}\n")

    # 1. 오케스트레이터 초기화
    repo_root = Path(__file__).parent.parent.parent

    orchestrator = GitkoIntegratedOrchestrator(
        repo_root=repo_root, use_inbox=False, use_powershell=True  # PowerShell 직접 실행
    )

    analyzer = IntegratedConversationAnalyzer(confidence_threshold=0.4)  # 0.6 → 0.4로 낮춤

    # 2. 작업 분석
    print("🔍 작업 분석 중...")
    task_ctx = analyzer.analyze(user_message)

    print("\n✅ 분석 완료:")
    print(f"   - 작업 타입: {task_ctx.task_type}")
    print(f"   - 신뢰도: {task_ctx.confidence:.0%}")
    print(f"   - 에이전트: {task_ctx.agent.value}")
    print(f"   - 키워드: {', '.join(task_ctx.keywords[:5])}")

    # 3. 작업 디스패치
    if task_ctx.task_type == "none":
        print("\n💬 일반 대화로 처리됩니다 (에이전트 실행 안 함)")
        print(f"\nGitko: 네, {user_message}에 대해 도와드리겠습니다.")
        return

    print(f"\n⏳ {task_ctx.agent.value.upper()} 에이전트 실행 중...")
    print("   (최대 30초 대기)\n")

    task_id = await orchestrator.dispatch_task(task_ctx)

    # 4. 결과 대기
    result = await orchestrator.get_result(task_id, timeout=30.0)

    # 5. 결과 출력
    print("\n" + "=" * 70)

    if result:
        print(orchestrator.format_result_summary(result))
    else:
        print("⏳ 작업이 백그라운드에서 계속 실행 중입니다.")
        print(f"   작업 ID: {task_id}")
        print("   나중에 확인하세요.")

    print("\n" + "=" * 70)
    print("✅ Gitko 작업 완료")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
