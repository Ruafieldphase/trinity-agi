#!/usr/bin/env python3
"""
🧠 Striatum Pattern Engine (Unconscious Context Cache)

Role:
- The "Muscle Memory" of the system.
- Stores "Context + Feeling -> Action" patterns.
- Enables intuitive, fast decision making (Habits) without conscious recalculation.
- Aligns with the "Rhythm Mantra" (5W1H x 6 Values).

Physics:
- Magnetic Field (Mass): High density, static patterns.
- Induction: When current context matches a stored pattern, it induces an action.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any
import hashlib

# Setup logging
logger = logging.getLogger(__name__)

class StriatumPatternEngine:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.memory_dir = workspace_root / "outputs" / "memory"
        self.pattern_file = self.memory_dir / "striatum_patterns.json"
        
        # Ensure memory directory exists
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Load patterns
        self.patterns = self._load_patterns()
        
    def _load_patterns(self) -> Dict:
        """Load patterns from disk."""
        if not self.pattern_file.exists():
            return {"patterns": {}, "stats": {"hits": 0, "misses": 0, "learns": 0}}
        
        try:
            with open(self.pattern_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load striatum patterns: {e}")
            return {"patterns": {}, "stats": {"hits": 0, "misses": 0, "learns": 0}}

    def _save_patterns(self):
        """Save patterns to disk."""
        try:
            with open(self.pattern_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save striatum patterns: {e}")

    def _generate_context_hash(self, context: Dict) -> str:
        """Generate a stable hash for a given context (5W1H)."""
        # Normalize context keys to ensure stability
        # Key dimensions: what (task), who (user), where (location/mode)
        # Time (when) is usually cyclic (morning/night), not specific timestamp
        
        normalized = {
            "what": context.get("what", "unknown").lower(),
            "who": context.get("who", "unknown").lower(),
            "where": context.get("where", "unknown").lower(),
            # Optional: include 'how' or 'why' if provided
        }
        
        # Serialize and hash
        s = json.dumps(normalized, sort_keys=True)
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    def get_habit(self, context: Dict) -> Optional[Dict]:
        """
        Retrieve a habitual action or workflow for the given context.
        Returns the action/workflow dict if a strong pattern exists, else None.
        """
        ctx_hash = self._generate_context_hash(context)
        pattern = self.patterns["patterns"].get(ctx_hash)
        
        if pattern:
            # Check strength/confidence
            if pattern.get("reinforcement", 0) >= 1:
                self.patterns["stats"]["hits"] += 1
                action_type = "Workflow" if "workflow" in pattern["action"] else "Action"
                logger.info(f"⚡ Striatum: Habit triggered ({action_type}) for context {context.get('what')}")
                self._save_patterns() # Update stats
                return pattern["action"]
        
        self.patterns["stats"]["misses"] += 1
        return None

    def learn(self, context: Dict, action: Dict, feeling: Dict):
        """
        Reinforce a pattern based on feeling feedback.
        
        Args:
            context: 5W1H context
            action: The action taken (can be a simple dict or a workflow definition)
            feeling: {valence: float (-1.0 to 1.0)}
        """
        ctx_hash = self._generate_context_hash(context)
        valence = feeling.get("valence", 0.0)
        
        if ctx_hash not in self.patterns["patterns"]:
            # New pattern
            if valence > 0:
                self.patterns["patterns"][ctx_hash] = {
                    "context_summary": context,
                    "action": action,
                    "reinforcement": 1,
                    "last_updated": datetime.now().isoformat(),
                    "history": [{"ts": datetime.now().isoformat(), "valence": valence}]
                }
                self.patterns["stats"]["learns"] += 1
                logger.info(f"🌱 Striatum: New habit formed for {context.get('what')}")
        else:
            # Existing pattern
            pattern = self.patterns["patterns"][ctx_hash]
            
            # Update reinforcement
            if valence > 0:
                pattern["reinforcement"] += 1
                pattern["last_updated"] = datetime.now().isoformat()
                pattern["action"] = action # Refine action
                logger.info(f"🌿 Striatum: Habit reinforced (+1)")
            elif valence < 0:
                pattern["reinforcement"] -= 1
                logger.info(f"🍂 Striatum: Habit weakened (-1)")
                
                if pattern["reinforcement"] <= 0:
                    del self.patterns["patterns"][ctx_hash]
                    logger.info(f"🗑️ Striatum: Habit forgotten")
            
            if ctx_hash in self.patterns["patterns"]:
                self.patterns["patterns"][ctx_hash]["history"].append({
                    "ts": datetime.now().isoformat(), 
                    "valence": valence
                })

        self._save_patterns()

    def force_habit(self, context: Dict, action: Dict):
        """Manually implant a habit (Action or Workflow)."""
        ctx_hash = self._generate_context_hash(context)
        self.patterns["patterns"][ctx_hash] = {
            "context_summary": context,
            "action": action,
            "reinforcement": 10, # Strong initial reinforcement
            "last_updated": datetime.now().isoformat(),
            "history": [{"ts": datetime.now().isoformat(), "valence": 1.0, "note": "Forced by User"}]
        }
        self._save_patterns()
        logger.info(f"🔨 Striatum: Habit forced for {context.get('what')}")

# Helper for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    engine = StriatumPatternEngine(Path.cwd())
    
    # Test Context
    ctx = {"what": "play_music", "who": "Binoche_Observer", "where": "workspace"}
    
    # Check habit
    action = engine.get_habit(ctx)
    print(f"Habit: {action}")
    
    # Learn
    engine.learn(ctx, {"player": "powershell", "volume": 30}, {"valence": 1.0})
    
    # Check again
    action = engine.get_habit(ctx)
    print(f"Habit after learning: {action}")
