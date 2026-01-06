# agi_core/executors/web_executor.py

from typing import Any, Dict

# AGI Core imports
from agi_core.meta_controller import Executor

# Gemini Tool imports
from default_api import web_fetch

class WebExecutor(Executor):
    """웹 관련 작업을 처리하는 실행기 (예: 웹페이지 가져오기)"""

    def get_domain(self) -> str:
        return "web"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action")
        parameters = task.get("parameters", {})
        
        try:
            if action == "fetch_content":
                url = parameters.get("url")
                if not url:
                    raise ValueError("'url' parameter is required for fetch_content action.")
                
                # web_fetch 도구는 프롬프트에 URL과 지시사항을 함께 전달해야 합니다.
                prompt = f"Please fetch the content from the URL: {url}"
                result = web_fetch(prompt=prompt)
                
                # web_fetch 결과가 어떻게 반환되는지 가정하고 요약 생성
                # 실제로는 결과 구조를 확인하고 파싱해야 합니다.
                content_snippet = str(result)[:200]
                summary = f"Fetched content from {url}. Snippet: {content_snippet}..."
                return {"success": True, "summary": summary, "output": result}

            else:
                raise NotImplementedError(f"Action '{action}' is not implemented in WebExecutor.")

        except Exception as e:
            error_message = f"Error executing '{action}' in WebExecutor: {e}"
            print(f"[Executor Error] {error_message}")
            return {"success": False, "summary": "Task failed.", "error_message": error_message}
