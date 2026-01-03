#!/usr/bin/env python3
"""
Test YouTube RAG - verify YouTube knowledge search
"""

import sys
from pathlib import Path
from workspace_root import get_workspace_root

# Add workspace to path
WORKSPACE_ROOT = get_workspace_root()
sys.path.insert(0, str(WORKSPACE_ROOT))

from fdo_agi_repo.memory.resonance_rag import ResonanceRAG

def test_youtube_search():
    print("=" * 60)
    print("🎬 Testing YouTube Knowledge Search")
    print("=" * 60)
    
    # Load YouTube RAG
    youtube_ledger = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "youtube_knowledge.jsonl"
    rag = ResonanceRAG(ledger_path=youtube_ledger)
    
    # Test queries
    queries = [
        "How to learn Python programming?",
        "Python tutorial for beginners",
        "Rick Astley song",
        "Never gonna give you up"
    ]
    
    for query in queries:
        print(f"\n❓ Query: \"{query}\"")
        results = rag.find_resonance(query, top_k=2)
        
        if results:
            for i, r in enumerate(results, 1):
                print(f"   {i}. {r['summary']}")
                print(f"      Score: {r.get('resonance_score', r.get('score', 0)):.3f}")
                print(f"      URL: {r.get('metadata', {}).get('url', 'N/A')}")
                keywords = r.get('metadata', {}).get('keywords', [])
                if keywords:
                    print(f"      Keywords: {', '.join(keywords[:5])}")
        else:
            print("   ❌ No results found")

if __name__ == "__main__":
    test_youtube_search()
