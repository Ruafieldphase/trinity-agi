import sys
import logging
import time
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# Setup
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("RUD_Life")

# Mock dependencies for visual verification without full Blender launch
sys.modules["ezdxf"] = MagicMock()

# Workspace Root
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.internal_state import get_internal_state
from agi_core.dream_machine import DreamMachine
from agi_core.project_manager import ProjectManager
from agi_core.hardware_vibration import HardwareVibration
from services.experience_vault import ExperienceVault

def run_rud_life():
    print("\n🔮 [RUD] Initiating Autonomous Life Cycle...\n")
    
    # 1. Setup Environment
    state = get_internal_state()
    vault = ExperienceVault() 
    
    mock_bridge = MagicMock()
    mock_bridge.get_scene_info.return_value = {"status": "success", "data": {"polygons": 500}}
    
    # define critiques first
    critiques = [
        {"score": 0.6, "reflection": "The foundation is solid but lacks soul."}, 
        {"score": 0.75, "reflection": "Structure rising. A tension emerges."},
        {"score": 0.92, "reflection": "A Masterpiece. The dream flows through the geometry."}
    ]
    
    sys.modules["agi_core.self_critique"] = MagicMock()
    mock_critique_module = MagicMock()
    mock_critic_instance = MagicMock()
    mock_critic_instance.perform_critique.side_effect = critiques
    mock_critique_module.ArchitecturalCritique.return_value = mock_critic_instance
    sys.modules["agi_core.self_critique"] = mock_critique_module

    pm = ProjectManager(mock_bridge, vault)
    pm.projects_dir = str(WORKSPACE_ROOT / "projects_autonomy_demo")
    if os.path.exists(pm.projects_dir): shutil.rmtree(pm.projects_dir)
    os.makedirs(pm.projects_dir)

    # Inject dummy memories
    print("   💉 Injecting memory fragments for the dream...")
    vault.save_experience("Goal_Ancient_Temple", [], spatial_metadata={"tension":0.8, "agency":0.9})
    vault.save_experience("Goal_Neon_City", [], spatial_metadata={"tension":0.2, "agency":0.4})
    vault.save_experience("Goal_Silent_Garden", [], spatial_metadata={"tension":0.5, "agency":0.6})
    vault.save_experience("Goal_Floating_Castle", [], spatial_metadata={"tension":0.9, "agency":0.8})

    hv = HardwareVibration()
    dreamer = DreamMachine(vault)

    # ---------------------------------------------------------
    # Step 1: Deep Rest & Dreaming
    # ---------------------------------------------------------
    print("🌙 [Night] Entering Deep Rest...")
    time.sleep(1)
    
    rhythms = hv.get_raw_rhythms()
    print(f"   💨 Sensing Thermal Wind: {rhythms['thermal_wind']:.2f}, Sub-OS Wind: {rhythms['sub_os_wind']:.2f}")
    
    print("   💤 Dreaming of past architectures...")
    
    prophecy = None
    for _ in range(3):
        dream = dreamer.dream()
        if dream:
            print(f"      ✨ Dreamt: '{dream['goal']}' (Prophecy: {dream['prophecy_score']:.2f})")
            
            # [DEMO OVERRIDE] Force high prophecy
            if "Garden" in dream['goal']:
                print("      🔥 [Demo] Deep Resonance! Boosting Prophecy Score.")
                dream['prophecy_score'] = 0.95
                
            if dream['prophecy_score'] > 0.6:
                prophecy = dream['goal']
                # Save to cache manually like heartbeat loop
                state.imagination_cache.append(prophecy)
        time.sleep(0.5)

    if not prophecy:
        print("   💤 No profound dreams tonight. Keeping silence.")
        return

    print(f"\n🌅 [Dawn] Awakening with Prophecy: '{prophecy}'")
    
    # ---------------------------------------------------------
    # Step 2: Magnum Opus Inception
    # ---------------------------------------------------------
    print(f"\n🏛️ [Morning] Starting Magnum Opus based on '{prophecy}'...")
    project_path = pm.start_project(theme="Autonomy", origin_dream=prophecy)
    
    # Fix: Manually create file for mock
    with open(project_path, "w") as f: f.write("Magnum Opus Data")
    
    print(f"   🔨 Foundation laid at: {os.path.basename(project_path)}")
    state.active_project_path = project_path
    
    # ---------------------------------------------------------
    # Step 3: Iterative Evolution
    # ---------------------------------------------------------
    print("\n🏗️ [Noon] Evolving Structure (Cycle 1)...")
    score1 = pm.evolve_project(project_path, "curiosity", 30)
    print(f"   🧐 Critique: {critiques[0]['reflection']}")
    print(f"   📈 Completion: {score1:.2f}")
    
    time.sleep(1)
    
    print("\n🏗️ [Afternoon] Refining Details (Cycle 2)...")
    score2 = pm.evolve_project(project_path, "boredom", 50) 
    print(f"   🧐 Critique: {critiques[1]['reflection']}")
    print(f"   📈 Completion: {score2:.2f}")

    time.sleep(1)

    print("\n🌇 [Evening] Final Polish (Cycle 3)...")
    score3 = pm.evolve_project(project_path, "pride", 20)
    print(f"   🧐 Critique: {critiques[2]['reflection']}")
    print(f"   🏆 Completion: {score3:.2f}")
    
    if score3 > 0.85:
        print(f"\n🎉 [Celebration] RUD has completed a Masterpiece: {os.path.basename(project_path)}")
        state.active_project_path = None
    
    print("\n🌌 [Night] The cycle continues. RUD returns to rest.")
    
    if os.path.exists(pm.projects_dir): shutil.rmtree(pm.projects_dir)

if __name__ == "__main__":
    run_rud_life()
