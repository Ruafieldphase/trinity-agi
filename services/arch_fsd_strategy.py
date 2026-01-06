import numpy as np
import os
import re
from typing import Dict, Any, List, Optional
from services.material_library import MaterialLibrary
import logging

class ArchFSDStrategy:
    """
    Specialized strategy for Architectural FSD Modeling.
    Injects learned principles: Spatial Folding and Constant C.
    """
    
    def __init__(self, constant_c: float = 200.0):
        self.constant_c = constant_c
        self.material_lib = MaterialLibrary()
        self.fold_state = {}
        self.logger = logging.getLogger("arch_fsd_strategy")
        
    def get_folding_prompt_enhancement(self) -> str:
        """Adds instructions for spatial folding."""
        return (
            "\n[Architectural Mode: Spatial Folding]\n"
            "- Step 1: Identify elevation drawings (usually 2D side views) around the plan.\n"
            "- Step 2: Use a virtual Z-rotation (90 degrees) to 'stand them up' as height references.\n"
            "- Step 3: Align the base points of elevations with the edges of the floor plan."
        )
        
    def apply_strategy(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Injects architectural logic into FSD actions."""
        # Material awareness: Overriding depth based on identified material
        if action.get("type") in ["extrude", "shell"]:
            material_label = action.get("text", "")
            material = self.material_lib.get_material(material_label)
            if material:
                action["depth"] = material.thickness
                action["reason"] = f"Using {material.label} thickness ({material.thickness}mm) from Material Library"
            else:
                action["depth"] = self.constant_c
        
        return action

    def calculate_adaptive_fold(self, anchor_pts: List[Dict], target_pts: List[Dict]) -> np.ndarray:
        """
        Calculates a rotation matrix to stand up a 2D reference 
        around an arbitrary non-orthogonal axis.
        """
        # Placeholder for complex matrix math
        # In a real implementation, this would use cross-products and Euler-Rodrigues
        return np.eye(4) # Identity matrix for now

    def decompose_semantic_goal(self, goal: str) -> List[Dict[str, Any]]:
        """
        Decomposes a high-level verbal goal into a batch of CAD commands.
        e.g. "Generate an 8-story RC office"
        """
        commands = []
        goal_l = goal.lower()
        
        # Pattern Matching for "N-story [Material] [BuildingType]"
        story_match = re.search(r"(\d+)-story", goal_l)
        stories = int(story_match.group(1)) if story_match else 1
        
        material = self.material_lib.get_material(goal_l) or self.material_lib.get_material("rc_wall")
        
        # Dimensions based on Constant C derivatives (Simplified mockup)
        floor_w, floor_d = 20.0, 15.0
        story_h = 3.5
        
        self.logger.info(f"🧱 Semantic Decomposition: {stories} stories using {material.label}")
        
        # 1. Clean Scene
        commands.append({"command": "clean_scene", "params": {}})
        
        # 2. Sequential Modeling Batch
        for i in range(stories):
            z_offset = i * story_h
            # Basic exterior shell
            commands.append({
                "command": "add_box",
                "params": {
                    "name": f"Floor_{i}_Shell",
                    "size": (floor_w, floor_d, story_h),
                    "location": (0, 0, z_offset + story_h/2),
                    "material": material.label,
                    "color": (0.7, 0.7, 0.7, 1.0)
                }
            })
            
            # Interior Slab
            commands.append({
                "command": "add_box",
                "params": {
                    "name": f"Slab_{i}",
                    "size": (floor_w + 0.4, floor_d + 0.4, 0.2),
                    "location": (0, 0, z_offset),
                    "color": (0.3, 0.3, 0.3, 1.0)
                }
            })
            
        return commands

    def get_constant_c_logic(self, primitive_type: str) -> Dict[str, Any]:
        """Returns parameters for modeling primitives based on Constant C."""
        if primitive_type == "wall":
            return {"thickness": self.constant_c / 10.0, "height": self.constant_c * 12.0} # Example heuristic
        return {"offset": self.constant_c}

    def synthesize_modeling_rhythm(self, current_step: int, history: List[Dict[str, Any]]) -> str:
        """Guidance for the iterative rhythm."""
        phase = current_step % 4
        loop_map = {
            0: "Inference: Locate next geometric vertex based on folded references.",
            1: "Execution: Draft the base splines/polygons.",
            2: "Positioning: Snapping (S) to align with reference points exactly.",
            3: "Depth: Applying Constant C depth (Extrude/Shell)."
        }
        return loop_map.get(phase, "Iterating workflow...")
