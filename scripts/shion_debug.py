
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
import os
from workspace_root import get_workspace_root

# Mock genai for debug
class MockGenAI:
    def configure(self, api_key): pass
    def GenerativeModel(self, name): return self
    def generate_content(self, prompt): 
        class Resp:
            text = "Debug response from Shion"
        return Resp()

genai = MockGenAI()
API_KEY = "debug_key"

class AutonomousCollaborationMode:
    """Debug Mode"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.ledger_path = workspace_root / "memory" / "resonance_ledger.jsonl" # Fixed path
        self.core_path = workspace_root / "outputs" / "core_state.json"
        self.last_check_file = workspace_root / "outputs" / "sena" / ".last_auto_response"
        self.enabled = True
        self.max_fear_threshold = 0.7
        
    def is_safe_to_respond(self) -> bool:
        return True
    
    def get_unanswered_questions(self) -> list:
        cutoff_time = datetime.now() - timedelta(hours=24) # Expanded for debug
        
        last_check = cutoff_time # Ignore last check file for debug
        
        print(f"DEBUG: Checking ledger at {self.ledger_path}")
        print(f"DEBUG: Cutoff time: {cutoff_time}")
        
        questions = []
        
        if not self.ledger_path.exists():
            print("DEBUG: Ledger not found!")
            return questions
        
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"DEBUG: Total lines in ledger: {len(lines)}")
            
            for i, line in enumerate(lines[-10:]): # Check last 10 lines
                try:
                    entry = json.loads(line)
                    print(f"\nDEBUG: Checking entry {i}: {entry.get('timestamp')} | Source: {entry.get('source')} | Type: {entry.get('type')}")
                    
                    if entry.get('source') != 'sena_external_ai':
                        print(f"  -> Skipped: Source mismatch ({entry.get('source')})")
                        continue
                    if entry.get('type') not in ['external_question', 'diagnostic_request', 'question', 'message']:
                        print(f"  -> Skipped: Type mismatch ({entry.get('type')})")
                        continue
                    
                    timestamp = datetime.fromisoformat(entry['timestamp'])
                    if timestamp <= last_check - timedelta(minutes=5):
                        print(f"  -> Skipped: Too old ({timestamp} <= {last_check})")
                        continue
                    
                    message_text = entry.get('question', entry.get('message', ''))
                    if 'Core' in message_text.lower() or '코어' in message_text:
                        print("  -> Skipped: Contains 'Core'")
                        continue
                    
                    print("  -> MATCHED! Adding to questions.")
                    questions.append(entry)
                    
                except Exception as e:
                    print(f"  -> Error parsing line: {e}")
                    continue
        
        return questions

    def run_once(self):
        print("=" * 60)
        print("🤖 DEBUG MODE")
        print("=" * 60)
        
        questions = self.get_unanswered_questions()
        
        if not questions:
            print("📭 No new questions from Sena")
            return
        
        print(f"📬 {len(questions)} new question(s) from Sena")

def main():
    workspace_root = get_workspace_root()
    mode = AutonomousCollaborationMode(workspace_root)
    mode.run_once()

if __name__ == "__main__":
    main()
