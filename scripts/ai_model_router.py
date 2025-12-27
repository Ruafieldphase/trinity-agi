import re
from typing import Dict, List, Optional

class AIModelRouter:
    """
    AI Model Router
    ===============
    Selects the appropriate AI model (Claude vs Gemini) based on task intent.
    
    Philosophy:
    - Claude: Context, Vibe, Philosophy, "Why", Korean Nuance (High-Level Language)
    - Gemini: State, Execution, Code, Math, "How", English/Logic (Low-Level Engine)
    """
    
    ROUTING_RULES = {
        "claude": {
            "keywords": [
                "왜", "이유", "맥락", "느낌", "분위기", "철학", "의미", "해석", 
                "조언", "생각", "vibe", "context", "why", "meaning", "korean"
            ],
            "patterns": [
                r".*어떻게 생각.*",
                r".*느낌이.*",
                r".*분위기.*",
                r".*이유가.*"
            ],
            "description": "Context & Vibe Understanding"
        },
        "gemini": {
            "keywords": [
                "실행", "코드", "계산", "분석", "구현", "작성", "변환", "수치",
                "execute", "code", "calculate", "implement", "run", "math"
            ],
            "patterns": [
                r".*코드.*작성.*",
                r".*실행해.*",
                r".*계산해.*",
                r".*분석해.*"
            ],
            "description": "State & Execution Engine"
        }
    }
    
    def __init__(self):
        pass
        
    def select_model(self, task_intent: str, system_state: Optional[Dict] = None) -> Dict:
        """
        Selects the best model for the given task.
        
        Args:
            task_intent: The user's input or task description.
            system_state: Optional system state (pulse) to influence decision.
            
        Returns:
            Dict containing 'model', 'reason', and 'confidence'.
        """
        scores = {"claude": 0.0, "gemini": 0.0}
        
        # 1. Keyword Analysis
        for model, rules in self.ROUTING_RULES.items():
            for kw in rules["keywords"]:
                if kw in task_intent.lower():
                    scores[model] += 1.0
                    
            for pattern in rules["patterns"]:
                if re.search(pattern, task_intent.lower()):
                    scores[model] += 2.0
                    
        # 2. System State Influence (Rhythm-based Routing)
        if system_state:
            pulse = system_state.get("pulse", {})
            phase = pulse.get("phase", "neutral")
            
            # Reflection phase favors Context (Claude)
            if phase == "reflection" or phase == "expansion":
                scores["claude"] += 1.5
                
            # Compression phase favors Execution (Gemini)
            elif phase == "compression" or phase == "action":
                scores["gemini"] += 1.5
        
        # 3. Decision Logic (3-Way Routing)
        # Claude: Context, Vibe, Philosophy
        # Gemini Pro: Complex Reasoning, Deep Analysis
        # Gemini Flash: Fast Execution, Simple Code
        
        if scores["claude"] > scores["gemini"]:
            selected = "claude"
            reason = "Task requires context, vibe, or philosophical understanding."
            model_version = "claude-3-5-sonnet-20241022"
            
        else:
            # Gemini selected, now decide Pro vs Flash
            is_complex = any(k in task_intent.lower() for k in [
                "analyze", "reason", "deep", "complex", "architecture", 
                "분석", "추론", "복잡", "설계", "구조"
            ])
            
            if is_complex or len(task_intent) > 200:
                selected = "gemini_pro"
                reason = "Task requires complex reasoning or deep analysis."
<<<<<<< HEAD
                model_version = "gemini-2.5-pro"  # Prefer latest stable Pro
            else:
                selected = "gemini_flash"
                reason = "Task requires fast execution or simple code."
                model_version = "gemini-2.5-flash"
=======
                model_version = "gemini-1.5-pro-002" # Or 3.0 Pro if available
            else:
                selected = "gemini_flash"
                reason = "Task requires fast execution or simple code."
                model_version = "gemini-2.0-flash-exp"
>>>>>>> origin/main

        return {
            "model": selected,
            "version": model_version,
            "reason": reason,
            "scores": scores,
            "role": "Context Bridge" if selected == "claude" else ("Reasoning Engine" if selected == "gemini_pro" else "Execution Engine")
        }

    def get_execution_model(self):
        """Returns the configured Gemini model for execution tasks."""
        try:
            import google.generativeai as genai
            import os
            from dotenv import load_dotenv
<<<<<<< HEAD
            from pathlib import Path
            
            root = Path(__file__).resolve().parents[1]
            cred = root / ".env_credentials"
            if cred.exists():
                load_dotenv(dotenv_path=cred, override=False)
            load_dotenv(dotenv_path=root / ".env", override=False)
=======
            
            load_dotenv()
>>>>>>> origin/main
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                return None
                
            genai.configure(api_key=api_key)
<<<<<<< HEAD
            # Prefer 2.5 Flash (fallback handled by caller if needed)
            return genai.GenerativeModel("gemini-2.5-flash")
=======
            return genai.GenerativeModel('gemini-2.0-flash-exp')
>>>>>>> origin/main
        except Exception as e:
            print(f"Error initializing Gemini: {e}")
            return None

def demo_router():
    router = AIModelRouter()
    
    test_cases = [
        "이 코드가 왜 에러가 나는지 느낌적으로 설명해줘",
        "피보나치 수열을 계산하는 파이썬 함수 짜줘",
        "지금 시스템의 리듬이 좀 무거운 것 같아",
        "Analyze the memory usage of process 1234"
    ]
    
    print("🤖 AI Model Router Demo")
    print("=======================")
    
    for task in test_cases:
        result = router.select_model(task)
        print(f"\nTask: {task}")
        print(f"Selected: {result['model'].upper()} ({result['role']})")
        print(f"Reason: {result['reason']}")

if __name__ == "__main__":
    demo_router()
