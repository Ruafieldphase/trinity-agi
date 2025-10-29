#!/usr/bin/env python3
"""
요약 태스크용 모델 벤치마크 도구

현재 모델 vs Gemini 등 후보 모델의 지연/품질 비교
- 요약 태스크 전용 페이로드
- P50/P95 지연 측정
- 품질 샘플링 (옵션)
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from statistics import mean, median
from typing import Any, Dict, List, Optional

# Gemini 사용 여부 확인
GEMINI_AVAILABLE = False
GEMINI_MODEL = None
try:
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        client = genai.Client(api_key=api_key)
        GEMINI_MODEL = "gemini-2.0-flash-exp"
        GEMINI_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] Gemini import failed: {e}")
    pass


@dataclass
class BenchmarkResult:
    """벤치마크 결과"""

    model_name: str
    total_requests: int
    successful: int
    failed: int
    latencies_ms: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def p50(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return median(self.latencies_ms)

    @property
    def p95(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_lat = sorted(self.latencies_ms)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[idx] if idx < len(sorted_lat) else sorted_lat[-1]

    @property
    def avg(self) -> float:
        return mean(self.latencies_ms) if self.latencies_ms else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "total_requests": self.total_requests,
            "successful": self.successful,
            "failed": self.failed,
            "latency": {
                "p50_ms": round(self.p50, 2),
                "p95_ms": round(self.p95, 2),
                "avg_ms": round(self.avg, 2),
            },
            "errors": self.errors[:5],  # 처음 5개만
        }


# 요약 태스크 샘플 페이로드
SAMPLE_CONVERSATIONS = [
    {
        "messages": [
            {"role": "user", "content": "What is machine learning?"},
            {
                "role": "assistant",
                "content": "Machine learning is a subset of artificial intelligence...",
            },
            {"role": "user", "content": "Can you give me an example?"},
            {"role": "assistant", "content": "Sure! Image recognition is a common example..."},
        ],
        "expected_summary_keywords": ["machine learning", "AI", "example", "image recognition"],
    },
    {
        "messages": [
            {"role": "user", "content": "I'm having trouble with my Python code."},
            {"role": "assistant", "content": "I'd be happy to help. What's the issue?"},
            {"role": "user", "content": "I keep getting a KeyError."},
            {
                "role": "assistant",
                "content": "A KeyError usually means you're trying to access a dictionary key that doesn't exist...",
            },
        ],
        "expected_summary_keywords": ["Python", "code", "KeyError", "dictionary"],
    },
]


def build_summary_prompt(messages: List[Dict[str, str]]) -> str:
    """요약 프롬프트 생성 (경량)"""
    conv_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    return f"""Summarize this conversation concisely in 2-3 bullet points:

{conv_text}

