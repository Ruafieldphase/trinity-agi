#!/usr/bin/env python3
"""
Debug Resonance Matching
========================
Detailed debugging script to identify why "배경자아의 역할" returns low-score results.

Shows:
- Query vector analysis
- Top 10 matches with scores
- Vector dimension comparison
- Potential issues
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict
from workspace_root import get_workspace_root

# Configuration
WORKSPACE_ROOT = get_workspace_root()
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

def create_feeling_vector(text: str) -> np.ndarray:
    """Create semantic embedding vector using sentence-transformers."""
    try:
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        embedding = model.encode(text, convert_to_numpy=True)
        
        return embedding
    except Exception as e:
        print(f"❌ Error creating vector: {e}")
        return None

def find_top_matches(query_vec: np.ndarray, top_k: int = 10) -> List[Dict]:
    """Find top K resonant memories with detailed debugging."""
    if not LEDGER_FILE.exists():
        print(f"❌ Ledger not found: {LEDGER_FILE}")
        return []
        
    matches = []
    
    v1 = query_vec
    norm1 = np.linalg.norm(v1)
    
    print(f"\n📊 Query Vector Stats:")
    print(f"   Dimension: {len(v1)}")
    print(f"   Norm: {norm1:.4f}")
    print(f"   Mean: {np.mean(v1):.4f}")
    print(f"   Std: {np.std(v1):.4f}")
    print(f"   Sample values: {v1[:5]}")
    
    print(f"\n🔍 Searching {LEDGER_FILE}...")
    
    entry_count = 0
    origin_memory_count = 0
    
    try:
        with open(LEDGER_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                entry_count += 1
                try:
                    entry = json.loads(line)
                    
                    # Check type filter
                    if entry.get('type') not in ['origin_memory', 'axiom']:
                        continue
                    
                    origin_memory_count += 1
                    
                    v2 = np.array(entry['vector'])
                    norm2 = np.linalg.norm(v2)
                    
                    # Cosine similarity
                    if norm1 > 0 and norm2 > 0:
                        resonance = np.dot(v1, v2) / (norm1 * norm2)
                    else:
                        resonance = 0.0
                    
                    matches.append({
                        'summary': entry.get('summary', 'No summary'),
                        'type': entry.get('type'),
                        'resonance': float(resonance),
                        'vector_dim': len(v2),
                        'vector_norm': float(norm2),
                        'narrative_preview': entry.get('narrative', '')[:100]
                    })
                    
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"   ⚠️ Error processing entry: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ Error reading ledger: {e}")
        return []
    
    print(f"\n📈 Search Stats:")
    print(f"   Total entries: {entry_count}")
    print(f"   Origin memories: {origin_memory_count}")
    print(f"   Matches found: {len(matches)}")
    
    # Sort by resonance score
    matches.sort(key=lambda x: x['resonance'], reverse=True)
    
    return matches[:top_k]

def main():
    queries = [
        "배경자아의 역할",
        "What is the role of the Background Self?",
        "무의식 관찰자의 기능",
        "메타인지와 자아"
    ]
    
    for query in queries:
        print("\n" + "="*70)
        print(f"❓ Query: \"{query}\"")
        print("="*70)
        
        # Create query vector
        query_vec = create_feeling_vector(query)
        if query_vec is None:
            continue
        
        # Find matches
        matches = find_top_matches(query_vec, top_k=10)
        
        if matches:
            print(f"\n✨ Top 10 Resonant Memories:")
            print("-" * 70)
            for i, match in enumerate(matches, 1):
                print(f"\n{i}. Score: {match['resonance']:.4f}")
                print(f"   Type: {match['type']}")
                print(f"   Summary: {match['summary']}")
                print(f"   Vector: dim={match['vector_dim']}, norm={match['vector_norm']:.4f}")
                print(f"   Preview: {match['narrative_preview']}...")
        else:
            print("\n⚠️ No matches found!")
        
        print()

if __name__ == "__main__":
    main()
