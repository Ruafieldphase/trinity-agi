import json
from retriever import rag_query

if __name__ == "__main__":
    print("=== Query 1: Actual task goal (evidence test) ===")
    q1 = "List 3 key benefits of BM25 retrieval with citations"
    res1 = rag_query(q1, top_k=5)
    print(json.dumps(res1, ensure_ascii=False, indent=2))
    print(f"\n  Ledger docs in top 5: {sum(1 for h in res1.get('hits', []) if h.get('source') == 'resonance_ledger')}")
    print(f"  Coordinate docs in top 5: {sum(1 for h in res1.get('hits', []) if h.get('source') == 'coordinate')}")
    
    print("\n=== Query 2: Another realistic goal ===")
    q2 = "Explain self-correction loop in AGI system"
    res2 = rag_query(q2, top_k=5)
    print(json.dumps(res2, ensure_ascii=False, indent=2))
    print(f"\n  Ledger docs in top 5: {sum(1 for h in res2.get('hits', []) if h.get('source') == 'resonance_ledger')}")
    print(f"  Coordinate docs in top 5: {sum(1 for h in res2.get('hits', []) if h.get('source') == 'coordinate')}")
    print("\n--- With source filtering (rune_validation + eval) ---")
    res2f = rag_query(q2, top_k=5, include_types=['rune_validation', 'eval'])
    print(json.dumps(res2f, ensure_ascii=False, indent=2))
    print(f"\n  Ledger docs in top 5: {sum(1 for h in res2f.get('hits', []) if h.get('source') == 'resonance_ledger')}")
    print(f"  Coordinate docs in top 5: {sum(1 for h in res2f.get('hits', []) if h.get('source') == 'coordinate')}")
    
    print("\n=== Query 3: Force replan goal (test case) ===")
    q3 = "force replan (no citations)"
    res3 = rag_query(q3, top_k=5)
    print(json.dumps(res3, ensure_ascii=False, indent=2))
    print(f"\n  Ledger docs in top 5: {sum(1 for h in res3.get('hits', []) if h.get('source') == 'resonance_ledger')}")
    print(f"  Coordinate docs in top 5: {sum(1 for h in res3.get('hits', []) if h.get('source') == 'coordinate')}")


