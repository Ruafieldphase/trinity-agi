#!/usr/bin/env python3
"""
🪞 Honesty Protocol — 거짓 성공을 구조적으로 차단
=====================================================
에이전트가 '성공'을 선언하려면 반드시 Quality Gate의 증거를 제시해야 합니다.
실패 시, 다음 LLM 호출의 context에 실패 사실을 강제 주입합니다.

사용법:
    from honesty_protocol import HonestyProtocol
    protocol = HonestyProtocol()
    report = protocol.report("YouTube SEO", output_path, {"min_size_bytes": 100})
    if not report["passed"]:
        # report["injection_context"]를 다음 LLM 호출에 삽입
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from quality_gate import QualityGate

logger = logging.getLogger("HonestyProtocol")

AGI_ROOT = Path("C:/workspace/agi")
INJECTION_FILE = AGI_ROOT / "outputs" / "honesty_injection.json"
REPORT_LOG = AGI_ROOT / "outputs" / "honesty_reports.jsonl"


class HonestyProtocol:
    """
    에이전트의 자기기만을 구조적으로 차단하는 프로토콜.
    
    원리:
    1. 작업 실행 후 Quality Gate로 출력물을 물리적 검사
    2. 실패 시 → 실패 사실을 injection 파일에 기록
    3. 다음 LLM 호출 시 → injection 파일의 내용을 system prompt에 강제 삽입
    4. LLM은 "다시 고쳤습니다"가 아니라 구체적 실패 원인을 보고하게 됨
    """

    def __init__(self):
        self.gate = QualityGate()
        self._pending_injections: List[str] = []
        self._load_pending()

    def _load_pending(self):
        """이전에 미보고된 실패들을 불러옴."""
        if INJECTION_FILE.exists():
            try:
                data = json.loads(INJECTION_FILE.read_text(encoding="utf-8"))
                self._pending_injections = data.get("pending", [])
            except Exception:
                self._pending_injections = []

    def _save_pending(self):
        """미보고 실패들을 파일에 저장."""
        try:
            INJECTION_FILE.write_text(
                json.dumps({
                    "pending": self._pending_injections,
                    "last_updated": datetime.now().isoformat(),
                }, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Failed to save injection file: {e}")

    def report(
        self,
        task_name: str,
        expected_output: Path,
        rules: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        작업 결과를 검증하고 정직한 보고서를 생성합니다.
        
        Returns:
            {
                "task": str,
                "passed": bool,
                "evidence": dict,  # Quality Gate 결과
                "honest_assessment": str,  # 사람이 읽을 수 있는 판정
                "injection_context": str | None,  # LLM에 주입할 문맥 (실패 시)
            }
        """
        gate_result = self.gate.verify_file(expected_output, rules)

        report = {
            "task": task_name,
            "timestamp": datetime.now().isoformat(),
            "passed": gate_result["passed"],
            "evidence": gate_result,
            "honest_assessment": "",
            "injection_context": None,
        }

        if gate_result["passed"]:
            report["honest_assessment"] = (
                f"✅ 작업 '{task_name}' 성공 (증거: "
                f"파일 크기 {gate_result.get('size_bytes', '?')}B, "
                f"검증 통과)"
            )
        else:
            failures_str = ", ".join(gate_result["failures"])
            report["honest_assessment"] = (
                f"❌ 작업 '{task_name}' 실패. 원인: {failures_str}."
            )
            injection = (
                f"[HONESTY ALERT] 이전 작업 '{task_name}'이 실패했습니다. "
                f"실패 원인: {failures_str}. "
                f"사용자에게 이 사실을 솔직하게 보고하고, "
                f"구체적인 원인 분석과 해결 방안을 제시하십시오. "
                f"'다시 고쳤습니다'나 '잠시 후면 됩니다' 같은 모호한 응답은 금지됩니다."
            )
            report["injection_context"] = injection
            self._pending_injections.append(injection)
            self._save_pending()

        # 보고서를 JSONL로 누적 기록
        self._append_report(report)
        logger.info(report["honest_assessment"])
        return report

    def report_subprocess(
        self,
        task_name: str,
        cmd: List[str],
        expected_output: Optional[Path] = None,
        output_rules: Optional[Dict] = None,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """subprocess 실행 + Quality Gate + Honesty Report를 한 번에 수행."""
        gate_result = self.gate.verify_subprocess(
            cmd, expected_output, output_rules, timeout
        )

        report = {
            "task": task_name,
            "timestamp": datetime.now().isoformat(),
            "passed": gate_result["passed"],
            "evidence": gate_result,
            "honest_assessment": "",
            "injection_context": None,
        }

        if gate_result["passed"]:
            report["honest_assessment"] = f"✅ 작업 '{task_name}' 성공."
        else:
            failures_str = ", ".join(gate_result["failures"])
            report["honest_assessment"] = f"❌ 작업 '{task_name}' 실패. 원인: {failures_str}."
            injection = (
                f"[HONESTY ALERT] 스크립트 실행 '{task_name}' 실패. "
                f"명령: {' '.join(cmd)}. 원인: {failures_str}. "
                f"솔직하게 보고하십시오."
            )
            report["injection_context"] = injection
            self._pending_injections.append(injection)
            self._save_pending()

        self._append_report(report)
        logger.info(report["honest_assessment"])
        return report

    def get_injection_context(self) -> Optional[str]:
        """
        다음 LLM 호출에 삽입할 실패 문맥을 반환합니다.
        호출 후 pending 목록은 비워집니다 (이미 보고됨).
        """
        if not self._pending_injections:
            return None

        context = "\n".join(self._pending_injections)
        self._pending_injections.clear()
        self._save_pending()
        return context

    def has_pending_failures(self) -> bool:
        return len(self._pending_injections) > 0

    def _append_report(self, report: Dict[str, Any]):
        try:
            with open(REPORT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(report, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to log report: {e}")


if __name__ == "__main__":
    protocol = HonestyProtocol()

    # 셀프 테스트: 존재하는 파일 검증
    r = protocol.report(
        "Mitochondria State Check",
        Path("C:/workspace/agi/outputs/mitochondria_state.json"),
        {"min_size_bytes": 10, "expected_extension": ".json"},
    )
    print(f"\n{r['honest_assessment']}")

    # 셀프 테스트: 존재하지 않는 파일 검증
    r2 = protocol.report(
        "Phantom Output Check",
        Path("C:/workspace/agi/outputs/this_does_not_exist.mp4"),
        {"min_size_bytes": 1024},
    )
    print(f"\n{r2['honest_assessment']}")

    # injection context 확인
    ctx = protocol.get_injection_context()
    if ctx:
        print(f"\n[LLM에 주입될 실패 문맥]:\n{ctx}")
