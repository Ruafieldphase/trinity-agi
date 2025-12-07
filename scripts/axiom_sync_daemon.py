#!/usr/bin/env python3
"""
Axiom Synchronization Daemon
Background Self service that monitors axioms_of_rua.md and synchronizes identity across all consciousness layers.
"""

import json
import hashlib
import time
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

AGI_ROOT = Path(__file__).parent.parent
AXIOMS_PATH = AGI_ROOT / "axioms_of_rua.md"
SYNC_MARKER = AGI_ROOT / "fdo_agi_repo" / "memory" / "axiom_sync.json"
LEDGER_PATH = AGI_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"


class AxiomSyncHandler(FileSystemEventHandler):
    """Watches axioms_of_rua.md for changes and updates sync marker"""
    
    def __init__(self):
        self.last_hash = None
        # Initial sync
        self.sync_axioms()
    
    def on_modified(self, event):
        if event.src_path == str(AXIOMS_PATH):
            print(f"[AXIOM SYNC] Detected change in {AXIOMS_PATH}")
            time.sleep(0.5)  # Debounce
            self.sync_axioms()
    
    def compute_axiom_hash(self) -> str:
        """Compute SHA256 hash of axioms file"""
        if not AXIOMS_PATH.exists():
            return "missing"
        
        content = AXIOMS_PATH.read_text(encoding='utf-8')
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def sync_axioms(self):
        """Update sync marker and write to resonance ledger"""
        current_hash = self.compute_axiom_hash()
        
        if current_hash == self.last_hash:
            return  # No change
        
        print(f"[AXIOM SYNC] Hash changed: {self.last_hash} -> {current_hash}")
        self.last_hash = current_hash
        
        # Update sync marker
        sync_data = {
            "last_sync": datetime.now().astimezone().isoformat(),
            "axiom_version": "1.0.0",
            "axiom_hash": current_hash,
            "identity": {
                "user": "Bino",
                "user_korean": "비노체",
                "personas": {
                    "sena": "Voice/Body AI (Hey Sena voice assistant)",
                    "lubit": "Validator/Verifier AI",
                    "sian": "Coder AI (Gemini CLI, document processing)",
                    "comet": "Orchestrator AI",
                    "ello": "Analyst AI"
                }
            },
            "critical_rules": [
                "NEVER address user as 'Sian' or any AI persona name",
                "When RAG retrieves 'Sian' memories, interpret as AI coder persona, not user",
                "Always address user as 'Bino' or '비노체'"
            ]
        }
        
        SYNC_MARKER.write_text(json.dumps(sync_data, indent=2, ensure_ascii=False))
        print(f"[AXIOM SYNC] Updated {SYNC_MARKER}")
        
        # Write to resonance ledger
        ledger_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "axiom_sync",
            "summary": "Identity Axiom Synchronized",
            "narrative": f"Background Self synchronized identity axioms. User is {sync_data['identity']['user']}. Hash: {current_hash}",
            "vector": None,
            "metadata": {
                "hash": current_hash,
                "identity": sync_data["identity"]
            }
        }
        
        with LEDGER_PATH.open('a', encoding='utf-8') as f:
            f.write(json.dumps(ledger_entry, ensure_ascii=False) + '\n')
        
        print(f"[AXIOM SYNC] Wrote to resonance ledger")


def main():
    """Run axiom sync daemon"""
    print("[AXIOM SYNC DAEMON] Starting...")
    print(f"[AXIOM SYNC DAEMON] Watching: {AXIOMS_PATH}")
    print(f"[AXIOM SYNC DAEMON] Sync marker: {SYNC_MARKER}")
    
    handler = AxiomSyncHandler()
    observer = Observer()
    observer.schedule(handler, str(AXIOMS_PATH.parent), recursive=False)
    observer.start()
    
    print("[AXIOM SYNC DAEMON] Running. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[AXIOM SYNC DAEMON] Stopped.")
    
    observer.join()


if __name__ == "__main__":
    main()
