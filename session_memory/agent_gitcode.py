#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitCode - 실행자 에이전트

GitCode는 다음 역할을 수행합니다:
1. 부분 작업 실행: Lubit으로부터 승인받은 부분 작업들 실행
2. 의존성 처리: 부분 작업들 간 의존성 관리
3. 실행 모니터링: 작업 진행 상황 모니터링
4. 실패 처리: 실패한 작업 복구 시도

메시지 라우터를 통해 RUNE으로 실행 결과 전달
"""

import sys
import io
import json
import time
import random
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from agent_interface import (
    ExecutionAgent, AgentConfig, AgentRole, TaskContext, ExecutionResult, MessageType
)

# UTF-8 인코딩 강제 설정 (Windows 호환)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class GitCodeAgent(ExecutionAgent):
    """
    GitCode - 실행자 에이전트 구현

    역할: 부분 작업을 실행하고 결과를 반환
    """

    def __init__(self, config: AgentConfig):
        """GitCode 에이전트 초기화"""
        super().__init__(config)
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.retry_count = 0

    def initialize(self) -> bool:
        """에이전트 초기화"""
        self.is_initialized = True
        self.log_message({
            "from": self.role.value,
            "message_type": "system",
            "content": "GitCode 에이전트 초기화 완료"
        }, direction="system")
        return True

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 처리"""
        self.log_message(message, direction="received")

        message_type = message.get("message_type")

        if message_type == "validation_result":
            return self._handle_validation_result(message)
        else:
            return {
                "success": False,
                "error": f"알 수 없는 메시지 타입: {message_type}"
            }

    def _handle_validation_result(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """검증 결과 처리"""
        task_id = message.get("task_id")
        content = message.get("content", {})
        verdict = content.get("verdict")

        if verdict != "approved":
            return {
                "success": False,
                "error": f"분석이 승인되지 않음: {verdict}"
            }

        # 부분 작업 실행
        sub_tasks = content.get("sub_tasks", [])
        execution_results = []

        print(f"\n[GitCode] 부분 작업 실행 시작: {task_id}")

        for sub_task in sub_tasks:
            result = self.execute_subtask(sub_task)
            execution_results.append(result)

        # 모든 부분 작업 실행 완료
        response = {
            "message_type": MessageType.EXECUTION_RESULT.value,
            "from_agent": self.role.value,
            "to_agent": "rune",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "content": {
                "sub_tasks": execution_results,
                "total_tasks": len(execution_results),
                "successful_tasks": sum(1 for r in execution_results if r.get("success")),
                "failed_tasks": sum(1 for r in execution_results if not r.get("success")),
                "execution_status": "completed"
            },
            "metadata": {
                "version": "1.0",
                "status": "execution_complete"
            }
        }

        self.log_message(response, direction="sent")
        self.log_task(task_id, "execution_complete", response)

        return response

    def execute_task(self, task_context: TaskContext) -> ExecutionResult:
        """작업 실행"""
        try:
            start_time = time.time()

            # 실제 작업 시뮬레이션
            self.execution_count += 1

            # 90% 성공률 시뮬레이션
            success = random.random() > 0.1

            if success:
                self.success_count += 1
                output = {
                    "task_id": task_context.task_id,
                    "status": "success",
                    "result": f"작업 완료: {task_context.description}"
                }
            else:
                self.failure_count += 1
                output = {
                    "task_id": task_context.task_id,
                    "status": "failure",
                    "error": "시뮬레이션 실패"
                }

            execution_time_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=success,
                output=output,
                execution_time_ms=execution_time_ms
            )
        except Exception as e:
            self.failure_count += 1
            return ExecutionResult(
                success=False,
                output=None,
                error=str(e)
            )

    def validate_input(self, input_data: Any) -> Tuple[bool, Optional[str]]:
        """입력 검증"""
        if not isinstance(input_data, dict):
            return False, "입력은 딕셔너리여야 합니다"

        if "sub_tasks" not in input_data:
            return False, "sub_tasks 필드가 필요합니다"

        sub_tasks = input_data.get("sub_tasks")
        if not isinstance(sub_tasks, list) or len(sub_tasks) == 0:
            return False, "sub_tasks는 공백이 아닌 리스트여야 합니다"

        return True, None

    def generate_response(self, task_result: ExecutionResult) -> Dict[str, Any]:
        """응답 생성"""
        if not task_result.success:
            return {
                "success": False,
                "error": task_result.error
            }

        output = task_result.output
        return {
            "success": True,
            "result": output,
            "execution_time_ms": task_result.execution_time_ms
        }

    def execute_subtask(self, subtask: Dict[str, Any]) -> Dict[str, Any]:
        """부분 작업 실행"""
        subtask_id = subtask.get("id", "unknown")
        subtask_desc = subtask.get("description", "작업")
        tools = subtask.get("tools", [])

        print(f"  → {subtask_id}: {subtask_desc} (도구: {', '.join(tools)})")

        # 90% 성공률로 부분 작업 실행
        success = random.random() > 0.1

        if success:
            result = {
                "subtask_id": subtask_id,
                "description": subtask_desc,
                "success": True,
                "output": f"부분 작업 '{subtask_id}' 성공적으로 완료",
                "tools_used": tools,
                "execution_time_ms": random.uniform(50, 500)
            }
            print(f"    ✓ 완료")
        else:
            result = {
                "subtask_id": subtask_id,
                "description": subtask_desc,
                "success": False,
                "error": f"부분 작업 '{subtask_id}' 실행 실패",
                "tools_used": tools,
                "execution_time_ms": random.uniform(10, 100)
            }
            print(f"    ✗ 실패")

        self.execution_log.append(result)
        return result

    def handle_dependencies(self, subtasks: List[Dict[str, Any]]) -> bool:
        """부분 작업들 간 의존성 처리"""
        # 부분 작업들이 순서대로 진행되도록 보장
        print(f"\n[의존성 처리] {len(subtasks)}개 부분 작업의 의존성 확인")

        for i, subtask in enumerate(subtasks):
            dependencies = subtask.get("dependencies", [])
            if dependencies:
                print(f"  - {subtask['id']}: {dependencies}에 의존")
            else:
                print(f"  - {subtask['id']}: 독립적")

        return True

    def monitor_execution(self, task_id: str) -> Dict[str, Any]:
        """실행 모니터링"""
        monitoring_info = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": (self.success_count / self.execution_count * 100) if self.execution_count > 0 else 0,
            "recent_executions": self.execution_log[-5:] if self.execution_log else []
        }
        return monitoring_info

    def handle_failure(self, subtask: Dict[str, Any], error: str) -> bool:
        """실패 처리"""
        subtask_id = subtask.get("id", "unknown")
        self.retry_count += 1

        print(f"\n[실패 처리] {subtask_id} 재시도: {self.retry_count}회")
        print(f"  에러: {error}")

        if self.retry_count < self.config.max_retries:
            print(f"  → 재시도 예정 ({self.retry_count}/{self.config.max_retries})")
            return True
        else:
            print(f"  → 최대 재시도 횟수 초과, 실패 처리")
            return False


