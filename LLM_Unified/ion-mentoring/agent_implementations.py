"""
실제 에이전트 구현 예제 - Sian (리팩터링 에이전트)
==================================================

목적: AgentBase를 상속받아 실제 작업을 수행하는 에이전트 구현
"""

from agent_base import AgentBase, TaskContext, TaskResult, TaskStatus


class SianAgent(AgentBase):
    """
    Sian: 리팩터링 및 개선 작업 전문 에이전트
    """

    def __init__(self):
        super().__init__("sian")
        self.gemini_cli = "gcloud"  # Gemini CLI 명령어

    async def execute_task(self, task: TaskContext) -> TaskResult:
        """
        작업 실행: Gemini API 호출하여 코드 개선

        Args:
            task: 실행할 작업

        Returns:
            실행 결과
        """
        print(f"[Sian] 🔧 리팩터링 시작: {task.description}")

        try:
            # 작업 타입에 따라 분기
            if "review" in task.description.lower():
                # 리뷰 후 Lubit에게 전달
                output = "코드 개선 완료: 함수 분리, 타입 힌트 추가"

                return TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.COMPLETED,
                    output=output,
                    artifacts=["refactored_code.py"],
                    next_agent="lubit",
                    next_task="개선된 코드를 리뷰해주세요",
                )

            else:
                # 일반 작업
                output = f"Sian이 처리 완료: {task.description}"

                return TaskResult(task_id=task.task_id, status=TaskStatus.COMPLETED, output=output)

        except Exception as e:
            return TaskResult(task_id=task.task_id, status=TaskStatus.FAILED, error_message=str(e))


class LubitAgent(AgentBase):
    """
    Lubit: 코드 리뷰 및 검증 전문 에이전트
    """

    def __init__(self):
        super().__init__("lubit")

    async def execute_task(self, task: TaskContext) -> TaskResult:
        """
        작업 실행: 코드 리뷰 수행

        Args:
            task: 실행할 작업

        Returns:
            실행 결과
        """
        print(f"[Lubit] 🔍 리뷰 시작: {task.description}")

        try:
            # 이전 작업 결과 확인
            if task.depends_on_results:
                print(f"[Lubit] 이전 작업 결과 확인: {task.depends_on_results}")

            # 리뷰 결과
            output = "리뷰 완료: 코드 품질 우수, 배포 승인"

            # 워크플로우 컨텍스트에 저장
            if task.workflow_id:
                self.save_to_context(
                    task.workflow_id, {"lubit_review": {"status": "approved", "comments": output}}
                )

            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                output=output,
                artifacts=["review_report.md"],
            )

        except Exception as e:
            return TaskResult(task_id=task.task_id, status=TaskStatus.FAILED, error_message=str(e))


class GitkoAgent(AgentBase):
    """
    Gitko: 오케스트레이션 및 배포 전문 에이전트
    """

    def __init__(self):
        super().__init__("gitko")

    async def execute_task(self, task: TaskContext) -> TaskResult:
        """
        작업 실행: 배포 또는 오케스트레이션

        Args:
            task: 실행할 작업

        Returns:
            실행 결과
        """
        print(f"[Gitko] 🚀 작업 시작: {task.description}")

        try:
            # 워크플로우 전체 컨텍스트 로드
            if task.workflow_id:
                context = self.load_from_context(task.workflow_id)
                print(f"[Gitko] 워크플로우 컨텍스트: {context}")

            output = f"Gitko 처리 완료: {task.description}"

            return TaskResult(task_id=task.task_id, status=TaskStatus.COMPLETED, output=output)

        except Exception as e:
            return TaskResult(task_id=task.task_id, status=TaskStatus.FAILED, error_message=str(e))
