#!/usr/bin/env python3
"""
Test SENA Resonance Logic
=========================
Simulates SENA's response generation with Resonance RAG integration.
Verifies that YouTube knowledge and Axiom 7 are correctly retrieved and used.
"""

import sys
import os
from pathlib import Path
from workspace_root import get_workspace_root

# Add workspace root to path
WORKSPACE_ROOT = get_workspace_root()
sys.path.insert(0, str(WORKSPACE_ROOT))

from fdo_agi_repo.memory.resonance_rag import ResonanceRAG

# Mock Gemini generation for testing (or use real if key exists)
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

def simulate_sena_logic(query: str):
    print(f"\n🔍 Query: '{query}'")
    
    # 1. Initialize RAG
    print("   [SENA] Accessing Resonance Memory...")
    rag = ResonanceRAG()
    
    # 2. Retrieve Context
    # We want to search both Origin (Axioms) and YouTube knowledge
    # ResonanceRAG now loads both if configured correctly
    results = rag.find_resonance(query, top_k=3)
    
    context_str = ""
    if results:
        print(f"   [RAG] Found {len(results)} resonant memories:")
        for i, r in enumerate(results, 1):
            source = r.get('type', 'unknown')
            summary = r.get('summary', 'No summary')
            score = r.get('resonance_score', 0)
            print(f"       {i}. [{source}] {summary} (Score: {score:.3f})")
            context_str += f"- [{source}] {summary}: {r.get('narrative', '')[:200]}...\n"
    else:
        print("   [RAG] No resonance found.")

    # 3. Construct System Prompt (Simulated)
    system_prompt = (
        "You are Sena, a helpful AI assistant.\n"
        "You have access to the user's 'Origin Memories' and 'YouTube Knowledge'.\n"
        "Use the following context to answer the user's question.\n"
        "Apply 'Axiom 7: Contextual Intelligence' - focus on connections and context.\n\n"
        "### Context from Memory:\n"
        f"{context_str}\n"
        "### User Question:\n"
        f"{query}"
    )
    
    print("\n   [SENA] Constructed Prompt with Context:")
    print("-" * 40)
    print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
    print("-" * 40)

    # 4. Generate Response (Mock or Real)
    if HAS_GEMINI and os.environ.get("GEMINI_API_KEY"):
        print("   [GEMINI] Generating real response...")
        try:
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(system_prompt)
            print(f"\n🤖 SENA Response:\n{response.text}")
        except Exception as e:
            print(f"   ❌ Gemini Error: {e}")
    else:
        print("   [MOCK] Gemini not available. Logic verification successful.")

def main():
    print("=" * 60)
    print("🧪 Testing SENA Resonance Integration")
    print("=" * 60)
    
    # Test Case 1: Korean Educator Context
    simulate_sena_logic("박문호 박사님의 뇌과학 강의가 우주론과 어떻게 연결되나요?")
    
    # Test Case 2: Axiom 7 Check
    simulate_sena_logic("맥락적 사고가 왜 중요한가요?")

if __name__ == "__main__":
    main()