# ============================================================================
# 데모: GitCode 에이전트
# ============================================================================

def demo_gitcode_agent():
    """GitCode 에이전트 데모"""
    print("=" * 80)
    print("GitCode (실행자) 에이전트 데모")
    print("=" * 80)

    # 1. GitCode 에이전트 생성
    print("\n[1단계] GitCode 에이전트 생성")
    print("-" * 80)

    config = AgentConfig(
        role=AgentRole.GITCODE,
        name="GitCode",
        description="실행자 - 작업을 실행하는 에이전트"
    )

    gitcode = GitCodeAgent(config)
    gitcode.initialize()
    print(f"GitCode 에이전트 생성 완료: {gitcode.agent_id}")

    # 2. 부분 작업 실행 테스트
    print("\n[2단계] 부분 작업 실행 테스트")
    print("-" * 80)

    subtasks = [
        {
            "id": "sub_1",
            "description": "데이터 수집",
            "tools": ["web_crawler"],
            "dependencies": []
        },
        {
            "id": "sub_2",
            "description": "데이터 정제",
            "tools": ["data_processor"],
            "dependencies": ["sub_1"]
        },
        {
            "id": "sub_3",
            "description": "통계 분석",
            "tools": ["statistical_analyzer"],
            "dependencies": ["sub_2"]
        },
        {
            "id": "sub_4",
            "description": "결과 시각화",
            "tools": ["visualizer"],
            "dependencies": ["sub_3"]
        }
    ]

    print("\n부분 작업 실행:")
    for subtask in subtasks:
        gitcode.execute_subtask(subtask)

    # 3. 의존성 처리 테스트
    print("\n[3단계] 의존성 처리 테스트")
    print("-" * 80)

    gitcode.handle_dependencies(subtasks)

    # 4. 실행 모니터링 테스트
    print("\n[4단계] 실행 모니터링 테스트")
    print("-" * 80)

    monitoring = gitcode.monitor_execution("task_001")
    print(f"\n모니터링 정보:")
    print(f"  - 총 실행: {monitoring['execution_count']}회")
    print(f"  - 성공: {monitoring['success_count']}회")
    print(f"  - 실패: {monitoring['failure_count']}회")
    print(f"  - 성공률: {monitoring['success_rate']:.1f}%")

    # 5. 메시지 처리 테스트
    print("\n[5단계] 메시지 처리 테스트")
    print("-" * 80)

    message = {
        "message_type": "validation_result",
        "task_id": "task_002",
        "from": "lubit",
        "to": "gitcode",
        "content": {
            "verdict": "approved",
            "sub_tasks": [
                {
                    "id": "sub_1",
                    "description": "작업 1",
                    "tools": ["tool1"]
                },
                {
                    "id": "sub_2",
                    "description": "작업 2",
                    "tools": ["tool2"]
                }
            ]
        }
    }

    print(f"\n검증 결과 수신: {message['content']['verdict']}")
    response = gitcode.process_message(message)

    if response.get("success") is False:
        print(f"  응답: {response['content']}")
    else:
        print(f"  실행 상태: {response['content']['execution_status']}")
        print(f"  성공한 작업: {response['content']['successful_tasks']}")
        print(f"  실패한 작업: {response['content']['failed_tasks']}")

    # 6. TaskContext를 이용한 execute_task 테스트
    print("\n[6단계] 작업 실행 테스트")
    print("-" * 80)

    task_context = TaskContext(
        task_id="task_003",
        task_type="execution",
        description="복잡한 데이터 처리 작업"
    )

    result = gitcode.execute_task(task_context)
    print(f"\n작업 실행 성공: {result.success}")
    print(f"실행 시간: {result.execution_time_ms:.2f}ms")
    print(f"결과: {result.output}")

    # 7. 실패 처리 테스트
    print("\n[7단계] 실패 처리 테스트")
    print("-" * 80)

    failed_subtask = {
        "id": "sub_failed",
        "description": "실패한 작업",
        "tools": ["tool1"]
    }

    gitcode.handle_failure(failed_subtask, "시뮬레이션 에러")

    # 8. 에이전트 상태 조회
    print("\n[8단계] 에이전트 상태 조회")
    print("-" * 80)

    status = gitcode.get_status()
    print(f"\n에이전트 상태:")
    print(f"  - ID: {status['agent_id']}")
    print(f"  - 역할: {status['role']}")
    print(f"  - 이름: {status['name']}")
    print(f"  - 초기화: {status['is_initialized']}")
    print(f"  - 처리한 메시지: {status['message_count']}")
    print(f"  - 처리한 작업: {status['task_count']}")

    print("\n" + "=" * 80)
    print("GitCode 에이전트 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_gitcode_agent()
