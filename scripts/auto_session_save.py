#!/usr/bin/env python3
"""
Automatic Session Save - Antigravity Agent Context Preservation

This script automatically saves the current Antigravity Agent session context
to resonance_ledger.jsonl when called. It should be triggered:
1. On user logout/shutdown
2. Periodically (via heartbeat)
3. On idle timeout

Usage:
    python scripts/auto_session_save.py
    python scripts/auto_session_save.py --session-id "custom_id"
"""
import argparse
import json
from datetime import datetime
from pathlib import Path
from workspace_root import get_workspace_root


def save_session_context(workspace_root: Path, session_id: str = None, summary: str = None):
    """
    Save current session context to resonance ledger
    
    Args:
        workspace_root: Workspace root path
        session_id: Optional custom session ID
        summary: Optional custom summary
    """
    if session_id is None:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    if summary is None:
        summary = "Antigravity Agent session - automatic save"
    
    ledger_path = workspace_root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "session_save_auto",
        "source": "auto_session_save",
        "session_id": session_id,
        "summary": summary,
        "resonance_score": 0.7,
        "where": "antigravity_workspace",
        "who": "antigravity_agent",
        "what": "session_context_preservation"
    }
    
    with open(ledger_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"✅ Session saved: {session_id}")
    print(f"   Ledger: {ledger_path}")
    
    # Also update GEMINI.md
    try:
        import sys
        sys.path.insert(0, str(workspace_root / "scripts"))
        from gemini_memory_manager import GeminiMemoryManager
        
        manager = GeminiMemoryManager(workspace_root)
        result = manager.compress_old_memories(dry_run=False)
        print(f"✅ GEMINI.md updated: {result.get('message', 'OK')}")
    except Exception as e:
        print(f"⚠️  GEMINI.md update skipped: {e}")
    
    return entry


def main():
    parser = argparse.ArgumentParser(description="Automatic Session Save")
    parser.add_argument("--session-id", type=str, help="Custom session ID")
    parser.add_argument("--summary", type=str, help="Custom session summary")
    
    args = parser.parse_args()
    
    workspace = get_workspace_root()
    
    print("💾 Automatic Session Save")
    print("=" * 60)
    
    result = save_session_context(
        workspace,
        session_id=args.session_id,
        summary=args.summary
    )
    
    print("\n" + "=" * 60)
    print("✅ Session context preserved automatically")


if __name__ == "__main__":
    main()
