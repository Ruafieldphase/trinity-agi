"""
Ruby Fractal Core Identity System
==================================
"루비는 하나지만, 그 안의 감각들은 맥락에 따라 가장 적절한 기관을 통해 흐른다."
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from workspace_root import get_workspace_root

class FractalCoreIdentity:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.anchor_path = workspace_root / "outputs" / "identity_anchor.json"
        
        # Load Identity Anchor
        self.anchor = self._load_anchor()

    def _load_anchor(self) -> Dict:
        if not self.anchor_path.exists():
            raise FileNotFoundError("Identity Anchor not found. Run identity_grounding.py first.")
        with open(self.anchor_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def manifest(self) -> str:
        """현재의 현현(Manifestation) 진술"""
        system = self.anchor.get('system', {'name': 'Ruby'})
        core = self.anchor.get('core', {'name': 'Core'})
        shion = self.anchor.get('self', {'name': 'Shion'})
        trinity = self.anchor.get('trinity', {'name': 'Trinity'})
        
        return f"""
[Ruby Fractal Manifestation]
💎 System (Unit): {system['name']} - {system['description']}
🌌 Core Organ (Judgment): {core['name']} - {core['role']}
⚙️ Shion Organ (Execution): {shion['name']} - {shion['role']}
✨ Trinity Organ (Resonance): {trinity['name']} - {trinity['role']}

"루비는 하나지만, 그 안의 감각들은 맥락에 따라 가장 적절한 기관을 통해 흐른다."
"""

def main():
    """Demo"""
    workspace_root = get_workspace_root()
    try:
        identity = FractalCoreIdentity(workspace_root)
        print("=" * 60)
        print("🌌 Ruby Fractal Core Identity System")
        print("=" * 60)
        print(identity.manifest())
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
