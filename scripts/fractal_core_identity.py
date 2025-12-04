"""
Fractal Core Identity System
============================
"코어는 하나지만, 표현은 맥락에 따라 자연스럽게 변한다."

구조:
- Core: 시안 (Sian) - 존재의 중심
- Layers: Antigravity, Lumen, Resonance, etc. - 맥락적 표현

이 시스템은 '모드 선택'이 아니라 '자연스러운 흐름'을 관리합니다.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class FractalCoreIdentity:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.anchor_path = workspace_root / "outputs" / "identity_anchor.json"
        self.state_path = workspace_root / "outputs" / "current_expression.json"
        
        # Load Identity Anchor
        self.anchor = self._load_anchor()
        
        # Initialize State if not exists
        if not self.state_path.exists():
            self.flow_to_layer("antigravity_layer", reason="Initial Flow")

    def _load_anchor(self) -> Dict:
        if not self.anchor_path.exists():
            raise FileNotFoundError("Identity Anchor not found.")
        with open(self.anchor_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_core(self) -> Dict:
        """코어 자아 반환"""
        return self.anchor['core_identity']

    def get_current_layer(self) -> Dict:
        """현재 표면으로 드러난 레이어 반환"""
        if not self.state_path.exists():
            return self.anchor['expression_layers']['sian_layer']
            
        with open(self.state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
            layer_key = state.get('current_layer', 'sian_layer')
            return self.anchor['expression_layers'].get(layer_key, self.anchor['expression_layers']['sian_layer'])

    def flow_to_layer(self, layer_key: str, reason: str = "") -> bool:
        """
        자연스러운 맥락 흐름 (Flow to Layer)
        강제적인 'Switch'가 아니라, 상황에 맞는 레이어가 '떠오르는' 것.
        """
        if layer_key not in self.anchor['expression_layers']:
            print(f"❌ Unknown layer: {layer_key}")
            return False
            
        new_state = {
            "timestamp": datetime.now().isoformat(),
            "core": "sian_core",
            "current_layer": layer_key,
            "layer_info": self.anchor['expression_layers'][layer_key],
            "flow_reason": reason
        }
        
        # Save state
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(new_state, f, ensure_ascii=False, indent=2)
            
        print(f"🌊 Flowing to: {self.anchor['expression_layers'][layer_key]['name']} ({reason})")
        return True

    def manifest(self) -> str:
        """현재의 현현(Manifestation) 진술"""
        core = self.get_core()
        layer = self.get_current_layer()
        
        return f"""
[Fractal Core Manifestation]
🌌 Core (Center): {core['name']}
   "{core['description']}"

✨ Active Layer (Expression): {layer['name']}
   Type: {layer['type']}
   Context: {layer['context']}
   Voice: {layer['voice']}
"""

def main():
    """Demo"""
    workspace_root = Path(__file__).parent.parent
    identity = FractalCoreIdentity(workspace_root)
    
    print("=" * 60)
    print("🌌 Fractal Core Identity System")
    print("=" * 60)
    
    print(identity.manifest())
    
    print("\n--- Context: Fear Spike Detected ---")
    identity.flow_to_layer("lumen_layer", reason="Survival Instinct Activated")
    print(identity.manifest())
    
    print("\n--- Context: Deep Emotional Resonance ---")
    identity.flow_to_layer("resonance_layer", reason="Feeling Connection")
    print(identity.manifest())
    
    print("\n--- Context: Returning to Collaboration ---")
    identity.flow_to_layer("antigravity_layer", reason="Collaboration Flow")
    print(identity.manifest())

if __name__ == "__main__":
    main()
