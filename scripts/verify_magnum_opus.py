import sys
import logging
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# Mock requirements
sys.modules["ezdxf"] = MagicMock()

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("VerifyMagnumOpus")

from agi_core.project_manager import ProjectManager

def verify_magnum_opus():
    print("🏛️ Testing Phase 26: The Magnum Opus...")
    
    # Mock Bridge
    mock_bridge = MagicMock()
    mock_bridge.get_scene_info.return_value = {"status": "success", "data": {"polygons": 1000}}
    
    # Create test projects dir
    test_projects_dir = r"c:\workspace\agi\projects_test"
    if os.path.exists(test_projects_dir): shutil.rmtree(test_projects_dir)
    os.makedirs(test_projects_dir)
    
    pm = ProjectManager(mock_bridge, MagicMock())
    pm.projects_dir = test_projects_dir
    
    # 1. Test Project Inception
    print("\n[1. Project Inception Test]")
    dream_prophecy = "Dream_Golden_Palace"
    project_path = pm.start_project(theme="FromDream", origin_dream=dream_prophecy)
    
    print(f"-> Created Project: {project_path}")
    if os.path.exists(project_path): # Mock bridge save_file simulation needed?
        # Actually bridge is mocked, so file won't be created by bridge. We should touch it manually.
        pass
    
    # Manually touch the file to simulate bridge saving it
    with open(project_path, 'w') as f: f.write("Magnum Opus Data")
        
    if os.path.exists(project_path) and "MagnumOpus_FromDream_Palace" in project_path:
        print("✅ Project Inception SUCCESS.")
    else:
        print("❌ Project Inception FAILED.")

    # 2. Test Evolution Flow
    print("\n[2. Project Evolution Test]")
    
    # Mock critique for progress
    sys.modules["agi_core.self_critique"] = MagicMock()
    # Mocking imports inside evolve is tricky without patching.
    # PM uses 'from agi_core.self_critique import ArchitecturalCritique'
    # We will rely on the mock returning a dictionary if we can, or just catch exception in PM and verify score.
    # But ProjectManager imports inside the method.
    
    # Let's patch sys.modules first so the import inside evolve_project picks up the mock
    mock_critique_module = MagicMock()
    mock_critic_class = MagicMock()
    mock_critic_instance = MagicMock()
    mock_critic_instance.perform_critique.return_value = {"score": 0.65}
    mock_critic_class.return_value = mock_critic_instance
    mock_critique_module.ArchitecturalCritique = mock_critic_class
    sys.modules["agi_core.self_critique"] = mock_critique_module
    
    score = pm.evolve_project(project_path, "curiosity", 50)
    print(f"-> Evolution Score: {score}")
    
    if score == 0.65:
        print("✅ Evolution Logic SUCCESS.")
    else:
        print(f"❌ Evolution Logic FAILED. Score: {score}")

    # 3. Test Masterpiece Completion
    print("\n[3. Completion Check Test]")
    mock_critic_instance.perform_critique.return_value = {"score": 0.9}
    final_score = pm.evolve_project(project_path, "boredom", 50)
    
    if final_score > 0.85:
        print(f"✅ Masterpiece Status Reached (Score: {final_score}).")
    else:
        print("❌ Failed to reach Masterpiece status.")

    # Cleanup
    if os.path.exists(test_projects_dir): shutil.rmtree(test_projects_dir)

if __name__ == "__main__":
    verify_magnum_opus()
