#!/usr/bin/env python3
"""
Save Conscious Learning
=======================
Allows the conscious layer (Windows Koa or Antigravity) to explicitly save learnings.
"""
import json
import argparse
from pathlib import Path
from datetime import datetime

# Paths
WORKSPACE_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
LEARNING_LOG = OUTPUTS_DIR / "conscious_learning.jsonl"

def save_learning(learnings=None, meta_insights=None, preferences=None, conversation_id=None, source="antigravity"):
    """Save conscious learnings to the log."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "conversation_id": conversation_id or "manual",
        "learnings": learnings or [],
        "meta_insights": meta_insights or [],
        "user_preferences": preferences or [],
        "source": source
    }
    
    try:
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(LEARNING_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"✅ Saved conscious learning to {LEARNING_LOG}")
        if learnings:
            for l in learnings:
                print(f"   📝 Learning: {l}")
        if meta_insights:
            for m in meta_insights:
                print(f"   🧠 Meta: {m}")
        if preferences:
            for p in preferences:
                print(f"   ⭐ Preference: {p}")
                
    except Exception as e:
        print(f"❌ Failed to save learning: {e}")

def main():
    parser = argparse.ArgumentParser(description="Save conscious learnings")
    parser.add_argument("--learning", "-l", action="append", help="Explicit insight or learning")
    parser.add_argument("--meta", "-m", action="append", help="Meta-cognitive insight")
    parser.add_argument("--preference", "-p", action="append", help="User preference")
    parser.add_argument("--conversation-id", "-c", help="Conversation ID")
    parser.add_argument("--source", "-s", default="antigravity", help="Source (antigravity, sian, sena, etc.)")
    
    args = parser.parse_args()
    
    if not (args.learning or args.meta or args.preference):
        print("❌ Please provide at least one learning, meta-insight, or preference")
        parser.print_help()
        return
    
    save_learning(
        learnings=args.learning,
        meta_insights=args.meta,
        preferences=args.preference,
        conversation_id=args.conversation_id,
        source=args.source
    )

if __name__ == "__main__":
    main()
