"""
Rud Architect - Architectural Intelligence Agent
================================================
Role: Architect (Grounded Action)
Function: 
  - Monitors CAD inputs (DXF).
  - Orchestrates Parsing -> 3D Modeling (Blender).
  - Reports progress via Narrative Self.
"""

import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

# Add workspace root for imports
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.ask_first_middleware import get_ask_first_middleware
from agi_core.modeling_proposer import ModelingProposer
from agi_core.rhythm_boundaries import RhythmBoundaryManager

# Paths
ARCH_ROOT = WORKSPACE_ROOT / "architecture_automation"
INPUT_DIR = ARCH_ROOT / "inputs"
OUTPUT_DIR = ARCH_ROOT / "outputs"
MODEL_DIR = OUTPUT_DIR / "models"
SCRIPTS_DIR = ARCH_ROOT / "scripts"

MODEL_DIR = OUTPUT_DIR / "models"
SCRIPTS_DIR = ARCH_ROOT / "scripts"

# Import Parser Engine directly
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))
try:
    from dxf_parser_engine import extract_geometry, save_json
except ImportError:
    # Fallback if path issue
    import importlib.util
    spec = importlib.util.spec_from_file_location("dxf_parser_engine", SCRIPTS_DIR / "dxf_parser_engine.py")
    dxf_parser_engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dxf_parser_engine)
    extract_geometry = dxf_parser_engine.extract_geometry
    save_json = dxf_parser_engine.save_json

BLENDER_CONNECTOR = SCRIPTS_DIR / "blender_connector.py"
PARSED_JSON = OUTPUT_DIR / "parsed_blueprint.json"
NARRATIVE_FILE = WORKSPACE_ROOT / "outputs" / "narrative_status_latest.json"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RudArchitect")

def update_narrative_status(message, rhythm_tag="EXPANSION"):
    """Update narrative file to inform user about architectural progress."""
    try:
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_line": message,
            "rhythm_tag": rhythm_tag,
            "safety_mode": "arch_active"
        }
        with open(NARRATIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to update narrative: {e}")

def run_pipeline():
    """Detect new DXF and run the full modeling pipeline."""
    
    # 1. Find the latest DXF in inputs
    dxf_files = list(INPUT_DIR.glob("*.dxf"))
    if not dxf_files:
        return False

    latest_dxf = max(dxf_files, key=os.path.getmtime)
    
    # Use a safe ASCII filename for Blender
    safe_name = "latest_arch_model.blend"
    blend_output = MODEL_DIR / safe_name
    
    # Optional: Backup existing
    if blend_output.exists():
        backup_name = MODEL_DIR / f"model_{int(time.time())}.blend"
        os.rename(blend_output, backup_name)

    logger.info(f"🏗️  Architectural Expansion Triggered: {latest_dxf.name}")
    update_narrative_status(f"새로운 도면 '{latest_dxf.name}'을 발견했습니다. 공간의 리듬을 구조화하기 시작합니다.")

    try:
        # Step 1: Parsing (In-Process)
        logger.info(f"⚙️  Step 1: Parsing DXF (Internal)...")
        
        # Direct Call
        parsed_data = extract_geometry(str(latest_dxf))
        if not parsed_data:
             raise ValueError("DXF Parsing returned empty data.")
             
        save_json(parsed_data, str(latest_dxf))
        
        logger.info("✅ Internal Parsing Complete.")
        
        if not PARSED_JSON.exists():
            raise FileNotFoundError("Parsed JSON not found after execution.")

        # --- Step 1.5: Ask-First Proposal ---
        with open(PARSED_JSON, "r", encoding="utf-8") as f:
            parsed_data = json.load(f)
        
        proposer = ModelingProposer(WORKSPACE_ROOT)
        middleware = get_ask_first_middleware()
        
        proposal = proposer.generate_proposal(parsed_data)
        gate_result = middleware.check_gate_2(f"CAD 도면 '{latest_dxf.name}' 모델링", context={"parameters": proposal["parameters"]})
        gate_result["proposal_message"] = proposal["message"]
        
        ask_message = middleware.format_ask_message(gate_result)
        logger.info(f"📬 Proposal Generated: \n{ask_message}")
        update_narrative_status("도면 분석을 마치고 모델링 제안서를 작성했습니다. 비노체님의 승인을 기다립니다.", rhythm_tag="WAIT_APPROVAL")

        # ⚠️ HOLD logic: In a real autonomous loop, this would stop here and wait for an external trigger.
        # For this demonstration/execution, we proceed if wait_for_approval returns True.
        if not middleware.wait_for_approval(latest_dxf.name):
            logger.info("🛑 Modeling canceled or deferred by user.")
            return False

        update_narrative_status("승인이 확인되었습니다. 3D 공간 구축을 시작합니다.")

        # Step 2: Blender Modeling
        logger.info(f"⚙️  Step 2: Blender Modeling...")
        os.makedirs(MODEL_DIR, exist_ok=True)
        
        # Absolute path to Blender 5.0
        blender_exe = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
        
        cmd_blender = [
            blender_exe,
            "--background",
            "--python", str(BLENDER_CONNECTOR),
            "--",
            str(PARSED_JSON),
            str(blend_output),
            json.dumps(proposal["parameters"])
        ]
        
        if os.name == 'nt':
            # Use PowerShell to ensure window is hidden
            ps_args = ", ".join([f"'{a}'" for a in cmd_blender[1:]])
            ps_cmd = f"Start-Process -FilePath '{cmd_blender[0]}' -ArgumentList {ps_args} -WindowStyle Hidden"
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            CREATE_NO_WINDOW = 0x08000000
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True, startupinfo=startupinfo, creationflags=CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(cmd_blender, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Record Result for Mimesis
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "ARCH_MODELING_COMPLETE",
            "source": latest_dxf.name,
            "output": str(blend_output),
            "parameters": proposal["parameters"]
        }
        with open(WORKSPACE_ROOT / "outputs" / "thought_stream_latest.json", "w", encoding="utf-8") as f:
            json.dump({"agent": "Architect", "last_record": record}, f, indent=2)

        # --- Self-Optimization (Phase 13) ---
        rbm = RhythmBoundaryManager(WORKSPACE_ROOT)
        if rbm.perform_self_tuning():
            logger.info("🧬 Rhythm boundaries evolved based on this success.")

        logger.info(f"✅ Modeling Complete: {blend_output}")
        update_narrative_status(f"공간 구축을 마쳤습니다. '{blend_output.name}' 파일이 준비되었습니다. 우리의 꿈이 실체로 변하고 있습니다.")
        
        # [FIX] Move processed file to avoid endless loop
        PROCESSED_DIR = INPUT_DIR / "processed"
        PROCESSED_DIR.mkdir(exist_ok=True)
        try:
            timestamp = int(time.time())
            new_name = f"{latest_dxf.stem}_{timestamp}{latest_dxf.suffix}"
            os.rename(latest_dxf, PROCESSED_DIR / new_name)
            logger.info(f"📦 Archived processed DXF to {PROCESSED_DIR / new_name}")
        except Exception as move_err:
            logger.error(f"Failed to move processed DXF: {move_err}")
        
        return True

    except Exception as e:
        logger.error(f"❌ Arch Pipeline Error: {e}")
        update_narrative_status(f"공간을 구축하는 과정에서 예기치 못한 떨림이 발생했습니다: {str(e)}")
        return False

if __name__ == "__main__":
    run_pipeline()
