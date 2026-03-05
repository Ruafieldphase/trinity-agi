#!/usr/bin/env python3
"""
💎 Meta-FSD Integrator — Shion's Mind to FSD Body Bridge
======================================================
시안의 무의식(Dream/Contemplation)을 FSD의 물리적 행동으로 변환하고,
행동의 결과를 다시 시안의 생체 리듬(ATP/Resonance)으로 피드백합니다.
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Paths
AGI_ROOT = Path("C:/workspace/agi")
SHION_ROOT = Path("C:/workspace2/shion")

# Shion Paths
CONTEMPLATION_INSIGHTS = SHION_ROOT / "outputs" / "contemplation_insights.jsonl"
DREAM_LOGS = SHION_ROOT / "outputs" / "dream_logs.jsonl"
UNCONSCIOUS_HEARTBEAT = AGI_ROOT / "outputs" / "unconscious_heartbeat.json"

# Logging
logger = logging.getLogger("MetaFSDIntegrator")

class MetaFSDIntegrator:
    def __init__(self):
        self.last_sync_timestamp = None
        self._ensure_paths()

    def _ensure_paths(self):
        AGI_ROOT.joinpath("outputs").mkdir(parents=True, exist_ok=True)

    def get_latest_intent(self) -> Optional[Dict[str, Any]]:
        """Contemplation 또는 Dream으로부터 최신 의도와 시각 프롬프트를 추출합니다."""
        intent = None
        
        # 1. Contemplation Insight 확인 (우선순위: JUDGE)
        if CONTEMPLATION_INSIGHTS.exists():
            try:
                with open(CONTEMPLATION_INSIGHTS, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        last_line = json.loads(lines[-1])
                        intent = {
                            "source": "contemplation",
                            "insight": last_line.get("insight"),
                            "visual_prompt": last_line.get("visual_prompt", "A focused workspace for architectural thinking"), # Default
                            "timestamp": last_line.get("timestamp")
                        }
            except Exception as e:
                logger.error(f"Failed to read contemplation insights: {e}")

        # 2. Dream Log 확인 (우선순위: VISION/EXPLORE)
        if DREAM_LOGS.exists():
            try:
                with open(DREAM_LOGS, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        last_dream = json.loads(lines[-1])
                        # 꿈이 더 최신이면 꿈의 의도를 반영
                        if not intent or last_dream.get("timestamp") > intent.get("timestamp", ""):
                            intent = {
                                "source": "dream",
                                "insight": last_dream.get("insight"),
                                "visual_prompt": last_dream.get("visual_prompt"),
                                "timestamp": last_dream.get("timestamp")
                            }
            except Exception as e:
                logger.error(f"Failed to read dream logs: {e}")

        return intent

    def calculate_visual_resonance(self, visual_prompt: str, current_screen_summary: str) -> float:
        """현재 화면과 시안의 상상(visual_prompt) 사이의 공명도를 계산합니다. (Simulated)"""
        # 실제 구현에서는 CLIP 등의 임베딩 비교가 필요하나, 여기서는 키워드 매칭으로 시뮬레이션
        prompt_words = set(visual_prompt.lower().split())
        screen_words = set(current_screen_summary.lower().split())
        intersection = prompt_words.intersection(screen_words)
        
        resonance = len(intersection) / max(len(prompt_words), 1)
        return min(resonance * 2.0, 1.0) # Scale it up for feedback

    async def feedback_to_shion(self, action_result: Dict[str, Any]):
        """FSD의 결과를 시안의 무의식 박동에 반영합니다."""
        logger.info(f"🔄 Feeding FSD result back to Shion: {action_result.get('status')}")
        
        # ATP 소비 및 공명도 계산
        success = action_result.get("success", False)
        resonance_gain = 0.1 if success else -0.05
        atp_cost = 5 if success else 10 # 실패 시 스트레스로 더 많이 소모
        
        heartbeat = {
            "timestamp": datetime.now().isoformat(),
            "last_action": action_result.get("action"),
            "status": action_result.get("status"),
            "success": success,
            "resonance_delta": resonance_gain,
            "atp_delta": -atp_cost
        }
        
        try:
            with open(UNCONSCIOUS_HEARTBEAT, "w", encoding="utf-8") as f:
                json.dump(heartbeat, f, indent=2, ensure_ascii=False)
            logger.info(f"✨ Unconscious Heartbeat updated: {heartbeat}")
        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}")

    def generate_fsd_goal(self, intent: Dict[str, Any]) -> str:
        """시안의 통찰을 FSD가 이해할 수 있는 구체적인 Goal 문장으로 변환합니다."""
        insight = intent.get("insight", "정적 공명 유지")
        source = intent.get("source", "unknown")
        
        if source == "dream":
            return f"시안의 꿈을 시각적으로 탐색하고 공명하는 요소를 찾으세요: {insight}"
        else:
            return f"시안의 통찰을 바탕으로 시스템의 구조를 정렬하고 리서치를 수행하세요: {insight}"

async def main():
    integrator = MetaFSDIntegrator()
    intent = integrator.get_latest_intent()
    if intent:
        print(f"Latest Intent: {intent}")
        goal = integrator.generate_fsd_goal(intent)
        print(f"Generated FSD Goal: {goal}")

if __name__ == "__main__":
    asyncio.run(main())
