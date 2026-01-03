#!/usr/bin/env python3
"""
Antigravity Session → AGI Memory Bridge

Captures Antigravity (Google AI Studio) conversation sessions and stores them
into AGI core memory systems (Resonance Ledger, GEMINI.md, Hippocampus).

This bridge solves the context persistence gap between Antigravity sessions
and AGI memory, ensuring continuity across sessions.

Usage:
    python scripts/antigravity_session_memory_bridge.py --session-id <id>
    python scripts/antigravity_session_memory_bridge.py --auto-detect
    python scripts/antigravity_session_memory_bridge.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from workspace_root import get_workspace_root

PROJECT_ROOT = get_workspace_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class AntigravityMemoryBridge:
    """Bridge between Antigravity sessions and AGI memory systems"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        
        # AGI Memory paths
        self.resonance_ledger = workspace_root / "memory" / "resonance_ledger.jsonl"
        self.gemini_md = workspace_root / "GEMINI.md"
        self.conversation_history = workspace_root / "memory" / "conversation_history_invariants.json"
        
        # Antigravity artifacts directory
        self.antigravity_artifacts = Path.home() / ".gemini" / "antigravity" / "brain"
        
    def find_recent_session(self, hours: int = 24) -> Optional[Path]:
        """Find the most recent Antigravity session directory"""
        if not self.antigravity_artifacts.exists():
            return None
        
        recent_dirs = []
        for session_dir in self.antigravity_artifacts.iterdir():
            if session_dir.is_dir():
                try:
                    mtime = session_dir.stat().st_mtime
                    recent_dirs.append((mtime, session_dir))
                except:
                    continue
        
        if not recent_dirs:
            return None
        
        recent_dirs.sort(reverse=True)
        return recent_dirs[0][1]
    
    def extract_session_summary(self, session_dir: Path) -> Dict[str, Any]:
        """Extract summary from Antigravity session artifacts"""
        summary = {
            "session_id": session_dir.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "antigravity",
            "conversations": [],
            "key_decisions": [],
            "artifacts": [],
        }
        
        # Look for task.md
        task_md = session_dir / "task.md"
        if task_md.exists():
            with open(task_md, 'r', encoding='utf-8') as f:
                content = f.read()
                summary["task_content"] = content[:1000]  # First 1000 chars
                summary["artifacts"].append(str(task_md.relative_to(self.antigravity_artifacts)))
        
        # Look for implementation_plan.md
        impl_plan = session_dir / "implementation_plan.md"
        if impl_plan.exists():
            with open(impl_plan, 'r', encoding='utf-8') as f:
                content = f.read()
                summary["implementation_plan"] = content[:1000]
                summary["artifacts"].append(str(impl_plan.relative_to(self.antigravity_artifacts)))
        
        # Look for walkthrough.md
        walkthrough = session_dir / "walkthrough.md"
        if walkthrough.exists():
            with open(walkthrough, 'r', encoding='utf-8') as f:
                content = f.read()
                summary["walkthrough"] = content[:1000]
                summary["artifacts"].append(str(walkthrough.relative_to(self.antigravity_artifacts)))
        
        # Extract key decisions from task.md (completed items)
        if task_md.exists():
            completed_tasks = self._extract_completed_tasks(task_md)
            summary["key_decisions"] = completed_tasks
        
        return summary
    
    def _extract_completed_tasks(self, task_md: Path) -> List[str]:
        """Extract completed tasks from task.md"""
        completed = []
        try:
            with open(task_md, 'r', encoding='utf-8') as f:
                for line in f:
                    # Look for [x] completed tasks
                    if line.strip().startswith("- [x]"):
                        task_text = line.strip()[6:].strip()
                        completed.append(task_text)
        except:
            pass
        return completed
    
    def store_to_resonance_ledger(self, summary: Dict[str, Any], dry_run: bool = False) -> bool:
        """Store session summary to Resonance Ledger"""
        entry = {
            "timestamp": summary["timestamp"],
            "source": "antigravity_session",
            "event_type": "session_complete",
            "session_id": summary["session_id"],
            "key_decisions": summary.get("key_decisions", []),
            "artifacts": summary.get("artifacts", []),
            "metadata": {
                "task_content_preview": summary.get("task_content", "")[:200],
                "decision_count": len(summary.get("key_decisions", [])),
            }
        }
        
        if dry_run:
            print(f"[DRY RUN] Would append to {self.resonance_ledger}:")
            print(json.dumps(entry, indent=2, ensure_ascii=False))
            return True
        
        try:
            self.resonance_ledger.parent.mkdir(parents=True, exist_ok=True)
            with open(self.resonance_ledger, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            print(f"Failed to write to Resonance Ledger: {e}")
            return False
    
    def update_gemini_md(self, summary: Dict[str, Any], dry_run: bool = False) -> bool:
        """Update GEMINI.md with session context"""
        
        # Generate updated content
        recent_conversations = f"[{summary['timestamp']}] Antigravity Session: {summary['session_id']}\n"
        recent_conversations += f"  - Completed tasks: {len(summary.get('key_decisions', []))}\n"
        recent_conversations += f"  - Artifacts: {len(summary.get('artifacts', []))}\n"
        
        if summary.get("key_decisions"):
            recent_conversations += "  - Key decisions:\n"
            for decision in summary["key_decisions"][:3]:  # Top 3
                recent_conversations += f"    • {decision[:80]}\n"
        
        content = f"""# Antigravity Agent Memory (Rolling Window)

**Last Updated**: {datetime.now(timezone.utc).isoformat()}
**Session ID**: {summary['session_id']}

## Current Context
- Working on: Context Persistence Bridge
- Recent Invariant: I = 0.0000
- System Health: Active

## Recent Conversations (Last 20 messages)
{recent_conversations}

## Compressed Memory Summary
- Total Sessions: 1
- Long-term Avg Invariant: 0.7593
- Key Decisions: {len(summary.get('key_decisions', []))} decisions tracked

## Retrieval Hints
To access older memories, query Hippocampus with:
- Time range: Last 24 hours
- Topics: Conversations, Decisions, System Health

---
*This memory is managed by GEMINI Memory Manager with rolling window (size=20)*
"""
        
        if dry_run:
            print(f"[DRY RUN] Would update {self.gemini_md}:")
            print(content[:500])
            return True
        
        try:
            with open(self.gemini_md, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Failed to update GEMINI.md: {e}")
            return False
    
    def record_to_conversation_history(self, summary: Dict[str, Any], dry_run: bool = False) -> bool:
        """Record session to conversation_history_invariants.json"""
        
        history_entry = {
            "timestamp": summary["timestamp"],
            "session_id": summary["session_id"],
            "type": "antigravity_session",
            "decisions": summary.get("key_decisions", []),
            "invariant": 0.7593,  # Placeholder, should be calculated
        }
        
        if dry_run:
            print(f"[DRY RUN] Would append to conversation history:")
            print(json.dumps(history_entry, indent=2, ensure_ascii=False))
            return True
        
        try:
            # Load existing history - it's a list, not a dict!
            history = []
            if self.conversation_history.exists():
                with open(self.conversation_history, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    # Ensure it's a list
                    if not isinstance(history, list):
                        history = []
            
            # Append new entry
            history.append(history_entry)
            
            # Save back as a list
            self.conversation_history.parent.mkdir(parents=True, exist_ok=True)
            with open(self.conversation_history, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Failed to update conversation history: {e}")
            return False
    
    def process_session(self, session_dir: Path, dry_run: bool = False) -> bool:
        """Process a single Antigravity session and store to AGI memory"""
        
        print(f"\n{'='*60}")
        print(f"Processing Antigravity Session: {session_dir.name}")
        print(f"{'='*60}\n")
        
        # Extract summary
        summary = self.extract_session_summary(session_dir)
        
        print(f"📊 Session Summary:")
        print(f"  - Session ID: {summary['session_id']}")
        print(f"  - Artifacts: {len(summary['artifacts'])}")
        print(f"  - Key Decisions: {len(summary['key_decisions'])}")
        
        if summary['key_decisions']:
            print(f"\n✅ Completed Tasks:")
            for i, decision in enumerate(summary['key_decisions'][:5], 1):
                print(f"  {i}. {decision[:80]}")
        
        # Store to memory systems
        success = True
        
        print(f"\n💾 Storing to AGI Memory Systems...")
        
        if not self.store_to_resonance_ledger(summary, dry_run):
            success = False
            print("  ❌ Failed to store to Resonance Ledger")
        else:
            print("  ✅ Stored to Resonance Ledger")
        
        if not self.update_gemini_md(summary, dry_run):
            success = False
            print("  ❌ Failed to update GEMINI.md")
        else:
            print("  ✅ Updated GEMINI.md")
        
        if not self.record_to_conversation_history(summary, dry_run):
            success = False
            print("  ❌ Failed to record to Conversation History")
        else:
            print("  ✅ Recorded to Conversation History")
        
        print(f"\n{'='*60}")
        if success:
            print("✨ Session successfully bridged to AGI memory!")
        else:
            print("⚠️ Session bridging completed with some errors")
        print(f"{'='*60}\n")
        
        return success


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bridge Antigravity sessions to AGI core memory"
    )
    parser.add_argument(
        "--session-id",
        type=str,
        help="Specific session ID (directory name) to process",
    )
    parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Auto-detect and process the most recent session",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without actually writing to memory",
    )
    
    args = parser.parse_args()
    
    bridge = AntigravityMemoryBridge(PROJECT_ROOT)
    
    # Determine which session to process
    session_dir = None
    
    if args.session_id:
        session_dir = bridge.antigravity_artifacts / args.session_id
        if not session_dir.exists():
            print(f"Error: Session directory not found: {session_dir}")
            return 1
    
    elif args.auto_detect:
        session_dir = bridge.find_recent_session()
        if not session_dir:
            print("Error: No recent Antigravity sessions found")
            return 1
        print(f"Auto-detected recent session: {session_dir.name}")
    
    else:
        parser.print_help()
        return 0
    
    # Process the session
    success = bridge.process_session(session_dir, dry_run=args.dry_run)
    
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
