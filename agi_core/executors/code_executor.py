# agi_core/executors/code_executor.py

from typing import Any, Dict

# AGI Core imports
from agi_core.meta_controller import Executor

# Gemini Tool imports
# 이 실행기는 내부적으로 셸 명령을 실행하는 도구를 사용해야 합니다.
from default_api import run_shell_command

class CodeExecutor(Executor):
    """코드 실행 관련 작업을 처리하는 실행기"""

    def get_domain(self) -> str:
        return "code"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action")
        parameters = task.get("parameters", {})
        
        try:
            if action == "run_script":
                script_path = parameters.get("script_path")
                if not script_path:
                    raise ValueError("'script_path' parameter is required for run_script action.")
                
                # 예: python script.py
                # 보안을 위해 실행할 수 있는 명령어는 제한되어야 하지만, 여기서는 개념 증명을 위해 직접 실행합니다.
                command = f"python {script_path}"
                
                # run_shell_command는 동기적으로 작동할 수 있으므로, 
                # 실제 구현에서는 asyncio.to_thread 등을 사용하여 비동기적으로 호출해야 할 수 있습니다.
                # 여기서는 도구의 반환 값을 직접 사용합니다.
                result = run_shell_command(command=command, description=f"Executing Python script: {script_path}")
                
                # 실행 결과 파싱
                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")
                exit_code = result.get("exit_code", -1)
                
                if exit_code == 0:
                    summary = f"Successfully executed script: {script_path}."
                    return {"success": True, "summary": summary, "output": stdout}
                else:
                    error_message = f"Script execution failed with exit code {exit_code}. Stderr: {stderr}"
                    return {"success": False, "summary": "Script failed.", "error_message": error_message, "output": stderr}

            else:
                raise NotImplementedError(f"Action '{action}' is not implemented in CodeExecutor.")

        except Exception as e:
            error_message = f"Error executing '{action}' in CodeExecutor: {e}"
            print(f"[Executor Error] {error_message}")
            return {"success": False, "summary": "Task failed.", "error_message": error_message}
