import os
import sys
from pathlib import Path

# Project paths
ROOT = "C:/workspace/agi"
if ROOT not in sys.path:
    sys.path.append(ROOT)

import subprocess
import json
import time

DXF_PATH = f"{ROOT}/architecture_automation/inputs/안내동(건축도면)도면정리.dxf"
PARSER_SCRIPT = f"{ROOT}/architecture_automation/scripts/dxf_parser_engine.py"
VISION_SCRIPT = f"{ROOT}/architecture_automation/scripts/vision_preprocessing_engine.py"
MODEL_OUTPUT = f"{ROOT}/outputs/architecture/final_detailed_model.blend"

def run_step(name, cmd_list):
    print(f"\n--- ⚡ Step: {name} ---")
    res = subprocess.run(cmd_list, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ {name} failed!\n{res.stderr}")
        return False
    print(f"✅ {name} complete.")
    print(res.stdout)
    return True

def main():
    # 1. Parse DXF
    if not run_step("DXF Parsing", [sys.executable, PARSER_SCRIPT, DXF_PATH]):
        return

    # 2. Vision Analysis & Merge
    vision_report = f"{ROOT}/outputs/vision_preprocessing/vision_report.json"
    if not os.path.exists(vision_report):
        if not run_step("Vision Preprocessing", [sys.executable, VISION_SCRIPT, DXF_PATH]):
            return
    else:
        print(f"⏩ Skipping Vision Analysis (Report already exists at {vision_report})")
        # Ensure it's merged into the blueprint
        run_step("Vision Merge (Resume)", [sys.executable, VISION_SCRIPT, DXF_PATH, "--merge-only"])

    # 3. Blender Modeling (Via TCP Bridge)
    from services.blender_bridge_service import BlenderBridgeService
    bridge = BlenderBridgeService()
    
    print("\n--- ⚡ Step: Blender Modeling ---")
    bridge.check_health()
    bridge.clean_scene()
    
    blueprint_path = f"{ROOT}/architecture_automation/outputs/parsed_blueprint.json"
    res = bridge.send_command("execute_python", {
        "code": f"import sys; sys.path.append('{ROOT}/architecture_automation/scripts'); "
                f"from blender_connector import run_spatial_folding_assembly; "
                f"run_spatial_folding_assembly('{blueprint_path}'); "
                f"import bpy; bpy.ops.wm.save_as_mainfile(filepath='{MODEL_OUTPUT}')"
    })
    print(f"Blender Response: {res}")
    
    # 4. Final Verification
    print("\n--- ⚡ Step: Final Verification ---")
    render_path = bridge.quick_render("final_detailed_verification.png")
    if render_path:
        print(f"Rendering done: {render_path}")
        verification = bridge.verify_quality(render_path)
        print("\n--- FINAL LLaVA EVALUATION ---")
        print(verification)
        print("-------------------------------")
    else:
        print("❌ Rendering failed for verification.")

if __name__ == "__main__":
    main()
