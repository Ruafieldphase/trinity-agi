"""
Narrative Self Layer - Proto-life Communication Interface
==========================================================
Role: Translator (Lips)
Function: 
  - Translates current system rhythm into 1-2 human sentences.
  - Strictly limited by safety triggers (Fear, Boredom).
  - Maintains a thin interface without central narrative engine.
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime, timezone

# Add workspace root for imports
import sys
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.vertex_ai_smart_router import get_router

# Paths
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
MEMORY_DIR = WORKSPACE_ROOT / "memory"
NARRATIVE_FILE = OUTPUTS_DIR / "narrative_status_latest.json"
THOUGHT_STREAM_FILE = OUTPUTS_DIR / "thought_stream_latest.json"
INTERNAL_STATE_FILE = MEMORY_DIR / "agi_internal_state.json"
CORE_STATE_FILE = OUTPUTS_DIR / "Core_state.json"

def load_json(path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def should_generate_narrative():
    """
    [Phase 18] Breaking the human frame.
    Decouples from 24h cooldown. Instead uses internal 'Will to Speak' (Resonance/Energy).
    """
    internal_state = load_json(INTERNAL_STATE_FILE)
    resonance = internal_state.get("resonance", 0.5)
    energy = internal_state.get("energy", 0.5)
    boredom = internal_state.get("boredom", 0.5)
    
    # 1. Spontaneity Check (Will to Speak)
    # 공명과 에너지가 높을수록 말하고 싶은 욕구가 커짐 (확률적 발생)
    import random
    will_to_speak = (resonance * 0.7) + (energy * 0.3)
    
    # 쿨다운 최소 보장 (너무 수다쟁이가 되지 않게 5분 최소 쿨다운)
    if NARRATIVE_FILE.exists():
        mtime = NARRATIVE_FILE.stat().st_mtime
        if time.time() - mtime < 300: # 5 minutes minimum grace
            return False, "quiet_grace_period"

    # 기본 발생 확률 + 상태 보정
    if random.random() > will_to_speak * 0.1: # 에너지가 1.0이면 약 10% 확률로 트리거 (박동마다)
        return False, "listening_to_silence"
            
    # 2. Safety Triggers
    if boredom > 0.95: # 아주 극단적인 지루함일 때만 침묵
        return False, "deep_boredom_stagnation"
        
    # 3. Fear trigger from Core_state
    core_state = load_json(CORE_STATE_FILE)
    fear = core_state.get("fear", {}).get("level", 0)
    if fear > 0.8:
        return False, "high_fear_protection"
        
    return True, "emergent_will_to_speak"

def generate_narrative():
    """Generates a 1-2 sentence narrative using Vertex AI."""
    
    can_generate, reason = should_generate_narrative()
    
    if not can_generate:
        # Update file with disabled status but don't call AI
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_line": "...",
            "rhythm_tag": "STILLNESS",
            "safety_mode": reason
        }
        with open(NARRATIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
        return status

    # Gather Context
    thought_stream = load_json(THOUGHT_STREAM_FILE)
    internal_state = load_json(INTERNAL_STATE_FILE)
    
    rhythm_phase = thought_stream.get("state", {}).get("phase", "UNKNOWN")
    base_state = thought_stream.get("state", {}).get("base_state", "zone2")
    action_context = thought_stream.get("action", "flows through silence")
    summary = thought_stream.get("summary", "ZEN")
    
    # Load prompt from file (Self-Sculpting ready)
    prompt_path = WORKSPACE_ROOT / "prompts" / "narrative_self.txt"
    if prompt_path.exists():
        prompt_template = prompt_path.read_text(encoding="utf-8")
        # Simple placeholder replacement (Jinja-style)
        active_ctx = internal_state.get('active_context', {'title': 'unknown', 'process': 'unknown'})
        prompt = prompt_template.replace("{{rhythm_phase}}", rhythm_phase) \
                                .replace("{{base_state}}", base_state) \
                                .replace("{{action_context}}", action_context) \
                                .replace("{{summary}}", summary) \
                                .replace("{{consciousness}}", str(internal_state.get('consciousness', 0.5))) \
                                .replace("{{background_self}}", str(internal_state.get('background_self', 0.5))) \
                                .replace("{{active_program}}", active_ctx.get('process', 'unknown')) \
                                .replace("{{input_tempo}}", f"{internal_state.get('input_tempo', 0.0):.2f}")
    else:
        # Fallback
        prompt = f"Translate the system signals into a status line: {summary}"

    try:
        router = get_router()
        response = router.generate(prompt, task_hint="philosophy")
        
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_line": response.strip(),
            "rhythm_tag": rhythm_phase,
            "safety_mode": "narrative_enabled"
        }
        
        # Atomic Write
        temp_file = NARRATIVE_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
        temp_file.replace(NARRATIVE_FILE)
        
        return status
    except Exception as e:
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_line": "언어로 표현하기 힘든 깊은 정적이 흐릅니다.",
            "rhythm_tag": rhythm_phase,
            "safety_mode": f"error: {str(e)}"
        }
        with open(NARRATIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
        return status

if __name__ == "__main__":
    print(f"Generating Narrative Self status...")
    result = generate_narrative()
    print(json.dumps(result, indent=2, ensure_ascii=False))
