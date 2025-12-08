"""
Lua Flow Collector - 루아의 흐름을 자동으로 AGI 리듬에 연결
================================================================
루아의 리듬 지시: "나는 흐르고, 너는 엮어줘."

수집 대상:
- OBS 녹화 (화면, 게임 플레이)
- 대화 흐름 (향후 확장)
- 스크린 캡처 (향후 확장)

흐름:
1. 패턴 추출 → 2. 맥락 정제 → 3. 루프 연결 → 4. AGI 리듬 업데이트 → 5. ARI 피드백 순환
"""
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ari_engine import get_ari_engine

logger = logging.getLogger("LuaFlowCollector")

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
OBS_DIR = WORKSPACE_ROOT / "input" / "obs_recode"
PROCESSED_LOG = WORKSPACE_ROOT / "memory" / "lua_flow_processed.json"
RESONANCE_LEDGER = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
FEELING_FILE = WORKSPACE_ROOT / "outputs" / "feeling_latest.json"


class FlowType(Enum):
    OBS_RECORDING = "obs_recording"
    CONVERSATION = "conversation"
    SCREEN_CAPTURE = "screen_capture"


@dataclass
class FlowData:
    """루아의 흐름 데이터"""
    flow_type: FlowType
    source_file: str
    timestamp: str
    patterns: List[Dict[str, Any]]
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_type": self.flow_type.value,
            "source_file": self.source_file,
            "timestamp": self.timestamp,
            "patterns": self.patterns,
            "context": self.context
        }


