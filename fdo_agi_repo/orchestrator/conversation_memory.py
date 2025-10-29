"""
Conversation Memory Module

BQI 통합 Phase 2: 대화 맥락 기억 시스템
- 질문-답변 쌍을 BQI 좌표와 함께 저장
- 과거 맥락 검색 (최근 N턴 / BQI 유사도 기반)
- Memory Bus 통합

Author: GitHub Copilot
Created: 2025-10-28
"""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from scripts.rune.bqi_adapter import BQICoordinate


@dataclass
class ConversationTurn:
    """단일 대화 턴 (질문 + 답변 + 메타데이터)"""
    question: str
    answer: str
    task_id: str
    bqi_coord: Dict[str, Any]  # BQICoordinate의 dict 표현
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "task_id": self.task_id,
            "bqi": self.bqi_coord,
            "timestamp": self.timestamp
        }


class ConversationMemory:
    """
    대화 맥락 기억 관리자
    
    기능:
    1. 질문-답변 턴 저장 (BQI 좌표 포함)
    2. 최근 N턴 검색
    3. BQI 유사도 기반 관련 맥락 검색
    4. JSONL 형식 영구 저장
    """
    
    def __init__(self, memory_file: str = "memory/conversation_history.jsonl"):
        """
        Args:
            memory_file: 대화 기록 저장 파일 경로 (프로젝트 루트 기준)
        """
        # 프로젝트 루트 기준으로 경로 설정
        project_root = Path(__file__).parent.parent
        self.memory_path = project_root / memory_file
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 메모리 캐시 (빠른 조회용)
        self._turns_cache: List[ConversationTurn] = []
        self._load_history()
    
    def _load_history(self):
        """저장된 대화 기록을 메모리에 로드"""
        if not self.memory_path.exists():
            return
        
        try:
            with open(self.memory_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        turn = ConversationTurn(
                            question=data["question"],
                            answer=data["answer"],
                            task_id=data["task_id"],
                            bqi_coord=data["bqi"],
                            timestamp=data["timestamp"]
                        )
                        self._turns_cache.append(turn)
        except Exception as e:
            print(f"⚠️  대화 기록 로드 실패: {e}")
    
    def add_turn(
        self,
        question: str,
        answer: str,
        task_id: str,
        bqi_coord: BQICoordinate
    ) -> ConversationTurn:
        """
        새 대화 턴 추가
        
        Args:
            question: 사용자 질문
            answer: 시스템 답변
            task_id: AGI 태스크 ID
            bqi_coord: BQI 좌표 객체
            
        Returns:
            저장된 ConversationTurn 객체
        """
        turn = ConversationTurn(
            question=question,
            answer=answer,
            task_id=task_id,
            bqi_coord=bqi_coord.to_dict(),  # datetime 처리된 dict 사용
            timestamp=datetime.now().isoformat()
        )
        
        # 메모리 캐시에 추가
        self._turns_cache.append(turn)
        
        # 파일에 영구 저장 (JSONL append)
        try:
            with open(self.memory_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(turn.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️  대화 기록 저장 실패: {e}")
        
        return turn
    
    def get_recent_turns(self, n: int = 10) -> List[ConversationTurn]:
        """
        최근 N개 대화 턴 반환
        
        Args:
            n: 반환할 턴 개수 (기본 10개)
            
        Returns:
            최근 N개 턴 리스트 (최신순)
        """
        return self._turns_cache[-n:] if len(self._turns_cache) >= n else self._turns_cache
    
    def get_relevant_context(
        self,
        current_question: str,
        top_k: int = 3,
        max_history: int = 100
    ) -> List[ConversationTurn]:
        """
        현재 질문과 관련된 과거 맥락 검색 (BQI 유사도 기반)
        
        Args:
            current_question: 현재 질문
            top_k: 반환할 맥락 개수 (기본 3개)
            max_history: 검색 대상 최근 기록 개수 (기본 100개)
            
        Returns:
            관련도 높은 순으로 정렬된 과거 턴 리스트
        """
        from scripts.rune.bqi_adapter import analyse_question
        
        # 현재 질문의 BQI 좌표 생성
        current_bqi = analyse_question(current_question)
        
        # 최근 max_history개 턴만 검색 대상
        search_pool = self._turns_cache[-max_history:] if len(self._turns_cache) > max_history else self._turns_cache
        
        # BQI 유사도 계산 및 정렬
        scored_turns = []
        for turn in search_pool:
            similarity = self._calculate_bqi_similarity(current_bqi, turn.bqi_coord)
            scored_turns.append((similarity, turn))
        
        # 유사도 높은 순으로 정렬 후 상위 top_k개 반환
        scored_turns.sort(key=lambda x: x[0], reverse=True)
        return [turn for _, turn in scored_turns[:top_k]]
    
    def _calculate_bqi_similarity(
        self,
        bqi1: BQICoordinate,
        bqi2_dict: Dict[str, Any]
    ) -> float:
        """
        두 BQI 좌표 간 유사도 계산 (0.0 ~ 1.0)
        
        계산 방식:
        - rhythm_phase 일치: +0.4
        - emotion 일치: +0.3
        - priority 차이 기반: +0.3 (차이가 작을수록 높음)
        
        Args:
            bqi1: BQICoordinate 객체
            bqi2_dict: BQI 좌표 딕셔너리
            
        Returns:
            유사도 점수 (0.0 ~ 1.0)
        """
        score = 0.0
        
        # Rhythm Phase 유사도 (완전 일치만 점수 부여)
        if bqi1.rhythm_phase == bqi2_dict.get("rhythm_phase"):
            score += 0.4
        
        # Emotion 유사도 (키워드 교집합 비율)
        emotion1_keywords = set(bqi1.emotion.get("keywords", []))
        emotion2_keywords = set(bqi2_dict.get("emotion", {}).get("keywords", []))
        
        if emotion1_keywords and emotion2_keywords:
            intersection = len(emotion1_keywords & emotion2_keywords)
            union = len(emotion1_keywords | emotion2_keywords)
            emotion_score = intersection / union if union > 0 else 0
            score += 0.3 * emotion_score
        
        # Priority 유사도 (차이가 작을수록 높음)
        priority1 = bqi1.priority
        priority2 = bqi2_dict.get("priority", 1)
        priority_diff = abs(priority1 - priority2)
        priority_score = max(0, 1 - (priority_diff / 3))  # 최대 차이 3으로 정규화
        score += 0.3 * priority_score
        
        return score
    
    def format_context_for_prompt(
        self,
        turns: List[ConversationTurn],
        max_chars_per_turn: int = 200
    ) -> str:
        """
        프롬프트에 삽입할 맥락 텍스트 생성
        
        Args:
            turns: 포맷팅할 대화 턴 리스트
            max_chars_per_turn: 턴당 최대 문자 수 (답변 길이 제한)
            
        Returns:
            프롬프트용 맥락 문자열
        """
        if not turns:
            return ""
        
        context_lines = ["📚 이전 대화 맥락:"]
        for i, turn in enumerate(turns, 1):
            # 답변 길이 제한 (너무 길면 요약)
            answer_preview = turn.answer[:max_chars_per_turn]
            if len(turn.answer) > max_chars_per_turn:
                answer_preview += "..."
            
            context_lines.append(
                f"\n[맥락 {i}] Q: {turn.question}\n"
                f"        A: {answer_preview}\n"
                f"        (Rhythm: {turn.bqi_coord.get('rhythm_phase')}, "
                f"Priority: {turn.bqi_coord.get('priority')})"
            )
        
        return "\n".join(context_lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        메모리 통계 반환
        
        Returns:
            통계 딕셔너리 (총 턴 수, rhythm/emotion 분포 등)
        """
        if not self._turns_cache:
            return {"total_turns": 0}
        
        rhythm_counts = {}
        emotion_counts = {}
        
        for turn in self._turns_cache:
            rhythm = turn.bqi_coord.get("rhythm_phase", "unknown")
            rhythm_counts[rhythm] = rhythm_counts.get(rhythm, 0) + 1
            
            emotions = turn.bqi_coord.get("emotion", {}).get("keywords", [])
            for emotion in emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        return {
            "total_turns": len(self._turns_cache),
            "rhythm_distribution": rhythm_counts,
            "emotion_distribution": emotion_counts,
            "memory_file": str(self.memory_path),
            "latest_timestamp": self._turns_cache[-1].timestamp if self._turns_cache else None
        }
