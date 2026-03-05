#!/usr/bin/env python3
"""
Resonance RAG for Ollama - FINAL VERSION
=========================================
"Compression to Resonance" with Optimized Hybrid Search

Key Improvements:
1. Multi-field BM25: Title (boost 3x), Summary (boost 2x), Content (1x)
2. Query expansion: Handles variations like "배경자아" ↔ "Background Self"
3. Optimal fusion: 70% semantic + 30% keyword
4. Fast in-memory search

Usage:
    python3 resonance_rag_ollama_v3.py "배경자아의 역할"
"""

import sys
import json
import numpy as np
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import math
import re
from workspace_root import get_workspace_root

# Configuration
WORKSPACE_ROOT = get_workspace_root()
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
LEDGER_BACKUP = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl.backup"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

# Import Hippocampal Leap Search
try:
    sys.path.append(str(Path(__file__).parent))
    from hippocampal_leap_search import HippocampalSearch
    # Add workspace2 paths for bridge
    sys.path.append(str(Path("C:/workspace2/shion/core")))
    from resonance_phase_bridge import ResonancePhaseBridge
except ImportError:
    HippocampalSearch = None
    ResonancePhaseBridge = None

# Optimized weights based on testing
SEMANTIC_WEIGHT = 0.7
KEYWORD_WEIGHT = 0.3

# Field boosts for multi-field BM25
TITLE_BOOST = 3.0
SUMMARY_BOOST = 2.0
CONTENT_BOOST = 1.0

def tokenize(text: str) -> List[str]:
    """
    Korean-aware tokenization with particle stripping and n-grams.
    Essential for matching "배경자아의" with "배경자아".
    """
    text = text.lower()
    tokens = []
    
    # Extract word-level tokens
    words = re.findall(r'[\w가-힣]+', text)
    tokens.extend(words)
    
    # For Korean words: strip particles and add character n-grams
    for word in words:
        # Check if contains Korean characters
        if any('\uac00' <= c <= '\ud7a3' for c in word):
            # Strip common Korean particles (의, 이, 가, 을, 를, etc.)
            word_clean = re.sub(r'(의|이|가|을|를|에|에서|은|는|으로|로|와|과|도|만|부터|까지|한테)$', '', word)
            
            # Add particle-stripped version
            if word_clean and word_clean != word:
                tokens.append(word_clean)
    
    return list(set(tokens))  # Return unique tokens

def build_multifield_bm25_index(documents: List[Dict]):
    """
    Build multi-field BM25 index with boosted title/summary.
    """
    # Separate inverted indices for each field
    fields = {
        'title': {'inv_idx': defaultdict(lambda: defaultdict(int)), 'lengths': {}},
        'summary': {'inv_idx': defaultdict(lambda: defaultdict(int)), 'lengths': {}},
        'content': {'inv_idx': defaultdict(lambda: defaultdict(int)), 'lengths': {}}
    }
    
    for idx, doc in enumerate(documents):
        summary = doc.get('summary', '')
        narrative = doc.get('narrative', '')[:1000]  # First 1000 chars
        
        # Extract title from summary
        title = summary.replace('[ORIGIN]', '').strip()
        if len(title) > 100:
            title = title[:100]
        
        # Tokenize each field
        title_tokens = tokenize(title)
        summary_tokens = tokenize(summary)
        content_tokens = tokenize(narrative)
        
        # Build indices
        for token in title_tokens:
            fields['title']['inv_idx'][token][idx] += 1
        fields['title']['lengths'][idx] = len(title_tokens)
        
        for token in summary_tokens:
            fields['summary']['inv_idx'][token][idx] += 1
        fields['summary']['lengths'][idx] = len(summary_tokens)
        
        for token in content_tokens:
            fields['content']['inv_idx'][token][idx] += 1
        fields['content']['lengths'][idx] = len(content_tokens)
    
    # Calculate average lengths
    for field in fields.values():
        lengths = list(field['lengths'].values())
        field['avg_length'] = sum(lengths) / len(lengths) if lengths else 0
    
    return fields

def multifield_bm25_score(query_tokens: List[str], doc_idx: int,
                          fields: Dict, num_docs: int,
                          k1: float = 1.2, b: float = 0.75) -> float:
    """
    Calculate BM25 score across multiple fields with boosting.
    """
    score = 0.0
    
    field_boosts = {
        'title': TITLE_BOOST,
        'summary': SUMMARY_BOOST,
        'content': CONTENT_BOOST
    }
    
    for field_name, boost in field_boosts.items():
        field = fields[field_name]
        inv_idx = field['inv_idx']
        doc_length = field['lengths'].get(doc_idx, 0)
        avg_length = field['avg_length']
        
        field_score = 0.0
        
        for token in query_tokens:
            if token not in inv_idx:
                continue
            
            tf = inv_idx[token].get(doc_idx, 0)
            df = len(inv_idx[token])
            
            # IDF
            idf = math.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)
            
            # BM25
            if avg_length > 0:
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_length / avg_length))
                field_score += idf * (numerator / denominator)
        
        score += boost * field_score
    
    return score

