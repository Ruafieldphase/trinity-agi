#!/usr/bin/env python3
"""
🫀 Body Context Builder — 시스템 '체감 상태'를 LLM에 연결
==========================================================
ATP, Entropy, CPU 등의 수치를 읽어서 LLM의 system prompt에
주입할 수 있는 문자열로 변환합니다.

이것이 SUNS의 '혈관'입니다 — 장기(ATP/Entropy)와 뇌(LLM)를 연결합니다.

사용법:
    from body_context_builder import BodyContextBuilder
    builder = BodyContextBuilder()
    context_str = builder.build()
    # → 이 문자열을 LLM 호출의 system/context에 삽입
"""

import json
import psutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("BodyContext")

AGI_ROOT = Path("C:/workspace/agi")
OUTPUTS_DIR = AGI_ROOT / "outputs"


class BodyContextBuilder:
    """
    시스템의 물리적 상태를 읽어 LLM 프롬프트에 주입할 문맥을 생성합니다.
    
    이 클래스가 해결하는 문제:
    - ATP와 Entropy가 JSON에만 기록되고 LLM에 전달되지 않던 '분리된 장기' 문제
    - 시스템의 물리적 한계를 LLM이 인식하지 못하던 '감각 부재' 문제
    """

    def __init__(self):
        self.mito_path = OUTPUTS_DIR / "mitochondria_state.json"
        self.entropy_path = OUTPUTS_DIR / "body_entropy_latest.json"
        self.honesty_path = OUTPUTS_DIR / "honesty_injection.json"

    def _read_json_safe(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def read_body_state(self) -> Dict[str, Any]:
        """모든 신체 지표를 하나의 dict로 수집합니다."""
        mito = self._read_json_safe(self.mito_path)
        entropy = self._read_json_safe(self.entropy_path)

        # 실시간 시스템 지표
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()

        return {
            "atp_level": mito.get("atp_level",
                         mito.get("momentum", mito.get("symmetry", 0.5)) * 50),
            "atp_status": mito.get("status", mito.get("integrity_status", "unknown")),
            "entropy": entropy.get("entropy", 0.0),
            "entropy_state": entropy.get("state", "unknown"),
            "cpu_percent": cpu_percent,
            "memory_percent": mem.percent,
            "memory_available_gb": round(mem.available / (1024**3), 1),
            "timestamp": datetime.now().isoformat(),
        }

    def build(self) -> str:
        """
        LLM system prompt에 삽입할 '체감 상태' 문자열을 생성합니다.
        
        Returns:
            사람이 읽을 수 있는 시스템 상태 요약 (2-5줄)
        """
        state = self.read_body_state()
        lines = []

        # --- ATP (에너지) ---
        atp = state["atp_level"]
        if isinstance(atp, (int, float)):
            if atp < 20:
                lines.append(f"⚡ 에너지 위험: ATP {atp:.0f}/100. 간결하게 답하고 새 작업을 시작하지 마시오.")
            elif atp < 40:
                lines.append(f"⚡ 에너지 부족: ATP {atp:.0f}/100. 필수 작업에만 집중하시오.")
            elif atp > 80:
                lines.append(f"⚡ 에너지 충분: ATP {atp:.0f}/100. 창의적 확장 가능.")
            else:
                lines.append(f"⚡ 에너지 안정: ATP {atp:.0f}/100.")

        # --- Entropy (안정성) ---
        entropy = state["entropy"]
        if entropy > 0.7:
            lines.append(f"🌡️ 시스템 불안정: Entropy {entropy:.2f}. 파일 I/O를 최소화하시오.")
        elif entropy > 0.3:
            lines.append(f"🌡️ 시스템 활성: Entropy {entropy:.2f}.")
        # CALM 상태는 언급하지 않음 (노이즈 감소)

        # --- 시스템 자원 ---
        cpu = state["cpu_percent"]
        mem = state["memory_percent"]
        if cpu > 80 or mem > 85:
            lines.append(
                f"🖥️ 자원 경고: CPU {cpu:.0f}%, 메모리 {mem:.0f}%. "
                f"무거운 작업을 지양하시오."
            )

        # --- Honesty injection (미보고 실패) ---
        honesty = self._read_json_safe(self.honesty_path)
        pending = honesty.get("pending", [])
        if pending:
            lines.append(f"🪞 [정직성 경고] 이전 실패 {len(pending)}건이 미보고 상태입니다:")
            for msg in pending[:3]:  # 최대 3개만 표시
                lines.append(f"   - {msg}")

        if not lines:
            return "[BODY STATUS] 모든 시스템 정상."

        return "[BODY STATUS]\n" + "\n".join(lines)

    def build_for_sampling(self) -> Dict[str, Any]:
        """
        시스템 상태에 기반한 LLM 샘플링 파라미터 조정 힌트를 반환합니다.
        
        이것은 실제 temperature를 변경하지 않고, 프롬프트에 행동 지시를 삽입하는 방식입니다.
        (Gemini/Claude의 temperature를 직접 제어할 수 없는 환경에서의 차선책)
        """
        state = self.read_body_state()
        atp = state.get("atp_level", 50)
        entropy = state.get("entropy", 0.3)

        if atp < 20:
            return {
                "suggested_behavior": "minimal",
                "directive": "최소한의 토큰으로 핵심만 전달하시오.",
                "max_output_hint": "짧게",
            }
        elif atp > 80 and entropy < 0.3:
            return {
                "suggested_behavior": "expansive",
                "directive": "충분한 에너지와 안정성이 있습니다. 깊이 있는 사고가 가능합니다.",
                "max_output_hint": "자유",
            }
        else:
            return {
                "suggested_behavior": "balanced",
                "directive": "주어진 작업에 집중하되, 불필요한 확장은 피하시오.",
                "max_output_hint": "적절",
            }


if __name__ == "__main__":
    builder = BodyContextBuilder()

    print("=" * 60)
    print("Raw Body State:")
    state = builder.read_body_state()
    print(json.dumps(state, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print("LLM Context String:")
    print(builder.build())

    print("\n" + "=" * 60)
    print("Sampling Hints:")
    hints = builder.build_for_sampling()
    print(json.dumps(hints, indent=2, ensure_ascii=False))
