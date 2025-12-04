#!/usr/bin/env python
"""
Baseline TTFT (Time To First Token) 측정 스크립트
Phase 2.6: Streaming Thesis 전 측정
"""
import os
import sys
import time
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).resolve().parent.parent / "fdo_agi_repo"
sys.path.insert(0, str(repo_root))

import google.generativeai as genai  # type: ignore[import]

def measure_baseline_ttft():
    """기존 non-streaming TTFT 측정"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set")
        return
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    prompt = (
        "# 작업: AGI 자기교정 루프 실증 3문장 작성\n\n"
        "## 증거\n"
        "[참고 #1] resonance_ledger.jsonl에서 최근 50개 event 분석...\n"
        "[참고 #2] 파이프라인 구조상 Thesis → Antithesis → Synthesis 순서...\n\n"
        "위 증거를 기반으로 **구체적 작업 계획 3문장**을 작성하세요.\n"
        "(각 문장은 출처를 명시하세요. 예: [참고 #1]에 따르면...)"
    )
    
    print("🔍 Baseline TTFT 측정 시작...")
    print(f"   Prompt: {len(prompt)} chars")
    print()
    
    results = []
    for i in range(3):
        t0 = time.perf_counter()
        try:
            response = model.generate_content(prompt)
            t1 = time.perf_counter()
            total_time = t1 - t0
            text = response.text
            token_count = len(text.split())  # Rough estimate
            
            results.append({
                "run": i + 1,
                "total_time": total_time,
                "ttft": total_time,  # Non-streaming: TTFT = Total
                "tokens": token_count,
                "chars": len(text)
            })
            
            print(f"Run {i+1}: {total_time:.2f}s, {token_count} tokens, {len(text)} chars")
        except Exception as e:
            print(f"Run {i+1}: ❌ {e}")
    
    if results:
        avg_total = sum(r["total_time"] for r in results) / len(results)
        avg_tokens = sum(r["tokens"] for r in results) / len(results)
        
        print()
        print("📊 Baseline 통계:")
        print(f"   Average Total Time: {avg_total:.2f}s")
        print(f"   Average Tokens: {avg_tokens:.0f}")
        print(f"   TTFT (non-streaming): {avg_total:.2f}s (= Total Time)")
        print()
        print("🎯 목표: Streaming으로 TTFT를 50% 감소 (예: 5s → 2.5s)")

def measure_streaming_ttft():
    """Streaming TTFT 측정"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set")
        return
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    prompt = (
        "# 작업: AGI 자기교정 루프 실증 3문장 작성\n\n"
        "## 증거\n"
        "[참고 #1] resonance_ledger.jsonl에서 최근 50개 event 분석...\n"
        "[참고 #2] 파이프라인 구조상 Thesis → Antithesis → Synthesis 순서...\n\n"
        "위 증거를 기반으로 **구체적 작업 계획 3문장**을 작성하세요.\n"
        "(각 문장은 출처를 명시하세요. 예: [참고 #1]에 따르면...)"
    )
    
    print("🔍 Streaming TTFT 측정 시작...")
    print(f"   Prompt: {len(prompt)} chars")
    print()
    
    results = []
    for i in range(3):
        t0 = time.perf_counter()
        ttft = None
        chunks = []
        
        try:
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if ttft is None:
                    ttft = time.perf_counter() - t0
                    print(f"   ⚡ First token at {ttft:.3f}s")
                
                if hasattr(chunk, 'text'):
                    chunks.append(chunk.text)
            
            t1 = time.perf_counter()
            total_time = t1 - t0
            text = "".join(chunks)
            token_count = len(text.split())
            
            results.append({
                "run": i + 1,
                "total_time": total_time,
                "ttft": ttft or total_time,
                "tokens": token_count,
                "chars": len(text)
            })
            
            print(f"Run {i+1}: Total {total_time:.2f}s, TTFT {ttft:.3f}s, {token_count} tokens")
        except Exception as e:
            print(f"Run {i+1}: ❌ {e}")
    
    if results:
        avg_total = sum(r["total_time"] for r in results) / len(results)
        avg_ttft = sum(r["ttft"] for r in results) / len(results)
        avg_tokens = sum(r["tokens"] for r in results) / len(results)
        
        print()
        print("📊 Streaming 통계:")
        print(f"   Average Total Time: {avg_total:.2f}s")
        print(f"   Average TTFT: {avg_ttft:.3f}s")
        print(f"   Average Tokens: {avg_tokens:.0f}")
        print(f"   Perceived Improvement: {(1 - avg_ttft/avg_total)*100:.1f}%")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    
    if mode == "streaming":
        measure_streaming_ttft()
    else:
        measure_baseline_ttft()