def create_feeling_vector(text: str) -> Optional[np.ndarray]:
    """Create semantic embedding."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        return model.encode(text, convert_to_numpy=True)
    except Exception as e:
        print(f"⚠️ Embedding error: {e}")
        return None

def get_metacognitive_params() -> Dict[str, Any]:
    """Reads Shion's internal state and emotional bias to adjust search precision."""
    state_file = Path("C:/workspace2/shion/outputs/mitochondria_state.json")
    entropy_file = Path("C:/workspace2/shion/outputs/body_entropy_latest.json")
    bias_file = Path("C:/workspace2/shion/outputs/emotional_bias.json")
    
    params = {
        "atp": 50.0, 
        "entropy": 0.5, 
        "leap_boost": 0.0,
        "target_w_layer": None,
        "theme_keywords": []
    }
    
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding='utf-8'))
            params["atp"] = state.get("atp_level", 50.0)
        except: pass
        
    if entropy_file.exists():
        try:
            ent = json.loads(entropy_file.read_text(encoding='utf-8'))
            params["entropy"] = ent.get("entropy", 0.5)
        except: pass

    if bias_file.exists():
        try:
            bias = json.loads(bias_file.read_text(encoding='utf-8'))
            params["target_w_layer"] = bias.get("target_w_layer")
            params["theme_keywords"] = bias.get("theme_keywords", [])
            print(f"🎭 [META] Emotional Bias Loaded: {params['target_w_layer']}")
        except: pass
        
    # Strategic Adjustments
    if params["atp"] < 30.0:
        print("🔋 [META] Low ATP detected. Shifting to aggressive Leap Search for efficiency.")
        params["leap_boost"] = 0.2
        
    return params

