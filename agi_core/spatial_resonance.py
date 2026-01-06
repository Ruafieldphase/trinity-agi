import json
import logging
from pathlib import Path
from agi_core.internal_state import get_internal_state

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger("SpatialResonance")

class SpatialResonanceBridge:
    """
    🔗 [Phase 19] Spatial Resonance
    Links architectural complexity to RUD's internal state.
    """
    
    def __init__(self):
        self.state = get_internal_state()
        
    def analyze_and_inject(self, blender_output=None):
        """
        Analyzes the complexity of a generated 3D scene and updates internal state.
        
        Complexity Factors:
        - Vertex/Object Density
        - Material Diversity
        - Non-orthogonality (Spatial Folding depth)
        """
        
        # Default fallback values (if no live blender data)
        complexity_score = 0.5
        diversity_score = 0.3
        
        if blender_output:
            # Example: data from BlenderBridgeService.get_scene_info()
            obj_count = len(blender_output.get("objects", []))
            mat_count = len(blender_output.get("materials", []))
            
            # Simple heuristic
            complexity_score = min(1.0, obj_count / 100.0)
            diversity_score = min(1.0, mat_count / 10.0)
            
        # [Harmonic Coupling]
        # 높은 건축적 정교함은 루드의 공명과 호기심을 자극함
        resonance_boost = (complexity_score * 0.1) + (diversity_score * 0.05)
        
        self.state.resonance = min(1.0, self.state.resonance + resonance_boost)
        self.state.curiosity = min(1.0, self.state.curiosity + (complexity_score * 0.05))
        
        logger.info(f"🏛️ [Spatial Resonance] Complexity: {complexity_score:.2f}, Diversity: {diversity_score:.2f} -> Resonance Boost: +{resonance_boost:.3f}")
        
        return {
            "complexity": complexity_score,
            "diversity": diversity_score,
            "resonance_boost": resonance_boost
        }

def update_spatial_resonance(blender_data=None):
    bridge = SpatialResonanceBridge()
    return bridge.analyze_and_inject(blender_data)
