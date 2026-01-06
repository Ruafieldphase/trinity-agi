# agi_core/meta_controller.py

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# ============================================================================ 
# Executor - Abstract Base Class
# ============================================================================ 

class Executor(ABC):
    """모든 실행기의 기반이 되는 추상 클래스"""

    @abstractmethod
    def get_domain(self) -> str:
        """자신이 처리할 도메인 이름을 반환합니다. (예: 'file_system')"""
        pass

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        주어진 작업을 실행하고 결과를 반환합니다.
        성공 시: {"success": True, "summary": "...", "output_path": "..."}
        실패 시: {"success": False, "summary": "...", "error_message": "..."}
        """
        pass

# ============================================================================ 
# Meta-Controller
# ============================================================================ 

class MetaController:
    """AGI 시스템의 중앙 지휘 센터"""

    def __init__(self):
        # In-memory storage for tasks and executors
        self.task_registry: Dict[str, Dict[str, Any]] = {}
        self.executor_registry: Dict[str, Executor] = {}
        self.is_running = False
        print("MetaController initialized.")

    def register_executor(self, executor: Executor):
        """실행기를 도메인과 함께 등록합니다."""
        domain = executor.get_domain()
        if domain in self.executor_registry:
            print(f"[Warning] Executor for domain '{domain}' is already registered. Overwriting.")
        self.executor_registry[domain] = executor
        print(f"Executor for domain '{domain}' registered.")

    def submit_goal(self, goal: str) -> str:
        """사용자로부터 새로운 목표를 제출받습니다."""
        # TODO: Goal Decomposer 구현
        # 현재는 단일 작업을 생성하는 것으로 가정합니다.
        print(f"New goal submitted: {goal}")
        task_id = str(uuid.uuid4())
        # 임시로 file_system 도메인의 list_directory 작업을 생성
        task = {
            "schema_version": "1.0",
            "task_id": task_id,
            "goal": goal,
            "domain": "file_system",
            "action": "list_directory",
            "parameters": {"path": "."},
            "dependencies": [],
            "status": "pending",
            "result": None,
            "metadata": {"created_at": asyncio.get_event_loop().time()}
        }
        self.task_registry[task_id] = task
        print(f"Task {task_id} created for goal.")
        return task_id # 목표를 대표하는 첫 작업 ID를 반환

    async def run(self):
        """메인 실행 루프를 시작합니다."""
        print("MetaController run loop started.")
        self.is_running = True
        while self.is_running:
            # 1. 실행 가능한 작업 찾기
            runnable_tasks = self._get_runnable_tasks()
            if runnable_tasks:
                print(f"Found {len(runnable_tasks)} runnable tasks.")
                # 2. 비동기적으로 실행
                await asyncio.gather(*[self._execute_task(task) for task in runnable_tasks])
            
            # 3. 잠시 대기
            await asyncio.sleep(1) 

    def stop(self):
        """실행 루프를 중지합니다."""
        self.is_running = False
        print("MetaController run loop stopped.")

    def _get_runnable_tasks(self) -> List[Dict[str, Any]]:
        """의존성이 해결되어 지금 당장 실행 가능한 작업 목록을 반환합니다."""
        runnable = []
        for task_id, task in self.task_registry.items():
            if task["status"] == "pending":
                # 의존성 체크
                deps = task.get("dependencies", [])
                if not deps or all(self.task_registry[dep_id]["status"] == "completed" for dep_id in deps):
                    runnable.append(task)
        return runnable

    async def _execute_task(self, task: Dict[str, Any]):
        """단일 작업을 실행하고 결과를 기록합니다."""
        task_id = task["task_id"]
        domain = task["domain"]
        
        # 실행기 찾기
        executor = self.executor_registry.get(domain)
        if not executor:
            error_msg = f"No executor found for domain: {domain}"
            print(f"[Error] {error_msg}")
            task["status"] = "failed"
            task["result"] = {"success": False, "summary": error_msg, "error_message": error_msg}
            return

        print(f"Executing task {task_id} with {executor.__class__.__name__}...")
        task["status"] = "in_progress"
        
        try:
            # 실행
            result = await executor.execute(task)
            task["result"] = result
            task["status"] = "completed" if result.get("success") else "failed"
            print(f"Task {task_id} finished with status: {task['status']}")
        except Exception as e:
            error_msg = f"An exception occurred during task execution: {e}"
            print(f"[Error] {error_msg}")
            task["status"] = "failed"
            task["result"] = {"success": False, "summary": error_msg, "error_message": str(e)}

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """특정 작업의 상태와 결과를 조회합니다."""
        return self.task_registry.get(task_id)

if __name__ == "__main__":
    # 다중 실행기 통합 테스트 로직
    from agi_core.executors.file_system_executor import FileSystemExecutor
    from agi_core.executors.web_executor import WebExecutor
    import json

    async def main_test():
        print("--- MetaController Multi-Executor Integration Test --- ")
        controller = MetaController()
        
        # 1. 여러 실행기 등록
        controller.register_executor(FileSystemExecutor())
        controller.register_executor(WebExecutor())
        
        # 2. 여러 도메인의 작업 제출
        fs_task_id = controller.submit_goal("List files in the current directory.")
        
        # Web 작업을 수동으로 추가
        web_task_id = str(uuid.uuid4())
        web_task = {
            "schema_version": "1.0",
            "task_id": web_task_id,
            "goal": "Fetch Google's homepage",
            "domain": "web",
            "action": "fetch_content",
            "parameters": {"url": "https://www.google.com"},
            "dependencies": [],
            "status": "pending",
            "result": None,
            "metadata": {"created_at": asyncio.get_event_loop().time()}
        }
        controller.task_registry[web_task_id] = web_task
        print(f"Task {web_task_id} created for goal: Fetch Google's homepage")

        # 3. 컨트롤러를 5초간 실행 (네트워크 작업 시간 고려)
        run_task = asyncio.create_task(controller.run())
        await asyncio.sleep(5)
        controller.stop()
        await run_task
        
        # 4. 최종 결과 확인
        fs_task_status = controller.get_task_status(fs_task_id)
        web_task_status = controller.get_task_status(web_task_id)

        print("\n--- Multi-Executor Test Result ---")
        # File System Task 결과
        print(f"[File System Task] Final Status: {fs_task_status.get('status')}")
        fs_result_output = fs_task_status.get('result', {}).get('output', {})
        if fs_result_output:
            files = fs_result_output.get('files', [])
            dirs = fs_result_output.get('directories', [])
            print(f"  -> Output: Found {len(files)} files and {len(dirs)} directories.")
        
        print("---")
        
        # Web Task 결과
        print(f"[Web Task] Final Status: {web_task_status.get('status')}")
        web_result_output = web_task_status.get('result', {}).get('output', {})
        if web_result_output:
            # web_fetch 결과는 복잡한 객체일 수 있으므로 요약 정보만 표시
            summary = web_task_status.get('result', {}).get('summary', 'No summary')
            print(f"  -> Output: {summary}")

        print("------------------------------------")

    asyncio.run(main_test())
