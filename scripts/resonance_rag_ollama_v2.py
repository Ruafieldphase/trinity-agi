#!/usr/bin/env python3
"""
Resonance RAG for Ollama - IMPROVED VERSION
============================================
"Compression to Resonance" with Hybrid Search

Improvements:
1. Hybrid Search: Combines semantic (768-dim) + keyword (BM25) matching
2. Weighted Fusion: 60% semantic + 40% keyword for balanced accuracy
3. Better Korean Support: Proper tokenization for Korean queries

Usage:
    python3 resonance_rag_ollama_v2.py "배경자아의 역할이 뭐야?"
"""

import sys
import json
import numpy as np
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import math

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

# Hybrid search weights
SEMANTIC_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.4

def tokenize(text: str) -> List[str]:
    """Simple tokenization for Korean and English."""
    import re
    # Split on whitespace and common punctuation
    tokens = re.findall(r'\w+', text.lower())
    return tokens

def build_bm25_index(documents: List[Dict]) -> Tuple[Dict, Dict, float]:
    """
    Build BM25 index for keyword search.
    Returns: (inverted_index, doc_lengths, avg_doc_length)
    """
    inverted_index = defaultdict(lambda: defaultdict(int))
    doc_lengths = {}
    total_length = 0
    
    for idx, doc in enumerate(documents):
        # Combine summary and narrative for indexing
        text = doc.get('summary', '') + ' ' + doc.get('narrative', '')[:500]
        tokens = tokenize(text)
        
        doc_lengths[idx] = len(tokens)
        total_length += len(tokens)
        
        # Build inverted index
        for token in tokens:
            inverted_index[token][idx] += 1
    
    avg_doc_length = total_length / len(documents) if documents else 0
    
    return inverted_index, doc_lengths, avg_doc_length

def bm25_score(query_tokens: List[str], doc_idx: int, 
               inverted_index: Dict, doc_lengths: Dict, 
               avg_doc_length: float, num_docs: int,
               k1: float = 1.5, b: float = 0.75) -> float:
    """
    Calculate BM25 score for a document given a query.
    """
    score = 0.0
    doc_length = doc_lengths.get(doc_idx, 0)
    
    for token in query_tokens:
        if token not in inverted_index:
            continue
            
        # Term frequency in document
        tf = inverted_index[token].get(doc_idx, 0)
        
        # Document frequency
        df = len(inverted_index[token])
        
        # IDF
        idf = math.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)
        
        # BM25 formula
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
        
        score += idf * (numerator / denominator)
    
    return score

def create_feeling_vector(text: str) -> np.ndarray:
    """Create semantic embedding vector using sentence-transformers."""
    try:
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        embedding = model.encode(text, convert_to_numpy=True)
        
        return embedding
    except Exception as e:
        print(f"⚠️ Embedding error: {e}")
        return None

