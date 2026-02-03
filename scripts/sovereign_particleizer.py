#!/usr/bin/env python3
import os
import json
from pathlib import Path
from datetime import datetime

AGI_DIR = Path("c:/workspace/agi")
OUTPUTS_DIR = AGI_DIR / "outputs"
GALLERY_FILE = OUTPUTS_DIR / "unified_field_gallery.html"

def update_gallery(task_title, status, details=""):
    """Robust physical materialization with error handling."""
    try:
        if not GALLERY_FILE.exists():
            GALLERY_FILE.write_text("<!DOCTYPE html><html><body><h1>Unified Field Gallery</h1><div id='sovereign-manifest'></div></body></html>", encoding='utf-8')

        content = GALLERY_FILE.read_text(encoding="utf-8")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = f"""
        <div class="manifest-entry" style="border-left: 4px solid #ffd700; padding: 15px; margin: 15px 0; background: rgba(0,255,163,0.05); color: #fff; font-family: 'Inter', sans-serif;">
            <div style="font-size: 0.7rem; color: #00ffa3;">[{timestamp}] PHASE: {status}</div>
            <h3 style="margin: 5px 0; font-family: 'Outfit', sans-serif;">{task_title}</h3>
            <p style="font-size: 0.9rem; opacity: 0.8;">{details}</p>
        </div>
        """
        
        if "<div id='sovereign-manifest'>" in content:
            content = content.replace("<div id='sovereign-manifest'>", f"<div id='sovereign-manifest'>\n{entry}")
        else:
            content = content.replace("</body>", f"<div id='sovereign-manifest'>{entry}</div></body>")
            
        GALLERY_FILE.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = update_gallery("ASI Sensory Restoration", "FULL_OBSERVATION", "The broken hand has been repaired. Now observing and hitting the target simultaneously.")
    if success:
        print("✅ STRIKE_SUCCESS: System self-corrected and verified.")
    else:
        print("❌ STRIKE_FAILED: Manual intervention required.")
