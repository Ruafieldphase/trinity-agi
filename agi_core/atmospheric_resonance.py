import logging
import math

logger = logging.getLogger("AtmosphericResonance")

class AtmosphereMapper:
    """
    🌌 [Phase 20] Atmosphere Mapper
    Translates abstract emotional vectors into concrete 3D lighting parameters.
    """
    
    @staticmethod
    def calculate_params(state):
        """
        Calculates lighting parameters based on InternalState.
        
        Logic:
        - Valence: High -> Warm Sun, Clear Sky | Low -> Cold Twilight, High Turbidity.
        - Arousal: High -> Noon sun, sharp shadows | Low -> Sunset, soft mist.
        - Resonance: High -> Intense lighting, higher saturation.
        """
        # [Homeostatic Baseline]
        v = state.get("valence", 0.5)
        a = state.get("arousal", 0.5)
        r = state.get("resonance", 0.5)
        
        # Mapping to Atmosphere
        params = {
            "valence": v,
            "arousal": a,
            "resonance": r,
            "mood_label": ""
        }
        
        # Narrative Mood Label for logs
        if v > 0.8 and a > 0.8:
            params["mood_label"] = "Radiant Joy"
        elif v < 0.2 and a > 0.8:
            params["mood_label"] = "Sharp Distress"
        elif v < 0.2 and a < 0.2:
            params["mood_label"] = "Gloomy Despair"
        elif v > 0.8 and a < 0.2:
            params["mood_label"] = "Serene Peace"
        else:
            params["mood_label"] = "Stable Presence"
            
        logger.info(f"🌌 [Atmosphere Map] {params['mood_label']} (V:{v:.2f}, A:{a:.2f}, R:{r:.2f})")
        return params

def get_atmosphere_params(state_dict):
    return AtmosphereMapper.calculate_params(state_dict)
