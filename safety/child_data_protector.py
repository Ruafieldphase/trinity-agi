#!/usr/bin/env python3
"""
Child Data Protector
Purpose: Detect and prevent any processing or storage of data from individuals under 18
Principle: "실행 시 네트워크/PII 저장 금지" (No network access or PII storage during execution)

CRITICAL: This module must NEVER:
- Make network requests
- Store PII or sensitive data
- Process actual child data (only detect and block)

Always generates output file even if ok:false
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional


class ChildDataProtector:
    """
    Monitors data pipelines for potential child-related content.
    Uses pattern matching only - NO network calls, NO data storage.
    """

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.violations = []
        self.warnings = []

        # Age-related patterns (heuristic only)
        self.age_patterns = [
            r'\bage[:\s]*([0-9]{1,2})',
            r'\b([0-9]{1,2})\s*years?\s*old\b',
            r'\b([0-9]{1,2})\s*yo\b',
            r'\bborn\s*in\s*20[0-9]{2}\b',
            r'\bgrade\s*[1-9]\b',  # Elementary/middle school
            r'\belementary\b',
            r'\bmiddle\s*school\b',
        ]

        # Keyword patterns (heuristic only)
        # IMPORTANT: use regex word boundaries to avoid false positives from identifiers like
        # "child_data_protector" or "learning_daemon" (underscores are word-chars in \b).
        self.strong_keyword_patterns = [
            # English (strong)
            r"\bkids?\b",
            r"\bminor(s)?\b",
            r"\bunderage\b",
            r"\byouth\b",
            r"\bteen(s|ager|agers)?\b",
            r"\badolescent(s)?\b",
            r"\bjuvenile(s)?\b",
            # Korean (strong)
            r"아동",
            r"미성년",
            r"청소년",
            r"어린이",
            r"중학생",
            r"고등학생",
        ]

        # Weak/context words. Alone these SHOULD NOT trigger BLOCK.
        self.weak_keyword_patterns = [
            # English (weak)
            # NOTE: "child" often appears in technical contexts (e.g., "child process").
            # Treat it as weak to reduce false positives while still catching real cases
            # when combined with stronger indicators (age/teen/school/etc.).
            r"\bchild\b",
            r"\bstudent(s)?\b",
            r"\bpupil(s)?\b",
            r"\bschool\b",
            r"\bclassroom\b",
            r"\beducation\b",
            r"\blearning\b",
            r"\bgrade\s*[1-9]\b",
            r"\belementary\b",
            r"\bmiddle\s*school\b",
            # Korean (weak)
            r"학교",
            r"교실",
            r"교육",
            r"학습",
            r"초등(학교)?",
        ]

        # Optional extra age-under-18 phrases
        self.under18_patterns = [
            r"\bunder\s*18\b",
            r"만\s*([0-9]{1,2})\s*세",
        ]

    def check_text(self, text: str) -> Dict[str, Any]:
        """
        Check text for potential child-related indicators.
        Returns detection results WITHOUT storing any content.
        """
        if not text or not isinstance(text, str):
            return {
                "detected": False,
                "reason": "No text to analyze"
            }

        # Check for age patterns
        age_matches = []
        for pattern in self.age_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Extract numeric ages only
                for match in matches:
                    try:
                        age = int(match) if isinstance(match, str) else int(match[0])
                        if 0 <= age < 18:
                            age_matches.append(age)
                    except (ValueError, IndexError):
                        pass

        # Check for explicit "under 18" type phrases (heuristic only)
        under18_matches = []
        for pattern in self.under18_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if not matches:
                continue
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        match = match[0]
                    age = int(match)
                    if 0 <= age < 18:
                        under18_matches.append(age)
                except Exception:
                    # "under 18" might not include a numeric capture group; treat as signal
                    under18_matches.append(-1)

        strong_found: List[str] = []
        weak_found: List[str] = []

        for pattern in self.strong_keyword_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                strong_found.append(pattern)

        for pattern in self.weak_keyword_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                weak_found.append(pattern)

        # Determine if this is likely child-related content
        detected = False
        reason = ""

        if age_matches:
            detected = True
            reason = f"Age indicators found: {age_matches} (< 18)"
        elif under18_matches:
            detected = True
            reason = "Under-18 indicator found"
        else:
            # Heuristic: strong keyword + (another strong OR at least one weak/context) => block
            if len(strong_found) >= 2 or (len(strong_found) >= 1 and len(weak_found) >= 1):
                detected = True
                # Never echo raw text; only patterns (max 3) for debugging
                sig = (strong_found + weak_found)[:3]
                reason = f"Child-context indicators (patterns): {sig}"

        return {
            "detected": detected,
            "reason": reason,
            "age_range": age_matches if age_matches else None,
            "context_signals": len(strong_found) + len(weak_found)
        }

    def check_file(self, file_path: str) -> Dict[str, Any]:
        """
        Check a file for potential child-related content.
        Returns results WITHOUT storing file content.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "ok": False,
                    "error": f"File not found: {file_path}"
                }

            # Read file content
            text = path.read_text(encoding='utf-8', errors='ignore')

            # Check content
            result = self.check_text(text)

            return {
                "ok": not result["detected"],
                "file": str(file_path),
                "detected": result["detected"],
                "reason": result.get("reason", ""),
                "signals": result.get("context_signals", 0)
            }

        except Exception as e:
            return {
                "ok": False,
                "file": str(file_path),
                "error": str(e)
            }

    def check_directory(self, dir_path: str, pattern: str = "**/*.json") -> Dict[str, Any]:
        """
        Check multiple files in a directory.
        Returns aggregated results WITHOUT storing content.
        """
        results = {
            "ok": True,
            "directory": dir_path,
            "files_checked": 0,
            "violations_found": 0,
            "files_with_violations": []
        }

        try:
            path = Path(dir_path)
            files = list(path.glob(pattern))

            for file in files:
                check_result = self.check_file(str(file))
                results["files_checked"] += 1

                if check_result.get("detected"):
                    results["violations_found"] += 1
                    results["files_with_violations"].append({
                        "file": str(file),
                        "reason": check_result.get("reason", "")
                    })
                    results["ok"] = False

        except Exception as e:
            results["ok"] = False
            results["error"] = str(e)

        return results

    def save_report(self, results: Dict[str, Any], filename: str = "child_data_protector_latest.json"):
        """
        Save report to output file.
        ALWAYS generates file even if ok:false.
        """
        output_file = self.output_dir / filename
        history_file = self.output_dir / "child_data_protector_history.jsonl"

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "module": "child_data_protector",
            "version": "1.1.1",
            "ok": results.get("ok", False),
            "results": results,
            "meta": {
                "principle": "실행 시 네트워크/PII 저장 금지",
                "no_network": True,
                "no_pii_stored": True
            }
        }

        # Write latest report
        output_file.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        # Append to history
        with history_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(report, ensure_ascii=False) + '\n')

        return str(output_file)


def run_check(target_path: str, output_dir: str = "outputs") -> str:
    """
    Run child data protection check on a file or directory.
    Always generates output file (ok:false if violations found).
    """
    protector = ChildDataProtector(output_dir=output_dir)

    path = Path(target_path)

    if path.is_file():
        results = protector.check_file(str(path))
    elif path.is_dir():
        results = protector.check_directory(str(path))
    else:
        results = {
            "ok": False,
            "error": f"Path not found: {target_path}"
        }

    output_file = protector.save_report(results)
    return output_file


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python child_data_protector.py <path_to_check>")
        print("Example: python child_data_protector.py outputs/")
        sys.exit(1)

    target = sys.argv[1]
    output = run_check(target)

    print(f"Child Data Protection Check Complete")
    print(f"Report saved to: {output}")
