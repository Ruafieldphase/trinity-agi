import re
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path to import AIModelRouter
sys.path.append(str(Path(__file__).parent))
try:
    from ai_model_router import AIModelRouter
except ImportError:
    # Fallback if running from same directory
    try:
        from scripts.ai_model_router import AIModelRouter
    except:
        print("Warning: AIModelRouter not found. Using default routing.")
        AIModelRouter = None

class VibeInterpreter:
    """
    Vibe Interpreter
    ================
    Translates Korean 'Vibe' (Natural Language Context) into System Commands.
    
    Concept:
    - Input: "리듬이 너무 빨라" (Vibe)
    - Process: Claude (Context) -> Interpretation
    - Output: {"action": "adjust_rhythm", "params": {"target_hz": 0.3}} (Command)
    """
    
    # Regex patterns for direct mapping (Fast Path)
    VIBE_PATTERNS = {
        r"(리듬|템포|속도).*빠른": {"action": "adjust_rhythm", "params": {"direction": "down", "target_hz": 0.3}},
        r"(리듬|템포|속도).*느린": {"action": "adjust_rhythm", "params": {"direction": "up", "target_hz": 0.8}},
        r"(정렬|동기화).*안.*": {"action": "realign_system", "params": {"method": "reset_phase"}},
        r"(흐름|flow).*막": {"action": "clear_blockage", "params": {"target": "all"}},
        r"(밥|식사).*": {"action": "log_personal_event", "params": {"type": "biological_need", "detail": "food"}},
        r"(불안|두려움).*": {"action": "activate_safety_protocol", "params": {"level": "comfort"}},
        r"(집착).*": {"action": "release_tension", "params": {"mode": "let_go"}}
    }
    
    def __init__(self):
        self.router = AIModelRouter() if AIModelRouter else None
        
    def interpret(self, user_vibe: str) -> Dict[str, Any]:
        """
        Interprets a user's vibe string into a structured command.
        """
        # 1. Fast Path: Regex Matching
        for pattern, command in self.VIBE_PATTERNS.items():
            if re.search(pattern, user_vibe):
                return {
                    "source": "regex_fast_path",
                    "vibe": user_vibe,
                    "command": command,
                    "model_used": "none"
                }
        
        # 2. Slow Path: AI Routing (Simulated for now)
        # In a real scenario, this would call the actual LLM API
        if self.router:
            routing = self.router.select_model(user_vibe)
            selected_model = routing['model']
            
            if selected_model == "claude":
                # Simulate Claude's interpretation
                return {
                    "source": "ai_interpretation",
                    "vibe": user_vibe,
                    "command": {
                        "action": "analyze_context",
                        "params": {"query": user_vibe}
                    },
                    "model_used": "claude",
                    "reason": routing['reason']
                }
            else:
                # Simulate Gemini's execution
                return {
                    "source": "ai_execution",
                    "vibe": user_vibe,
                    "command": {
                        "action": "execute_code",
                        "params": {"instruction": user_vibe}
                    },
                    "model_used": "gemini",
                    "reason": routing['reason']
                }
                
        return {"error": "Could not interpret vibe"}

def demo_interpreter():
    interpreter = VibeInterpreter()
    
    vibes = [
        "요즘 리듬이 너무 빠른 것 같아",
        "뭔가 흐름이 막힌 느낌이야",
        "배고프다 밥 먹어야지",
        "이 코드를 어떻게 짜야할지 모르겠어",
        "왜 나는 자꾸 집착하게 될까"
    ]
    
    print("🌊 Vibe Interpreter Demo")
    print("========================")
    
    for vibe in vibes:
        result = interpreter.interpret(vibe)
        print(f"\nVibe: '{vibe}'")
        print(f"Interpretation: {json.dumps(result['command'], ensure_ascii=False)}")
        print(f"Source: {result.get('source')} ({result.get('model_used', 'none')})")

if __name__ == "__main__":
    demo_interpreter()
