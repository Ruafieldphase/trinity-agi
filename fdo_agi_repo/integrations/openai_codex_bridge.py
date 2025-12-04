"""
OpenAI Codex Bridge (Lubit) - Fallback CLI Agent
Activates when Copilot encounters 400 invalid_request_body errors
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    import openai
    import pyperclip
except ImportError:
    print("❌ Missing dependencies. Install: pip install openai pyperclip")
    sys.exit(1)

class OpenAICodexBridge:
    def __init__(self, api_key=None):
        self.api_key = api_key or Path("c:/workspace/agi/.env").read_text().split("OPENAI_API_KEY=")[1].strip()
        openai.api_key = self.api_key
        self.log_file = Path("c:/workspace/agi/outputs/lubit_recovery_log.jsonl")
        
    def recover_from_error(self, context: str, mode: str = "error-recovery"):
        """
        Processes error context from clipboard and provides recovery suggestions
        """
        print("🔄 Lubit (OpenAI Codex) activated for error recovery...")
        
        prompt = f"""
You are Lubit, an OpenAI Codex-powered fallback agent for VS Code Copilot errors.

**Error Context:**
{context[:2000]}  # Truncate to avoid token limits

**Task:**
1. Diagnose the likely root cause (request body size, malformed JSON, encoding issue)
2. Provide 2-3 actionable fix suggestions
3. If applicable, suggest minimal code snippet to test fix

**Output Format:**
- Diagnosis: [brief analysis]
- Fix 1: [action]
- Fix 2: [action]
- Test Snippet: [if applicable]
"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a debugging assistant specializing in API error recovery."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            print("\n✅ Lubit Recovery Suggestion:\n")
            print(result)
            
            # Log result
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "mode": mode,
                "context_length": len(context),
                "suggestion": result[:200]  # Truncated for log
            }
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            return result
            
        except Exception as e:
            print(f"❌ Lubit failed: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="OpenAI Codex Bridge (Lubit)")
    parser.add_argument("--mode", default="error-recovery", help="Operation mode")
    parser.add_argument("--context", default="clipboard", help="Source of error context")
    args = parser.parse_args()
    
    bridge = OpenAICodexBridge()
    
    if args.context == "clipboard":
        try:
            context = pyperclip.paste()
        except Exception:
            print("⚠️ Clipboard access failed. Using fallback context.")
            context = "No context available"
    else:
        context = args.context
    
    bridge.recover_from_error(context, mode=args.mode)

if __name__ == "__main__":
    main()
