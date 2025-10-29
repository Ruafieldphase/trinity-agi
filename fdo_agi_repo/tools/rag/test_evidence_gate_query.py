#!/usr/bin/env python3
"""Test evidence_gate RAG query with exact parameters to debug hits=0 issue."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tools.rag.config_loader import get_rag_config
from tools.rag.retriever import rag_query

def test_evidence_gate_query():
    """Replicate evidence_gate RAG call with exact config."""
    # Load evidence_gate config
    rcfg = get_rag_config().get("evidence_gate", {})
    top_k = int(rcfg.get("top_k", 5))
    include_types = rcfg.get("include_types")
    min_relevance = float(rcfg.get("min_relevance", 0.3))
    
    # Test query (from task 3c77c761)
    query = "force replan (no citations)"
    
    print(f"Testing evidence_gate RAG query:")
    print(f"  Query: {query}")
    print(f"  top_k: {top_k}")
    print(f"  include_types: {include_types}")
    print(f"  min_relevance: {min_relevance}")
    print()
    
    # Call RAG
    result = rag_query(query, top_k=top_k, include_types=include_types)
    
    print(f"Result:")
    print(f"  ok: {result.get('ok')}")
    print(f"  total_found (initial): {result.get('initial_total_found')}")
    print(f"  total_found (after filters): {result.get('total_found')}")
    print(f"  hits returned: {len(result.get('hits', []))}")
    print(f"  used_fallback: {result.get('used_fallback')}")
    print()
    
    hits = result.get('hits', [])
    if hits:
        print(f"Top {min(3, len(hits))} hits:")
        for i, h in enumerate(hits[:3], 1):
            print(f"  {i}. coord_id={h.get('id', 'N/A')[:12]}... rel={h.get('relevance', 0):.4f}")
            print(f"     snippet: {h.get('snippet', '')[:80]}...")
    else:
        print("  No hits returned!")
    
    # Check quality filter
    print()
    print(f"Quality filter (rel >= {min_relevance}):")
    quality_hits = [h for h in hits if h.get('relevance', 0) >= min_relevance]
    print(f"  Quality hits: {len(quality_hits)} / {len(hits)}")
    if not quality_hits and hits:
        print(f"  All hits filtered out! Top relevance: {max(h.get('relevance', 0) for h in hits):.4f}")

if __name__ == "__main__":
    test_evidence_gate_query()
