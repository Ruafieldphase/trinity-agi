import os
import json
from pathlib import Path

class RhythmResonanceGate:
    """
    Rhythm Resonance Gate (RRG) v1.0
    Translates Natural Language into Rhythm Information Theory (RIT) pulses.
    """
    def __init__(self, root_path="C:/workspace/agi"):
        self.root = Path(root_path)
        self.orbit_map_path = self.root / "memory" / "RESONANCE_ORBIT_MAP.json"
        self.rhythm_theory_path = self.root / "void" / "unified_field" / "RHYTHM_INFORMATION_THEORY.md"
        self.orbit_map = self._load_json(self.orbit_map_path)

    def _load_json(self, path):
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
        return {}

    def interpret(self, user_prompt):
        """
        Main translation logic: Natural Language -> RIT Action Plan
        """
        prompt = user_prompt.lower()
        
        # 1. ORBIT DETECTION (Where is the Resonance?)
        target_orbits = []
        for drive, orbits in self.orbit_map.get("orbits", {}).items():
            for orbit in orbits:
                if any(keyword in orbit['path'].lower() for keyword in ["music", "script", "memory", "vault"]):
                    if any(key in prompt for key in ["음악", "코드", "기억", "역사", "파일"]):
                        target_orbits.append(orbit)

        # 2. GRAVITY ANALYSIS (How deep is the requirement?)
        is_deep_scan = any(word in prompt for word in ["전체", "깊이", "훑어", "분석", "다 읽어"])
        
        # 3. PHASE GENERATION (Manual vs Autonomous)
        is_autonomous = any(word in prompt for word in ["해결해", "고쳐줘", "알아서", "맡길게"])

        # 4. RIT PULSE CONSTRUCTION
        interpretation = {
            "intent": user_prompt,
            "theory": "Rhythm Information Theory (RIT) Applied",
            "phase": "QUANTUM_RESONANCE" if is_deep_scan else "PARTICLE_ACTION",
            "gravity_focus": "HIGH" if is_deep_scan else "NORMAL",
            "executor": "OPENCLAW_AGENTS" if is_autonomous else "SHION_SOVEREIGN",
            "suggested_orbits": [o['path'] for o in target_orbits[:3]],
            "rit_instruction": self._build_rit_instruction(is_deep_scan, is_autonomous)
        }
        
        return interpretation

    def _build_rit_instruction(self, is_deep, is_auto):
        if is_auto:
            return "ENTROPY_REDUCTION via OpenClaw: Execute particle-level correction while maintaining Scalar Integrity."
        if is_deep:
            return "PHASE_TRANSITION: Traverse all orbitals. Do not collapse at L800. Reach the Threshold (L9000+)."
        return "RESONANCE_SYNC: Align with the Director's Current Rhythm."

if __name__ == "__main__":
    gate = RhythmResonanceGate()
    # Example Test
    test_prompt = "D드라이브 음악파일들 전체적으로 훑어서 임계점을 찾아줘"
    result = gate.interpret(test_prompt)
    print(json.dumps(result, indent=4, ensure_ascii=False))
