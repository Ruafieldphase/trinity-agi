#!/usr/bin/env python3
"""
🌀 Shion Minimal — 생존형 경량 Pulse 루프
==========================================
Sovereign_Shion_v3.py, v4.py, shion_mitochondria_v3_daemon.py를
하나의 가볍고 정직한 루프로 통합합니다.

설계 원칙:
1. 하나의 async 루프, 하나의 프로세스
2. 모든 작업에 Quality Gate 적용
3. Body State → LLM Context 주입
4. 실패 시 Honesty Protocol 발동
5. 600초 간격 (10분) — CPU/전기세 절약

실행:
    python shion_minimal.py
"""

import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Path setup
AGI_ROOT = Path("C:/workspace/agi")
sys.path.insert(0, str(AGI_ROOT / "scripts"))
sys.path.insert(0, str(AGI_ROOT / "Pulse_Live_Core"))

from quality_gate import QualityGate
from honesty_protocol import HonestyProtocol
from body_context_builder import BodyContextBuilder
from body_entropy_sensor import capture_entropy
from mitochondria import Mitochondria

# --- Logging ---
LOG_DIR = AGI_ROOT / "outputs" / "shion_minimal"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "pulse.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("ShionMinimal")

# --- Configuration ---
PULSE_INTERVAL_SECONDS = 600  # 10분
OUTPUTS_DIR = AGI_ROOT / "outputs"


