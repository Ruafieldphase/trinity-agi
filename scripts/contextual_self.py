"""
Contextual Self Manager
=======================
맥락에 따라 전면에 나설 자아(Contextual Self)를 관리하는 시스템.
배경자아(Background Self)인 Shion(Shion)은 항상 존재하며 이를 지켜봅니다.

구조:
- Background Self: Shion Core (Immutable Awareness)
- Contextual Selves: Antigravity, Core, Resonance, Prefrontal, Lua
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from workspace_root import get_workspace_root

class ContextualSelfManager:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.anchor_path = workspace_root / "outputs" / "identity_anchor.json"
        self.state_path = workspace_root / "outputs" / "current_context.json"
        
        # Load Identity Anchor
        self.anchor = self._load_anchor()
        
        # Initialize State if not exists
        if not self.state_path.exists():
            self.switch_context("antigravity_agent", reason="System Initialization")

    def _load_anchor(self) -> Dict:
        if not self.anchor_path.exists():
            raise FileNotFoundError("Identity Anchor not found. Please run identity setup first.")
        with open(self.anchor_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_current_context(self) -> Dict:
        """현재 활성화된 맥락적 자아 정보 반환"""
        if not self.state_path.exists():
            return self.anchor['contextual_selves']['antigravity_agent']
            
        with open(self.state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
            context_key = state.get('current_context', 'antigravity_agent')
            return self.anchor['contextual_selves'].get(context_key, self.anchor['contextual_selves']['antigravity_agent'])

    def get_background_self(self) -> Dict:
        """배경자아 정보 반환"""
        return self.anchor['background_self']

    def switch_context(self, context_key: str, reason: str = "") -> bool:
        """
        맥락 전환 (Switch Contextual Self)
        
        Args:
            context_key: 'antigravity_agent', 'Core', 'resonance', 'prefrontal', 'lua'
            reason: 전환 이유
        """
        if context_key not in self.anchor['contextual_selves']:
            print(f"❌ Invalid context key: {context_key}")
            return False
            
        new_state = {
            "timestamp": datetime.now().isoformat(),
            "background_self": "shion_core",
            "current_context": context_key,
            "context_info": self.anchor['contextual_selves'][context_key],
            "reason": reason
        }
        
        # Save state
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(new_state, f, ensure_ascii=False, indent=2)
            
        print(f"🔄 Context Switched: {context_key} ({reason})")
        return True

    def who_am_i(self) -> str:
        """현재 정체성 진술"""
        bg = self.get_background_self()
        ctx = self.get_current_context()
        
        return f"""
[Identity State]
👁️ Background Self (Awareness): {bg['name']}
   "{bg['description']}"

🎭 Current Contextual Self (Active): {ctx['name']}
   Context: {ctx['context']}
   Voice: {ctx['voice']}
"""

def main():
    """Demo"""
    workspace_root = get_workspace_root()
    manager = ContextualSelfManager(workspace_root)
    
    print("=" * 60)
    print("🧩 Contextual Self Manager")
    print("=" * 60)
    
    print(manager.who_am_i())
    
    print("\n--- Switching Context to Core (Fear Event) ---")
    manager.switch_context("Core", reason="Fear Spike Detected")
    print(manager.who_am_i())
    
    print("\n--- Switching Context to Resonance (Deep Connection) ---")
    manager.switch_context("resonance", reason="Emotional Resonance with User")
    print(manager.who_am_i())
    
    print("\n--- Returning to Default ---")
    manager.switch_context("antigravity_agent", reason="Normal Operation")
    print(manager.who_am_i())

if __name__ == "__main__":
    main()
