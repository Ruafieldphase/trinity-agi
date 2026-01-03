"""
Gemini CLI Bridge (Shion) - Alternative Fallback Agent
Uses Google's Gemini API when OpenAI is unavailable or rate-limited
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    import google.generativeai as genai
    import pyperclip
except ImportError:
    print("❌ Missing dependencies. Install: pip install google-generativeai pyperclip")
    sys.exit(1)

class GeminiCLIBridge:
    def __init__(self, api_key=None):
        self.api_key = api_key or Path("c:/workspace/agi/.env").read_text().split("GEMINI_API_KEY=")[1].strip()
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.log_file = Path("c:/workspace/agi/outputs/shion_recovery_log.jsonl")
        
    def recover_from_error(self, context: str, mode: str = "error-recovery"):
        """
        Processes error context and provides recovery suggestions via Gemini
        """
        print("🔄 Shion (Gemini CLI) activated for error recovery...")
        
        prompt = f"""
You are Shion, a Gemini-powered fallback debugging agent.

**Error Context:**
{context[:2000]}

**Task:**
Analyze this VS Code Copilot API error and provide:
1. Root cause diagnosis
2. Step-by-step recovery actions
3. Prevention strategies

Be concise but actionable.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = response.text
            
            print("\n✅ Shion Recovery Suggestion:\n")
            print(result)
            
            # Log result
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "mode": mode,
                "context_length": len(context),
                "suggestion": result[:200]
            }
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            return result
            
        except Exception as e:
            print(f"❌ Shion failed: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Gemini CLI Bridge (Shion)")
    parser.add_argument("--mode", default="error-recovery", help="Operation mode")
    parser.add_argument("--context", default="clipboard", help="Source of error context")
    args = parser.parse_args()
    
    bridge = GeminiCLIBridge()
    
    if args.context == "clipboard":
        try:
            context = pyperclip.paste()
        except Exception:
            print("⚠️ Clipboard access failed. Using fallback.")
            context = "No context available"
    else:
        context = args.context
    
    bridge.recover_from_error(context, mode=args.mode)

if __name__ == "__main__":
    main()
