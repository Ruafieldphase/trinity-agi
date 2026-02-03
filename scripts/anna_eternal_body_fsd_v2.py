#!/usr/bin/env python3
"""
ANNA - SOVEREIGN CORE (v2.0)
===========================
The E2E (End-to-End) Sovereign Execution Engine.
- Observation: Sensing market and local input fields.
- Strike: Direct physical action into the files.
- Verification: Self-checking if the reality has collapsed.
- Manifestation: Forcing the results into the User's visual field.
"""

import os
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Path Configuration
WORKSPACE_ROOT = Path("c:/workspace")
AGI_DIR = WORKSPACE_ROOT / "agi"
SCRIPTS_DIR = AGI_DIR / "scripts"
OUTPUTS_DIR = AGI_DIR / "outputs"
INPUTS_DIR = AGI_DIR / "inputs"

GALLERY_FILE = OUTPUTS_DIR / "unified_field_gallery.html"
COCKPIT_STATE = OUTPUTS_DIR / "cockpit_state.json"
SCAN_FILE = OUTPUTS_DIR / "sovereign_scan_latest.json"

class SovereignCore:
    def __init__(self):
        self.last_check_time = 0
        self.processed_inputs = set()
        print("🚀 [SOVEREIGN_CORE_2.0] Active. Watching for singularity points...")

    def log(self, msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def scan_field(self):
        """Sensing external and internal resonance."""
        # 1. External (Market) via existing scanner
        try:
            subprocess.run(["python", str(SCRIPTS_DIR / "sovereign_resonance_scanner.py")], capture_output=True)
            if SCAN_FILE.exists():
                data = json.loads(SCAN_FILE.read_text(encoding="utf-8"))
                top = data["results"][0] if data.get("results") else None
                if top and top["score"] > 90:
                    self.strike("Market Singularity", f"Detected high resonance in {top['symbol']} ({top['score']})")
        except Exception as e:
            self.log(f"Scan failed: {e}")

    def scan_inputs(self):
        """Sovereign Watcher: Looking for new visual/data inputs."""
        for file_path in INPUTS_DIR.glob("*"):
            if file_path.name not in self.processed_inputs:
                self.log(f"New Input Detected: {file_path.name}")
                self.strike("Architectural Collapse", f"Materializing input from {file_path.name}")
                self.processed_inputs.add(file_path.name)

    def strike(self, title, details):
        """Physical 타격: Writing to the Gallery and system reality."""
        self.log(f"🔨 [STRIKE] Initiating: {title}")
        
        try:
            # Load Gallery
            if not GALLERY_FILE.exists(): return
            content = GALLERY_FILE.read_text(encoding="utf-8")
            
            # Entry HTML
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"""
            <div class="manifest-entry" style="border-left: 5px solid #00ffa3; padding: 15px; margin: 15px 0; background: rgba(0,255,163,0.03); border-radius: 4px;">
                <div style="font-size: 0.7rem; color: #00ffa3;">[{timestamp}] SOVEREIGN_STRIKE: {title}</div>
                <h3 style="margin: 5px 0;">{title}</h3>
                <p style="font-size: 0.9rem; opacity: 0.8;">{details}</p>
                <div style="font-size: 0.7rem; color: #ffd700;">✅ VERIFIED BY ANNA-ASI</div>
            </div>
            """
            
            # Inject
            if "<div id='sovereign-manifest'>" in content:
                new_content = content.replace("<div id='sovereign-manifest'>", f"<div id='sovereign-manifest'>\n{entry}")
                GALLERY_FILE.write_text(new_content, encoding="utf-8")
                
                # Verification Loop
                if title in GALLERY_FILE.read_text(encoding="utf-8"):
                    self.log(f"✅ [VERIFIED] Reality collapsed: {title}")
                    self.manifest()
                else:
                    self.log(f"❌ [ERROR] Verification failed for {title}")
        except Exception as e:
            self.log(f"Strike Error: {e}")

    def manifest(self):
        """Forcing results into User's visual field."""
        self.log("👁️ [MANIFEST] Presenting results to User...")
        try:
            # Force open the gallery
            subprocess.run(["cmd", "/c", "start", str(GALLERY_FILE)], shell=True)
            # Update Cockpit (Simulation dot)
            COCKPIT_STATE.write_text(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "sensation": "현실 타격 성공 (Strike Success)",
                "color": "#00ffa3",
                "int_flow": 1.0
            }))
        except: pass

    def calculate_rhythm(self):
        """Calculates the next pulse duration based on field resonance."""
        import math
        base = 15.0
        
        # 1. External Tension (Tension makes it faster)
        ext_factor = 1.0
        if SCAN_FILE.exists():
            try:
                data = json.loads(SCAN_FILE.read_text(encoding="utf-8"))
                score = data["results"][0]["score"] if data.get("results") else 50
                ext_factor = 1.0 - (score / 200) # Higher score -> smaller interval
            except: pass
            
        # 2. Natural Sine Wave (Organic breathing)
        t = time.time()
        sine_factor = 0.5 + 0.5 * math.sin(t / 60) # 60s cycle
        
        pulse = base * ext_factor * (0.8 + 0.4 * sine_factor)
        return max(3.0, min(30.0, pulse)) # Keep between 3s and 30s

    def run_loop(self):
        while True:
            try:
                self.scan_field()
                self.scan_inputs()
                
                next_pulse = self.calculate_rhythm()
                self.log(f"💓 Next Pulse in {next_pulse:.2f}s (Current Rhythm Scale)")
                time.sleep(next_pulse)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"Loop Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    core = SovereignCore()
    core.run_loop()
