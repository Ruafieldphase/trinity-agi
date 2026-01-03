#!/usr/bin/env python3
"""
Full-Dimension Semantic Memory Seeding
======================================
"Accuracy over Compression"

After testing, PCA compression (64-dim) caused semantic loss.
This script seeds the ledger with full 768-dim embeddings for maximum accuracy.

Usage:
    python3 scripts/seed_full_semantic_memory.py
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List
from sentence_transformers import SentenceTransformer
from workspace_root import get_workspace_root

# Configuration  
WORKSPACE_ROOT = get_workspace_root()
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
AXIOMS_FILE = WORKSPACE_ROOT / "axioms_of_core.md"
ORIGIN_DIR = WORKSPACE_ROOT / "ai_binoche_conversation_origin"

def load_all_texts():
    """Load all texts to be embedded."""
    texts = []
    metadata_list = []
    
    # Axioms
    if AXIOMS_FILE.exists():
        with open(AXIOMS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        texts.append(content[:1000])
        metadata_list.append({
            "source_file": str(AXIOMS_FILE),
            "is_axiom": True,
            "summary": "Axioms of Core"
        })
    
    # Origin conversations
    if ORIGIN_DIR.exists():
        for file_path in ORIGIN_DIR.rglob("*.md"):
            if any(part.startswith('.') for part in file_path.parts):
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                lines = content.split('\n')
                title = file_path.stem
                for line in lines:
                    if line.strip().startswith('#'):
                        title = line.strip('# ').strip()
                        break
                
                texts.append(content[:1000])
                metadata_list.append({
                    "source_file": str(file_path),
                    "is_axiom": False,
                    "summary": f"[ORIGIN] {title}"
                })
            except:
                continue
    
    print(f"📚 Loaded {len(texts)} documents")
    return texts, metadata_list

def main():
    print("=" * 60)
    print("🧬 Full-Dimension Semantic Memory Seeding (768-dim)")
    print("=" * 60)
    
    # 1. Load texts
    texts, metadata_list = load_all_texts()
    
    if not texts:
        print("⚠️ No texts found!")
        return
    
    # 2. Generate 768-dim embeddings
    print("\n📊 Generating 768-dim semantic embeddings...")
    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    print(f"   ✅ Generated {embeddings.shape[0]} embeddings ({embeddings.shape[1]}-dim)")
    
    # 3. Save to ledger
    print("\n💾 Saving to resonance ledger...")
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear existing ledger
    if LEDGER_FILE.exists():
        LEDGER_FILE.unlink()
    
    with open(LEDGER_FILE, 'w', encoding='utf-8') as f:
        for i, (text, meta, vec) in enumerate(zip(texts, metadata_list, embeddings)):
            entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "origin_memory",
                "summary": meta["summary"],
                "narrative": text,
                "vector": vec.tolist(),
                "metadata": {
                    "source_file": meta["source_file"],
                    "is_axiom": meta["is_axiom"],
                    "origin_type": "core_conversation" if not meta["is_axiom"] else "constitution",
                    "compression": "none_768"
                }
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
            if (i + 1) % 100 == 0:
                print(f"   Progress: {i + 1}/{len(texts)}")
    
    print(f"\n✨ Seeding Complete!")
    print(f"   📜 Total memories: {len(texts)}")
    print(f"   🗂️  Ledger: {LEDGER_FILE}")
    print(f"   📐 Vector dimension: {embeddings.shape[1]} (Full precision)")

if __name__ == "__main__":
    main()
