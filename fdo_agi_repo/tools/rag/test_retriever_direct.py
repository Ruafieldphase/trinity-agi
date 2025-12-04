#!/usr/bin/env python3
"""Direct retriever test for failing evidence_correction cases"""
import sys
import os
import json
import pytest

# Add repo root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.rag.retriever import rag_query

@pytest.mark.skip(reason="manual smoke script; not a pytest-driven unit test")
def test_query(query, include_types=None, top_k=8):
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"include_types: {include_types}")
    print(f"top_k: {top_k}")
    print(f"{'='*60}")
    
    result = rag_query(
        query=query,
        top_k=top_k,
        include_types=include_types,
        fallback_on_empty=True
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nSummary:")
    print(f"  OK: {result.get('ok')}")
    print(f"  Hits: {len(result.get('hits', []))}")
    print(f"  Total found: {result.get('total_found')}")
    print(f"  Initial total: {result.get('initial_total_found')}")
    print(f"  Used fallback: {result.get('used_fallback')}")
    
    if result.get('hits'):
        print(f"\n  Top 3 hits:")
        for i, hit in enumerate(result['hits'][:3], 1):
            print(f"    {i}. [{hit.get('source')}] {hit.get('id')} (rel: {hit.get('relevance')})")
            print(f"       Snippet: {hit.get('snippet', '')[:80]}")

if __name__ == "__main__":
    # Test 1: Force replan case (common in failing evidence_correction)
    test_query(
        "force replan (no citations)",
        include_types=['rune_validation', 'eval', 'rune', 'task_start', 'routing']
    )
    
    # Test 2: Korean realistic goal
    test_query(
        "AGI 자기교정 루프 설명 3문장",
        include_types=['rune_validation', 'eval', 'rune', 'task_start', 'routing']
    )
    
    # Test 3: Without filter (to see if filtering is the issue)
    test_query(
        "force replan (no citations)",
        include_types=None
    )
    
    # Test 4: Evidence test case
    test_query(
        "List 3 key benefits of BM25 retrieval with citations",
        include_types=['rune_validation', 'eval', 'rune', 'task_start', 'routing']
    )
