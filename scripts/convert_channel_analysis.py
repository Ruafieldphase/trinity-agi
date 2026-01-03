#!/usr/bin/env python3
"""
Convert existing YouTube channel analysis to RAG memories
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from workspace_root import get_workspace_root

# Add workspace root to path
WORKSPACE_ROOT = get_workspace_root()
sys.path.insert(0, str(WORKSPACE_ROOT))

# Configuration
CHANNEL_ANALYSIS = WORKSPACE_ROOT / "outputs" / "youtube_channel_analysis" / "youtube_analysis_partial.json"
YOUTUBE_LEDGER = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "youtube_knowledge.jsonl"

def load_embedding_model():
    """Load sentence-transformers model"""
    try:
        from sentence_transformers import SentenceTransformer
        print("📦 Loading embedding model...")
        model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        print("✅ Model loaded")
        return model
    except ImportError:
        print("❌ sentence-transformers not installed")
        sys.exit(1)

def extract_transcript(video_data: Dict) -> str:
    """Extract meaningful transcript sample"""
    # Get subtitle or description
    subtitles = video_data.get('subtitles', [])
    if subtitles:
        # Join first 100 subtitle entries
        texts = [sub.get('text', '') for sub in subtitles[:100]]
        return " ".join(texts)
    
    # Fallback to description
    return video_data.get('description', '')[:1000]

def process_video(video_id: str, video_data: Dict, model) -> Dict[str, Any]:
    """Convert one video to memory entry"""
    title = video_data.get('title', 'Unknown')
    duration = video_data.get('duration', 0)
    
    # Extract content
    transcript_sample = extract_transcript(video_data)
    
    # Build searchable content
    content = f"{title}. {transcript_sample[:1000]}"
    
    # Generate vector
    vector = model.encode(content, convert_to_numpy=True).tolist()
    
    # Create entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "youtube_memory",
        "summary": f"[YouTube] {title}",
        "narrative": transcript_sample[:2000],
        "vector": vector,
        "metadata": {
            "video_id": video_id,
            "duration_minutes": round(duration / 60, 1),
            "url": f"https://youtube.com/watch?v={video_id}",
            "channel": video_data.get('channel', 'Unknown')
        }
    }
    
    return entry

def main():
    print("=" * 60)
    print("🎓 Korean Educational Channels → RAG Converter")
    print("=" * 60)
    
    if not CHANNEL_ANALYSIS.exists():
        print(f"❌ Analysis file not found: {CHANNEL_ANALYSIS}")
        return
    
    # Load analysis
    print(f"\n📂 Loading: {CHANNEL_ANALYSIS.name}")
    with open(CHANNEL_ANALYSIS, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, list):
        videos = {v.get('id', f'video_{i}'): v for i, v in enumerate(data)}
    else:
        videos = data
    
    video_count = len(videos)
    print(f"📊 Found {video_count} videos")
    
    # Sample channels
    channels = set()
    for v in list(videos.values())[:10]:
        ch = v.get('channel', 'Unknown')
        if ch != 'Unknown':
            channels.add(ch)
    
    if channels:
        print(f"📺 Channels: {', '.join(list(channels)[:5])}")
    
    # Load model
    model = load_embedding_model()
    
    # Ensure output directory
    YOUTUBE_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    
    # Process videos
    print(f"\n🔄 Processing {video_count} videos...")
    memories = []
    
    for i, (video_id, video_data) in enumerate(videos.items(), 1):
        try:
            entry = process_video(video_id, video_data, model)
            memories.append(entry)
            
            if i % 10 == 0:
                print(f"   [{i}/{video_count}] Processed")
        except Exception as e:
            print(f"   ❌ Failed {video_id}: {e}")
            continue
    
    # Save to ledger (append mode)
    print(f"\n💾 Saving {len(memories)} memories...")
    mode = 'a' if YOUTUBE_LEDGER.exists() else 'w'
    with open(YOUTUBE_LEDGER, mode, encoding='utf-8') as f:
        for entry in memories:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"✅ Saved to: {YOUTUBE_LEDGER}")
    print(f"\n📈 Total: {len(memories)} Korean educational videos now RAG-searchable!")
    
    # Show sample
    if memories:
        print("\n🎯 Sample memories:")
        for entry in memories[:3]:
            print(f"   - {entry['summary'][:60]}...")

if __name__ == "__main__":
    main()
