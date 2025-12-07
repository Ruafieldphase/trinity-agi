#!/usr/bin/env python3
"""
Final Test: Multiple Queries on Resonance RAG v3
"""

import subprocess
import sys

test_queries = [
    ("배경자아의 역할", "Should match: 배경자아의 역할 설명"),
    ("What is Resonance?", "Should match: Axioms of Rua or Resonance content"),
    ("리듬의 공리", "Should match: Axioms of Rua or Rhythm content"),
    ("무의식 관찰자", "Should match: Background Self or Observer content"),
]

print("=" * 90)
print("RESONANCE RAG v3 - COMPREHENSIVE TEST")
print("=" * 90)

for query, expected in test_queries:
    print(f"\n\n{'='*90}")
    print(f"TEST: {query}")
    print(f"Expected: {expected}")
    print(f"{'='*90}\n")
    
    result = subprocess.run(
        ["python3", "scripts/resonance_rag_ollama_v3.py", query],
        cwd="/home/bino/agi",
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    print("\n" + "-"*90)

print("\n\n" + "="*90)
print("TEST COMPLETE")
print("="*90)