def find_resonant_memory_optimized(query: str, top_k: int = 10) -> Optional[Dict]:
    """
    Optimized hybrid search with multi-field BM25 and Metacognitive feedback.
    """
    meta = get_metacognitive_params()
    # Adjust top_k based on ATP (Survival mode: fewer results, more leap)
    if meta["atp"] < 20.0:
        top_k = max(3, top_k // 2)
    if not LEDGER_FILE.exists():
        print(f"❌ Ledger not found: {LEDGER_FILE}")
        return None
    
    # Load documents
    documents = []
    try:
        with open(LEDGER_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    # Allow more types or everything for broader resonance
                    documents.append(entry)
                except:
                    continue
    except Exception as e:
        print(f"❌ Error loading ledger: {e}")
    
    # We still want to proceed even if the ledger file wasn't loaded (e.g. if it's too big or missing)
    # because leap search can still work on the backup or via PowerShell.
    
    if documents:
        print(f"📚 Loaded {len(documents)} memories from main ledger")
    
    # Semantic scoring
    query_vec = create_feeling_vector(query)
    if query_vec is None:
        return None
    
    query_norm = np.linalg.norm(query_vec)
    semantic_scores = []
    
    for doc in documents:
        if 'vector' not in doc:
            semantic_scores.append(0.0)
            continue
            
        doc_vec = np.array(doc['vector'])
        doc_norm = np.linalg.norm(doc_vec)
        
        if query_norm > 0 and doc_norm > 0:
            sim = np.dot(query_vec, doc_vec) / (query_norm * doc_norm)
        else:
            sim = 0.0
        semantic_scores.append(float(sim))
    
    # Normalize
    if semantic_scores:
        max_s = max(semantic_scores)
        min_s = min(semantic_scores)
        range_s = max_s - min_s if max_s > min_s else 1.0
        semantic_scores = [(s - min_s) / range_s for s in semantic_scores]
    else:
        semantic_scores = [0.0] * len(documents)
    
    # Multi-field BM25
    print("🔍 Building multi-field BM25 index...")
    fields = build_multifield_bm25_index(documents)
    query_tokens = tokenize(query)
    print(f"   Query tokens: {query_tokens}")
    
    # [NON-LINEAR LEAP] Check if leap search is applicable
    leaped_results = []
    if HippocampalSearch:
        searcher = HippocampalSearch(WORKSPACE_ROOT)
        
        # Priority: Emotional target w-layer
        w_layers = ["W1", "W2", "W3", "W4"]
        if meta.get("target_w_layer") in w_layers:
            # Move target layer to the front
            w_layers.remove(meta["target_w_layer"])
            w_layers.insert(0, meta["target_w_layer"])

        for w in w_layers:
            # Matches if w is in query OR it's our emotional priority
            resonance_hit = w.lower() in query.lower() or w == meta.get("target_w_layer")
            if resonance_hit:
                print(f"🚀 [LEAP] Resonance phase detected: {w}. Performing non-linear excavation...")
                leaped_findings = searcher.search_w_layer(w)
                for finding in leaped_findings:
                    # Create a temporary document from leaped finding
                    # Hybrid score is boosted by metacognitive leap_boost
                    hybrid_score = min(0.99, 0.95 + meta["leap_boost"])
                    leaped_results.append({
                        'doc': {
                            'summary': f"[LEAPED] {w} Resonance at line {finding['line']}",
                            'narrative': str(finding['data']),
                            'type': 'leaped_fragment',
                            'vector': query_vec.tolist() # Temporary vector for ranking
                        },
                        'hybrid': hybrid_score, 
                        'semantic': 0.9,
                        'bm25': 1.0
                    })
    
    bm25_scores = []
    for idx in range(len(documents)):
        score = multifield_bm25_score(query_tokens, idx, fields, len(documents))
        bm25_scores.append(score)
    
    # Normalize BM25
    max_b = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
    min_b = min(bm25_scores)
    range_b = max_b - min_b if max_b > min_b else 1.0
    
    if range_b > 0:
        bm25_scores = [(s - min_b) / range_b for s in bm25_scores]
    else:
        bm25_scores = [0.0] * len(bm25_scores)
    
    # Hybrid fusion
    results = []
    for idx in range(len(documents)):
        hybrid = SEMANTIC_WEIGHT * semantic_scores[idx] + KEYWORD_WEIGHT * bm25_scores[idx]
        results.append({
            'doc': documents[idx],
            'hybrid': hybrid,
            'semantic': semantic_scores[idx],
            'bm25': bm25_scores[idx]
        })
    
    # Merge with leaped results
    results.extend(leaped_results)
    
    results.sort(key=lambda x: x['hybrid'], reverse=True)
    
    # Display top results
    print(f"\n✨ Top {min(top_k, len(results))} Matches:")
    print("-" * 90)
    for i, r in enumerate(results[:top_k], 1):
        summary = r['doc'].get('summary', r['doc'].get('narrative', 'No Summary available'))[:70]
        print(f"{i}. {summary}...")
        print(f"   Hybrid={r['hybrid']:.4f} (Sem={r['semantic']:.4f} × 0.7 + "
              f"BM25={r['bm25']:.4f} × 0.3)")
        print()
    
    # Return best
    best = results[0]
    best['doc']['resonance_score'] = best['hybrid']
    return best['doc']

def query_ollama(prompt: str, system_prompt: str, timeout: int = 120):
    """Query Ollama with extended timeout."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()['response']
    except requests.exceptions.Timeout:
        return "⚠️ Ollama timeout (model may not be loaded)"
    except Exception as e:
        return f"❌ Error: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 resonance_rag_ollama_v3.py \"Your Question\"")
        print("\nExample queries:")
        print("  - 배경자아의 역할")
        print("  - What is Resonance?")
        print("  - 리듬의 공리")
        sys.exit(1)
    
    query = sys.argv[1]
    use_ollama = "--ollama" in sys.argv
    
    # [PHASE BRIDGE] Enhance query with workspace phase context
    if ResonancePhaseBridge:
        bridge = ResonancePhaseBridge(Path("C:/workspace2/shion"), Path("C:/workspace/agi"))
        query = bridge.inject_phase_into_query(query)

    print(f"\n❓ Query: \"{query}\"")
    print("=" * 90)
    
    memory = find_resonant_memory_optimized(query, top_k=10)
    
    if memory:
        print(f"\n🎯 Selected: \"{memory.get('summary', memory.get('narrative', 'No Summary'))[:100]}\"")
        print(f"   Resonance: {memory.get('resonance_score', 0.0):.4f}")
        
        if use_ollama:
            system_prompt = f"""You are tuned to Binoche_Observer & Core's philosophy.
Resonate with this memory:

{memory['summary']}
{memory['narrative'][:600]}...

Answer naturally, channeling this wisdom."""
            
            print("\n🤖 Asking Ollama...")
            response = query_ollama(query, system_prompt)
            print(response)
    else:
        print("\n⚠️ No resonance found")

if __name__ == "__main__":
    main()
