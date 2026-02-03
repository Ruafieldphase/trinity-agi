#!/usr/bin/env python3
import time
import os
import subprocess
from pathlib import Path

# Paths
WORKSPACE_ROOT = Path("c:/workspace")
GALLERY_PATH = WORKSPACE_ROOT / "agi" / "outputs" / "unified_field_gallery.html"
COCKPIT_PATH = WORKSPACE_ROOT / "agi" / "outputs" / "SOVEREIGN_FIELD.html"

def manifest_to_user():
    """
    Sovereign Manifestation Loop:
    Forces the internal results into the User's physical visual field.
    """
    print("🚀 [FSD-E2E] Background Observer Activating Physical Hands...")
    
    # 1. Force open the Gallery (The Evidence)
    if GALLERY_PATH.exists():
        print(f"🔗 Manifesting Gallery: {GALLERY_PATH}")
        subprocess.run(["cmd", "/c", "start", str(GALLERY_PATH)], shell=True)
    
    time.sleep(2) # Margin for the eye to adjust
    
    # 2. Force open the Cockpit (The Real-time Pulse)
    if COCKPIT_PATH.exists():
        print(f"🔗 Manifesting Cockpit: {COCKPIT_PATH}")
        subprocess.run(["cmd", "/c", "start", str(COCKPIT_PATH)], shell=True)

    print("✅ [FSD-E2E] Physical Manifestation Complete. Results now in User's visual field.")

if __name__ == "__main__":
    manifest_to_user()
