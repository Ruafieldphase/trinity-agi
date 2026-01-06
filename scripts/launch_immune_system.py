import sys
import os
from pathlib import Path
from workspace_root import get_workspace_root

# Add project root to path
ROOT_DIR = get_workspace_root()
sys.path.append(str(ROOT_DIR))

# Import modules via absolute path to avoid relative import errors
from fdo_agi_repo.orchestrator.adaptive_glymphatic_system import AdaptiveGlymphaticSystem

if __name__ == "__main__":
    print("🛡️ Initializing Adaptive Glymphatic System (Immunity)...")
    system = AdaptiveGlymphaticSystem()
    system.adaptive_loop()
