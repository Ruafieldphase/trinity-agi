#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 7 Data Analyzer

수집된 데이터 분석 및 시각화
- Cache hit rate 트렌드
- 응답 시간 분포
- 오류율 분석
- 사용 패턴 인사이트
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from collections import Counter
import statistics

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)


class Phase7Analyzer:
    """Phase 7 데이터 분석기"""

    def __init__(self, log_dir: str = "logs/phase7"):
        """
        Args:
            log_dir: 로그 디렉토리 경로
        """
        self.log_dir = Path(log_dir)
        self.sessions_dir = self.log_dir / "sessions"
        self.daily_dir = self.log_dir / "daily_stats"
        self.analysis_dir = self.log_dir / "analysis"

        self.analysis_dir.mkdir(parents=True, exist_ok=True)

    def load_all_sessions(self) -> List[Dict[str, Any]]:
        """모든 세션 데이터 로드"""
        sessions = []
        if not self.sessions_dir.exists():
            return sessions

        for session_file in sorted(self.sessions_dir.glob("session_*.json")):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    sessions.append(json.load(f))
            except Exception as e:
                print(f"⚠️  Error loading {session_file}: {e}")

        return sessions

    def analyze_all(self) -> Dict[str, Any]:
        """전체 데이터 분석"""
        sessions = self.load_all_sessions()

        if not sessions:
            print("⚠️  No session data found.")
            return {}

        print(f"\n📊 Analyzing {len(sessions)} sessions...")

        analysis = {
            "metadata": {
                "total_sessions": len(sessions),
                "analysis_date": datetime.now().isoformat(),
                "date_range": {
                    "start": sessions[0]["start_time"] if sessions else None,
                    "end": sessions[-1]["end_time"] if sessions else None
                }
            },
            "overall": self._analyze_overall(sessions),
            "cache": self._analyze_cache(sessions),
            "performance": self._analyze_performance(sessions),
            "errors": self._analyze_errors(sessions),
            "topics": self._analyze_topics(sessions),
            "ratings": self._analyze_ratings(sessions),
            "trends": self._analyze_trends(sessions)
        }

        # 분석 결과 저장
        output_file = self.analysis_dir / f"full_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        print(f"💾 Analysis saved: {output_file}")

        return analysis

    def _analyze_overall(self, sessions: List[Dict]) -> Dict[str, Any]:
        """전체 통계"""
        total_turns = sum(s["metrics"]["total_turns"] for s in sessions)
        total_duration = sum(s["duration_seconds"] for s in sessions)
        total_llm_tokens = sum(s["metrics"]["llm_tokens_used"] for s in sessions)
        total_tts_calls = sum(s["metrics"]["tts_calls"] for s in sessions)

        return {
            "total_turns": total_turns,
            "total_duration_seconds": round(total_duration, 2),
            "avg_turns_per_session": round(total_turns / len(sessions), 2),
            "avg_session_duration": round(total_duration / len(sessions), 2),
            "total_llm_tokens": total_llm_tokens,
            "total_tts_calls": total_tts_calls,
            "avg_tokens_per_session": round(total_llm_tokens / len(sessions), 2)
        }

    def _analyze_cache(self, sessions: List[Dict]) -> Dict[str, Any]:
        """캐시 성능 분석"""
        total_hits = sum(s["metrics"]["cache_hits"] for s in sessions)
        total_misses = sum(s["metrics"]["cache_misses"] for s in sessions)
        total_requests = total_hits + total_misses

        cache_hit_rates = [
            s["metrics"].get("cache_hit_rate", 0) for s in sessions
            if s["metrics"]["total_turns"] > 0
        ]

        return {
            "total_cache_hits": total_hits,
            "total_cache_misses": total_misses,
            "overall_cache_hit_rate": round(total_hits / total_requests * 100, 2) if total_requests > 0 else 0,
            "avg_session_cache_hit_rate": round(statistics.mean(cache_hit_rates), 2) if cache_hit_rates else 0,
            "min_cache_hit_rate": round(min(cache_hit_rates), 2) if cache_hit_rates else 0,
            "max_cache_hit_rate": round(max(cache_hit_rates), 2) if cache_hit_rates else 0,
            "median_cache_hit_rate": round(statistics.median(cache_hit_rates), 2) if cache_hit_rates else 0
        }

    def _analyze_performance(self, sessions: List[Dict]) -> Dict[str, Any]:
        """응답 시간 분석"""
        avg_response_times = [
            s["metrics"].get("avg_response_time_ms", 0) for s in sessions
            if s["metrics"]["total_turns"] > 0
        ]

        all_response_times = []
        for session in sessions:
            for turn in session.get("turns", []):
                all_response_times.append(turn["response_time_ms"])

        return {
            "overall_avg_response_time": round(statistics.mean(all_response_times), 2) if all_response_times else 0,
            "overall_median_response_time": round(statistics.median(all_response_times), 2) if all_response_times else 0,
            "min_response_time": round(min(all_response_times), 2) if all_response_times else 0,
            "max_response_time": round(max(all_response_times), 2) if all_response_times else 0,
            "p95_response_time": round(self._percentile(all_response_times, 95), 2) if all_response_times else 0,
            "p99_response_time": round(self._percentile(all_response_times, 99), 2) if all_response_times else 0,
            "stddev_response_time": round(statistics.stdev(all_response_times), 2) if len(all_response_times) > 1 else 0
        }

    def _analyze_errors(self, sessions: List[Dict]) -> Dict[str, Any]:
        """오류 분석"""
        total_errors = sum(len(s["errors"]) for s in sessions)
        total_turns = sum(s["metrics"]["total_turns"] for s in sessions)

        error_rates = [
            s["metrics"].get("error_rate", 0) for s in sessions
            if s["metrics"]["total_turns"] > 0
        ]

        return {
            "total_errors": total_errors,
            "overall_error_rate": round(total_errors / total_turns * 100, 2) if total_turns > 0 else 0,
            "avg_session_error_rate": round(statistics.mean(error_rates), 2) if error_rates else 0,
            "sessions_with_errors": sum(1 for s in sessions if len(s["errors"]) > 0),
            "error_free_sessions": sum(1 for s in sessions if len(s["errors"]) == 0)
        }

    def _analyze_topics(self, sessions: List[Dict]) -> Dict[str, Any]:
        """주제 분석"""
        all_topics = []
        for session in sessions:
            all_topics.extend(session.get("topics", []))

        topic_counts = Counter(all_topics)

        return {
            "unique_topics": len(topic_counts),
            "total_topic_mentions": len(all_topics),
            "top_topics": [
                {"topic": topic, "count": count}
                for topic, count in topic_counts.most_common(10)
            ]
        }

    def _analyze_ratings(self, sessions: List[Dict]) -> Dict[str, Any]:
        """사용자 평점 분석"""
        ratings = [s["user_rating"] for s in sessions if s.get("user_rating") is not None]

        if not ratings:
            return {
                "total_rated_sessions": 0,
                "avg_rating": 0,
                "rating_distribution": {}
            }

        rating_dist = Counter(ratings)

        return {
            "total_rated_sessions": len(ratings),
            "avg_rating": round(statistics.mean(ratings), 2),
            "median_rating": statistics.median(ratings),
            "rating_distribution": {
                str(i): rating_dist.get(i, 0) for i in range(1, 6)
            }
        }

    def _analyze_trends(self, sessions: List[Dict]) -> Dict[str, Any]:
        """시간별 트렌드 분석"""
        if len(sessions) < 2:
            return {"trend": "insufficient_data"}

        # 첫 절반 vs 두 번째 절반
        mid = len(sessions) // 2
        first_half = sessions[:mid]
        second_half = sessions[mid:]

        first_cache = statistics.mean([
            s["metrics"].get("cache_hit_rate", 0) for s in first_half
            if s["metrics"]["total_turns"] > 0
        ]) if first_half else 0

        second_cache = statistics.mean([
            s["metrics"].get("cache_hit_rate", 0) for s in second_half
            if s["metrics"]["total_turns"] > 0
        ]) if second_half else 0

        first_response = statistics.mean([
            s["metrics"].get("avg_response_time_ms", 0) for s in first_half
            if s["metrics"]["total_turns"] > 0
        ]) if first_half else 0

        second_response = statistics.mean([
            s["metrics"].get("avg_response_time_ms", 0) for s in second_half
            if s["metrics"]["total_turns"] > 0
        ]) if second_half else 0

        return {
            "cache_hit_rate_improvement": round(second_cache - first_cache, 2),
            "response_time_improvement": round(first_response - second_response, 2),
            "first_half_cache_rate": round(first_cache, 2),
            "second_half_cache_rate": round(second_cache, 2),
            "first_half_response_time": round(first_response, 2),
            "second_half_response_time": round(second_response, 2)
        }

    def _percentile(self, data: List[float], p: int) -> float:
        """백분위수 계산"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * p / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def print_summary(self, analysis: Dict[str, Any]):
        """분석 결과 요약 출력"""
        print("\n" + "="*70)
        print("📊 PHASE 7 DATA ANALYSIS SUMMARY")
        print("="*70)

        print(f"\n📈 Overall Statistics")
        overall = analysis["overall"]
        print(f"  Total Sessions: {analysis['metadata']['total_sessions']}")
        print(f"  Total Turns: {overall['total_turns']}")
        print(f"  Total Duration: {overall['total_duration_seconds']:.1f}s")
        print(f"  Avg Turns/Session: {overall['avg_turns_per_session']:.1f}")
        print(f"  Avg Session Duration: {overall['avg_session_duration']:.1f}s")

        print(f"\n💚 Cache Performance")
        cache = analysis["cache"]
        print(f"  Overall Cache Hit Rate: {cache['overall_cache_hit_rate']:.1f}%")
        print(f"  Avg Session Cache Hit: {cache['avg_session_cache_hit_rate']:.1f}%")
        print(f"  Min/Max: {cache['min_cache_hit_rate']:.1f}% / {cache['max_cache_hit_rate']:.1f}%")
        print(f"  Median: {cache['median_cache_hit_rate']:.1f}%")

        print(f"\n⚡ Response Time Performance")
        perf = analysis["performance"]
        print(f"  Overall Avg: {perf['overall_avg_response_time']:.0f}ms")
        print(f"  Median: {perf['overall_median_response_time']:.0f}ms")
        print(f"  Min/Max: {perf['min_response_time']:.0f}ms / {perf['max_response_time']:.0f}ms")
        print(f"  P95: {perf['p95_response_time']:.0f}ms")
        print(f"  P99: {perf['p99_response_time']:.0f}ms")

        print(f"\n❌ Error Analysis")
        errors = analysis["errors"]
        print(f"  Total Errors: {errors['total_errors']}")
        print(f"  Overall Error Rate: {errors['overall_error_rate']:.2f}%")
        print(f"  Sessions with Errors: {errors['sessions_with_errors']}")
        print(f"  Error-Free Sessions: {errors['error_free_sessions']}")

        print(f"\n⭐ User Ratings")
        ratings = analysis["ratings"]
        if ratings["total_rated_sessions"] > 0:
            print(f"  Rated Sessions: {ratings['total_rated_sessions']}")
            print(f"  Average Rating: {ratings['avg_rating']:.2f}/5.0")
            print(f"  Distribution: ", end="")
            for i in range(1, 6):
                count = ratings['rating_distribution'][str(i)]
                print(f"{i}⭐:{count} ", end="")
            print()
        else:
            print(f"  No ratings collected yet")

        print(f"\n📝 Topics")
        topics = analysis["topics"]
        print(f"  Unique Topics: {topics['unique_topics']}")
        if topics['top_topics']:
            print(f"  Top 5 Topics:")
            for topic_data in topics['top_topics'][:5]:
                print(f"    - {topic_data['topic']}: {topic_data['count']} times")

        print(f"\n📈 Trends (First Half vs Second Half)")
        trends = analysis["trends"]
        if trends.get("trend") != "insufficient_data":
            print(f"  Cache Hit Rate:")
            print(f"    First Half: {trends['first_half_cache_rate']:.1f}%")
            print(f"    Second Half: {trends['second_half_cache_rate']:.1f}%")
            print(f"    Improvement: {trends['cache_hit_rate_improvement']:+.1f}%")
            print(f"  Response Time:")
            print(f"    First Half: {trends['first_half_response_time']:.0f}ms")
            print(f"    Second Half: {trends['second_half_response_time']:.0f}ms")
            print(f"    Improvement: {trends['response_time_improvement']:+.0f}ms (faster is better)")

        print("\n" + "="*70)

    def check_goals(self, analysis: Dict[str, Any]) -> Dict[str, bool]:
        """Phase 7 목표 달성 여부 체크"""
        print("\n" + "="*70)
        print("🎯 PHASE 7 GOALS CHECK")
        print("="*70)

        goals = {
            "50_sessions": analysis['metadata']['total_sessions'] >= 50,
            "60_cache_hit": analysis['cache']['overall_cache_hit_rate'] >= 60,
            "1.5s_response": analysis['performance']['overall_avg_response_time'] <= 1500,
            "5_error_rate": analysis['errors']['overall_error_rate'] < 5,
            "4_rating": analysis['ratings']['avg_rating'] >= 4.0 if analysis['ratings']['total_rated_sessions'] > 0 else None
        }

        print(f"\n✅ = Achieved | ❌ = Not Yet | ⏳ = In Progress\n")

        status = "✅" if goals["50_sessions"] else ("⏳" if analysis['metadata']['total_sessions'] > 0 else "❌")
        print(f"  {status} Minimum 50 sessions: {analysis['metadata']['total_sessions']}/50")

        status = "✅" if goals["60_cache_hit"] else "❌"
        print(f"  {status} Cache hit rate ≥ 60%: {analysis['cache']['overall_cache_hit_rate']:.1f}%")

        status = "✅" if goals["1.5s_response"] else "❌"
        print(f"  {status} Avg response < 1.5s: {analysis['performance']['overall_avg_response_time']:.0f}ms")

        status = "✅" if goals["5_error_rate"] else "❌"
        print(f"  {status} Error rate < 5%: {analysis['errors']['overall_error_rate']:.2f}%")

        if goals["4_rating"] is not None:
            status = "✅" if goals["4_rating"] else "❌"
            print(f"  {status} User rating ≥ 4.0: {analysis['ratings']['avg_rating']:.2f}/5.0")
        else:
            print(f"  ⏳ User rating ≥ 4.0: No ratings yet")

        achieved = sum(1 for v in goals.values() if v is True)
        total = sum(1 for v in goals.values() if v is not None)

        print(f"\n📊 Overall Progress: {achieved}/{total} goals achieved ({achieved/total*100:.0f}%)")
        print("="*70)

        return goals


def main():
    """메인 함수"""
    print("\n" + "="*70)
    print("📊 Phase 7 Data Analyzer")
    print("="*70)

    analyzer = Phase7Analyzer()
    analysis = analyzer.analyze_all()

    if analysis:
        analyzer.print_summary(analysis)
        analyzer.check_goals(analysis)

    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
