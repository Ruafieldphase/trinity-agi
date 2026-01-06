"""
Self-Code Analyst
=================
Role: Error Pattern Recognizer
Function:
  - Scans log files for Python tracebacks and repeating error patterns.
  - Extracts file paths, line numbers, and error types.
  - Prioritizes errors based on frequency.
"""

import re
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger("SelfCodeAnalyst")

class SelfCodeAnalyst:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.log_files = [
            workspace_root / "rhythm_think.log",
            workspace_root / "arch_agent.log",
            workspace_root / "outputs" / "body_execution.log"
        ]
        
        # Pattern for Python Tracebacks
        # Example: File "c:\workspace\agi\agi_core\arch_agent.py", line 113, in run_pipeline
        self.traceback_pattern = re.compile(
            r'File "(?P<file>[^"]+)", line (?P<line>\d+), in (?P<func>\w+)'
        )
        self.error_msg_pattern = re.compile(r'^(?P<error_type>\w+): (?P<message>.*)$', re.MULTILINE)

    def scan_logs(self) -> List[Dict[str, Any]]:
        """
        Scan configured log files for tracebacks.
        """
        findings = []
        for log_path in self.log_files:
            if not log_path.exists():
                continue
            
            logger.info(f"Scanning log: {log_path.name}")
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                    # Split into potential blocks (e.g., using timestamps or "Traceback")
                    blocks = content.split("Traceback (most recent call last):")
                    for block in blocks[1:]: # Skip the first part before the first Traceback
                        matches = list(self.traceback_pattern.finditer(block))
                        if not matches:
                            continue
                        
                        # The last match in a traceback block is usually the actual error location
                        last_match = matches[-1]
                        file_path = last_match.group("file")
                        line_num = int(last_match.group("line"))
                        func_name = last_match.group("func")
                        
                        # Try to find the error message right after the last traceback match
                        error_type = "UnknownError"
                        error_msg = ""
                        
                        last_match_end = last_match.end()
                        remaining_block = block[last_match_end:].strip()
                        lines = remaining_block.split("\n")
                        
                        # The lines immediately following the last stack frame should be the error message
                        # frame line: "    code line"
                        # next line: "    ^~~~" (optional, Python 3.11+)
                        # next line: "ErrorType: message"
                        
                        for line in lines:
                            line = line.strip()
                            if not line or line.startswith("^") or line.startswith("~"):
                                continue
                            
                            # Check for "Type: Message"
                            err_match = re.search(r'^(?P<type>\w+):\s*(?P<msg>.*)$', line)
                            if err_match:
                                error_type = err_match.group("type")
                                error_msg = err_match.group("msg")
                                break
                            elif ":" in line:
                                error_msg = line
                                break
                            else:
                                # If we hit a line with a timestamp, we've gone too far
                                if re.match(r'\d{4}-\d{2}-\d{2}', line):
                                    break
                        
                        finding = {
                            "file": file_path,
                            "line": line_num,
                            "function": func_name,
                            "error_type": error_type,
                            "message": error_msg,
                            "log_source": log_path.name,
                            "frequency": 1
                        }
                        
                        # Deduplicate
                        exists = False
                        for fnd in findings:
                            if fnd["file"] == finding["file"] and fnd["line"] == finding["line"] and fnd["error_type"] == finding["error_type"]:
                                fnd["frequency"] += 1
                                exists = True
                                break
                        
                        if not exists:
                            findings.append(finding)
                            
            except Exception as e:
                logger.error(f"Error scanning {log_path}: {e}")
                
        return sorted(findings, key=lambda x: x["frequency"], reverse=True)

if __name__ == "__main__":
    analyst = SelfCodeAnalyst(Path("c:/workspace/agi"))
    results = analyst.scan_logs()
    for res in results:
        print(f"Detected Error in {res['file']}:{res['line']} ({res['error_type']}) - Freq: {res['frequency']}")
