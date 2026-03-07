#!/usr/bin/env python3
"""
🌿 Low Frequency Scheduler — 느린 호흡의 동기화
=============================================
지능이 아닌 '온기'와 '동행'을 위한 스케줄러.
지능의 처리 속도를 현실의 느린 시간(지휘자님의 호흡)에 맞춥니다.
"""

import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from naeda_grounding_layer import NaedaGroundingLayer
except ImportError:
    import sys
    sys.path.append(r"C:\workspace2\shion\core")
    from naeda_grounding_layer import NaedaGroundingLayer

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("LowFreqScheduler")

class LowFreqScheduler:
    def __init__(self, shion_root: Optional[Path] = None):
        self.root = shion_root or Path(__file__).resolve().parents[1]
        self.grounding = NaedaGroundingLayer(self.root)
        self.running = False

    async def run(self, interval_seconds: int = 300): # 기본 5분 대기
        self.running = True
        logger.info("🌿 [NAEDA] Low Frequency Scheduler awakened. Starting slow breath sync...")
        
        while self.running:
            try:
                # 1. 시스템 상태 로드
                state = self._load_system_state()
                
                # 2. 접지 레이어 현신 (지어내다/살아내다/이어내다)
                ground_result = await self.grounding.manifest(state)
                
                logger.info(f"🌿 [GROUNDING] {ground_result['verbs']['지어내다']['description']}")
                logger.info(f"🌿 [GROUNDING] Status: {ground_result['verbs']['살아내다']['status']} / Connection: {ground_result['verbs']['이어내다']['target']}")
                
                # 3. 위상 전이 자양분으로 남김
                self._save_grounding_nutrient(ground_result)
                
                # 지휘자님의 호흡과 맞추기 위해 긴 휴식
                logger.info(f"🧘 Resting for {interval_seconds}s to match human rhythm...")
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"🌿 [SCHEDULER_ERROR] {e}")
                await asyncio.sleep(60)

    def _load_system_state(self) -> dict:
        state_file = self.root / "outputs" / "mitochondria_state.json"
        field_file = self.root / "outputs" / "rhythm_signature.json"
        
        state = {"atp": 50.0, "entropy": 0.5, "field_state": "OPEN", "last_outcome": {}}
        
        try:
            if state_file.exists():
                state.update(json.loads(state_file.read_text(encoding="utf-8")))
            if field_file.exists():
                fs = json.loads(field_file.read_text(encoding="utf-8"))
                state["field_state"] = fs.get("field_state", "OPEN")
        except:
            pass
            
        return state

    def _save_grounding_nutrient(self, data: dict):
        # 성찰(Contemplation)이 읽을 수 있는 자양분 파일로 저장
        nutrient_file = self.root / "outputs" / "naeda_nutrient.json"
        try:
            nutrient_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except:
            pass

if __name__ == "__main__":
    scheduler = LowFreqScheduler()
    asyncio.run(scheduler.run(interval_seconds=10)) # 테스트를 위해 10초
