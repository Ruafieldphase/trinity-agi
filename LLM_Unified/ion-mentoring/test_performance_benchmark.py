"""
성능 벤치마크 테스트

Legacy System vs Lumen Gateway 성능 비교
- 응답 시간 측정
- Confidence 비교
- 페르소나 선택 정확도
- 통계 분석 및 시각화
"""

import asyncio
import json
import statistics
import time
from datetime import datetime
from typing import Any, Dict, List

import httpx


class PerformanceBenchmark:
    """성능 벤치마크 실행 클래스"""

    def __init__(self, ion_api_url: str = "http://localhost:8000", iterations: int = 100):
        self.ion_api_url = ion_api_url
        self.iterations = iterations
        self.results = {"lumen": [], "legacy": []}

    async def _call_api(
        self, query: str, user_id: str, force_legacy: bool = False
    ) -> Dict[str, Any]:
        """
        Ion API 호출 (단일 요청)

        Args:
            query: 사용자 쿼리
            user_id: 사용자 ID
            force_legacy: Legacy 강제 사용 (Feature Flag 무시)

        Returns:
            Dict: 응답 데이터 + 메타데이터
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            start_time = time.time()

            payload = {
                "user_id": user_id,
                "query": query,
                "options": {"style": "concise", "force_legacy": force_legacy},  # 추후 구현 필요
            }

            try:
                response = await client.post(
                    f"{self.ion_api_url}/api/v2/recommend/personalized",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                elapsed_time = (time.time() - start_time) * 1000  # ms

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "response_time_ms": elapsed_time,
                        "persona": data.get("primary_persona"),
                        "confidence": data.get("confidence"),
                        "algorithm": data.get("metadata", {}).get("algorithm"),
                        "ab_group": data.get("metadata", {}).get("ab_group"),
                        "lumen_persona": data.get("metadata", {}).get("lumen_persona"),
                        "error": None,
                    }
                else:
                    return {
                        "success": False,
                        "response_time_ms": elapsed_time,
                        "error": f"HTTP {response.status_code}",
                    }

            except Exception as e:
                elapsed_time = (time.time() - start_time) * 1000
                return {"success": False, "response_time_ms": elapsed_time, "error": str(e)}

    async def run_benchmark(self):
        """벤치마크 실행"""
        print(f"\n{'='*70}")
        print("🔬 Performance Benchmark: Legacy vs Lumen Gateway")
        print(f"{'='*70}\n")
        print("📊 설정:")
        print(f"  • Iterations: {self.iterations}")
        print(f"  • API Endpoint: {self.ion_api_url}")
        print("  • Test Queries: 4가지 페르소나 타입\n")

        # 테스트 쿼리 (각 페르소나별)
        test_queries = [
            ("창의적이고 혁신적인 아이디어를 제안해줘", "moon", "Lua"),
            ("이 문제를 체계적으로 단계별로 분석해줘", "square", "Elro"),
            ("전체적인 패턴을 관찰하고 메타 분석해줘", "earth", "Riri"),
            ("여러 관점을 통합해서 설명해줘", "pen", "Nana"),
        ]

        # Lumen Gateway 벤치마크
        print("🚀 Phase 1: Lumen Gateway 벤치마크 실행 중...")
        lumen_results = []

        for i in range(self.iterations):
            query, expected_persona_key, expected_persona_name = test_queries[i % len(test_queries)]
            user_id = f"benchmark_lumen_{i}"

            result = await self._call_api(query, user_id, force_legacy=False)
            result["iteration"] = i + 1
            result["query_type"] = expected_persona_key
            result["expected_persona"] = expected_persona_name
            lumen_results.append(result)

            if (i + 1) % 10 == 0:
                success_count = sum(1 for r in lumen_results if r["success"])
                print(
                    f"  Progress: {i+1}/{self.iterations} iterations "
                    f"(Success: {success_count}/{i+1})"
                )

        self.results["lumen"] = lumen_results
        print(f"✅ Lumen Gateway 벤치마크 완료: {len(lumen_results)} iterations\n")

        # Legacy System 벤치마크
        print("🔄 Phase 2: Legacy System 벤치마크 실행 중...")
        print("⚠️  주의: Legacy 모드 강제 활성화 필요 (LUMEN_GATE_ENABLED=false)\n")

        # 현재는 Feature Flag를 수동으로 변경해야 함
        # 추후 API에서 force_legacy 파라미터 지원 필요

        print("⏸️  Legacy 벤치마크는 수동 설정 후 재실행 필요")
        print("   1. .env에서 LUMEN_GATE_ENABLED=false 설정")
        print("   2. Ion API 재시작")
        print("   3. 이 스크립트 재실행\n")

    def analyze_results(self):
        """결과 분석"""
        print(f"\n{'='*70}")
        print("📊 성능 분석 결과")
        print(f"{'='*70}\n")

        # Lumen Gateway 분석
        lumen_results = [r for r in self.results["lumen"] if r["success"]]

        if not lumen_results:
            print("❌ Lumen Gateway 결과가 없습니다.\n")
            return

        print(f"🌟 Lumen Gateway 분석 ({len(lumen_results)} successful iterations):\n")

        # 응답 시간 통계
        response_times = [r["response_time_ms"] for r in lumen_results]
        print("⏱️  응답 시간:")
        print(f"  • 평균: {statistics.mean(response_times):.2f}ms")
        print(f"  • 중앙값: {statistics.median(response_times):.2f}ms")
        print(f"  • 최소: {min(response_times):.2f}ms")
        print(f"  • 최대: {max(response_times):.2f}ms")
        print(f"  • 표준편차: {statistics.stdev(response_times):.2f}ms\n")

        # Confidence 통계
        confidences = [r["confidence"] for r in lumen_results if r.get("confidence")]
        if confidences:
            print("🎯 Confidence:")
            print(f"  • 평균: {statistics.mean(confidences)*100:.2f}%")
            print(f"  • 중앙값: {statistics.median(confidences)*100:.2f}%")
            print(f"  • 최소: {min(confidences)*100:.2f}%")
            print(f"  • 최대: {max(confidences)*100:.2f}%\n")

        # 알고리즘 사용 분포
        algorithms = {}
        for r in lumen_results:
            algo = r.get("algorithm", "unknown")
            algorithms[algo] = algorithms.get(algo, 0) + 1

        print("🔧 알고리즘 사용 분포:")
        for algo, count in algorithms.items():
            percentage = (count / len(lumen_results)) * 100
            print(f"  • {algo}: {count} ({percentage:.1f}%)")
        print()

        # 페르소나 정확도
        correct_personas = sum(
            1 for r in lumen_results if r.get("persona") == r.get("expected_persona")
        )
        persona_accuracy = (correct_personas / len(lumen_results)) * 100
        print("🎭 페르소나 선택 정확도:")
        print(f"  • 정확도: {correct_personas}/{len(lumen_results)} ({persona_accuracy:.1f}%)\n")

        # 성공률
        total_requests = len(self.results["lumen"])
        success_rate = (len(lumen_results) / total_requests) * 100
        print("✅ 성공률:")
        print(f"  • {len(lumen_results)}/{total_requests} ({success_rate:.1f}%)\n")

    def save_results(self, output_path: str = "outputs/benchmark_results.json"):
        """결과 저장"""
        import os

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        summary = {
            "timestamp": datetime.now().isoformat(),
            "iterations": self.iterations,
            "api_endpoint": self.ion_api_url,
            "results": self.results,
            "summary": {
                "lumen": self._summarize_results(self.results["lumen"]),
                "legacy": self._summarize_results(self.results["legacy"]),
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"💾 결과 저장: {output_path}\n")

    def _summarize_results(self, results: List[Dict]) -> Dict:
        """결과 요약"""
        if not results:
            return {"status": "no_data"}

        successful = [r for r in results if r["success"]]

        if not successful:
            return {"status": "all_failed"}

        response_times = [r["response_time_ms"] for r in successful]
        confidences = [r["confidence"] for r in successful if r.get("confidence")]

        return {
            "total_requests": len(results),
            "successful_requests": len(successful),
            "success_rate": len(successful) / len(results),
            "response_time": {
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "stdev": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            },
            "confidence": {
                "mean": statistics.mean(confidences) if confidences else 0,
                "median": statistics.median(confidences) if confidences else 0,
                "min": min(confidences) if confidences else 0,
                "max": max(confidences) if confidences else 0,
            },
        }


async def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="Performance Benchmark: Legacy vs Lumen")
    parser.add_argument(
        "--iterations", type=int, default=100, help="Number of iterations (default: 100)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="Ion API URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/benchmark_results.json",
        help="Output JSON file path (default: outputs/benchmark_results.json)",
    )

    args = parser.parse_args()

    # 벤치마크 실행
    benchmark = PerformanceBenchmark(ion_api_url=args.api_url, iterations=args.iterations)

    await benchmark.run_benchmark()

    # 결과 분석
    benchmark.analyze_results()

    # 결과 저장
    benchmark.save_results(args.output)

    print(f"{'='*70}")
    print("✅ 벤치마크 완료!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(main())
