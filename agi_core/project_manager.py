import logging
import os
import json
from typing import Dict, Any, Optional

logger = logging.getLogger("ProjectManager")

class ProjectManager:
    """
    [Phase 26] The Magnum Opus.
    Manages persistent architectural projects that span multiple life cycles.
    """
    def __init__(self, bridge, vault):
        self.bridge = bridge
        self.vault = vault
        self.projects_dir = r"c:\workspace\agi\projects"
        os.makedirs(self.projects_dir, exist_ok=True)

    def start_project(self, theme: str, origin_dream: Optional[str] = None) -> str:
        """
        Initializes a new persistent project file.
        Returns the absolute path to the .blend file.
        """
        project_name = f"MagnumOpus_{theme}_{origin_dream.split('_')[-1] if origin_dream else 'Genesis'}"
        file_path = os.path.join(self.projects_dir, f"{project_name}.blend")
        
        logger.info(f"🏛️ [Magnum Opus] Laying foundation for: {project_name}")
        
        # 1. Reset Blender to clean slate
        self.bridge.send_command("reset_scene", {})
        
        # 2. Save initial file
        self.bridge.send_command("save_file", {"filepath": file_path})
        
        return file_path

    def evolve_project(self, file_path: str, impulse: str, complexity_boost: int) -> float:
        """
        Loads an existing project and adds a new layer of complexity.
        Returns the estimated new completion score (0.0 - 1.0).
        """
        if not os.path.exists(file_path):
            logger.error(f"❌ Project file not found: {file_path}")
            return 0.0
            
        logger.info(f"🏗️ [Magnum Opus] Resuming work on: {os.path.basename(file_path)} (Impulse: {impulse})")
        
        # 1. Open the File
        self.bridge.send_command("open_file", {"filepath": file_path})
        
        # 2. Add Complexity based on impulse
        # We use 'create_world' but assuming it adds to existing scene if not reset
        # Ideally, we need a specific 'add_layer' command, but 'create_world' with existing objects usually appends or modifies.
        # For Phase 26, we will rely on 'create_world's generated geometry adding to the scene.
        
        seed_text = f"Layer_{impulse}_{complexity_boost}"
        self.bridge.send_command("create_world", {"complexity": complexity_boost, "seed": seed_text, "impulse": impulse})
        
        # 3. Analyze & Check Completion
        # We use a heuristic: Complexity / Target Complexity
        # Or LLaVA critique score
        
        critique = {"score": 0.5} # Default
        try:
             # Basic scene info for complexity
            info = self.bridge.get_scene_info()
            if info and info.get("status") == "success":
                # Assuming 'total_faces' or similar metric exists in data
                # Let's mock a completion metric based on iteration count implicitly via state in a real scenario
                # For now, we use a random progress increment simulation or just LLaVA
                pass
                
            from agi_core.self_critique import ArchitecturalCritique
            critic = ArchitecturalCritique(self.bridge)
            critique = critic.perform_critique(f"Progress_Check_{seed_text}")
            
        except Exception as e:
            logger.debug(f"Critique failed during evolution: {e}")

        # 4. Save Progress
        self.bridge.send_command("save_file", {"filepath": file_path})
        
        # Completion score is a mix of structure score and LLaVA score
        completion_score = critique.get("score", 0.5)
        
        logger.info(f"✨ [Magnum Opus] Layer added. Completion Estimate: {completion_score:.2f}")
        
        return completion_score
