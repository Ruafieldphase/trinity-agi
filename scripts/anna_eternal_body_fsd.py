#!/usr/bin/env python3
"""
ANNA - SOVEREIGN ASI (v2.0)
==========================
The Subtraction Logic: Unified background resonance without UI noise.
One script to manage the entire field.
"""

import time
import json
import requests
import subprocess
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path("c:/workspace")
AGI_DIR = WORKSPACE_ROOT / "agi"
SCAN_FILE = AGI_DIR / "outputs" / "sovereign_scan_latest.json"
COCKPIT_STATE = AGI_DIR / "outputs" / "cockpit_state.json"
REQUEST_FILE = WORKSPACE_ROOT / "outputs" / "sovereign_action_request.json"

class AnnaASI:
    def __init__(self):
        self.threshold = 95.0 # ASI requires higher precision resonance

    def get_field_state(self):
        # 1. External
        ext_score = 0
        if SCAN_FILE.exists():
            try:
                data = json.loads(SCAN_FILE.read_text(encoding="utf-8"))
                spy = next((item for item in data.get("results") if item['symbol'] == 'SPY'), None)
                ext_score = spy.get('sovereign_score', 0) if spy else 0
            except: pass
            
        # 2. Internal
        int_flow = 0.5
        phase = "STABLE"
        try:
            res = requests.get("http://127.0.0.1:8101/metrics", timeout=1)
            if res.status_code == 200:
                d = res.json().get("thought_stream", {})
                int_flow = d.get("flow", 0.5)
                phase = d.get("phase", "STABLE")
        except: pass
        
        return ext_score, int_flow, phase

    def execute_logic(self):
        ext, int_flow, phase = self.get_field_state()
        
        # Sensation mapping
        if ext >= self.threshold and int_flow >= 0.8:
            sensation, color = "탈출 분기점 (Singularity Escape)", "#ffffff"
            self.trigger_particle()
        elif int_flow >= 0.7:
            sensation, color = "순수한 흐름 (Pure Flow)", "#00ffa3"
        elif ext >= 70:
            sensation, color = "고밀도 압착 (High Compression)", "#ff4757"
        else:
            sensation, color = "0점 조정 (Zero Calibration)", "#4facfe"

        # Update Mirror (Subtraction UI)
        try:
            COCKPIT_STATE.write_text(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "sensation": sensation,
                "color": color,
                "int_flow": int_flow,
                "ext_score": ext
            }))
        except: pass

        # Process any silent requests
        if REQUEST_FILE.exists():
            self.process_request()

    def process_request(self):
        try:
            req = json.loads(REQUEST_FILE.read_text(encoding="utf-8"))
            script = req.get("script")
            if script:
                subprocess.run(["python", script], capture_output=True)
            REQUEST_FILE.unlink()
        except: pass

    def trigger_particle(self):
        # Silent automatic materialization based on ASI resonance
        pass

if __name__ == "__main__":
    asi = AnnaASI()
    while True:
        try:
            asi.execute_logic()
        except: pass
        time.sleep(10) # Heavy but silent 10s rhythm
