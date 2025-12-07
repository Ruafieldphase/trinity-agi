#!/usr/bin/env python3
"""
YouTube Memory Seeder
======================
Converts YouTube analysis data into RAG-searchable memories.

This script:
1. Reads existing YouTube analysis JSON files
2. Generates semantic embeddings for video content
3. Saves to YouTube Knowledge Ledger for RAG search
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

# Configuration
YOUTUBE_DIR = WORKSPACE_ROOT / "outputs" / "youtube_learner"
YOUTUBE_LEDGER = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "youtube_knowledge.jsonl"

def load_embedding_model():
    """Load sentence-transformers model for embeddings"""
    try:
        from sentence_transformers import SentenceTransformer
        print("📦 Loading embedding model...")
        model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        print("✅ Model loaded")
        return model
    except ImportError:
        print("❌ sentence-transformers not installed")
        print("   Install: pip install sentence-transformers")
        sys.exit(1)

def extract_transcript_sample(subtitles: List[Dict], max_words: int = 500) -> str:
    """Extract a meaningful sample from the transcript"""
    words = []
    for sub in subtitles:
        words.extend(sub['text'].split())
        if len(words) >= max_words:
            break
    return " ".join(words[:max_words])

def process_video_analysis(analysis_path: Path, model) -> Dict[str, Any]:
    """Convert a single YouTube analysis into a memory entry"""
    print(f"\n📹 Processing: {analysis_path.stem}")
    
    with open(analysis_path, 'r', encoding='utf-8') as f:
        analysis = json.load(f)
    
    video_id = analysis['video_id']
    title = analysis['title']
    duration_min = analysis['duration'] / 60
    keywords = analysis.get('keywords', [])
    subtitles = analysis.get('subtitles', [])
    
    # Create summary
    transcript_sample = extract_transcript_sample(subtitles, max_words=500)
    summary_text = f"[YouTube] {title}"
    
    # Create searchable content
    content = f"{title}. Keywords: {', '.join(keywords[:10])}. {transcript_sample}"
    
    # Generate semantic vector
    print(f"   🧠 Generating embedding...")
    vector = model.encode(content, convert_to_numpy=True).tolist()
    
    # Create memory entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "youtube_memory",
        "summary": summary_text,
        "narrative": transcript_sample[:2000],  # First 2000 chars
        "vector": vector,
        "metadata": {
            "video_id": video_id,
            "duration_minutes": round(duration_min, 1),
            "keywords": keywords[:15],
            "url": f"https://youtube.com/watch?v={video_id}",
            "subtitle_count": len(subtitles)
        }
    }
    
    print(f"   ✅ Processed: {title[:50]}...")
    print(f"      Duration: {duration_min:.1f} min")
    print(f"      Keywords: {', '.join(keywords[:5])}")
    
    return entry

def main():
    print("=" * 60)
    print("🎬 YouTube Memory Seeder")
    print("=" * 60)
    
    # Find all analysis files
    analysis_files = list(YOUTUBE_DIR.glob("*_analysis.json"))
    
    if not analysis_files:
        print("⚠️ No YouTube analysis files found")
        print(f"   Expected location: {YOUTUBE_DIR}")
        return
    
    print(f"\n📊 Found {len(analysis_files)} YouTube analysis files")
    
    # Load embedding model
    model = load_embedding_model()
    
    # Ensure output directory exists
    YOUTUBE_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    
    # Process each video
    memories = []
    for analysis_file in analysis_files:
        try:
            entry = process_video_analysis(analysis_file, model)
            memories.append(entry)
        except Exception as e:
            print(f"   ❌ Failed to process {analysis_file.stem}: {e}")
            continue
    
    # Save to ledger
    print(f"\n💾 Saving {len(memories)} memories to ledger...")
    
    # Append to existing ledger (or create new)
    mode = 'a' if YOUTUBE_LEDGER.exists() else 'w'
    with open(YOUTUBE_LEDGER, mode, encoding='utf-8') as f:
        for entry in memories:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"✅ Saved to: {YOUTUBE_LEDGER}")
    print(f"\n📈 Total YouTube memories: {len(memories)}")
    
    # Show sample
    if memories:
        print("\n🎯 Sample memory:")
        sample = memories[0]
        print(f"   Title: {sample['summary']}")
        print(f"   Keywords: {', '.join(sample['metadata']['keywords'][:5])}")
        print(f"   URL: {sample['metadata']['url']}")
    
    print("\n✨ YouTube knowledge is now RAG-searchable!")

if __name__ == "__main__":
    main()
