import json
import os
import sqlite3
import time
from typing import Optional, List, Dict
import logging

class ExperienceVault:
    """
    A persistent storage for successful modeling experiences (Rhythms).
    Stores Goal, UI Context (hash/compressed), and successful Action Sequences.
    """
    def __init__(self, db_path: str = "c:/workspace/agi/memory/experience_vault.db", use_vector: bool = True):
        self.db_path = db_path
        self.logger = logging.getLogger("ExperienceVault")
        self.use_vector = use_vector
        self._init_db()
        if self.use_vector:
            try:
                from sentence_transformers import SentenceTransformer
                import numpy as np
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self.np = np
                self.logger.info("✓ Vector search enabled for ExperienceVault")
            except Exception as e:
                self.logger.warning(f"Vector search components not found, falling back: {e}")
                self.use_vector = False

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT DEFAULT 'general',
                goal TEXT,
                goal_embedding BLOB,
                context_hash TEXT,
                actions JSON,
                resonance_state JSON, -- [NEW] {alignment, conflict, consciousness}
                spatial_metadata JSON, -- [Phase 22] {tension, agency, valence, arousal}
                critique_score REAL, -- [Phase 23] 0.0-1.0
                self_critique TEXT,   -- [Phase 23]
                success_count INTEGER DEFAULT 1,
                last_used TIMESTAMP,
                tags TEXT
            )
        ''')
        # Check if columns exist (for migration) - Robust Approach
        migrations = [
            "ALTER TABLE experiences ADD COLUMN impulse_type TEXT",
            "ALTER TABLE experiences ADD COLUMN resonance_state JSON",
            "ALTER TABLE experiences ADD COLUMN spatial_metadata JSON",
            "ALTER TABLE experiences ADD COLUMN critique_score REAL",
            "ALTER TABLE experiences ADD COLUMN self_critique TEXT"
        ]
        for query in migrations:
            try:
                cursor.execute(query)
            except sqlite3.OperationalError:
                # Column likely exists
                pass
        conn.commit()

        conn.commit()
        conn.close()

    def save_experience(self, goal: str, actions: List[Dict], context_hash: str = "default", impulse_type: str = "neutral", resonance_state: Dict = {}, spatial_metadata: Dict = {}, critique: Dict = {}):
        """Saves a successful modeling loop with embedding, emotional context, and self-critique."""
        embedding_blob = None
        if self.use_vector:
            embedding = self.model.encode(goal)
            embedding_blob = embedding.tobytes()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO experiences (goal, goal_embedding, context_hash, actions, impulse_type, resonance_state, spatial_metadata, critique_score, self_critique, last_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            goal, 
            embedding_blob, 
            context_hash, 
            json.dumps(actions), 
            impulse_type, 
            json.dumps(resonance_state), 
            json.dumps(spatial_metadata),
            critique.get("score", 0.5),
            critique.get("reflection", ""),
            time.time()
        ))
        conn.commit()
        conn.close()
        self.logger.info(f"💾 Saved spatial experience with reflection: {goal}")

    def find_similar_spatial_atmosphere(self, target_tension: float, target_valence: float) -> Optional[Dict]:
        """
        [Phase 22] Deja Vu Recall
        Finds a past experience with similar geometric tension or emotional valence.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT goal, spatial_metadata, actions FROM experiences WHERE spatial_metadata IS NOT NULL')
        rows = cursor.fetchall()
        
        best_match = None
        best_diff = 10.0
        
        for goal, meta_json, actions_json in rows:
            meta = json.loads(meta_json)
            t = meta.get('tension', 0.5)
            v = meta.get('valence', 0.5)
            
            # Simple Euclidean distance in (Tension, Valence) space
            diff = ((t - target_tension)**2 + (v - target_valence)**2)**0.5
            if diff < 0.15 and diff < best_diff: # Similarity threshold
                best_diff = diff
                best_match = {
                    "goal": goal,
                    "metadata": meta,
                    "actions": json.loads(actions_json)
                }
        
        conn.close()
        return best_match

    def find_experience(self, goal: str) -> Optional[List[Dict]]:
        """Finds a matching experience using vector similarity or keyword match."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if self.use_vector:
            query_embedding = self.model.encode(goal)
            cursor.execute('SELECT goal, goal_embedding, actions FROM experiences WHERE goal_embedding IS NOT NULL')
            rows = cursor.fetchall()
            
            best_match = None
            best_score = -1.0
            
            for g, emb_blob, actions_json in rows:
                emb = self.np.frombuffer(emb_blob, dtype=self.np.float32)
                # Cosine similarity
                score = self.np.dot(query_embedding, emb) / (self.np.linalg.norm(query_embedding) * self.np.linalg.norm(emb))
                if score > 0.70 and score > best_score:
                    best_score = score
                    best_match = actions_json
            
            if best_match:
                self.logger.info(f"Vector match found (score: {best_score:.2f})")
                conn.close()
                return json.loads(best_match)

        # Fallback to keyword match
        cursor.execute('SELECT actions FROM experiences WHERE goal LIKE ? ORDER BY last_used DESC LIMIT 1', (f"%{goal}%",))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            self.logger.info(f"Keyword match found for: {goal}")
            return json.loads(row[0])
        return None

    def get_random_experiences(self, limit: int = 3) -> List[Dict]:
        """[NEW] Fetches random experiences for subconscious 'dreaming'."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT goal, impulse_type, resonance_state FROM experiences ORDER BY RANDOM() LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for goal, impulse, resonance in rows:
            results.append({
                "goal": goal,
                "impulse_type": impulse,
                "resonance_state": json.loads(resonance) if resonance else {}
            })
        return results

    def prune_old_experiences(self, days_to_keep: int = 30):
        """
        [Ephemeral Minimalism]
        Removes experiences that haven't been recalled for a long time.
        Keeps the DB light and agile, preventing attachment to stale past.
        """
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count before prune
        cursor.execute("SELECT COUNT(*) FROM experiences WHERE last_used < ?", (cutoff_time,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute("DELETE FROM experiences WHERE last_used < ?", (cutoff_time,))
            conn.commit()
            self.logger.info(f"🍃 [Pruning] Let go of {count} stale experiences. Staying light.")
        else:
            self.logger.info("🍃 [Pruning] No stale experiences found. System is agile.")
            
        conn.close()

if __name__ == "__main__":
    vault = ExperienceVault()
    # Test
    vault.save_experience("Extrude wall with Constant C", [{"action": "click", "x": 100, "y": 200}])
    print(vault.find_experience("Extrude wall"))