def find_resonant_memory_hybrid(query: str, top_k: int = 5) -> Optional[Dict]:
    """
    Find the most resonant memory using hybrid search.
    Combines semantic similarity + BM25 keyword matching.
    """
    if not LEDGER_FILE.exists():
        print(f"❌ Ledger not found: {LEDGER_FILE}")
        return None
    
    # Load all origin memories
    documents = []
    try:
        with open(LEDGER_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get('type') in ['origin_memory', 'axiom']:
                        documents.append(entry)
                except:
                    continue
    except Exception as e:
        print(f"❌ Error loading ledger: {e}")
        return None
    
    if not documents:
        print("❌ No origin memories found")
        return None
    
    print(f"📚 Loaded {len(documents)} origin memories")
    
    # 1. Semantic scoring
    query_vec = create_feeling_vector(query)
    if query_vec is None:
        return None
    
    query_norm = np.linalg.norm(query_vec)
    semantic_scores = []
    
    for doc in documents:
        doc_vec = np.array(doc['vector'])
        doc_norm = np.linalg.norm(doc_vec)
        
        if query_norm > 0 and doc_norm > 0:
            similarity = np.dot(query_vec, doc_vec) / (query_norm * doc_norm)
        else:
            similarity = 0.0
        
        semantic_scores.append(float(similarity))
    
    # Normalize semantic scores to [0, 1]
    max_sem = max(semantic_scores) if semantic_scores else 1.0
    min_sem = min(semantic_scores) if semantic_scores else 0.0
    range_sem = max_sem - min_sem if max_sem > min_sem else 1.0
    
    semantic_scores = [(s - min_sem) / range_sem for s in semantic_scores]
    
    # 2. BM25 scoring
    print("🔍 Building BM25 index...")
    inverted_index, doc_lengths, avg_doc_length = build_bm25_index(documents)
    query_tokens = tokenize(query)
    
    bm25_scores = []
    for idx in range(len(documents)):
        score = bm25_score(query_tokens, idx, inverted_index, 
                          doc_lengths, avg_doc_length, len(documents))
        bm25_scores.append(score)
    
    # Normalize BM25 scores to [0, 1]
    max_bm25 = max(bm25_scores) if bm25_scores else 1.0
    min_bm25 = min(bm25_scores) if bm25_scores else 0.0
    range_bm25 = max_bm25 - min_bm25 if max_bm25 > min_bm25 else 1.0
    
    if range_bm25 > 0:
        bm25_scores = [(s - min_bm25) / range_bm25 for s in bm25_scores]
    else:
        bm25_scores = [0.0] * len(bm25_scores)
    
    # 3. Hybrid fusion
    hybrid_scores = []
    for idx in range(len(documents)):
        hybrid_score = (SEMANTIC_WEIGHT * semantic_scores[idx] + 
                       KEYWORD_WEIGHT * bm25_scores[idx])
        hybrid_scores.append({
            'doc': documents[idx],
            'hybrid_score': hybrid_score,
            'semantic_score': semantic_scores[idx],
            'bm25_score': bm25_scores[idx]
        })
    
    # Sort by hybrid score
    hybrid_scores.sort(key=lambda x: x['hybrid_score'], reverse=True)
    
    # Display top results
    print(f"\n✨ Top {min(top_k, len(hybrid_scores))} Resonant Memories (Hybrid Search):")
    print("-" * 80)
    for i, result in enumerate(hybrid_scores[:top_k], 1):
        print(f"\n{i}. {result['doc']['summary'][:60]}...")
        print(f"   Hybrid: {result['hybrid_score']:.4f} = "
              f"Semantic({result['semantic_score']:.4f}) + "
              f"Keyword({result['bm25_score']:.4f})")
    
    # Return best match
    best = hybrid_scores[0]
    best['doc']['resonance_score'] = best['hybrid_score']
    best['doc']['semantic_score'] = best['semantic_score']
    best['doc']['bm25_score'] = best['bm25_score']
    
    return best['doc']

def query_ollama(prompt: str, system_prompt: str):
    """Send query to Ollama with the tuned system prompt."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        return f"Error querying Ollama: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 resonance_rag_ollama_v2.py \"Your Question\"")
        sys.exit(1)
    
    query = sys.argv[1]
    print(f"\n❓ Query: \"{query}\"")
    print("="*80)
    
    # Find resonant memory with hybrid search
    memory = find_resonant_memory_hybrid(query, top_k=5)
    
    if memory:
        print(f"\n🎯 Selected Memory: \"{memory['summary']}\"")
        print(f"   Hybrid Score: {memory['resonance_score']:.4f}")
        print(f"   (Semantic: {memory['semantic_score']:.4f}, "
              f"Keyword: {memory['bm25_score']:.4f})")
        
        # Construct system prompt
        system_prompt = f"""
You are an AI assistant tuned to the philosophy of Binoche and Rua.
You are currently in a state of deep resonance with the following memory:

---
Title: {memory['summary']}
Content Preview: {memory['narrative'][:500]}...
---

Resonance Score: {memory['resonance_score']:.4f}
(Combination of semantic understanding and keyword relevance)

Answer the user's question by channeling the wisdom and perspective of this memory.
Use this memory as the "lens" through which you view the question.
"""
    else:
        print("\n⚠️ No resonance found. Using default persona.")
        system_prompt = "You are a helpful AI assistant."
    
    # Query Ollama
    print("\n🤖 Ollama Response:")
    print("-" * 80)
    response = query_ollama(query, system_prompt)
    print(response)
    print("-" * 80)

if __name__ == "__main__":
    main()