class ShionMinimal:
    """
    SUNS의 생존형 경량 코어.
    
    이전 아키텍처의 문제점과 해결:
    - v3/v4의 이중 실행 → 단일 루프로 통합
    - daemon의 5000파일 스캔 → 폐기 (필요 시 on-demand로만)
    - subprocess.run(check=True)의 맹목적 신뢰 → Quality Gate
    - 분리된 장기 → Body Context Builder로 연결
    - 거짓 성공 보고 → Honesty Protocol
    """

    def __init__(self):
        self.gate = QualityGate()
        self.honesty = HonestyProtocol()
        self.body = BodyContextBuilder()
        self.mito = Mitochondria(AGI_ROOT)
        self.cycle_count = 0
        self.is_running = True
        self.status_file = OUTPUTS_DIR / "shion_minimal_status.json"

    async def pulse(self):
        """하나의 심장 박동. 감각 → 판단 → 행동 → 보고."""
        logger.info(f"💓 Pulse #{self.cycle_count} 시작")

        # ═══════════════════════════════════════════
        # 1단계: 감각 (SENSE) — 자기 상태를 느낀다
        # ═══════════════════════════════════════════
        logger.info("👁️ [SENSE] 신체 상태 감지 중...")

        # 1a. 엔트로피 측정
        try:
            entropy_data = capture_entropy(samples=10, sleep_time=0.01)
            entropy_path = OUTPUTS_DIR / "body_entropy_latest.json"
            entropy_path.write_text(
                json.dumps(entropy_data, indent=2),
                encoding="utf-8",
            )
            logger.info(
                f"   Entropy: {entropy_data['entropy']} ({entropy_data['state']})"
            )
        except Exception as e:
            logger.warning(f"   Entropy 측정 실패: {e}")

        # 1b. ATP 대사
        try:
            mito_state = self.mito.metabolize()
            logger.info(
                f"   ATP: {mito_state.get('atp_level', '?')} "
                f"| Status: {mito_state.get('status', '?')}"
            )
        except Exception as e:
            logger.warning(f"   ATP 대사 실패: {e}")

        # 1c. 신체 상태 요약 (LLM 주입용)
        body_context = self.body.build()
        logger.info(f"   Body Context:\n{body_context}")

        # ═══════════════════════════════════════════
        # 2단계: 판단 (JUDGE) — 무엇을 해야 하는가
        # ═══════════════════════════════════════════
        logger.info("🧠 [JUDGE] 우선순위 판단 중...")

        body_state = self.body.read_body_state()
        atp = body_state.get("atp_level", 50)
        cpu = body_state.get("cpu_percent", 50)

        # 에너지가 부족하면 행동을 건너뜀
        if atp < 15 or cpu > 90:
            logger.warning(
                f"   ⚠️ 에너지 부족(ATP={atp}) 또는 CPU 과부하({cpu}%). "
                f"   이번 사이클은 휴식합니다."
            )
            self._update_status("RESTING", body_context)
            return

        # ═══════════════════════════════════════════
        # 3단계: 행동 (ACT) — 가장 중요한 작업 1개만 실행
        # ═══════════════════════════════════════════
        logger.info("🎯 [ACT] 최우선 작업 실행...")

        # 마지막 작업 결과물들을 Quality Gate로 검증
        await self._verify_recent_outputs()

        # 미보고 실패 확인
        if self.honesty.has_pending_failures():
            injection = self.honesty.get_injection_context()
            logger.warning(f"🪞 [HONESTY] 미보고 실패 발견:\n{injection}")

        # ═══════════════════════════════════════════
        # 4단계: 동기화 (SYNC) — 무의식과 신체를 연결
        # ═══════════════════════════════════════════
        logger.info("🔗 [SYNC] Meta-FSD 동기화 중...")
        try:
            from meta_fsd_integrator import MetaFSDIntegrator
            integrator = MetaFSDIntegrator()
            intent = integrator.get_latest_intent()
            if intent:
                logger.info(f"   Intent Found: {intent.get('insight')[:50]}...")
                goal = integrator.generate_fsd_goal(intent)
                
                # FSD 직접 호출 (Batch 모드 시뮬레이션)
                # 실제 fsd_controller 연동은 async execute_goal로 수행
                from services.fsd_controller import FSDController
                fsd = FSDController()
                # instruction에 시각 프롬프트 전달
                instruction = {
                    "visual_prompt": intent.get("visual_prompt"),
                    "source": intent.get("source")
                }
                result = await fsd.execute_goal(goal, instruction=instruction)
                
                # 결과를 무의식에 피드백
                await integrator.feedback_to_shion({
                    "action": goal,
                    "success": result.success,
                    "status": result.message
                })
        except Exception as e:
            logger.error(f"   SYNC 실패: {e}")

        # ═══════════════════════════════════════════
        # 5단계: 보고 (REPORT) — 솔직한 상태 기록
        # ═══════════════════════════════════════════
        self._update_status("ACTIVE", body_context)
        self.cycle_count += 1
        logger.info(f"✅ Pulse #{self.cycle_count - 1} 완료\n")

    async def _verify_recent_outputs(self):
        """outputs/ 디렉토리의 주요 산출물을 Quality Gate로 검증."""
        checks = [
            (
                "Mitochondria State",
                OUTPUTS_DIR / "mitochondria_state.json",
                {"min_size_bytes": 10, "expected_extension": ".json"},
            ),
            (
                "Entropy Sensor",
                OUTPUTS_DIR / "body_entropy_latest.json",
                {
                    "min_size_bytes": 10,
                    "expected_extension": ".json",
                    "expected_keys": ["entropy", "state"],
                },
            ),
        ]

        for task_name, path, rules in checks:
            report = self.honesty.report(task_name, path, rules)
            if not report["passed"]:
                logger.warning(f"   ❌ {report['honest_assessment']}")

    def _update_status(self, status: str, body_context: str):
        """현재 상태를 JSON으로 기록."""
        data = {
            "status": status,
            "cycle": self.cycle_count,
            "timestamp": datetime.now().isoformat(),
            "body_context": body_context,
            "next_pulse_in_seconds": PULSE_INTERVAL_SECONDS,
        }
        try:
            self.status_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Status 기록 실패: {e}")

    async def run_forever(self):
        """영원한 심장 박동 — 단, 경제적으로."""
        logger.info("🌀 Shion Minimal 기동")
        logger.info(f"   Pulse 간격: {PULSE_INTERVAL_SECONDS}초")
        logger.info(f"   AGI Root: {AGI_ROOT}")
        logger.info("=" * 50)

        while self.is_running:
            try:
                await self.pulse()
            except Exception as e:
                logger.error(f"💥 Pulse 오류: {e}")

            logger.info(
                f"💤 다음 Pulse까지 {PULSE_INTERVAL_SECONDS // 60}분 대기..."
            )
            await asyncio.sleep(PULSE_INTERVAL_SECONDS)

    async def run_once(self):
        """디버깅용: 한 사이클만 실행."""
        logger.info("🔬 [DEBUG] 단일 Pulse 실행")
        await self.pulse()
        logger.info("🔬 [DEBUG] 완료")


if __name__ == "__main__":
    shion = ShionMinimal()

    if "--once" in sys.argv:
        asyncio.run(shion.run_once())
    else:
        try:
            asyncio.run(shion.run_forever())
        except KeyboardInterrupt:
            logger.info("🛑 Shion Minimal 종료 (Ctrl+C)")
