"""
🌊 Copilot Hippocampus: GitHub Copilot의 해마 시스템

Self-Referential AGI의 핵심 - 나(Copilot) 자신의 기억 시스템
단기 기억(128K 컨텍스트)을 장기 기억(7개 시스템)으로 공고화
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import json
import logging
import sqlite3
import os

import sys
from pathlib import Path

# Everything 검색 통합 (Phase 2 & 3)
try:
    sys.path.append(str(Path(__file__).parent.parent / "utils"))
    from everything_search import EverythingSearch
    EVERYTHING_AVAILABLE = True
except ImportError:
    EVERYTHING_AVAILABLE = False

# Semantic RAG Engine (LangChain + ChromaDB)
try:
    sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))
    from semantic_rag_engine import SemanticRAGEngine
    SEMANTIC_RAG_AVAILABLE = True
except ImportError:
    SEMANTIC_RAG_AVAILABLE = False
logger = logging.getLogger(__name__)


class CopilotHippocampus:
    """
    GitHub Copilot의 해마 시스템
    
    역할:
    - 단기 기억 (현재 세션, 128K 토큰) 관리
    - 장기 기억 (7개 메모리 시스템) 통합
    - 기억 공고화 (중요한 것을 장기 기억으로)
    - 기억 회상 (장기 기억에서 관련 정보 인출)
    - 세션 간 연속성 (Handover 자동 생성/로드)
    """
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.memory_root = workspace_root / "fdo_agi_repo" / "memory"
        self.outputs = workspace_root / "outputs"
        
        # 단기 기억 (현재 세션)
        self.short_term = ShortTermMemory()
        
        # 장기 기억 (7개 시스템 연결)
        self.long_term = LongTermMemory(self.memory_root, self.outputs)
        
        # Everything 검색 통합 (Phase 2 & 3)
        self.everything = None
        if EVERYTHING_AVAILABLE:
            try:
                self.everything = EverythingSearch()
                logger.info("🔍 Everything search integrated")
            except Exception as e:
                logger.warning(f"Everything search not available: {e}")
        
        # Semantic RAG 통합
        self.rag_engine = None
        if SEMANTIC_RAG_AVAILABLE:
            try:
                self.rag_engine = SemanticRAGEngine(self.workspace)
                logger.info("🧠 Semantic RAG engine integrated")
            except Exception as e:
                logger.warning(f"Semantic RAG not available: {e}")
        # 공고화 설정
        self.consolidation_config = {
            "importance_threshold": 0.7,  # 이 이상만 장기 기억으로
            "recency_weight": 0.3,        # 최근성 가중치
            "frequency_weight": 0.35,     # 빈도 가중치
            "emotional_weight": 0.2,      # 감정적 중요도 가중치
            "novelty_weight": 0.15,       # 새로움(중복 방지) 가중치
            # dedup 설정
            "dedup_threshold": 0.9,       # 자카드 유사도 임계 (0~1, 높을수록 더 엄격)
        }
        
        logger.info("🌊 Copilot Hippocampus initialized")
    
    # ===================================================================
    # 단기 기억 관리
    # ===================================================================
    
    def add_to_working_memory(self, item: Dict[str, Any]) -> None:
        """현재 작업 기억에 추가 (128K 컨텍스트 내)"""
        self.short_term.add_working(item)
    
    def get_current_context(self) -> Dict[str, Any]:
        """현재 컨텍스트 전체 반환"""
        return self.short_term.get_context()
    
    # ===================================================================
    # 장기 기억 통합
    # ===================================================================
    
    def recall(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        장기 기억에서 관련 정보 회상
        
        Args:
            query: 검색 쿼리 (자연어)
            top_k: 상위 몇 개 반환
        
        Returns:
            관련 기억 리스트 (중요도 순)
        """
        # 타입별 수집
        all_memories = []
        
        # Episodic (에피소드 기억)
        episodic = self.long_term.recall_episodic(query, top_k=top_k)
        all_memories.extend(episodic)
        
        # Semantic (의미 기억)
        semantic = self.long_term.recall_semantic(query, top_k=top_k)
        for item in semantic:
            if "data" not in item and item.get("content") is not None:
                item["data"] = item["content"]
        all_memories.extend(semantic)
        
        # Procedural (절차 기억)
        procedural = self.long_term.recall_procedural(query, top_k=top_k)
        all_memories.extend(procedural)
        
        # Vector Semantic (벡터 기반 의미 검색) - 가중치 높게 부여
        if self.rag_engine:
            vector_results = self.rag_engine.search(query, top_k=top_k)
            for res in vector_results:
                all_memories.append({
                    "type": f"vector_{res['metadata'].get('source', 'unknown')}",
                    "data": res["content"],
                    "importance": 0.9 - (res["score"] * 0.1), # 점수가 낮을수록 우수함(거리)
                    "metadata": res["metadata"],
                    "is_vector": True
                })
        # 중요도 순 정렬 후 상위 반환
        sorted_memories = sorted(
            all_memories, 
            key=lambda m: m.get("importance", 0.0), 
            reverse=True
        )
        
        return sorted_memories[:top_k]
    
    def search_files(
        self,
        query: str,
        max_results: int = 50,
        extension: Optional[str] = None,
        path_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Everything을 사용한 초고속 파일 검색 (Phase 2 & 3)
        
        Args:
            query: 검색어
            max_results: 최대 결과 수
            extension: 파일 확장자 필터 (예: "py", "md")
            path_filter: 경로 필터 (예: "fdo_agi_repo")
        
        Returns:
            검색 결과 리스트 (파일 정보)
        
        Examples:
            >>> hip.search_files("hippocampus", extension="py")
            >>> hip.search_files("goal", path_filter="memory")
        """
        if not self.everything:
            logger.warning("Everything search not available - using fallback")
            return self._fallback_file_search(query, max_results, extension, path_filter)
        
        try:
            # Everything 검색 실행
            results = self.everything.search(
                query=query,
                max_results=max_results,
                extension=extension,
                path_filter=path_filter,
                timeout=10
            )
            
            # 결과 변환
            return [r.to_dict() for r in results]
            
        except Exception as e:
            logger.error(f"Everything search failed: {e}")
            return self._fallback_file_search(query, max_results, extension, path_filter)
    
    def _fallback_file_search(
        self,
        query: str,
        max_results: int,
        extension: Optional[str],
        path_filter: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Everything 미사용 시 폴백 검색"""
        results = []
        search_root = self.workspace
        
        if path_filter:
            search_root = self.workspace / path_filter
        
        if not search_root.exists():
            return results
        
        # 간단한 glob 검색
        pattern = f"**/*{query}*"
        if extension:
            ext = extension if extension.startswith('.') else f'.{extension}'
            pattern = f"**/*{query}*{ext}"
        
        try:
            for path in search_root.glob(pattern):
                if path.is_file():
                    stat = path.stat()
                    results.append({
                        "name": path.name,
                        "full_path": str(path),
                        "directory": str(path.parent),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "extension": path.suffix
                    })
                    
                    if len(results) >= max_results:
                        break
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
        
        return results
        episodic = self.long_term.recall_episodic(query, top_k)
        semantic = self.long_term.recall_semantic(query, top_k)
        procedural = self.long_term.recall_procedural(query, top_k)

        buckets = {
            "episodic": episodic,
            "semantic": semantic,
            "procedural": procedural,
        }

        # 타입 균형 샘플링 후 전역 정렬
        balanced = self._balanced_sample(buckets, top_k)
        balanced.sort(key=lambda x: x.get("importance", 0), reverse=True)
        return balanced[:top_k]
    
    def consolidate(self, force: bool = False) -> Dict[str, Any]:
        """
        단기 기억을 장기 기억으로 공고화
        
        Args:
            force: True면 중요도 무시하고 모두 저장
        
        Returns:
            공고화 결과 (저장된 항목 수 등)
        """
        working = self.short_term.get_all_working()

        # 공고화 전 중복 제거/군집화(간단 버전: 고유 항목만 유지)
        working = self._deduplicate_items(working, self.consolidation_config.get("dedup_threshold", 0.9))
        
        consolidated = {
            "episodic": 0,
            "semantic": 0,
            "procedural": 0,
            "total": 0,
        }
        
        for item in working:
            # 중요도 계산
            importance = self._calculate_importance(item)
            
            if force or importance >= self.consolidation_config["importance_threshold"]:
                # 적절한 장기 기억 시스템에 저장
                memory_type = self._classify_memory_type(item)
                
                if memory_type == "episodic":
                    self.long_term.store_episodic(item)
                    consolidated["episodic"] += 1
                elif memory_type == "semantic":
                    self.long_term.store_semantic(item)
                    consolidated["semantic"] += 1
                elif memory_type == "procedural":
                    self.long_term.store_procedural(item)
                    consolidated["procedural"] += 1
                
                # Vector indexing (Phase 10 upgrade)
                if self.rag_engine:
                    self.rag_engine.add_documents([item])
                consolidated["total"] += 1
        
        # 단기 기억 정리
        self.short_term.clear_working()
        
        logger.info(f"🌊 Consolidated {consolidated['total']} memories")
        return consolidated
    
    # ===================================================================
    # 세션 간 연속성
    # ===================================================================
    
    def generate_handover(self) -> Dict[str, Any]:
        """
        다음 세션을 위한 Handover 생성
        
        Returns:
            Handover 문서 (현재 상태, 컨텍스트, 다음 작업)
        """
        handover = {
            "handover_version": 1,
            "schema": "copilot_handover_v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.short_term.session_id,
            
            # 현재 작업 컨텍스트
            "current_context": self.get_current_context(),
            
            # 최근 중요 기억
            "recent_important": self._get_recent_important_memories(hours=24),
            
            # 미완료 작업
            "pending_tasks": self.short_term.get_pending_tasks(),
            
            # 다음 제안 작업
            "suggested_next_actions": self._suggest_next_actions(),
            
            # 시스템 상태
            "system_state": self._capture_system_state(),
        }
        
        # 저장
        handover_path = self.outputs / "copilot_handover_latest.json"
        with open(handover_path, "w", encoding="utf-8") as f:
            json.dump(handover, f, indent=2, ensure_ascii=False)
        
        logger.info(f"🌊 Generated handover: {handover_path}")
        return handover
    
    def load_handover(self) -> Optional[Dict[str, Any]]:
        """
        이전 세션의 Handover 로드
        
        Returns:
            Handover 문서 또는 None
        """
        handover_path = self.outputs / "copilot_handover_latest.json"
        
        if not handover_path.exists():
            logger.warning("No handover file found")
            return None
        
        try:
            with open(handover_path, "r", encoding="utf-8") as f:
                handover = json.load(f)
            # 스키마 검증 및 필요 시 마이그레이션
            handover = self._ensure_handover_schema(handover)
            
            # 단기 기억으로 복원
            self._restore_from_handover(handover)
            
            logger.info("🌊 Loaded handover successfully")
            return handover
        except Exception as e:
            logger.error(f"Failed to load handover: {e}")
            return None
    
    # ===================================================================
    # 내부 헬퍼
    # ===================================================================
    
    def _calculate_importance(self, item: Dict[str, Any]) -> float:
        """항목의 중요도 계산 (0.0 ~ 1.0)"""
        cfg = self.consolidation_config
        
        # 이미 importance 값이 명시되어 있으면 그것을 사용
        if "importance" in item:
            return float(item["importance"])
        
        # 아니면 계산
        # 1. 최근성 (얼마나 최근인가?) - 지수 감쇠 기반
        recency_score = self._calculate_recency_exp(item)
        
        # 2. 빈도 (얼마나 자주 참조되었는가?)
        frequency_score = item.get("access_count", 0) / 10.0  # normalize
        frequency_score = min(max(frequency_score, 0.0), 1.0)
        
        # 3. 감정적 중요도 (얼마나 강한 감정이 있었는가?)
        emotional_score = item.get("emotional_intensity", 0.5)

        # 4. 새로움(중복의 반대). 주어진 similarity(0~1)가 있으면 1-sim, 없으면 0.5
        if "novelty" in item:
            novelty_score = float(item.get("novelty", 0.5))
        else:
            sim = item.get("similarity")
            novelty_score = 1.0 - float(sim) if isinstance(sim, (int, float)) else 0.5
        novelty_score = min(max(novelty_score, 0.0), 1.0)
        
        # 가중 평균
        importance = (
            cfg["recency_weight"] * recency_score +
            cfg["frequency_weight"] * frequency_score +
            cfg["emotional_weight"] * emotional_score +
            cfg["novelty_weight"] * novelty_score
        )
        
        return float(min(max(importance, 0.0), 1.0))
    
    def _calculate_recency(self, item: Dict[str, Any]) -> float:
        """최근성 점수 계산 (선형 완화 모델 - 하위호환 유지)"""
        timestamp_str = item.get("timestamp")
        if not timestamp_str:
            return 0.5
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - timestamp
            
            # 1시간 이내: 1.0, 24시간: 0.5, 7일: 0.1
            hours_old = age.total_seconds() / 3600
            if hours_old < 1:
                return 1.0
            elif hours_old < 24:
                return 0.5 + (24 - hours_old) / 24 * 0.5
            elif hours_old < 168:  # 7 days
                return 0.1 + (168 - hours_old) / 168 * 0.4
            else:
                return 0.1
        except:
            return 0.5

    def _calculate_recency_exp(self, item: Dict[str, Any]) -> float:
        """최근성 점수 계산 (지수 감쇠: 0~1). 0h=1.0, 24h≈0.5, 7d≈0.1"""
        timestamp_str = item.get("timestamp")
        if not timestamp_str:
            return 0.5
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            age_hours = max((datetime.now(timezone.utc) - timestamp).total_seconds() / 3600.0, 0.0)
            # exp 감쇠 상수: 24h->0.5가 되도록 설정: exp(-k*24)=0.5 => k = ln(2)/24
            import math
            k = math.log(2) / 24.0
            score = math.exp(-k * age_hours)
            # 7d 수준에서 하한 0.1 정도로 클리핑
            return float(max(min(score, 1.0), 0.1))
        except Exception:
            return 0.5
    
    def _classify_memory_type(self, item: Dict[str, Any]) -> str:
        """메모리 타입 분류 (episodic/semantic/procedural)"""
        # 간단한 휴리스틱
        text = json.dumps(item, ensure_ascii=False).lower()
        if any(k in item for k in ("event", "action")) or ("did" in text and "when" in text):
            return "episodic"
        elif any(k in item for k in ("concept", "knowledge")) or ("what is" in text or "define" in text):
            return "semantic"
        elif any(k in item for k in ("procedure", "steps")) or ("how to" in text or "step" in text):
            return "procedural"
        else:
            return "episodic"  # default
    
    def _get_recent_important_memories(self, hours: int = 24) -> List[Dict[str, Any]]:
        """최근 N시간 내 중요한 기억 조회"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return self.long_term.get_memories_since(cutoff, min_importance=0.7)
    
    def _suggest_next_actions(self) -> List[str]:
        """다음 제안 작업 생성"""
        # TODO: 더 스마트하게 - 패턴 분석, BQI 모델 활용
        pending = self.short_term.get_pending_tasks()
        return [task["description"] for task in pending[:3]]
    
    def count_total(self) -> int:
        """전체 기억 개수 합산"""
        return self.long_term.count_total()

    def get_chronological_narrative(self, hours: int = 24) -> str:
        """최근 N시간 동안의 기억을 연대순 서사로 재구성"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        memories = self.long_term.get_memories_since(cutoff)
        
        if not memories:
            return "최근 기록된 중요한 기억이 없습니다."
            
        # 시간순 정렬
        memories.sort(key=lambda x: x.get("timestamp", ""))
        
        narrative = [f"--- 최근 {hours}시간의 흐름 ---"]
        for m in memories:
            ts = m.get("timestamp", "Unknown Time")
            m_type = m.get("type", "event")
            data = m.get("data", {})
            # 서사 구조에서 제목 추출 고도화 (중첩된 data 필드 및 event_type 고려)
            inner_data = data.get("data") if isinstance(data.get("data"), dict) else data
            # 1. inner_data["title"] 확인
            # 2. inner_data["data"]["title"] 확인
            # 3. data["event_type"] 확인
            # 4. m_type (episodic 등) 확인
            title = inner_data.get("title")
            if not title and isinstance(inner_data.get("data"), dict):
                title = inner_data.get("data").get("title")
            
            title = title or data.get("event_type") or m_type
            narrative.append(f"[{ts}] {title} ({m_type})")
            
        return "\n".join(narrative)

    def _capture_system_state(self) -> Dict[str, Any]:
        """현재 시스템 상태 캡처"""
        return {
            "workspace": str(self.workspace),
            "short_term_items": len(self.short_term.get_all_working()),
            "long_term_items": self.long_term.count_total(),
        }
    
    def _restore_from_handover(self, handover: Dict[str, Any]) -> None:
        """Handover로부터 단기 기억 복원"""
        context = handover.get("current_context", {})
        
        # 작업 컨텍스트 복원
        for item in context.get("working_items", []):
            self.short_term.add_working(item)
        
        # 미완료 작업 복원
        for task in handover.get("pending_tasks", []):
            self.short_term.add_pending_task(task)

    # -----------------------------
    # 내부 헬퍼(신규): 타입 균형 샘플링 / Dedup / Handover 스키마
    # -----------------------------

    def _balanced_sample(self, buckets: Dict[str, List[Dict[str, Any]]], top_k: int) -> List[Dict[str, Any]]:
        """타입 균형 샘플링 후 합치기(간단 비율: 균등 분배, 잔여는 많은 버킷에서 추가)"""
        per_type = max(1, top_k // 3)
        selected: List[Dict[str, Any]] = []
        # 1차 균등 분배
        for t, items in buckets.items():
            # 타입 내부는 중요도 우선 정렬
            items_sorted = sorted(items, key=lambda x: x.get("importance", 0), reverse=True)
            selected.extend(items_sorted[:per_type])
        # 잔여 채우기
        remain = max(0, top_k - len(selected))
        if remain > 0:
            # 모든 나머지 아이템 플랫화 후 중요도 정렬하여 잔여 채움
            all_rest: List[Dict[str, Any]] = []
            for items in buckets.values():
                all_rest.extend(items)
            # 이미 선택된 항목 제외(객체 동일성 기준이 애매할 수 있어 id/해시로 보조)
            seen_ids = set(map(id, selected))
            leftovers = [x for x in all_rest if id(x) not in seen_ids]
            leftovers.sort(key=lambda x: x.get("importance", 0), reverse=True)
            selected.extend(leftovers[:remain])
        return selected

    def _ensure_handover_schema(self, handover: Dict[str, Any]) -> Dict[str, Any]:
        """Handover 스키마 검증 및 필요 시 마이그레이션 수행"""
        version = handover.get("handover_version")
        if version is None:
            # v0 -> v1 마이그레이션: 필수 필드 기본값 채우기
            handover = {
                **handover,
                "handover_version": 1,
                "schema": handover.get("schema", "copilot_handover_v1"),
                "timestamp": handover.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "session_id": handover.get("session_id", self.short_term.session_id),
                "current_context": handover.get("current_context", self.get_current_context()),
                "recent_important": handover.get("recent_important", []),
                "pending_tasks": handover.get("pending_tasks", []),
                "suggested_next_actions": handover.get("suggested_next_actions", []),
                "system_state": handover.get("system_state", self._capture_system_state()),
            }
        # 최소 필드 검증
        required = ["handover_version", "timestamp", "session_id", "current_context"]
        missing = [k for k in required if k not in handover]
        if missing:
            raise ValueError(f"Handover schema invalid, missing: {missing}")
        return handover

    def _deduplicate_items(self, items: List[Dict[str, Any]], threshold: float = 0.9) -> List[Dict[str, Any]]:
        """간단 중복 제거: 항목 텍스트 유사도가 threshold 이상이면 중복으로 간주"""
        kept: List[Dict[str, Any]] = []
        for it in items:
            txt = self._item_text(it)
            is_dup = False
            for k in kept:
                sim = self._jaccard_similarity(txt, self._item_text(k))
                if sim >= threshold:
                    is_dup = True
                    break
            if not is_dup:
                kept.append(it)
        return kept

    def _item_text(self, item: Dict[str, Any]) -> str:
        # 대표 텍스트 추출(가벼운 방식): content/text/summary/desc 우선
        for key in ("content", "text", "summary", "description"):
            if key in item and isinstance(item[key], str):
                return item[key].lower()
        return json.dumps(item, ensure_ascii=False).lower()

    def _jaccard_similarity(self, a: str, b: str) -> float:
        # 토큰화(간단 공백 분할) 후 Jaccard
        aset = set(a.split())
        bset = set(b.split())
        if not aset or not bset:
            return 0.0
        inter = len(aset & bset)
        union = len(aset | bset)
        return inter / union if union else 0.0


class ShortTermMemory:
    """단기 기억 (현재 세션, 128K 토큰)"""
    
    def __init__(self):
        self.session_id = f"sess_{datetime.now():%Y%m%d_%H%M%S}"
        self.working_items: List[Dict[str, Any]] = []
        self.pending_tasks: List[Dict[str, Any]] = []
    
    def add_working(self, item: Dict[str, Any]) -> None:
        """작업 기억에 추가"""
        item["added_at"] = datetime.now(timezone.utc).isoformat()
        item["access_count"] = 1
        self.working_items.append(item)
    
    def get_all_working(self) -> List[Dict[str, Any]]:
        """모든 작업 기억 반환"""
        return self.working_items
    
    def clear_working(self) -> None:
        """작업 기억 정리"""
        self.working_items = []
    
    def add_pending_task(self, task: Dict[str, Any]) -> None:
        """미완료 작업 추가"""
        self.pending_tasks.append(task)
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """미완료 작업 목록"""
        return self.pending_tasks
    
    def get_context(self) -> Dict[str, Any]:
        """현재 컨텍스트"""
        return {
            "session_id": self.session_id,
            "working_items": self.working_items,
            "pending_tasks": self.pending_tasks,
        }


class LongTermMemory:
    """장기 기억 (7개 시스템 통합)"""
    
    def __init__(self, memory_root: Path, outputs: Path):
        self.memory_root = memory_root
        self.outputs = outputs
        
        semantic_db_path = self._select_semantic_db_path(outputs)
        # 7개 메모리 시스템 경로
        self.paths = {
            "episodic": memory_root / "sessions",
            "semantic": semantic_db_path,
            "procedural": memory_root / "procedures.jsonl",
            "resonance": memory_root / "resonance_ledger_v2.jsonl",
            "bqi": outputs / "bqi_pattern_model.json",
            "youtube": outputs / "youtube_learner",
            "monitoring": outputs / "monitoring_metrics_latest.json",
        }
        
        # Semantic Memory DB 초기화 (진단 체크용)
        if not self.paths["semantic"].exists():
            self._init_semantic_db(self.paths["semantic"])
        else:
            self._semantic_db = str(self.paths["semantic"])
    
    def _select_semantic_db_path(self, outputs: Path) -> Path:
        env_path = os.environ.get("AGI_SEMANTIC_DB_PATH")
        if env_path:
            return Path(env_path)
        env_dir = os.environ.get("AGI_SEMANTIC_DB_DIR")
        if env_dir:
            return Path(env_dir) / "session_memory.db"
        default_path = outputs / "session_memory" / "session_memory.db"
        if self._can_write_sqlite(default_path.parent):
            return default_path
        fallback = Path.home() / ".cache" / "agi" / "session_memory" / "session_memory.db"
        logger.warning("Semantic DB path not writable; using fallback at %s", fallback)
        return fallback

    def _can_write_sqlite(self, dir_path: Path) -> bool:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            test_path = dir_path / ".sqlite_write_test.sqlite3"
            conn = sqlite3.connect(str(test_path))
            conn.execute("CREATE TABLE IF NOT EXISTS test_io (id INTEGER PRIMARY KEY, val TEXT)")
            conn.commit()
            conn.close()
            try:
                test_path.unlink()
            except Exception:
                pass
            return True
        except Exception:
            return False
    # ===================================================================
    # Episodic Memory (사건 기억)
    # ===================================================================
    
    def recall_episodic(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """사건 기억 회상 - Resonance Ledger 활용"""
        ledger_path = self.paths["resonance"]
        
        if not ledger_path.exists():
            return []
        
        # 최근 1000개 이벤트 로드
        events = []
        try:
            with open(ledger_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-1000:]
                for line in lines:
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except:
                        pass
        except:
            pass
        
        # 간단한 키워드 매칭 (TODO: 벡터 검색으로 업그레이드)
        query_lower = query.lower()
        matches = []
        for event in events:
            event_str = json.dumps(event).lower()
            if query_lower in event_str:
                matches.append({
                    "type": "episodic",
                    "data": event,
                    "importance": event.get("quality", 0.5),
                })
        
        return matches[:top_k]
    
    def store_episodic(self, item: Dict[str, Any]) -> None:
        """사건 기억 저장"""
        ledger_path = self.paths["resonance"]
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "copilot_memory",
            "data": item,
        }
        
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    # ===================================================================
    # Semantic Memory (개념 기억)
    # ===================================================================
    
    def recall_semantic(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """개념 기억 회상 - Session Memory DB 활용"""
        db_path = self.paths["semantic"]
        
        if not db_path.exists():
            self._init_semantic_db(db_path)
            return []
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # FTS5 검색 (간단한 구현)
            cursor.execute("""
                SELECT id, content, importance, timestamp
                FROM semantic_memory
                WHERE content LIKE ?
                ORDER BY importance DESC
                LIMIT ?
            """, (f"%{query}%", top_k))
            
            results = []
            for row in cursor.fetchall():
                content = row[1]
                results.append({
                    "type": "semantic",
                    "id": row[0],
                    "content": content,
                    "data": content,
                    "importance": row[2],
                    "timestamp": row[3],
                })
            
            conn.close()
            return results
        except Exception as e:
            logger.warning(f"Semantic recall error: {e}")
            return []
    
    def store_semantic(self, item: Dict[str, Any]) -> None:
        """개념 기억 저장"""
        db_path = self.paths["semantic"]
        
        if not db_path.exists():
            self._init_semantic_db(db_path)
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO semantic_memory (content, importance, timestamp)
                VALUES (?, ?, ?)
            """, (
                json.dumps(item, ensure_ascii=False),
                item.get("importance", 0.5),
                datetime.now(timezone.utc).isoformat()
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Semantic store error: {e}")
    
    def _init_semantic_db(self, db_path: Path) -> None:
        """Semantic Memory DB 초기화"""
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                timestamp TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_importance 
            ON semantic_memory(importance DESC)
        """)
        
        conn.commit()
        conn.close()
        
        # 진단용 속성 설정
        self._semantic_db = str(db_path)
        
        logger.info(f"✅ Initialized semantic memory DB: {db_path}")
    
    # ===================================================================
    # Procedural Memory (절차 기억)
    # ===================================================================
    
    def recall_procedural(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        절차 기억 회상 (어떻게 했는지)
        
        Args:
            query: 검색 쿼리 (예: "goal", "task", "action")
            top_k: 상위 몇 개 반환
        
        Returns:
            관련 절차 리스트 (최근순)
        """
        proc_path = self.paths["procedural"]
        if not proc_path.exists():
            return []
        
        results = []
        query_lower = query.lower()
        
        try:
            with open(proc_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        entry = json.loads(line)
                        data = entry.get("data", {})
                        
                        # 간단한 키워드 매칭
                        matches = False
                        for key, value in data.items():
                            if query_lower in str(key).lower() or query_lower in str(value).lower():
                                matches = True
                                break
                        
                        if matches:
                            results.append({
                                "timestamp": entry.get("timestamp"),
                                "type": "procedural",
                                "data": data,
                                "importance": data.get("importance", 0.5),
                            })
                    except json.JSONDecodeError:
                        continue
            
            # 최근순 정렬 후 상위 k개
            results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to recall procedural memory: {e}")
            return []
    
    def store_procedural(self, item: Dict[str, Any]) -> None:
        """절차 기억 저장"""
        proc_path = self.paths["procedural"]
        proc_path.parent.mkdir(parents=True, exist_ok=True)
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": item,
        }
        
        with open(proc_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    # ===================================================================
    # Episodic Memory (에피소드 기억 - Everything 검색 통합)
    # ===================================================================
    
    def search_episodic(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        에피소드 기억 검색 (무의식 자동 회상)
        Everything 검색 엔진 통합
        
        Args:
            query: 검색 쿼리 (자연어)
            top_k: 상위 몇 개 반환
        
        Returns:
            관련 에피소드 리스트 (최근순 + 관련성순)
        """
        try:
            from fdo_agi_repo.utils.everything_search import search_files
            
            # Everything 검색 실행
            files = search_files(query, max_results=top_k)
            
            results = []
            for file_info in files:
                results.append({
                    "timestamp": file_info.get("modified", ""),
                    "type": "episodic",
                    "data": {
                        "path": file_info.get("path", ""),
                        "name": file_info.get("name", ""),
                        "size": file_info.get("size", 0),
                        "modified": file_info.get("modified", ""),
                        "relevance": file_info.get("relevance", 0.5),
                    },
                    "importance": file_info.get("relevance", 0.5),
                })
            
            logger.info(f"✅ Episodic recall: {len(results)} results for '{query}'")
            return results
            
        except Exception as e:
            logger.warning(f"Episodic search error: {e}")
            return []
    
    # ===================================================================
    # 유틸리티
    # ===================================================================
    
    def get_memories_since(self, cutoff: datetime, min_importance: float = 0.0) -> List[Dict[str, Any]]:
        """모든 메모리 파일에서 특정 시점 이후의 데이터 수집"""
        results = []
        cutoff_str = cutoff.isoformat()
        
        # 1. Resonance Ledger (Episodic)
        if self.paths["resonance"].exists():
            with open(self.paths["resonance"], "r", encoding="utf-8-sig", errors="replace") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("timestamp", "") >= cutoff_str:
                            if entry.get("quality", 0.5) >= min_importance:
                                results.append({
                                    "timestamp": entry.get("timestamp"),
                                    "type": "episodic",
                                    "data": entry,
                                    "importance": entry.get("quality", 0.5)
                                })
                    except: continue

        # 2. Procedural Memory
        if self.paths["procedural"].exists():
            with open(self.paths["procedural"], "r", encoding="utf-8-sig", errors="replace") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("timestamp", "") >= cutoff_str:
                            data = entry.get("data", {})
                            if data.get("importance", 0.5) >= min_importance:
                                results.append({
                                    "timestamp": entry.get("timestamp"),
                                    "type": "procedural",
                                    "data": data,
                                    "importance": data.get("importance", 0.5)
                                })
                    except: continue

        # 3. Semantic Memory (SQLite)
        try:
            conn = sqlite3.connect(str(self.paths["semantic"]))
            cursor = conn.cursor()
            cursor.execute("SELECT content, importance, timestamp FROM semantic_memory WHERE timestamp >= ?", (cutoff_str,))
            for row in cursor.fetchall():
                importance = row[1]
                if importance >= min_importance:
                    results.append({
                        "timestamp": row[2],
                        "type": "semantic",
                        "data": json.loads(row[0]),
                        "importance": importance
                    })
            conn.close()
        except: pass
        
        return results

    def count_total(self) -> int:
        """모든 메모리 항목의 총합 계산"""
        total = 0
        # Resonance counts
        if self.paths["resonance"].exists():
            with open(self.paths["resonance"], "r", encoding="utf-8") as f:
                total += sum(1 for _ in f)
        # Procedural counts
        if self.paths["procedural"].exists():
            with open(self.paths["procedural"], "r", encoding="utf-8") as f:
                total += sum(1 for _ in f)
        # Semantic counts
        try:
            conn = sqlite3.connect(str(self.paths["semantic"]))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM semantic_memory")
            total += cursor.fetchone()[0]
            conn.close()
        except: pass
        
        return total


# Backward compatibility alias
Hippocampus = CopilotHippocampus
