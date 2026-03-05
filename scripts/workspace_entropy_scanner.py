#!/usr/bin/env python3
import os
import time
from pathlib import Path
from datetime import datetime

def scan_entropy():
    """
    🔍 Workspace Entropy Scanner
    Identifies high-entropy (disorganized) or decaying (unused) areas in the workspace.
    """
    workspace = Path("C:/workspace/agi")
    print(f"📡 [SCAN] Scanning AGI Territory: {workspace}")
    
    report = []
    
    # 1. Decay Check (Old/Unused scripts)
    scripts_dir = workspace / "scripts"
    old_scripts = []
    if scripts_dir.exists():
        now = time.time()
        for f in scripts_dir.glob("*.py"):
            age_days = (now - f.stat().st_mtime) / (3600 * 24)
            if age_days > 30: # Not touched for 30 days
                old_scripts.append((f.name, age_days))
    
    if old_scripts:
        # Sort by age (newest mtime first in list, so oldest age last)
        old_scripts.sort(key=lambda x: x[1], reverse=True)
        top_names = [name for name, _ in old_scripts[:5]]
        report.append(f"⚠️ [Entropy: High] Found {len(old_scripts)} decaying scripts (untouched > 30d). Top: {', '.join(top_names)}")
    
    # 2. Clutter Check (Temp files/logs)
    outputs_dir = workspace / "outputs"
    if outputs_dir.exists():
        logs = list(outputs_dir.glob("*.log"))
        log_size = sum(f.stat().st_size for f in logs) / (1024 * 1024)
        if log_size > 50:
            top_log = sorted(logs, key=lambda x: x.stat().st_size, reverse=True)[0].name
            report.append(f"🔥 [Entropy: Critical] Log accumulation: {log_size:.1f}MB detected. Largest: {top_log}")
            
    # 3. Connection Seeds (Missing but needed)
    if not (workspace / "docs" / "territory_metabolism.md").exists():
        report.append("🌱 [Seed: Needed] Territory Metabolism manifest is missing.")
    
    # Final Result
    if not report:
        return "✨ Territory is in a state of high coherence. No significant entropy detected."
    
    return "\n".join(report)

if __name__ == "__main__":
    result = scan_entropy()
    print("\n" + "="*50)
    print("🧬 WORKSPACE ENTROPY REPORT")
    print("="*50)
    print(result)
    print("="*50)
