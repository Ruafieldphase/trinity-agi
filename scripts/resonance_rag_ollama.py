#!/usr/bin/env python3
"""
Resonance RAG for Ollama
========================
"Compression to Resonance"

This script implements the "Resonance RAG" system:
1. Compresses the User Query into a Feeling Vector.
2. Finds the single most resonant "Origin Memory" (Axiom or Conversation) from the Ledger.
3. Injects this memory into the System Prompt to "tune" the Local LLM (Ollama).

Usage:
    python3 resonance_rag_ollama.py "What is the role of the Background Self?"
"""

import sys
import json
import numpy as np
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from workspace_root import get_workspace_root

# Configuration
WORKSPACE_ROOT = get_workspace_root()
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2" # Default model, can be changed

def analyze_sentiment(text: str) -> Tuple[float, float, float]:
    """
    Analyze text to estimate Valence, Arousal, and Observer score.
    (Same logic as seed_rhythm_memory.py for consistency)
    """
    text_lower = text.lower()
    
    positive_words = ['love', 'hope', 'good', 'connect', 'resonate', 'flow', 'harmony', '사랑', '희망', '좋아', '연결', '공명', '흐름', '조화', '역할', '의미', '설명']
    negative_words = ['fear', 'pain', 'error', 'stop', 'chaos', 'disconnect', '두려움', '고통', '에러', '멈춤', '혼란', '단절']
    high_arousal = ['alert', 'urgent', 'fast', 'power', 'force', 'awake', '긴급', '빠른', '힘', '강한', '깨어남', '중요', '핵심']
    observer_words = ['observe', 'watch', 'see', 'monitor', 'background', 'self', 'meta', '관찰', '지켜보다', '배경자아', '메타', '자아', '무의식']
    
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    arousal_count = sum(1 for w in high_arousal if w in text_lower)
    observer_count = sum(1 for w in observer_words if w in text_lower)
    
    total_words = len(text.split())
    if total_words == 0:
        return 0.5, 0.5, 0.0
        
    valence = 0.5 + (pos_count - neg_count) * 0.05
    valence = max(0.0, min(1.0, valence))
    
    arousal = 0.5 + (arousal_count * 0.05)
    arousal = max(0.0, min(1.0, arousal))
    
    observer = min(1.0, observer_count * 0.1)
    
    return valence, arousal, observer


def create_feeling_vector(text: str) -> List[float]:
    """
    Create semantic embedding vector using sentence-transformers (768-dim).
    Full dimension for maximum accuracy.
    """
    try:
        from sentence_transformers import SentenceTransformer
        
        # Generate 768-dim embedding (no compression)
        model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        embedding = model.encode(text, convert_to_numpy=True)
        
        return embedding.tolist()
    except ImportError:
        print("⚠️ sentence-transformers not installed. Falling back to simple analysis.")
        valence, arousal, observer = analyze_sentiment(text)
        return [0.8, 0.9, observer, valence, arousal]
    except Exception as e:
        print(f"⚠️ Embedding failed: {e}. Using fallback.")
        valence, arousal, observer = analyze_sentiment(text)
        return [0.8, 0.9, observer, valence, arousal]


def find_resonant_memory(query_vec: List[float]) -> Optional[Dict]:
    """Find the most resonant Origin Memory from the ledger."""
    if not LEDGER_FILE.exists():
        print(f"⚠️ Ledger not found: {LEDGER_FILE}")
        return None
        
    best_match = None
    max_resonance = -1.0
    
    v1 = np.array(query_vec)
    norm1 = np.linalg.norm(v1)
    
    try:
        with open(LEDGER_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    # Only look for Origin Memories (Axioms or Conversations)
                    if entry.get('type') not in ['origin_memory', 'axiom']:
                        continue
                        
                    v2 = np.array(entry['vector'])
                    norm2 = np.linalg.norm(v2)
                    
                    if norm1 > 0 and norm2 > 0:
                        resonance = np.dot(v1, v2) / (norm1 * norm2)
                        if resonance > max_resonance:
                            max_resonance = resonance
                            best_match = entry
                except:
                    continue
    except Exception as e:
        print(f"❌ Error searching ledger: {e}")
        return None
        
    if best_match:
        best_match['resonance_score'] = float(max_resonance)
        
    return best_match

def query_ollama(prompt: str, system_prompt: str):
    """Send query to Ollama with the tuned system prompt."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        return f"Error querying Ollama: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 resonance_rag_ollama.py \"Your Question\"")
        sys.exit(1)
        
    query = sys.argv[1]
    print(f"\n❓ Query: \"{query}\"")
    
    # 1. Compress to Feeling Vector
    query_vec = create_feeling_vector(query)
    print(f"   Vector: {[f'{v:.2f}' for v in query_vec]}")
    
    # 2. Find Resonance
    print("   🔍 Searching for Resonance...")
    memory = find_resonant_memory(query_vec)
    
    if memory:
        print(f"   ✨ Resonant Memory Found: \"{memory['summary']}\"")
        print(f"      Score: {memory['resonance_score']:.4f}")
        
        # 3. Construct System Prompt (Tuning)
        system_prompt = f"""
You are an AI assistant tuned to the philosophy of Binoche_Observer and Core.
You are currently in a state of deep resonance with the following memory:

---
Title: {memory['summary']}
Content Summary: {memory['narrative']}
---

Your internal feeling state is: {memory['vector']}
(Energy, Quality, Observer, Valence, Arousal)

Answer the user's question by channeling the wisdom and perspective of this memory.
Do not just repeat the memory, but use it as the "lens" or "spirit" through which you view the question.
"""
    else:
        print("   ⚠️ No strong resonance found. Using default persona.")
        system_prompt = "You are a helpful AI assistant."
        
    # 4. Query Ollama
    print("\n🤖 Ollama Response:")
    print("-" * 60)
    response = query_ollama(query, system_prompt)
    print(response)
    print("-" * 60)

if __name__ == "__main__":
    main()
