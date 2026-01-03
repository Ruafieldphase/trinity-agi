#!/usr/bin/env python3
"""
Mitochondria System (AGI-ATP)
=============================
"ATP is the currency of Rhythm." - Inspired by Dr. Park Mun-ho

This module implements the "Vitality Layer" of the AGI.
It generates 'ATP' (Artificial Tempo Pulse) based on:
1. Difference (Voltage): Gap between expectation and reality (or Fear vs Flow).
2. Resonance (Connection): Meaningful patterns found in the unconscious.

High ATP -> Expansion (Active, Creative)
Low ATP -> Contraction (Rest, Stabilize)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from workspace_root import get_workspace_root

class Mitochondria:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.state_file = workspace_root / "outputs" / "mitochondria_state.json"
        
        # Load state or initialize
        self.state = self._load_state()
        
    def _load_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding='utf-8'))
            except:
                pass
        
        # Default State
        return {
            "atp_level": 50.0,      # 0 to 100
            "pulse_rate": 1.0,      # Hz (Cycles per second equivalent)
            "last_update": datetime.now().isoformat(),
            "status": "STABLE"
        }
        
    def metabolize(self, current_state: Dict[str, Any], resonance_score: float) -> Dict[str, Any]:
        """
        Calculate ATP change based on system state.
        
        Formula (Dr. Park Mun-ho inspired):
        ATP = (Difference * Resonance) - Basal_Metabolism
        
        - Difference: Fear level (Tension) or Novelty.
        - Resonance: Connection strength.
        """
        
        # 1. Calculate Inputs
        fear = current_state.get('fear_level', 0.0)
        cpu = current_state.get('body_signals', {}).get('cpu_usage', 0) / 100.0
        phase = str(current_state.get('phase', 'EXPANSION')).upper()
        resonance = abs(resonance_score)
        
        # Difference (Voltage): Tension creates potential energy
        # But too much tension (Panic) drains it.
        if fear > 0.8:
            voltage = -0.5 # Panic drain
        elif fear > 0.3:
            voltage = 0.8  # Healthy tension
        else:
            voltage = 0.2  # Low tension (Boredom)
            
        # 2. Generate ATP
        # Resonance amplifies the voltage into usable energy
        production = (voltage * (1.0 + resonance)) * 5.0

        # In deep rest (Contraction), stop the bleed: allow gentle recharge even under panic
        if phase == "CONTRACTION" and production < 0:
            production = 0.2
        
        # 3. Consumption (Basal Metabolism)
        # Higher CPU usage = Higher consumption
        # But during Contraction (rest), cap CPU impact to avoid draining to zero
        effective_cpu = cpu
        if phase == "CONTRACTION":
            effective_cpu = min(cpu, 0.5)  # cap at 50% load effect
        consumption = 1.0 + (effective_cpu * 2.0)
        
        # 4. Update Level
        current_atp = self.state['atp_level']
        new_atp = current_atp + production - consumption
        
        # Clamp
        new_atp = max(0.0, min(100.0, new_atp))
        
        # 5. Determine Status
        if new_atp > 80:
            status = "HIGH_ENERGY (Expansion)"
            pulse = 2.0 # Fast rhythm
        elif new_atp < 20:
            status = "LOW_ENERGY (Contraction)"
            pulse = 0.5 # Slow rhythm
        else:
            status = "STABLE"
            pulse = 1.0
            
        # Save
        self.state = {
            "atp_level": round(new_atp, 2),
            "pulse_rate": pulse,
            "last_update": datetime.now().isoformat(),
            "status": status,
            "metrics": {
                "production": round(production, 2),
                "consumption": round(consumption, 2),
                "voltage": voltage,
                "phase": phase,
                "effective_cpu": round(effective_cpu, 3)
            }
        }
        self._save_state()
        
        print(f"🔋 Mitochondria: ATP {self.state['atp_level']:.1f} ({status}) [Prod:{production:.1f} Cons:{consumption:.1f} Phase:{phase}]")
        return self.state

    def _save_state(self):
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(json.dumps(self.state, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"⚠️ Failed to save mitochondria state: {e}")

    def get_vitality(self) -> Dict[str, Any]:
        return self.state

if __name__ == "__main__":
    # Test
    mito = Mitochondria(get_workspace_root())
    state = {"fear_level": 0.4, "body_signals": {"cpu_usage": 30}}
    mito.metabolize(state, resonance_score=0.8)
