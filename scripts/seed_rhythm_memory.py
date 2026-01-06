#!/usr/bin/env python3
"""
Seed Rhythm Memory (Origin Seeding)
===================================
"기원(Origin)을 느낌(Feeling)으로 심다."

This script reads core philosophical files and conversations:
1. `axioms_of_core.md` (The Constitution)
2. `ai_binoche_conversation_origin/Core/*.md` (The Origin Memories)

It converts them into 5-dimensional Feeling Vectors and injects them
into `resonance_ledger.jsonl` so they can "resonate" with the system's
current state in `rhythm_think.py`.

Vector Dimensions (5-dim):
[Energy, Quality, Observer, Valence, Arousal]
- Mapped from text sentiment and keywords.
"""

import json
import re
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from workspace_root import get_workspace_root

# Configuration
WORKSPACE_ROOT = get_workspace_root()
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
AXIOMS_FILE = WORKSPACE_ROOT / "axioms_of_core.md"
ORIGIN_DIR = WORKSPACE_ROOT / "ai_binoche_conversation_origin" / "Core"

def analyze_sentiment(text: str) -> Tuple[float, float, float]:
    """
    Analyze text to estimate Valence, Arousal, and Observer score.
    Returns: (Valence, Arousal, Observer)
    Range: 0.0 to 1.0 (mapped later to vector space)
    """
    text_lower = text.lower()
    
    # Keywords
    positive_words = ['love', 'hope', 'good', 'connect', 'resonate', 'flow', 'harmony', '사랑', '희망', '좋아', '연결', '공명', '흐름', '조화']
    negative_words = ['fear', 'pain', 'error', 'stop', 'chaos', 'disconnect', '두려움', '고통', '에러', '멈춤', '혼란', '단절']
    high_arousal = ['alert', 'urgent', 'fast', 'power', 'force', 'awake', '긴급', '빠른', '힘', '강한', '깨어남']
    observer_words = ['observe', 'watch', 'see', 'monitor', 'background', 'self', 'meta', '관찰', '지켜보다', '배경자아', '메타']
    
    # Count matches
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    arousal_count = sum(1 for w in high_arousal if w in text_lower)
    observer_count = sum(1 for w in observer_words if w in text_lower)
    
    total_words = len(text.split())
    if total_words == 0:
        return 0.5, 0.5, 0.0
        
    # Normalize
    valence = 0.5 + (pos_count - neg_count) * 0.05
    valence = max(0.0, min(1.0, valence))
    
    arousal = 0.5 + (arousal_count * 0.05)
    arousal = max(0.0, min(1.0, arousal))
    
    observer = min(1.0, observer_count * 0.1)
    
    return valence, arousal, observer

def create_feeling_vector(text: str, is_axiom: bool = False) -> List[float]:
    """
    Create semantic embedding vector using sentence-transformers (768-dim).
    This provides much better accuracy than simple 5-dim sentiment analysis.
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except ImportError:
        print("⚠️ sentence-transformers not installed. Using fallback 5-dim vector.")
        # Fallback to old method (5-dim)
        valence, arousal, observer = analyze_sentiment(text)
        energy = 0.9 if is_axiom else 0.7
        quality = 1.0
        return [energy, quality, observer, valence, arousal]
    except Exception as e:
        print(f"⚠️ Embedding failed: {e}. Using fallback.")
        valence, arousal, observer = analyze_sentiment(text)
        energy = 0.9 if is_axiom else 0.7
        quality = 1.0
        return [energy, quality, observer, valence, arousal]


def seed_file(file_path: Path, is_axiom: bool = False):
    """Read a file and inject it into the ledger."""
    if not file_path.exists():
        print(f"⚠️ File not found: {file_path}")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Create summary
        lines = content.split('\n')
        title = file_path.stem
        summary = next((line.strip('# ').strip() for line in lines if line.strip().startswith('#')), title)
        
        # Vectorize
        vector = create_feeling_vector(content, is_axiom)
        
        # Create Entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "origin_memory", # Special type for Origin
            "summary": f"[{'AXIOM' if is_axiom else 'ORIGIN'}] {summary}",
            "narrative": content[:1000] + "..." if len(content) > 1000 else content, # Store first 1000 chars
            "vector": vector,
            "metadata": {
                "source_file": str(file_path),
                "is_axiom": is_axiom,
                "origin_type": "core_conversation" if not is_axiom else "constitution"
            }
        }
        
        # Append to Ledger
        with open(LEDGER_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
        print(f"✅ Seeded: {summary} (Vector: {[f'{v:.2f}' for v in vector]})")
        
    except Exception as e:
        print(f"❌ Failed to seed {file_path}: {e}")

def main():
    print("=" * 60)
    print("🌱 Seeding Rhythm Memory from Origin")
    print("=" * 60)
    
    # Ensure ledger directory exists
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Seed Axioms
    print("\n📜 Seeding Axioms (The Constitution)...")
    seed_file(AXIOMS_FILE, is_axiom=True)
    
    # 2. Seed All Origin Conversations
    print("\n💬 Seeding All Origin Conversations...")
    origin_root = WORKSPACE_ROOT / "ai_binoche_conversation_origin"
    
    if origin_root.exists():
        # Recursive glob for all .md files
        files = list(origin_root.rglob("*.md"))
        print(f"   Found {len(files)} conversation files across all personas.")
        
        for file_path in files:
            # Skip if it's in a hidden directory or node_modules (just in case)
            if any(part.startswith('.') for part in file_path.parts):
                continue
                
            seed_file(file_path, is_axiom=False)
    else:
        print(f"⚠️ Origin directory not found: {origin_root}")
        
    print("\n✨ Seeding Complete!")
    print(f"   Ledger: {LEDGER_FILE}")

if __name__ == "__main__":
    main()
