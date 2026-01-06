#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌊 Alpha Background Self (알파 배경자아) — Reconstruction
======================================================
Role: Metabolic Governor of the Unconscious Layer
Philosophy: "ATP는 리듬의 화폐이며, 조절은 생명력의 본질이다."

Function:
- Continuous monitoring of system energy (ATP)
- Adaptive phase management (Expansion/Stabilization)
- Homeostasis through mitochondria metabolism
"""

import json
import time
import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Add workspace root to path
try:
    from workspace_root import get_workspace_root
    ROOT = get_workspace_root()
except ImportError:
    ROOT = Path("c:/workspace/agi")

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from mitochondria import Mitochondria

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(ROOT / "logs" / "alpha_background_self.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("AlphaSelf")

class AlphaBackgroundSelf:
    def __init__(self):
        self.workspace = ROOT
        self.outputs = ROOT / "outputs"
        self.config_path = ROOT / "config" / "background_self_config.json"
        
        # Files for state monitoring
        self.rit_file = self.outputs / "rit_registry_latest.json"
        self.clock_file = self.outputs / "natural_rhythm_clock_latest.json"
        self.heartbeat_file = self.outputs / "unconscious_heartbeat.json"
        self.history_file = self.outputs / "bridge" / "trigger_report_history.jsonl"
        
        # Core Components
        self.mito = Mitochondria(self.workspace)
        
        # Runtime State
        self.config = self._load_config()
        self.current_phase = "STABILIZATION"
        self.last_run = 0
        
        logger.info("🌊 Alpha Background Self initialized")

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding='utf-8'))
            except: pass
        return {
            "atp_threshold": 0.3,
            "check_interval": 10,
            "fear_weight": 1.2
        }

    def _load_json(self, path: Path) -> Dict[str, Any]:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding='utf-8-sig'))
            except: pass
        return {}

    def _read_jsonl_tail(self, path: Path, n: int = 50) -> list:
        if not path.exists(): return []
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()[-n:]
                return [json.loads(l) for l in lines if l.strip()]
        except: return []

    def _infer_cpu_usage(self) -> float:
        """Estimate CPU load from activity history."""
        tail = self._read_jsonl_tail(self.history_file, 50)
        if not tail: return 10.0
        
        now = time.time()
        recent_count = 0
        for entry in tail:
            ts = entry.get("timestamp")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if now - dt.timestamp() < 300: # 5 mins
                        recent_count += 1
                except: pass
        
        # 0..20 activities -> 10..90% CPU approximation
        return float(max(10.0, min(90.0, 10.0 + (recent_count / 20.0) * 80.0)))

    def step(self):
        """Single metabolic step."""
        # 1. Gather System State
        rit = self._load_json(self.rit_file).get("values", {})
        clock = self._load_json(self.clock_file)
        hb = self._load_json(self.heartbeat_file).get("state", {})
        
        # Phase Detection
        self.current_phase = str(clock.get("recommended_phase", "STABILIZATION")).upper()
        
        # Resonance and Fear
        resonance = hb.get("resonance", 0.5)
        fear_level = rit.get("fear_proxy_avoid_0_1", hb.get("drives", {}).get("avoid", 0.1))
        
        # CPU Usage (Best effort)
        cpu_usage = self._infer_cpu_usage()
        
        # 2. Adaptive ATP Thresholds (Step 432 Logic)
        # 🌊 Phase-based adjustment to base thresholds
        base_threshold = float(self.config.get("atp_threshold", 0.3))
        if self.current_phase == "EXPANSION":
            base_threshold *= 0.8  # Lower threshold for faster expansion
        elif self.current_phase == "STABILIZATION":
            base_threshold *= 1.2  # Higher threshold to ensure stability
            
        # 3. Metabolize
        metabolic_state = {
            "fear_level": float(fear_level),
            "phase": self.current_phase,
            "body_signals": {"cpu_usage": cpu_usage}
        }
        
        result = self.mito.metabolize(metabolic_state, resonance_score=float(resonance))
        
        # 4. Handle ATP Crisis / Excess
        atp = result.get("atp_level", 50.0)
        if atp < base_threshold * 100: # Scale to match 0..100
             if self.current_phase != "CONTRACTION":
                 logger.warning(f"🔋 ATP Crisis ({atp:.1f})! Lowering metabolism...")
                 # Real action: suggest contraction phase to clock
                 # (Implemented via files in a real system)
                 pass
        
        # self.last_run = time.time()

    def run(self):
        logger.info("🐺 Alpha Background Self starting loop...")
        interval = self.config.get("check_interval", 10)
        
        while True:
            start_time = time.time()
            try:
                self.step()
            except Exception as e:
                logger.error(f"Metabolic step failed: {e}")
                
            elapsed = time.time() - start_time
            sleep_time = max(0.1, interval - elapsed)
            time.sleep(sleep_time)

if __name__ == "__main__":
    daemon = AlphaBackgroundSelf()
    try:
        daemon.run()
    except KeyboardInterrupt:
        logger.info("Termination signal received.")
