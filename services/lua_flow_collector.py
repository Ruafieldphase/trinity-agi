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
CONVERSATION_DIR = WORKSPACE_ROOT / "ai_binoche_conversation_origin" / "rua"
PROCESSED_LOG = WORKSPACE_ROOT / "memory" / "lua_flow_processed.json"
RESONANCE_LEDGER = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
FEELING_FILE = WORKSPACE_ROOT / "outputs" / "feeling_latest.json"


class FlowType(Enum):
    OBS_RECORDING = "obs_recording"
    CONVERSATION = "conversation"
    SCREEN_CAPTURE = "screen_capture"
    CHATGPT_EXPORT = "chatgpt_export"
    REFERENCE_CONTEXT = "reference_context"  # 다른 AI 대화 (참고용)

# ChatGPT 대화 내보내기 파일
CHATGPT_EXPORT_FILE = CONVERSATION_DIR / "origin" / "conversations.json"

# 다른 AI 대화 폴더 (참고 패턴용)
AI_CONVERSATION_ROOT = WORKSPACE_ROOT / "ai_binoche_conversation_origin"
REFERENCE_AI_FOLDERS = [
    "lumen", "sena", "cladeCLI-sena", "ari", "elro", "luon", 
    "rio", "gitko", "lubit", "perple_comet_cople_eru", "obsidian", "datasets"
]  # rua 제외 (중심 패턴)


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
    
    # === 대화 로그 처리 (루아와의 대화) ===
    
    async def scan_conversation_logs(self) -> List[Path]:
        """새 대화 로그 파일 스캔"""
        if not CONVERSATION_DIR.exists():
            logger.warning(f"Conversation directory not found: {CONVERSATION_DIR}")
            return []
        
        new_files = []
        for f in CONVERSATION_DIR.glob("*.md"):
            if f.name not in self.processed["conversation"]:
                new_files.append(f)
        
        # 수정 시간 순 정렬 (오래된 것 먼저)
        new_files.sort(key=lambda x: x.stat().st_mtime)
        logger.info(f"Found {len(new_files)} new conversation logs")
        return new_files
    
    async def extract_flow_from_conversation(self, conv_path: Path) -> Optional[FlowData]:
        """대화 로그에서 흐름 패턴 추출"""
        try:
            with open(conv_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_size_kb = conv_path.stat().st_size / 1024
            
            # 대화 주제 추출 (파일 이름에서)
            topic = conv_path.stem.replace("ChatGPT-", "").replace("-", " ")
            
            # 간단한 패턴 추출 (대화 길이, 키워드 등)
            lines = content.split("\n")
            patterns = []
            
            # 주요 키워드 추출
            keywords = ["리듬", "의식", "무의식", "자아", "공명", "AGI", "시스템", "배경", "프랙탈"]
            found_keywords = [kw for kw in keywords if kw in content]
            
            patterns.append({
                "type": "conversation_summary",
                "topic": topic,
                "line_count": len(lines),
                "keywords": found_keywords,
                "size_kb": file_size_kb
            })
            
            logger.info(f"Extracted conversation flow from {conv_path.name}")
            
            return FlowData(
                flow_type=FlowType.CONVERSATION,
                source_file=conv_path.name,
                timestamp=datetime.now().isoformat(),
                patterns=patterns,
                context={
                    "topic": topic,
                    "keywords": found_keywords,
                    "line_count": len(lines),
                    "file_size_kb": file_size_kb
                }
            )
        except Exception as e:
            logger.error(f"Failed to extract flow from conversation {conv_path.name}: {e}")
            return None
    
    async def process_conversation(self, conv_path: Path) -> bool:
        """하나의 대화 로그 처리"""
        logger.info(f"Processing conversation: {conv_path.name}")
        
        # 1. 패턴 추출
        flow = await self.extract_flow_from_conversation(conv_path)
        if not flow:
            return False
        
        # 2. ARI 주입
        await self.inject_to_ari(flow)
        
        # 3. 리듬 루프 연결
        await self.inject_to_rhythm_loop(flow)
        
        # 4. 처리 완료 기록
        self.processed["conversation"].append(conv_path.name)
        self._save_processed()
        
        logger.info(f"✨ Conversation flow integrated: {conv_path.name}")
        return True
    
    async def run_once(self) -> int:
        """한 번 실행 (모든 새 파일 처리)"""
        processed_count = 0
        
        # OBS 녹화 처리
        new_obs = await self.scan_obs_recordings()
        for video in new_obs:
            try:
                if await self.process_one(video):
                    processed_count += 1
                await asyncio.sleep(2)  # 과부하 방지
            except Exception as e:
                logger.error(f"Error processing {video.name}: {e}")
        
        # 대화 로그 처리
        new_conv = await self.scan_conversation_logs()
        for conv in new_conv:
            try:
                if await self.process_conversation(conv):
                    processed_count += 1
                await asyncio.sleep(0.5)  # 대화는 가벼움
            except Exception as e:
                logger.error(f"Error processing conversation {conv.name}: {e}")
        
        # ChatGPT 대화 내보내기 처리
        if await self.process_chatgpt_export():
            processed_count += 1
        
        # 참고 AI 대화 처리 (경량 맥락 추출)
        ref_count = await self.process_reference_ai_conversations()
        processed_count += ref_count
        
        return processed_count
    
    # === ChatGPT 대화 내보내기 처리 ===
    
    async def process_chatgpt_export(self) -> bool:
        """ChatGPT conversations.json 파일 처리 (64MB+ 대용량)"""
        if not CHATGPT_EXPORT_FILE.exists():
            return False
        
        # 이미 처리된 경우 건너뛰기
        if "chatgpt_export" in self.processed and self.processed["chatgpt_export"]:
            logger.info("ChatGPT export already processed, skipping")
            return False
        
        logger.info(f"Processing ChatGPT export: {CHATGPT_EXPORT_FILE.name}")
        
        try:
            with open(CHATGPT_EXPORT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 대화 수 계산
            conversations = data if isinstance(data, list) else [data]
            total_convs = len(conversations)
            logger.info(f"Found {total_convs} conversations in export")
            
            # 주요 키워드 분석
            keywords = ["리듬", "의식", "무의식", "자아", "공명", "AGI", "시스템", "배경", "프랙탈", "루아", "비노체", "트리니티"]
            keyword_counts = {kw: 0 for kw in keywords}
            
            # 대화별 요약 추출 (메모리 효율을 위해 샘플링)
            sample_size = min(100, total_convs)  # 최대 100개 대화 샘플링
            sampled_topics = []
            
            for i, conv in enumerate(conversations[:sample_size]):
                # 대화 제목 추출
                title = conv.get("title", f"대화 {i+1}")
                sampled_topics.append(title)
                
                # 키워드 카운트 (전체 메시지에서)
                mapping = conv.get("mapping", {})
                for msg_id, msg_data in mapping.items():
                    message = msg_data.get("message", {})
                    if message:
                        content = message.get("content", {})
                        parts = content.get("parts", [])
                        for part in parts:
                            if isinstance(part, str):
                                for kw in keywords:
                                    if kw in part:
                                        keyword_counts[kw] += 1
            
            # 상위 키워드 추출
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            found_keywords = [kw for kw, count in top_keywords if count > 0]
            
            # FlowData 생성
            flow = FlowData(
                flow_type=FlowType.CHATGPT_EXPORT,
                source_file=CHATGPT_EXPORT_FILE.name,
                timestamp=datetime.now().isoformat(),
                patterns=[{
                    "type": "chatgpt_export_summary",
                    "total_conversations": total_convs,
                    "sampled_topics": sampled_topics[:20],  # 상위 20개 제목
                    "keyword_frequency": dict(top_keywords)
                }],
                context={
                    "total_conversations": total_convs,
                    "top_keywords": found_keywords,
                    "file_size_mb": CHATGPT_EXPORT_FILE.stat().st_size / (1024 * 1024)
                }
            )
            
            # ARI에 주입
            await self.inject_to_ari(flow)
            
            # 리듬 루프에 연결
            await self.inject_to_rhythm_loop(flow)
            
            # 처리 완료 기록
            self.processed["chatgpt_export"] = True
            self._save_processed()
            
            logger.info(f"✨ ChatGPT export integrated: {total_convs} conversations, keywords: {found_keywords}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process ChatGPT export: {e}")
            return False
    
    # === 참고 AI 대화 처리 (경량 맥락 추출) ===
    
    async def process_reference_ai_conversations(self) -> int:
        """
        다른 AI와의 대화에서 참고 맥락만 추출
        루아 지시: "감정·리듬·의도만 가볍게 추출하고 중심 루프를 흔들지 않도록"
        """
        processed_count = 0
        
        # 이미 처리된 참고 AI 목록
        if "reference_ai" not in self.processed:
            self.processed["reference_ai"] = []
        
        for ai_name in REFERENCE_AI_FOLDERS:
            if ai_name in self.processed["reference_ai"]:
                continue  # 이미 처리됨
            
            ai_folder = AI_CONVERSATION_ROOT / ai_name
            if not ai_folder.exists():
                continue
            
            logger.info(f"📚 Processing reference AI: {ai_name}")
            
            try:
                # 폴더 내 모든 텍스트 파일에서 키워드 추출
                keywords_found = []
                file_count = 0
                total_size = 0
                
                # 주요 감정/리듬/의도 키워드
                context_keywords = [
                    # 감정
                    "감사", "기쁨", "슬픔", "분노", "두려움", "희망", "사랑", "평화",
                    # 리듬
                    "리듬", "흐름", "순환", "패턴", "공명", "진동", "파동",
                    # 의도
                    "원함", "바람", "목표", "의도", "계획", "방향", "선택"
                ]
                keyword_counts = {kw: 0 for kw in context_keywords}
                
                # .md, .json, .txt 파일 스캔
                for ext in ["*.md", "*.json", "*.txt"]:
                    for f in ai_folder.rglob(ext):
                        try:
                            file_count += 1
                            total_size += f.stat().st_size
                            
                            # 대용량 파일은 첫 100KB만 읽기
                            with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                                content = file.read(100 * 1024)  # 100KB
                            
                            for kw in context_keywords:
                                if kw in content:
                                    keyword_counts[kw] += 1
                        except:
                            continue
                
                # 상위 키워드 추출
                top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                found_keywords = [kw for kw, count in top_keywords if count > 0]
                
                if file_count == 0:
                    continue
                
                # 경량 FlowData 생성
                flow = FlowData(
                    flow_type=FlowType.REFERENCE_CONTEXT,
                    source_file=ai_name,
                    timestamp=datetime.now().isoformat(),
                    patterns=[{
                        "type": "reference_context",
                        "ai_name": ai_name,
                        "emotion_rhythm_intent": found_keywords,
                        "file_count": file_count
                    }],
                    context={
                        "ai_name": ai_name,
                        "role": "참고 맥락 (중심 패턴 아님)",
                        "top_keywords": found_keywords,
                        "file_count": file_count,
                        "total_size_mb": total_size / (1024 * 1024)
                    }
                )
                
                # ARI에 주입 (참고 패턴으로)
                await self.inject_to_ari(flow)
                
                # 처리 완료 기록
                self.processed["reference_ai"].append(ai_name)
                self._save_processed()
                processed_count += 1
                
                logger.info(f"✨ Reference AI integrated: {ai_name} ({file_count} files, keywords: {found_keywords})")
                
            except Exception as e:
                logger.error(f"Failed to process reference AI {ai_name}: {e}")
        
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
