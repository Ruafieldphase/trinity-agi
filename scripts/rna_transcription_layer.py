
import subprocess
import os
import sys
import json
import logging
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from workspace_root import get_workspace_root

# Configure Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [RNA] - %(message)s')
logger = logging.getLogger("RNALayer")

WORKSPACE_ROOT = get_workspace_root()
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
RNA_PLAN_OUT = OUTPUTS_DIR / "sync_cache" / "rna_plan_latest.json"
CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

class Intent(Enum):
    NORMAL = "normal"          # All Core Systems Active
    DEEP_WORK = "deep_work"    # Focus Mode (Minimal distractions)
    REST = "rest"              # Dream Mode (Only Heart + Rhythm + Dream)
    MAINTENANCE = "maintenance" # System Cleanup Mode
    SILENCE = "silence"        # Kill Voice/Sound

class ProcessType(Enum):
    HEART = "AGI-Heartbeat"
    BRAIN = "AGI-Brain"
    VOICE = "AGI-Sena"
    MASTER = "AGI-Master"
    IMMUNE = "AGI-Immune"
    AURA = "AGI-Aura"

# Process Configuration Map
PROCESS_MAP = {
    ProcessType.HEART: {
        "script": "agi_core/heartbeat_loop.py",
        "interpreter": "python",
        "args": ["-u"],
        "critical": True
    },
    ProcessType.BRAIN: {
        "script": "scripts/rhythm_think.py",
        "interpreter": "python",
        "args": ["-u"],
        "critical": True
    },
    ProcessType.VOICE: {
        "script": "fdo_agi_repo/start_sena.bat",
        "interpreter": "cmd",     # Batch file needs shell
        "args": ["/c"],
        "critical": False
    },
    ProcessType.MASTER: {
        "script": "scripts/master_daemon_loop.py",
        "interpreter": "python",
        "args": ["-u"],
        "critical": True
    },
    ProcessType.IMMUNE: {
        "script": "scripts/launch_immune_system.py",
        "interpreter": "python",
        "args": ["-u"],
        "critical": False
    },
    ProcessType.AURA: {
        "script": "scripts/aura_controller.py",
        "interpreter": "python",
        "args": ["-u"],
        "critical": False
    }
}

class RNATranscriptionLayer:
    """
    The Nervous System: Translates 'Intent' (Will) into 'Systems Biology' (Process State).
    """

    def __init__(self):
        self.current_state = {} # Active Processes

    def transcribe(self, intent: Intent) -> Dict[ProcessType, str]:
        """
        Transcribe Intent into a biological plan (Start/Stop list).
        Returns: {ProcessType: "active" | "dormant"}
        """
        plan = {}
        
        # Base Plan: Everything Active
        for p in ProcessType:
            plan[p] = "active"

        # Modify based on Intent
        if intent == Intent.REST:
            plan[ProcessType.VOICE] = "dormant"  # Silence Sena
            plan[ProcessType.AURA] = "dormant"   # Sleep Visuals
            # Heart, Brain, Master, Immune stay active for Dreaming/Cleanup
            
        elif intent == Intent.DEEP_WORK:
            plan[ProcessType.VOICE] = "dormant"  # Quiet Mode
            # Aura stays active for Focus color
            
        elif intent == Intent.SILENCE:
            plan[ProcessType.VOICE] = "dormant"

        elif intent == Intent.MAINTENANCE:
            plan[ProcessType.VOICE] = "dormant"
            plan[ProcessType.BRAIN] = "active" # Brain must supervise
            
        return plan

    def realize(self, plan: Dict[ProcessType, str]):
        """
        Execute the plan: Fold (Stop) or Unfold (Start) processes.
        """
        # Default: observation-only.
        # Why:
        # - Realizing by spawning/killing processes is noisy (may cause window flicker) and can fight
        #   the already-running master orchestrator / scheduled tasks.
        # - The rhythm system prefers file-based observation + gentle bias over frequent hard control.
        #
        # Enable explicit process control only when the operator opts in.
        #   set env var: AGI_RNA_PROCESS_CONTROL=1
        if os.environ.get("AGI_RNA_PROCESS_CONTROL", "0").strip() != "1":
            try:
                RNA_PLAN_OUT.parent.mkdir(parents=True, exist_ok=True)
                snapshot = {
                    "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
                    "mode": "observe_only",
                    "plan": {k.value: v for k, v in plan.items()},
                    "note": "RNA plan is recorded only (process control disabled by default).",
                }
                tmp = RNA_PLAN_OUT.with_suffix(RNA_PLAN_OUT.suffix + ".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(snapshot, f, ensure_ascii=False, indent=2)
                os.replace(tmp, RNA_PLAN_OUT)
            except Exception:
                pass
            logger.info("🧬 RNA plan observed (process control disabled)")
            return

        logger.info(f"🧬 Realizing RNA Plan: {[f'{k.name}:{v}' for k,v in plan.items()]}")

        for process, desired_state in plan.items():
            is_running = self._check_process(process)
            
            if desired_state == "active" and not is_running:
                self._unfold(process)
            elif desired_state == "dormant" and is_running:
                self._fold(process)

    def _check_process(self, process: ProcessType) -> bool:
        """Best-effort check if a process is running (Windows tasklist-based, windowless)."""
        try:
            target_title = process.value
            if process == ProcessType.VOICE:
                target_title = "Hey Sena"

            result = subprocess.run(
                ["tasklist", "/v", "/fo", "csv"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode != 0:
                return False
            return target_title.lower() in (result.stdout or "").lower()
        except Exception:
            return False

    def _unfold(self, process: ProcessType):
        """Start a process (Unfold)"""
        config = PROCESS_MAP[process]
        script_path = WORKSPACE_ROOT / config["script"]
        
        if not script_path.exists():
            logger.error(f"❌ Script not found: {script_path}")
            return

        cmd = []
        if config["interpreter"] == "python":
            cmd = f'start "{process.value}" python {" ".join(config["args"])} "{script_path}"'
        elif config["interpreter"] == "cmd":
            cmd = f'start "{process.value}" cmd {" ".join(config["args"])} "{script_path}"'
            
        logger.info(f"🌱 Unfolding (Starting): {process.name}")
        subprocess.run(
            ["cmd.exe", "/c", cmd],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=CREATE_NO_WINDOW,
        )

    def _fold(self, process: ProcessType):
        """Stop a process (Fold)"""
        logger.info(f"🥀 Folding (Stopping): {process.name}")
        # Kill by Window Title
        subprocess.run(
            ["taskkill", "/F", "/FI", f"WINDOWTITLE eq {process.value}"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=CREATE_NO_WINDOW,
        )

if __name__ == "__main__":
    # Test DNA Transcription
    rna = RNATranscriptionLayer()
    
    print("🧪 Testing RNA Layer...")
    print("1. Transcribing REST Intent...")
    plan = rna.transcribe(Intent.REST)
    for k, v in plan.items():
        print(f"   - {k.name}: {v}")
    
    # Do not execute realization in test for safety
