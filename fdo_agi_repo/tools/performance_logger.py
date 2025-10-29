#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Logger for Hey Sena Phase 7 Validation

실시간 성능 메트릭 수집 및 저장
- 모든 대화 세션 자동 로깅
- JSON 형식으로 저장
- 통계 자동 계산
- Phase 7 검증용
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)


class PerformanceLogger:
    """세션별 성능 메트릭 수집 및 로깅"""

    def __init__(self, log_dir: str = "logs/phase7"):
        """
        Args:
            log_dir: 로그 저장 디렉토리 경로
        """
        self.log_dir = Path(log_dir)
        self.sessions_dir = self.log_dir / "sessions"
        self.daily_dir = self.log_dir / "daily_stats"

        # 디렉토리 생성
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.daily_dir.mkdir(parents=True, exist_ok=True)

        # 현재 세션 데이터
        self.current_session: Optional[Dict[str, Any]] = None
        self.session_start_time: Optional[float] = None

    def start_session(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        새로운 세션 시작

        Args:
            metadata: 세션 메타데이터 (선택)

        Returns:
            session_id
        """
        session_id = str(uuid.uuid4())[:8]
        self.session_start_time = time.time()

        self.current_session = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "metadata": metadata or {},
            "turns": [],
            "errors": [],
            "metrics": {
                "total_turns": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "total_response_time_ms": 0,
                "llm_tokens_used": 0,
                "tts_calls": 0,
            },
            "topics": []
        }

        print(f"\n📊 [Logger] Session started: {session_id}")
        return session_id

    def log_turn(
        self,
        question: str,
        answer: str,
        response_time_ms: float,
        cache_hit: bool = False,
        llm_tokens: int = 0,
        tts_used: bool = False,
        error: Optional[str] = None
    ):
        """
        개별 턴 메트릭 기록

        Args:
            question: 사용자 질문
            answer: 시스템 응답
            response_time_ms: 응답 시간 (밀리초)
            cache_hit: 캐시에서 응답했는지 여부
            llm_tokens: 사용된 LLM 토큰 수
            tts_used: TTS 사용 여부
            error: 오류 메시지 (있는 경우)
        """
        if not self.current_session:
            print("⚠️  [Logger] No active session. Call start_session() first.")
            return

        turn_data = {
            "turn_number": len(self.current_session["turns"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "question": question[:200],  # 처음 200자만 저장
            "answer": answer[:200] if answer else None,
            "response_time_ms": round(response_time_ms, 2),
            "cache_hit": cache_hit,
            "llm_tokens": llm_tokens,
            "tts_used": tts_used,
            "error": error
        }

        self.current_session["turns"].append(turn_data)

        # 메트릭 업데이트
        metrics = self.current_session["metrics"]
        metrics["total_turns"] += 1
        metrics["total_response_time_ms"] += response_time_ms

        if cache_hit:
            metrics["cache_hits"] += 1
        else:
            metrics["cache_misses"] += 1

        if llm_tokens > 0:
            metrics["llm_tokens_used"] += llm_tokens

        if tts_used:
            metrics["tts_calls"] += 1

        if error:
            self.current_session["errors"].append({
                "turn": turn_data["turn_number"],
                "error": error,
                "timestamp": datetime.now().isoformat()
            })

        # 실시간 피드백 (간단)
        status = "💚 HIT" if cache_hit else "⚡ LLM"
        print(f"📊 [Logger] Turn {turn_data['turn_number']}: {status} | {response_time_ms:.0f}ms")

    def add_topic(self, topic: str):
        """대화 주제 추가"""
        if self.current_session and topic not in self.current_session["topics"]:
            self.current_session["topics"].append(topic)

    def end_session(self, user_rating: Optional[int] = None, notes: str = "") -> Dict[str, Any]:
        """
        세션 종료 및 저장

        Args:
            user_rating: 사용자 만족도 (1-5)
            notes: 추가 메모

        Returns:
            세션 요약 통계
        """
        if not self.current_session:
            print("⚠️  [Logger] No active session to end.")
            return {}

        # 세션 종료 시간 및 기간
        end_time = time.time()
        duration_seconds = end_time - self.session_start_time

        self.current_session["end_time"] = datetime.now().isoformat()
        self.current_session["duration_seconds"] = round(duration_seconds, 2)
        self.current_session["user_rating"] = user_rating
        self.current_session["notes"] = notes

        # 통계 계산
        metrics = self.current_session["metrics"]
        total_turns = metrics["total_turns"]

        if total_turns > 0:
            metrics["cache_hit_rate"] = round(
                metrics["cache_hits"] / total_turns * 100, 2
            )
            metrics["avg_response_time_ms"] = round(
                metrics["total_response_time_ms"] / total_turns, 2
            )

            # 응답 시간 통계
            response_times = [t["response_time_ms"] for t in self.current_session["turns"]]
            metrics["min_response_time_ms"] = round(min(response_times), 2)
            metrics["max_response_time_ms"] = round(max(response_times), 2)
        else:
            metrics["cache_hit_rate"] = 0
            metrics["avg_response_time_ms"] = 0
            metrics["min_response_time_ms"] = 0
            metrics["max_response_time_ms"] = 0

        # 오류율
        metrics["error_rate"] = round(
            len(self.current_session["errors"]) / max(total_turns, 1) * 100, 2
        )

        # 파일 저장
        session_id = self.current_session["session_id"]
        filename = f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.sessions_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.current_session, f, indent=2, ensure_ascii=False)

        # 일일 통계 업데이트
        self._update_daily_stats()

        # 요약 출력
        summary = self._print_summary()

        # 세션 초기화
        self.current_session = None
        self.session_start_time = None

        print(f"\n💾 [Logger] Session saved: {filepath}")
        return summary

    def _update_daily_stats(self):
        """일일 통계 업데이트"""
        today = datetime.now().strftime('%Y-%m-%d')
        daily_file = self.daily_dir / f"{today}.json"

        # 기존 데이터 로드
        if daily_file.exists():
            with open(daily_file, 'r', encoding='utf-8') as f:
                daily_stats = json.load(f)
        else:
            daily_stats = {
                "date": today,
                "total_sessions": 0,
                "total_turns": 0,
                "total_cache_hits": 0,
                "total_cache_misses": 0,
                "total_errors": 0,
                "sessions": []
            }

        # 현재 세션 추가
        metrics = self.current_session["metrics"]
        daily_stats["total_sessions"] += 1
        daily_stats["total_turns"] += metrics["total_turns"]
        daily_stats["total_cache_hits"] += metrics["cache_hits"]
        daily_stats["total_cache_misses"] += metrics["cache_misses"]
        daily_stats["total_errors"] += len(self.current_session["errors"])

        daily_stats["sessions"].append({
            "session_id": self.current_session["session_id"],
            "turns": metrics["total_turns"],
            "duration": self.current_session["duration_seconds"],
            "cache_hit_rate": metrics.get("cache_hit_rate", 0),
            "avg_response_time": metrics.get("avg_response_time_ms", 0),
            "rating": self.current_session.get("user_rating")
        })

        # 일일 통계 계산
        if daily_stats["total_turns"] > 0:
            daily_stats["overall_cache_hit_rate"] = round(
                daily_stats["total_cache_hits"] / daily_stats["total_turns"] * 100, 2
            )
            daily_stats["overall_error_rate"] = round(
                daily_stats["total_errors"] / daily_stats["total_turns"] * 100, 2
            )

        # 저장
        with open(daily_file, 'w', encoding='utf-8') as f:
            json.dump(daily_stats, f, indent=2, ensure_ascii=False)

    def _print_summary(self) -> Dict[str, Any]:
        """세션 요약 출력 및 반환"""
        metrics = self.current_session["metrics"]

        print("\n" + "="*60)
        print("📊 SESSION SUMMARY")
        print("="*60)
        print(f"Session ID: {self.current_session['session_id']}")
        print(f"Duration: {self.current_session['duration_seconds']:.1f}s")
        print(f"Turns: {metrics['total_turns']}")
        print(f"Cache Hit Rate: {metrics.get('cache_hit_rate', 0):.1f}%")
        print(f"Avg Response Time: {metrics.get('avg_response_time_ms', 0):.0f}ms")
        print(f"Min/Max Response: {metrics.get('min_response_time_ms', 0):.0f}ms / {metrics.get('max_response_time_ms', 0):.0f}ms")
        print(f"LLM Tokens: {metrics['llm_tokens_used']}")
        print(f"TTS Calls: {metrics['tts_calls']}")
        print(f"Errors: {len(self.current_session['errors'])} ({metrics.get('error_rate', 0):.1f}%)")

        if self.current_session.get('user_rating'):
            print(f"User Rating: {'⭐' * self.current_session['user_rating']}")

        if self.current_session['topics']:
            print(f"Topics: {', '.join(self.current_session['topics'][:3])}")

        print("="*60)

        return {
            "session_id": self.current_session['session_id'],
            "duration": self.current_session['duration_seconds'],
            "turns": metrics['total_turns'],
            "cache_hit_rate": metrics.get('cache_hit_rate', 0),
            "avg_response_time": metrics.get('avg_response_time_ms', 0),
            "error_rate": metrics.get('error_rate', 0)
        }

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """모든 저장된 세션 로드"""
        sessions = []
        for session_file in sorted(self.sessions_dir.glob("session_*.json")):
            with open(session_file, 'r', encoding='utf-8') as f:
                sessions.append(json.load(f))
        return sessions

    def get_daily_stats(self, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        특정 날짜의 통계 가져오기

        Args:
            date: YYYY-MM-DD 형식 (None이면 오늘)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        daily_file = self.daily_dir / f"{date}.json"
        if not daily_file.exists():
            return None

        with open(daily_file, 'r', encoding='utf-8') as f:
            return json.load(f)


# Singleton instance
_logger_instance = None

def get_logger(log_dir: str = "logs/phase7") -> PerformanceLogger:
    """Singleton 패턴으로 로거 인스턴스 가져오기"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = PerformanceLogger(log_dir)
    return _logger_instance


# 간편 사용 예제
if __name__ == "__main__":
    print("="*60)
    print("📊 Performance Logger - Example Usage")
    print("="*60)

    # 로거 초기화
    logger = get_logger()

    # 세션 시작
    session_id = logger.start_session(metadata={"version": "v4.1", "user": "test"})

    # 몇 가지 턴 시뮬레이션
    import random

    questions = [
        "안녕하세요",
        "오늘 날씨 어때?",
        "파이썬이 뭐야?",
        "좋은 영화 추천해줘",
        "고마워"
    ]

    for i, q in enumerate(questions):
        time.sleep(0.1)  # 약간의 지연

        # 무작위 메트릭 생성
        cache_hit = random.random() < 0.6  # 60% cache hit
        response_time = random.uniform(100, 2000) if not cache_hit else random.uniform(1, 10)
        llm_tokens = 0 if cache_hit else random.randint(50, 200)

        logger.log_turn(
            question=q,
            answer=f"답변 {i+1}",
            response_time_ms=response_time,
            cache_hit=cache_hit,
            llm_tokens=llm_tokens,
            tts_used=True
        )

    # 주제 추가
    logger.add_topic("날씨")
    logger.add_topic("프로그래밍")
    logger.add_topic("영화")

    # 세션 종료
    summary = logger.end_session(user_rating=5, notes="테스트 세션")

    print("\n✅ Example completed!")
    print(f"Check logs in: logs/phase7/sessions/")
