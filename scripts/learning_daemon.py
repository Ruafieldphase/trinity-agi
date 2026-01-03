#!/usr/bin/env python3
"""
🧠 Learning Daemon
==================
Watches the Resonance Ledger for new experiences and reinforces patterns
in the Striatum Pattern Engine.

Flow:
1. Tail `resonance_ledger.jsonl`
2. Detect 'thought_stream' or 'action' entries
3. Extract Context (5W1H) + Action + Feeling/Outcome
4. Call StriatumPatternEngine.learn()
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, Optional

# Add script directory to path
import sys
from workspace_root import get_workspace_root
sys.path.append(str(Path(__file__).parent))

from striatum_pattern_engine import StriatumPatternEngine

# Configuration
WORKSPACE_ROOT = get_workspace_root()
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(WORKSPACE_ROOT / "outputs" / "logs" / "learning_daemon.log")
    ]
)
logger = logging.getLogger("LearningDaemon")

class LearningDaemon:
    def __init__(self):
        self.engine = StriatumPatternEngine(WORKSPACE_ROOT)
        self.ledger_path = LEDGER_FILE
        self.last_position = 0
        
    def _follow(self, file):
        """Generator that yields new lines from a file."""
        file.seek(0, 2) # Go to end
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

    def _extract_learning_data(self, entry: Dict) -> Optional[Dict]:
        """Extract Context, Action, Feeling from a ledger entry."""
        try:
            # We only learn from entries that have a clear outcome/feeling
            if entry.get('type') not in ['thought_stream', 'action_result', 'experience']:
                return None
                
            # Extract Context (Simplified for now)
            context = {
                "what": entry.get('summary', 'unknown'),
                "who": "system", # Default
                "where": "linux_brain", # Default
                "timestamp": entry.get('timestamp')
            }
            
            # Extract Action
            if entry.get('type') == 'thought_stream':
                # From Rhythm Think
                narrative = entry.get('narrative', '')
                # Parse narrative or use metadata?
                # Using metadata is safer if available
                meta = entry.get('metadata', {})
                action = {"decision": "unknown"} # Placeholder
                if 'related_pattern' in meta:
                    action['related_pattern'] = meta['related_pattern']
            else:
                action = entry.get('action', {})

            # Extract Feeling/Valence
            # If thought_stream, we might have resonance score
            meta = entry.get('metadata', {})
            valence = 0.0
            
            if 'resonance_score' in meta:
                valence = float(meta['resonance_score'])
            elif 'success' in entry:
                valence = 1.0 if entry['success'] else -0.5
            
            if valence == 0.0:
                return None # Nothing to learn
                
            return {
                "context": context,
                "action": action,
                "feeling": {"valence": valence}
            }
            
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return None

    def run(self):
        logger.info(f"🎓 Learning Daemon started. Watching {self.ledger_path}")
        
        # Ensure log dir exists
        (WORKSPACE_ROOT / "outputs" / "logs").mkdir(parents=True, exist_ok=True)
        
        if not self.ledger_path.exists():
            logger.warning(f"Ledger file not found at {self.ledger_path}. Waiting...")
            while not self.ledger_path.exists():
                time.sleep(5)
                
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            # Go to end of file
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if not line:
                    time.sleep(1.0)
                    continue
                    
                try:
                    entry = json.loads(line)
                    data = self._extract_learning_data(entry)
                    
                    if data:
                        self.engine.learn(
                            data['context'],
                            data['action'],
                            data['feeling']
                        )
                        # logger.info(f"Learned from entry: {entry.get('summary')}")
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error processing line: {e}")

if __name__ == "__main__":
    daemon = LearningDaemon()
    try:
        daemon.run()
    except KeyboardInterrupt:
        logger.info("Stopping Learning Daemon...")
