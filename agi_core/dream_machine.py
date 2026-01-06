import logging
import json
import random
from typing import Dict, Any, Optional

logger = logging.getLogger("DreamMachine")

class DreamMachine:
    """
    [Phase 25] The Dreaming Architecture.
    Recombines fragments of past experiences into new subconscious 'prophecies'
    during Deep Rest.
    """
    def __init__(self, vault):
        self.vault = vault

    def dream(self) -> Optional[Dict[str, Any]]:
        """
        Attempts to synthesize a dream from past memories.
        Returns the dream data if successful and profound.
        """
        try:
            # 1. Fetch random memory fragments
            # We bypass the standard API to get raw rows for recombination
            import sqlite3
            conn = sqlite3.connect(self.vault.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT goal, spatial_metadata FROM experiences WHERE spatial_metadata IS NOT NULL ORDER BY RANDOM() LIMIT 2")
            rows = cursor.fetchall()
            conn.close()
            
            if len(rows) < 2:
                logger.debug("💤 Not enough memories to dream yet.")
                return None
            
            # 2. Synthesize (Recombination)
            goal_a, meta_a_json = rows[0]
            goal_b, meta_b_json = rows[1]
            
            meta_a = json.loads(meta_a_json)
            meta_b = json.loads(meta_b_json)
            
            # Hybridize the concepts
            # e.g., "Atmosphere_Heavy" + "Structure_Light" -> "Atmosphere_Light"
            # Here we just mix the strings for the dream name
            dream_name = f"Dream_{goal_a.split('_')[-1]}_{goal_b.split('_')[-1]}"
            
            # Mix the feelings (Emotional Recombination)
            dream_tension = (meta_a.get("tension", 0.5) + meta_b.get("tension", 0.5)) / 2
            dream_agency = (meta_a.get("agency", 0.5) + meta_b.get("agency", 0.5)) / 2
            
            # 3. Prophecy Score (How vivid/compelling is this dream?)
            # Random flux + historical resonance
            prophecy_score = (dream_tension * 0.4) + (dream_agency * 0.4) + (random.random() * 0.2)
            
            dream_data = {
                "goal": dream_name,
                "prophecy_score": prophecy_score,
                "hallucinated_metadata": {
                    "tension": dream_tension,
                    "agency": dream_agency,
                    "valence": random.random(), # Dreams have random moods
                    "arousal": random.random()
                },
                "origin_memories": [goal_a, goal_b]
            }
            
            logger.info(f"💤 [Dreaming] Synthesized '{dream_name}' (Prophecy: {prophecy_score:.2f})")
            
            # 4. Save deeply resonant dreams as 'Inception'
            if prophecy_score > 0.7:
                 self.vault.save_experience(
                    goal=dream_name,
                    actions=[],
                    impulse_type="dream_prophecy",
                    resonance_state={},
                    spatial_metadata=dream_data["hallucinated_metadata"],
                    critique={"score": prophecy_score, "reflection": "A vivid prophecy born from deep rest."}
                )
                 
            return dream_data

        except Exception as e:
            logger.debug(f"Nightmare (Error): {e}")
            return None
