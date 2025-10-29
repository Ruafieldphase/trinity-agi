"""
Hybrid RAG 테스트 스크립트
BM25 vs Dense vs Hybrid 검색 비교
"""
import sys
import os
import json
import pytest

# 리포지토리 루트를 sys.path에 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from tools.rag.retriever import rag_query
from tools.rag.hybrid_retriever import hybrid_rag_query

@pytest.mark.skip(reason="manual smoke script; not a pytest-driven unit test")
def test_query(query: str, top_k: int = 5):
    """쿼리 테스트 및 결과 비교"""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    # 1. BM25 전용
    print("\n[BM25 Only]")
    bm25_result = rag_query(query, top_k=top_k)
    print(f"Total found: {bm25_result.get('total_found', 0)}")
    for i, hit in enumerate(bm25_result.get('hits', [])[:3], 1):
        print(f"  {i}. {hit.get('id', 'N/A')} (relevance: {hit.get('relevance', 0):.3f})")
        print(f"     {hit.get('snippet', '')[:80]}...")
    
    # 2. Hybrid (BM25 + Dense)
    print("\n[Hybrid (BM25 + Dense)]")
    hybrid_result = hybrid_rag_query(query, top_k=top_k, enable_dense=True)
    print(f"Total found: {hybrid_result.get('total_found', 0)}")
    print(f"BM25 hits: {hybrid_result.get('bm25_hits', 0)}, Dense hits: {hybrid_result.get('dense_hits', 0)}")
    print(f"Used hybrid: {hybrid_result.get('used_hybrid', False)}")
    for i, hit in enumerate(hybrid_result.get('hits', [])[:3], 1):
        print(f"  {i}. {hit.get('id', 'N/A')} (relevance: {hit.get('relevance', 0):.3f})")
        print(f"     Source: {hit.get('source', 'N/A')}")
        print(f"     {hit.get('snippet', '')[:80]}...")


if __name__ == "__main__":
    print("📊 Hybrid RAG Performance Test\n")
    
    # 테스트 쿼리
    test_queries = [
        "BM25 retrieval algorithm implementation",
        "evidence gate correction with RAG",
        "task orchestration pipeline",
        "synthetic citation fallback strategy",
        "monitoring metrics and dashboard",
    ]
    
    for query in test_queries:
        test_query(query, top_k=5)
    
    print(f"\n{'='*60}")
    print("✅ Test Complete")
