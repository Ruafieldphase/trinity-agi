"""
Self-Patch Generator
====================
Role: Automatic Fixer
Function:
  - Takes error findings from SelfCodeAnalyst.
  - Reads relevant source code.
  - Queries LLM (Gemini) to generate a fix.
  - Produces a proposed Patch (Diff or Replacement).
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account

logger = logging.getLogger("SelfPatchGenerator")

class SelfPatchGenerator:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        
        # Use Vertex AI Service Account
        self.project_id = "naeda-genesis"
        self.location = "us-central1"
        self.credentials_path = self.workspace_root / "config" / "secrets" / "naeda-genesis-key.json"
        
        if self.credentials_path.exists():
            try:
                self.credentials = service_account.Credentials.from_service_account_file(str(self.credentials_path))
                vertexai.init(project=self.project_id, location=self.location, credentials=self.credentials)
                self.model = GenerativeModel("gemini-1.5-flash-002")
                logger.info("Vertex AI initialized successfully with Service Account.")
            except Exception as e:
                logger.error(f"Vertex AI initialization failed: {e}")
                self.model = None
        else:
            logger.error(f"Service account key not found at {self.credentials_path}")
            self.model = None
        
        # Safety: Files that should never be modified automatically
        self.protected_files = [
            "breathing_boundary.py",
            "self_code_analyst.py",
            "self_patch_generator.py",
            "self_optimizer.py"
        ]

    def generate_fix(self, finding: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        file_path = Path(finding["file"])
        if not file_path.is_absolute():
            file_path = self.workspace_root / file_path
            
        if any(p in file_path.name for p in self.protected_files):
            logger.warning(f"Skipping protected file: {file_path}")
            return None

        if not file_path.exists():
            logger.error(f"File not found for patching: {file_path}")
            return None

        # 1. Try LLM first if available
        if self.model:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code_content = f.read()
                
                prompt = f"""
                당신은 AGI 시스템의 코드를 자가 개선하는 'Self-Patch Generator'입니다.
                다음 에러 정보를 바탕으로 코드를 분석하고 수정한 버전을 제안해주세요.
                
                [에러 정보]
                - 파일: {finding['file']}
                - 라인: {finding['line']}
                - 함수: {finding.get('func', finding.get('function', 'unknown'))}
                - 에러 타입: {finding['error_type']}
                - 메시지: {finding['message']}
                
                [원본 코드]
                ```python
                {code_content}
                ```
                
                [지침]
                1. 에러를 근본적으로 해결할 수 있는 수정을 제안하세요.
                2. 코드 전체를 제공하지 말고, 수정된 함수나 관련 블록만 JSON 형식으로 반환하세요.
                3. 'reason' 필드에 수정 이유를 명확히 설명하세요.
                
                [반환 형식 (JSON)]
                {{
                    "original_snippet": "수정할 원본 코드 블록",
                    "replacement_snippet": "새로운 코드 블록",
                    "reason": "수정 이유 (한국어)"
                }}
                """
                
                response = self.model.generate_content(prompt, generation_config={"temperature": 0.1})
                text = response.text
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                
                patch = json.loads(text.strip())
                patch["target_file"] = str(file_path)
                logger.info(f"Successfully generated patch for {file_path}")
                return patch
            except Exception as e:
                logger.error(f"LLM Patch generation failed: {e}")

        # 2. Fallback to Heuristic Fixer
        logger.info(f"Using Heuristic Fixer for {finding.get('error_type')}")
        return self._generate_heuristic_fix(finding)

    def _generate_heuristic_fix(self, finding: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """간단한 에러 패턴에 대한 규칙 기반 수정안 제안"""
        file_path = Path(finding.get('file'))
        if not file_path.is_absolute():
            file_path = self.workspace_root / file_path
            
        error_type = finding.get('error_type')
        line_no = finding.get('line')
        
        if not file_path.exists():
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except:
            return None
            
        if line_no > len(lines):
            return None
            
        target_line = lines[line_no - 1]
        
        # ZeroDivisionError 처리
        if error_type == "ZeroDivisionError":
            indent = len(target_line) - len(target_line.lstrip())
            original = target_line.strip()
            
            # 간단한 변수 추출 (a / b -> b)
            if "/" in original:
                parts = original.split("/")
                divisor = parts[-1].split(")")[0].strip()
                
                replacement = f"{' ' * indent}if {divisor} == 0: return 0  # Heuristic safeguard\n{target_line}"
                
                return {
                    "target_file": str(file_path),
                    "original_snippet": target_line,
                    "replacement_snippet": replacement,
                    "reason": "ZeroDivisionError 방지를 위한 휴리스틱 가드 추가 (API 불능 시)"
                }
        
        return None

if __name__ == "__main__":
    # Test (Simulated finding)
    gen = SelfPatchGenerator(Path("c:/workspace/agi"))
    dummy_finding = {
        "file": "c:/workspace/agi/agi_core/test_file.py",
        "line": 10,
        "function": "calculate",
        "error_type": "ZeroDivisionError",
        "message": "division by zero"
    }
    # Note: Requires test_file.py to actually exist for real test
    # print(gen.generate_fix(dummy_finding))