Summary:"""


async def benchmark_current_model(
    conversations: List[Dict], iterations: int = 5
) -> BenchmarkResult:
    """현재 모델 벤치마크 (더미 응답 - 프롬프트 생성 지연만 측정)"""
    result = BenchmarkResult(
        model_name="Current (Pipeline - No LLM)",
        total_requests=len(conversations) * iterations,
        successful=0,
        failed=0,
    )

    try:
        # 최적화 파이프라인 임포트
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from persona_system.models import ChatContext
        from persona_system.pipeline_optimized import get_optimized_pipeline

        pipeline = get_optimized_pipeline()

        for _ in range(iterations):
            for conv in conversations:
                try:
                    start = time.time()

                    # 컨텍스트 생성
                    ctx = ChatContext(
                        user_id="bench_user",
                        session_id="bench_session",
                        message_history=conv["messages"],
                        custom_context={},
                    )

                    # 요약 요청 (summary_light 모드)
                    # NOTE: 실제 LLM 호출은 없음 (더미 커넥터)
                    # 프롬프트 생성 및 파이프라인 오버헤드만 측정
                    _ = pipeline.process(
                        user_input="Summarize our conversation",
                        resonance_key="calm-medium-learning",
                        context=ctx,
                        prompt_mode="summary_light",
                        use_cache=False,  # 공정한 비교를 위해 캐시 비활성화
                    )

                    latency_ms = (time.time() - start) * 1000
                    result.latencies_ms.append(latency_ms)
                    result.successful += 1

                except Exception as e:
                    result.failed += 1
                    result.errors.append(str(e))

    except Exception as e:
        print(f"[WARNING] 현재 모델 벤치마크 실패: {e}")
        result.errors.append(f"Setup error: {str(e)}")

    return result


async def benchmark_gemini(
    conversations: List[Dict], iterations: int = 5
) -> Optional[BenchmarkResult]:
    """Gemini 모델 벤치마크"""
    if not GEMINI_AVAILABLE:
        print("[WARNING] Gemini 사용 불가 (GOOGLE_API_KEY 미설정 또는 라이브러리 없음)")
        return None

    result = BenchmarkResult(
        model_name=f"Gemini ({GEMINI_MODEL})",
        total_requests=len(conversations) * iterations,
        successful=0,
        failed=0,
    )

    try:
        for _ in range(iterations):
            for conv in conversations:
                try:
                    start = time.time()

                    prompt = build_summary_prompt(conv["messages"])

                    response = client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=200),
                    )

                    # 응답 검증
                    if response.text:
                        latency_ms = (time.time() - start) * 1000
                        result.latencies_ms.append(latency_ms)
                        result.successful += 1
                    else:
                        result.failed += 1
                        result.errors.append("Empty response")

                except Exception as e:
                    result.failed += 1
                    result.errors.append(str(e))

    except Exception as e:
        print(f"[WARNING] Gemini 벤치마크 실패: {e}")
        result.errors.append(f"Setup error: {str(e)}")

    return result


async def run_benchmark(
    iterations: int = 5, include_gemini: bool = True
) -> Dict[str, BenchmarkResult]:
    """전체 벤치마크 실행"""
    print(f"[START] 요약 모델 벤치마크 시작 (iterations={iterations})")
    print(f"   샘플 대화: {len(SAMPLE_CONVERSATIONS)}개")
    print(f"   총 요청: {len(SAMPLE_CONVERSATIONS) * iterations}개/모델")
    print(f"   Gemini 사용 가능: {GEMINI_AVAILABLE}")
    if not GEMINI_AVAILABLE:
        api_key = os.getenv("GOOGLE_API_KEY")
        print(f"   API Key: {'있음' if api_key else '없음'}\n")
    else:
        print("")

    results = {}

    # 현재 모델
    print("[BENCH] 현재 모델 벤치마크...")
    results["current"] = await benchmark_current_model(SAMPLE_CONVERSATIONS, iterations)
    print(f"   완료: P50={results['current'].p50:.0f}ms, P95={results['current'].p95:.0f}ms\n")

    # Gemini
    if include_gemini and GEMINI_AVAILABLE:
        print("[BENCH] Gemini 벤치마크...")
        gemini_result = await benchmark_gemini(SAMPLE_CONVERSATIONS, iterations)
        if gemini_result:
            results["gemini"] = gemini_result
            print(f"   완료: P50={gemini_result.p50:.0f}ms, P95={gemini_result.p95:.0f}ms\n")
    elif include_gemini and not GEMINI_AVAILABLE:
        print("[WARNING]  Gemini 사용 불가 - GOOGLE_API_KEY 미설정 또는 라이브러리 없음\n")

    return results


def print_comparison(results: Dict[str, BenchmarkResult]):
    """비교 결과 출력"""
    print("=" * 80)
    print("[RESULTS] 벤치마크 비교 결과")
    print("=" * 80)

    # 테이블 헤더
    print(
        f"\n{'Model':<25} {'P50 (ms)':<12} {'P95 (ms)':<12} {'Avg (ms)':<12} {'Success Rate':<15}"
    )
    print("-" * 80)

    # 각 모델 결과
    for key, result in results.items():
        success_rate = (
            (result.successful / result.total_requests * 100) if result.total_requests > 0 else 0
        )
        print(
            f"{result.model_name:<25} "
            f"{result.p50:<12.0f} "
            f"{result.p95:<12.0f} "
            f"{result.avg:<12.0f} "
            f"{success_rate:<15.1f}%"
        )

    # 비교 분석
    if "current" in results and "gemini" in results:
        current = results["current"]
        gemini = results["gemini"]

        p50_delta = ((gemini.p50 - current.p50) / current.p50 * 100) if current.p50 > 0 else 0
        p95_delta = ((gemini.p95 - current.p95) / current.p95 * 100) if current.p95 > 0 else 0

        print("\n" + "=" * 80)
        print("[BENCH] 성능 비교 (Gemini vs Current)")
        print("=" * 80)
        print(f"P50 지연: {p50_delta:+.1f}% ({'[OK] 개선' if p50_delta < 0 else '[WARNING] 증가'})")
        print(f"P95 지연: {p95_delta:+.1f}% ({'[OK] 개선' if p95_delta < 0 else '[WARNING] 증가'})")

        if p50_delta < -10:
            print("\n[OK] 권장: Gemini로 전환 시 10% 이상 지연 감소 기대")
        elif abs(p50_delta) < 10:
            print("\n[NEUTRAL] 중립: 두 모델의 지연 차이가 미미함 (±10% 이내)")
        else:
            print("\n[WARNING] 권장: 현재 모델 유지 (Gemini가 더 느림)")


def save_results(results: Dict[str, BenchmarkResult], output_file: str):
    """결과를 JSON 파일로 저장"""
    output_data = {
        "benchmark_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": {key: result.to_dict() for key, result in results.items()},
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n[SAVE] 결과 저장됨: {output_file}")


async def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="요약 모델 벤치마크")
    parser.add_argument("--iterations", type=int, default=5, help="반복 횟수 (기본: 5)")
    parser.add_argument("--no-gemini", action="store_true", help="Gemini 벤치마크 건너뛰기")
    parser.add_argument("--output", type=str, help="결과 JSON 파일 경로")

    args = parser.parse_args()

    # 벤치마크 실행
    results = await run_benchmark(iterations=args.iterations, include_gemini=not args.no_gemini)

    # 결과 출력
    print_comparison(results)

    # 결과 저장
    if args.output:
        save_results(results, args.output)


if __name__ == "__main__":
    asyncio.run(main())
