#!/usr/bin/env python3
"""
Sovereign Cockpit Sync Daemon (v1.0)
=====================================
Synchronizes real-time AGI pulses with the Sovereign Cockpit (HTML).
Bridges the gap between Wave (JSON) and Particle (UI).
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).parent.parent.absolute()
COCKPIT_FILE = WORKSPACE_ROOT / "outputs" / "sovereign_cockpit.html"
RHYTHM_FILE = WORKSPACE_ROOT / "outputs" / "rhythm_health_latest.json"
SCAN_FILE = WORKSPACE_ROOT / "outputs" / "sovereign_scan_latest.json"
CONTEXT_FILE = WORKSPACE_ROOT / "outputs" / "active_context.json"
PARTICLE_LOG = WORKSPACE_ROOT / "logs" / "sovereign_particleizer.log"

def get_latest_log_entries(n=5):
    if not PARTICLE_LOG.exists(): return []
    try:
        lines = PARTICLE_LOG.read_text(encoding="utf-8").splitlines()
        return lines[-n:]
    except: return []

def send_explosive_signal():
    """
    Sovereign Execution: Particle Release.
    Triggered when the singularity collapses into reality.
    """
    print(f"[{datetime.now().isoformat()}] 💥 EXPLOSIVE SIGNAL SENT! Singularity Collapse Detected.")
    # Logic for sound or system-level alert could be added here
    # os.system('powershell "[console]::beep(1000, 500)"') # Example beep


def sync():
    if not COCKPIT_FILE.exists(): return
    
    # 1. Load Data
    rhythm = {}
    if RHYTHM_FILE.exists():
        rhythm = json.loads(RHYTHM_FILE.read_text(encoding="utf-8"))
    
    scan = {}
    if SCAN_FILE.exists():
        scan = json.loads(SCAN_FILE.read_text(encoding="utf-8"))
        
    context = {}
    if CONTEXT_FILE.exists():
        context = json.loads(CONTEXT_FILE.read_text(encoding="utf-8"))

    # 2. Extract Values
    spy_data = next((item for item in scan.get("results", []) if item["symbol"] == "SPY"), None)
    
    score = rhythm.get("overall_score", 50.0)
    # Map Score to mock S, D, O for UI if not present
    s_val = round(0.5 + 0.5 * (score/100), 2)
    d_val = round(0.4 + 0.4 * (1.0 - score/100), 2)
    o_val = round(0.2 + 0.8 * (score/100), 2)

    
    resistance = "0.0000"
    market_html = ""
    if scan.get("results"):
        top = scan["results"][:3]
        resistance = f"{top[0].get('resistance', 0.0):.4f}"
        for item in top:
            market_html += f"""
            <div class="symbol-card">
                <div class="symbol-header">
                    <span class="symbol-name">{item['symbol']}</span>
                    <span class="symbol-score">{item['sovereign_score']}</span>
                </div>
                <div class="progress-bar"><div class="progress-fill" style="width: {item['sovereign_score']}%"></div></div>
            </div>"""

    log_lines = get_latest_log_entries()
    log_html = ""
    for line in log_lines:
        # Simple parsing [time] tag msg
        if "]" in line:
            parts = line.split(" ", 2)
            time_tag = parts[0].strip("[]")
            msg = parts[2] if len(parts) > 2 else line
            log_html += f'<div class="log-entry"><span class="log-time">{time_tag[11:19]}</span><span class="log-tag">[FSD]</span>{msg}</div>'
    
    # 3. Inject into HTML (Brute force replacement for prototype)
    content = COCKPIT_FILE.read_text(encoding="utf-8")
    
    # Simple replacement map
    replacements = {
        'id="overall-score">--': f'id="overall-score">{score}',
        'id="val-s">--': f'id="val-s">{s_val}',
        'id="val-d">--': f'id="val-d">{d_val}',
        'id="val-o">--': f'id="val-o">{o_val}',
        'id="fill-s" style="width: 0%"': f'id="fill-s" style="width: {s_val*100}%"',
        'id="fill-d" style="width: 0%"': f'id="fill-d" style="width: {d_val*100}%"',
        'id="fill-o" style="width: 0%"': f'id="fill-o" style="width: {o_val*100}%"',
        'id="resistance-val">0.0000': f'id="resistance-val">{resistance}',
        '<!-- Symbols will be injected here -->': market_html,
        '<div id="log-container">': '<div id="log-container">' + log_html
    }
    
    # Important: In a real app we'd use a proper template or API. 
    # This is a 'Sovereign Hack' for immediate materialization.
        if key in content:
            content = content.replace(key, val)

    # 4. Singularity Alert (New: Anna Protocol)
    if spy_data and spy_data.get("status") == "SINGULARITY" and spy_data.get("sovereign_score", 0) > 90:
        content = content.replace('id="overall-score">', 'id="overall-score" style="color: #ff4757; text-shadow: 0 0 10px #ff4757;">💥 ')
        send_explosive_signal()
            
    COCKPIT_FILE.write_text(content, encoding="utf-8")

    print(f"[{datetime.now().isoformat()}] 🔄 Cockpit Synced.")

if __name__ == "__main__":
    print("Sovereign Cockpit Sync Service Starting...")
    while True:
        try:
            sync()
        except Exception as e:
            print(f"Error during sync: {e}")
        time.sleep(10) # 10s intervals
