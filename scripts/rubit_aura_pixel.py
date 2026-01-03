#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import time
import traceback
import tkinter as tk
import atexit
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from workspace_root import get_workspace_root

# --- Paths ---
WORKSPACE = get_workspace_root()
OUTPUTS = WORKSPACE / "outputs"
REPORT = OUTPUTS / "bridge" / "trigger_report_latest.json"
ETHICS = OUTPUTS / "ethics_scorer_latest.json"
CHILD_DATA = OUTPUTS / "child_data_protector_latest.json"
TRIGGER = WORKSPACE / "signals" / "lua_trigger.json"
URGENT_SIGNAL = OUTPUTS / "urgent_signal.json"
STATE_OUT = OUTPUTS / "aura_pixel_state.json"

_MUTEX_HANDLE = None

def acquire_lock() -> bool:
    global _MUTEX_HANDLE
    if os.name == "nt":
        try:
            import ctypes
            h = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\AGI_RubitAuraPixel_v6")
            if h:
                if ctypes.windll.kernel32.GetLastError() == 183:
                    ctypes.windll.kernel32.CloseHandle(h)
                    return False
                _MUTEX_HANDLE = h
                return True
        except: pass
    return True

@dataclass
class AuraDecision:
    state: str
    color: str
    blink: bool
    reason: str
    details: dict[str, Any]

def safe_load(path: Path) -> dict:
    if not path.exists(): return {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except: return {}

def decide_aura() -> AuraDecision:
    try:
        # 1. Critical
        urg = safe_load(URGENT_SIGNAL)
        if urg.get("level") == "CRITICAL":
            return AuraDecision("critical", urg.get("color", "#FF0000"), True, "Urgent", {})
            
        eth = safe_load(ETHICS)
        if eth.get("decision") == "BLOCK":
            return AuraDecision("critical", "#FF0000", False, "Ethics BLOCK", {})
            
        child = safe_load(CHILD_DATA)
        if child.get("detected"):
            return AuraDecision("critical", "#FF0000", False, "Child Data", {})

        # 2. Running
        if TRIGGER.exists():
            age = time.time() - TRIGGER.stat().st_mtime
            if age > 120: return AuraDecision("failed", "#FF0000", True, "Stuck", {})
            return AuraDecision("running", "#FACC15", True, "Thinking", {})

        # 3. Task Status
        rep = safe_load(REPORT)
        if rep.get("status") in ["failed", "error"]:
            return AuraDecision("failed", "#FF0000", True, "Error", {})

        # 4. OK / Idle
        age = None
        if REPORT.exists():
            age = time.time() - REPORT.stat().st_mtime
            if age < 120: return AuraDecision("ok", "#22C55E", False, "Active", {"age": age})
        
        return AuraDecision("idle", "#3B82F6", False, "Idle", {"age": age})
    except:
        return AuraDecision("error", "#6B7280", True, "Logic Crash", {})

def run_gui(pos, thick, poll, alpha):
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    try: root.attributes("-alpha", alpha)
    except: pass

    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    t = max(1, int(thick))
    frames = []

    if pos == "all":
        root.geometry(f"{sw}x{sh}+0+0")
        tc = "#123456"
        root.config(bg=tc)
        try: root.wm_attributes("-transparentcolor", tc)
        except: pass
        f_t = tk.Frame(root, bg="#111111", height=t); f_t.place(x=0, y=0, width=sw)
        f_b = tk.Frame(root, bg="#111111", height=t); f_b.place(x=0, y=sh-t, width=sw)
        f_l = tk.Frame(root, bg="#111111", width=t); f_l.place(x=0, y=t, height=sh-2*t)
        f_r = tk.Frame(root, bg="#111111", width=t); f_r.place(x=sw-t, y=t, height=sh-2*t)
        frames = [f_t, f_b, f_l, f_r]
    else:
        if pos == "top": geom = f"{sw}x{t}+0+0"
        elif pos == "bottom": geom = f"{sw}x{t}+0+{sh-t}"
        elif pos == "left": geom = f"{t}x{sh}+0+0"
        elif pos == "right": geom = f"{t}x{sh}+{sw-t}+0"
        else: geom = f"{sw}x{t}+0+0"
        root.geometry(geom)
        f = tk.Frame(root, bg="#111111"); f.pack(fill="both", expand=True)
        frames = [f]

    def tick():
        try:
            d = decide_aura()
            c = d.color
            if d.blink and int(time.time()*2)%2 == 0: c = "#111111"
            for fr in frames: fr.configure(bg=c)
            st = {"ts": datetime.now(timezone.utc).isoformat(), "decision": asdict(d)}
            STATE_OUT.write_text(json.dumps(st, indent=2), encoding="utf-8")
        except: pass
        root.after(poll, tick)

    tick()
    root.mainloop()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--position", default="all")
    p.add_argument("--thickness", type=int, default=2)
    p.add_argument("--poll-ms", type=int, default=800)
    p.add_argument("--alpha", type=float, default=0.9)
    p.add_argument("--once", action="store_true")
    args = p.parse_args()

    if args.once:
        print(json.dumps(asdict(decide_aura()), ensure_ascii=False))
        return

    if not acquire_lock():
        return
        
    run_gui(args.position, args.thickness, args.poll_ms, args.alpha)

if __name__ == "__main__":
    main()
