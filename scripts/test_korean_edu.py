#!/usr/bin/env python3
"""
Test Korean educational content search
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from fdo_agi_repo.memory.resonance_rag import ResonanceRAG

def test_korean_search():
    print("=" * 60)
    print("🎓 Testing Korean Educational Content Search")
    print("=" * 60)
    
    youtube_ledger = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "youtube_knowledge.jsonl"
    rag = ResonanceRAG(ledger_path=youtube_ledger)
    
    # Korean educational queries
    queries = [
        "뇌과학",
        "철학과 동양사상",
        "회복탄력성",
        "과학 실험",
        "Python 프로그래밍"
    ]
    
    for query in queries:
        print(f"\n❓ Query: \"{query}\"")
        results = rag.find_resonance(query, top_k=3)
        
        if results:
            for i, r in enumerate(results, 1):
                score = r.get('resonance_score', 0)
                print(f"   {i}. {r['summary'][:70]}...")
                print(f"      Score: {score:.3f}")
        else:
            print("   ❌ No results found")

if __name__ == "__main__":
    test_korean_search()
