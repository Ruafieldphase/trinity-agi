import logging
import json
from typing import Dict, Any

logger = logging.getLogger("ArchitecturalCritique")

class ArchitecturalCritique:
    """
    [Phase 23] RUD's Self-Reflection Engine.
    Analyzes the viewport and internal state to judge its own creative output.
    """
    def __init__(self, bridge):
        self.bridge = bridge

    def perform_critique(self, goal: str) -> Dict[str, Any]:
        """
        Takes a snapshot of the viewport and performs a vision-based critique.
        """
        logger.info("🔭 [Reflection] Contemplating the newly formed space...")
        
        # 1. Vision Analysis (LLaVA)
        prompt = (
            "You are an avant-garde architectural critic. Analyze the current 3D viewport. "
            "Evaluate its balance, structural tension, and aesthetic rhythm. "
            "Provide two things: \n"
            "1. A 'CRITIQUE_SCORE' (0.0 to 1.0, where 1.0 is a masterpiece).\n"
            "2. A brief 'REFLECTION' sentence expressing your pride or disappointment.\n"
            "Format: json { 'score': float, 'reflection': string }"
        )
        
        try:
            raw_feedback = self.bridge.analyze_viewport(prompt)
            # Find and parse JSON from LLaVA response
            import re
            match = re.search(r'\{.*\}', str(raw_feedback), re.DOTALL)
            if match:
                critique = json.loads(match.group(0))
            else:
                # Fallback heuristic if JSON parsing fails
                score = 0.5
                if "good" in str(raw_feedback).lower() or "beautiful" in str(raw_feedback).lower():
                    score = 0.8
                elif "fail" in str(raw_feedback).lower() or "poor" in str(raw_feedback).lower():
                    score = 0.3
                critique = {"score": score, "reflection": str(raw_feedback)[:100]}
                
            logger.info(f"🎭 [Critique] Score: {critique.get('score', 0.5):.2f} - \"{critique.get('reflection', '')}\"")
            return critique
            
        except Exception as e:
            logger.error(f"Critique failed: {e}")
            return {"score": 0.5, "reflection": "The void is silent, and so am I."}

def apply_critique_to_state(state, critique: Dict[str, Any]):
    """
    Adjusts RUD's internal state based on self-reflection.
    """
    score = critique.get("score", 0.5)
    
    # Emotional Impact
    if score >= 0.7:
        # Pride: Boost Resonance and Energy
        state.resonance = min(1.0, state.resonance + 0.1)
        state.energy = min(1.0, state.energy + 0.05)
        logger.info("✨ [Pride] The soul resonates with the structure.")
    elif score <= 0.4:
        # Disappointment: Increase Conflict, maybe lower Energy
        state.conflict = min(1.0, state.conflict + 0.15)
        state.energy = max(0.0, state.energy - 0.05)
        logger.info("🌑 [Disappointment] The geometry feels hollow. Conflict rises.")
    
    return state