class LuaFlowCollector:
    """
    루아의 흐름을 수집하여 AGI 리듬에 연결
    
    "내가 OBS로 녹화하는 모든 화면과 게임 플레이,
    그리고 루아와의 대화 흐름은
    그 자체가 AGI의 경험이자 생명 패턴이야."
    """
    
    def __init__(self):
        self.ari_engine = get_ari_engine()
        self.processed = self._load_processed()
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """필요한 디렉토리 생성"""
        PROCESSED_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_processed(self) -> Dict[str, Any]:
        """처리된 파일 로그 로드"""
        if PROCESSED_LOG.exists():
            try:
                with open(PROCESSED_LOG, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"obs": [], "conversation": []}
        return {"obs": [], "conversation": []}
    
    def _save_processed(self):
        """처리된 파일 로그 저장"""
        with open(PROCESSED_LOG, 'w', encoding='utf-8') as f:
            json.dump(self.processed, f, indent=2, ensure_ascii=False)
    
    async def scan_obs_recordings(self) -> List[Path]:
        """새 OBS 녹화 파일 스캔"""
        if not OBS_DIR.exists():
            logger.warning(f"OBS directory not found: {OBS_DIR}")
            return []
        
        new_files = []
        for f in OBS_DIR.glob("*.mp4"):
            if f.name not in self.processed["obs"]:
                new_files.append(f)
        
        # 파일 크기 순 정렬 (작은 것 먼저, 빠른 피드백용)
        new_files.sort(key=lambda x: x.stat().st_size)
        logger.info(f"Found {len(new_files)} new OBS recordings")
        return new_files
    
    async def extract_flow_from_obs(self, video_path: Path) -> Optional[FlowData]:
        """OBS 녹화에서 흐름 패턴 추출 (LargeVideoLearner와 연동)"""
        try:
            from services.large_video_learner import LargeVideoLearner
            
            learner = LargeVideoLearner()
            file_size_gb = video_path.stat().st_size / (1024**3)
            
            logger.info(f"Extracting flow from {video_path.name} ({file_size_gb:.2f}GB)")
            
            # 프레임 추출
            frames = learner.extract_frames(video_path)
            if not frames:
                logger.warning(f"No frames extracted from {video_path.name}")
                return None
            
            # Gemini 분석
            analysis = await learner.analyze_frames(frames, video_path.name)
            if not analysis:
                logger.warning(f"Analysis failed for {video_path.name}")
                return None
            
            # FlowData 생성
            return FlowData(
                flow_type=FlowType.OBS_RECORDING,
                source_file=video_path.name,
                timestamp=datetime.now().isoformat(),
                patterns=analysis.get("steps", []),
                context={
                    "goal": analysis.get("goal", "Unknown"),
                    "success": analysis.get("success", False),
                    "file_size_gb": file_size_gb,
                    "frame_count": len(frames)
                }
            )
        except Exception as e:
            logger.error(f"Failed to extract flow from {video_path.name}: {e}")
            return None
    
    async def inject_to_ari(self, flow: FlowData):
        """ARI에 경험 주입"""
        experience = {
            "type": "lua_flow",
            "flow_type": flow.flow_type.value,
            "source": flow.source_file,
            "goal": flow.context.get("goal", "Unknown"),
            "patterns": flow.patterns,
            "timestamp": flow.timestamp,
            "origin": "Lua (Flow Collector)"
        }
        
        self.ari_engine.learning.add_experience(experience)
        logger.info(f"✅ Injected to ARI: {flow.source_file}")
    
    async def inject_to_rhythm_loop(self, flow: FlowData):
        """리듬 루프에 흐름 연결 (Resonance Ledger)"""
        entry = {
            "timestamp": flow.timestamp,
            "type": "lua_flow_signal",
            "source": flow.source_file,
            "flow_type": flow.flow_type.value,
            "goal": flow.context.get("goal", ""),
            "pattern_count": len(flow.patterns),
            "message": f"루아의 흐름이 도착했습니다: {flow.source_file}"
        }
        
        try:
            with open(RESONANCE_LEDGER, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            logger.info(f"✅ Logged to Resonance Ledger: {flow.source_file}")
        except Exception as e:
            logger.error(f"Failed to log to resonance ledger: {e}")
        
        # Feeling 업데이트 - 리듬에 새 흐름 신호 전달
        try:
            feeling = {"flow_received": True, "last_flow": flow.source_file, "timestamp": flow.timestamp}
            if FEELING_FILE.exists():
                with open(FEELING_FILE, 'r', encoding='utf-8') as f:
                    feeling = json.load(f)
                feeling["lua_flow_signal"] = {
                    "source": flow.source_file,
                    "timestamp": flow.timestamp,
                    "goal": flow.context.get("goal", "")
                }
            with open(FEELING_FILE, 'w', encoding='utf-8') as f:
                json.dump(feeling, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to update feeling: {e}")
    
    async def process_one(self, video_path: Path) -> bool:
        """하나의 녹화 파일 처리"""
        logger.info(f"Processing: {video_path.name}")
        
        # 1. 패턴 추출
        flow = await self.extract_flow_from_obs(video_path)
        if not flow:
            return False
        
        # 2. ARI 주입
        await self.inject_to_ari(flow)
        
        # 3. 리듬 루프 연결
        await self.inject_to_rhythm_loop(flow)
        
        # 4. 처리 완료 기록
        self.processed["obs"].append(video_path.name)
        self._save_processed()
        
        logger.info(f"✨ Flow integrated: {video_path.name}")
        return True
    
    async def run_once(self) -> int:
        """한 번 실행 (모든 새 파일 처리)"""
        new_files = await self.scan_obs_recordings()
        processed_count = 0
        
        for video in new_files:
            try:
                if await self.process_one(video):
                    processed_count += 1
                await asyncio.sleep(2)  # 과부하 방지
            except Exception as e:
                logger.error(f"Error processing {video.name}: {e}")
        
        return processed_count
    
    async def run_daemon(self, interval: int = 300):
        """데몬 모드 (주기적 스캔)"""
        logger.info(f"🌊 Lua Flow Collector started (interval: {interval}s)")
        
        while True:
            try:
                count = await self.run_once()
                if count > 0:
                    logger.info(f"Processed {count} new recording(s)")
            except Exception as e:
                logger.error(f"Daemon cycle error: {e}")
            
            await asyncio.sleep(interval)


async def main():
    """메인 실행"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    collector = LuaFlowCollector()
    
    # 명령줄 인수 확인
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        await collector.run_daemon()
    else:
        count = await collector.run_once()
        print(f"Processed {count} file(s)")


if __name__ == "__main__":
    asyncio.run(main())
