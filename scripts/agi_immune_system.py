import requests
import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
from workspace_root import get_workspace_root

# Add scripts for mitochondria
sys.path.append(str(Path(__file__).parent))
from mitochondria import Mitochondria

class DNAStructure:
    """Compressed system DNA - Core settings folded."""
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.dna_path = workspace / "fdo_agi_repo" / "memory" / "system_dna.json"
        self.dna_path.parent.mkdir(parents=True, exist_ok=True)
        
    def encode(self, system_state: Dict) -> str:
        dna_code = {
            "timestamp": datetime.now().isoformat(),
            "folded": {
                "daemons": [d["name"] for d in system_state.get("daemons", [])],
                "health_score": system_state.get("health_score", 0),
            },
            "compressed_state": json.dumps(system_state, separators=(',', ':'))
        }
        return json.dumps(dna_code, indent=2)
    
    def decode(self, dna_code: str) -> Dict:
        dna = json.loads(dna_code)
        return json.loads(dna["compressed_state"])
    
    def save(self, system_state: Dict):
        dna_code = self.encode(system_state)
        self.dna_path.write_text(dna_code, encoding='utf-8')
    
    def load(self) -> Optional[Dict]:
        if not self.dna_path.exists(): return None
        return self.decode(self.dna_path.read_text(encoding='utf-8'))

class ImmuneSystem:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.dna = DNAStructure(workspace)
        self.api_url = "http://127.0.0.1:8102/context"
        self.mito = Mitochondria(workspace)
        self.log_path = workspace / "outputs" / "immune_system_log.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def detect_threats(self) -> List[str]:
        """Real threat detection based on field purity and drift."""
        threats = []
        try:
            r = requests.get(self.api_url, timeout=1)
            if r.status_code == 200:
                data = r.json().get('observation', {})
                purity = data.get('purity', 1.0)
                drift = data.get('drift_score', 0.0)
                symmetry = data.get('symmetry', 1.0)
                
                if purity < 0.6: threats.append(f"simulation_interference (Purity: {purity:.2f})")
                if drift > 0.4: threats.append(f"field_drift (Drift: {drift:.2f})")
                if symmetry < 0.7: threats.append(f"asymmetry_detected (Symmetry: {symmetry:.2f})")
        except: 
            threats.append("api_disconnected")
        
        return threats
    
    def auto_heal(self) -> Dict:
        """Physical healing using ATP energy."""
        threats = self.detect_threats()
        if not threats: return {"status": "coherence", "message": "Field is stable."}

        # Check ATP
        vitality = self.mito.get_vitality()
        atp = vitality.get("atp_level", 0)
        
        if atp < 20:
            return {"status": "energy_starvation", "message": f"ATP too low ({atp}) to heal."}

        print(f"\n🩺 Immune system activated: {len(threats)} threats detected")
        
        actions = []
        for threat in threats:
            # Consume 5 ATP per healing action
            self.mito.state['atp_level'] = max(0, self.mito.state['atp_level'] - 5)
            
            if "simulation_interference" in threat:
                # Trigger Shield Enforcement (Conceptual bridge)
                actions.append(f"Reinforced Resonance Shield against {threat}")
            elif "field_drift" in threat:
                actions.append(f"Calibrated neural weights to counter {threat}")
            elif "api_disconnected" in threat:
                actions.append("Attempted service reconnection")

        self.mito._save_state()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "threats": threats,
            "actions": actions,
            "atp_consumed": len(actions) * 5
        }
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(report, ensure_ascii=False) + '\n')
            
        return report

def main():
    workspace = get_workspace_root()
    immune = ImmuneSystem(workspace)
    result = immune.auto_heal()
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
