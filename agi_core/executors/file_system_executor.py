# agi_core/executors/file_system_executor.py

import json
from typing import Any, Dict

# AGI Core imports
from agi_core.meta_controller import Executor

# Gemini Tool imports
from default_api import read_file, write_file, list_directory

class FileSystemExecutor(Executor):
    """파일 시스템 작업을 처리하는 실행기"""

    def get_domain(self) -> str:
        return "file_system"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action")
        parameters = task.get("parameters", {})
        
        try:
            if action == "list_directory":
                path = parameters.get("path", ".")
                result = list_directory(path=path)
                # Assuming the tool returns a dict that can be serialized
                summary = f"Listed directory: {path}. Found {len(result.get('files', []))} files and {len(result.get('directories', []))} directories."
                return {"success": True, "summary": summary, "output": result}

            elif action == "read_file":
                path = parameters.get("path")
                if not path:
                    raise ValueError("'path' parameter is required for read_file action.")
                
                result = read_file(absolute_path=path)
                content = result.get("output", "")
                summary = f"Read file: {path}. Length: {len(content)} characters."
                return {"success": True, "summary": summary, "output": content}

            elif action == "write_file":
                path = parameters.get("path")
                content = parameters.get("content", "")
                if not path:
                    raise ValueError("'path' parameter is required for write_file action.")
                
                write_file(file_path=path, content=content)
                summary = f"Wrote {len(content)} characters to file: {path}."
                return {"success": True, "summary": summary}

            else:
                raise NotImplementedError(f"Action '{action}' is not implemented in FileSystemExecutor.")

        except Exception as e:
            error_message = f"Error executing '{action}' in FileSystemExecutor: {e}"
            print(f"[Executor Error] {error_message}")
            return {"success": False, "summary": "Task failed.", "error_message": error_message}
