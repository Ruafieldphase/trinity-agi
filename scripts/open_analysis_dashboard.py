#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Analysis Dashboard
Opens all analysis reports in VS Code for easy comparison
"""
import os
import sys
import subprocess
from pathlib import Path
from workspace_root import get_workspace_root

BASE = get_workspace_root()
OUTPUTS = BASE / "outputs"

# Report files to open
REPORTS = [
    ("Sena Correlation (MD)", OUTPUTS / "sena_correlation_latest.md"),
    ("Sena Correlation (JSON)", OUTPUTS / "sena_correlation_latest.json"),
    ("Cache Analysis (MD)", OUTPUTS / "cache_analysis_latest.md"),
    ("Cache Analysis (JSON)", OUTPUTS / "cache_analysis_latest.json"),
    ("Session Summary", BASE / "ÍπÉÏΩî_?∏ÏÖò_?ÑÎ£å_SenaÎ∂ÑÏÑù_Ï∫êÏãúÏµúÏ†Å??2025-10-28.md"),
]

def main():
    print("?ìä Opening Analysis Dashboard...\n")
    
    opened = 0
    missing = []
    
    for name, path in REPORTS:
        if path.exists():
            try:
                subprocess.run(["code", str(path)], check=False)
                print(f"??{name}")
                opened += 1
            except Exception as e:
                print(f"?†Ô∏è  {name}: Failed to open ({e})")
        else:
            print(f"??{name}: Not found")
            missing.append(name)
    
    print(f"\n?ìà Dashboard Summary:")
    print(f"   Opened: {opened}/{len(REPORTS)}")
    
    if missing:
        print(f"   Missing: {', '.join(missing)}")
        print("\n?í° Run analysis tasks to generate missing reports:")
        print("   - ?ìä Analysis: Sena Correlation (10m window)")
        print("   - ?ìà Analysis: Cache Effectiveness Report")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
