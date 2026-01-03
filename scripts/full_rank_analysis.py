#!/usr/bin/env python3
"""
Complete Resonance Analysis
Find and score ALL documents, show where "배경자아의 역할 설명" ranks
"""

import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from workspace_root import get_workspace_root

WORKSPACE_ROOT = get_workspace_root()
LEDGER = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

query = "배경자아의 역할"

print("Loading model...")
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
query_vec = model.encode(query, convert_to_numpy=True)
query_norm = np.linalg.norm(query_vec)

print(f"Analyzing query: {query}\n")

results = []
target_found = False

with open(LEDGER, 'r') as f:
    for i, line in enumerate(f, 1):
        try:
            doc = json.loads(line)
            if doc.get('type') not in ['origin_memory', 'axiom']:
                continue
            
            summary = doc.get('summary', '')
            doc_vec = np.array(doc['vector'])
            doc_norm = np.linalg.norm(doc_vec)
            
            semantic = np.dot(query_vec, doc_vec) / (query_norm * doc_norm) if query_norm > 0 and doc_norm > 0 else 0.0
            
            results.append({
                'line': i,
                'summary': summary,
                'semantic': semantic
            })
            
            if '배경자아의 역할 설명' in summary:
                target_found = True
                print(f"🎯 TARGET FOUND at line {i}")
                print(f"   Summary: {summary}")
                print(f"   Raw Semantic Score: {semantic:.4f}")
                print()
                
        except:
            continue

# Sort by semantic score
results.sort(key=lambda x: x['semantic'], reverse=True)

print(f"Total documents: {len(results)}\n")

# Find target rank
target_rank = None
for rank, r in enumerate(results, 1):
    if '배경자아의 역할 설명' in r['summary']:
        target_rank = rank
        print(f"📊 TARGET RANK: {rank} / {len(results)}")
        print(f"   Semantic Score: {r['semantic']:.4f}")
        print()
        break

if not target_found:
    print("❌ Target document NOT FOUND in ledger!")
else:
    print("\n🏆 Top 20 by Semantic Score:")
    print("-" * 80)
    for i, r in enumerate(results[:20], 1):
        marker = " 🎯" if '배경자아의 역할 설명' in r['summary'] else ""
        print(f"{i}. {r['semantic']:.4f} - {r['summary'][:70]}...{marker}")
