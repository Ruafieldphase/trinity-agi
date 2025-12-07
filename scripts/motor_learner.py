
import cv2
import easyocr
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

class MotorLearner:
    def __init__(self):
        print("👁️ Initializing Motor Learner (Vision + OCR)...")
        # Initialize EasyOCR for English (keys are usually English)
        self.reader = easyocr.Reader(['en'], gpu=False) 
        print("✅ Motor Learner Ready.")

    def learn_from_video(self, video_path: str, task_name: str) -> Dict[str, Any]:
        """
        Analyzes a video file to extract motor patterns (keys + screen state).
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        print(f"🎬 Analyzing video: {video_path.name}...")
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        print(f"   Duration: {duration:.2f}s, FPS: {fps}")

        actions = []
        last_text = ""
        
        # Process 1 frame every 0.5 seconds
        step = int(fps * 0.5)
        
        for i in range(0, frame_count, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                break
                
            # OCR to find keys (Carnac usually displays keys clearly)
            # Optimization: Crop to bottom area where keys usually appear?
            # For now, scan whole frame (slow but safe)
            results = self.reader.readtext(frame, detail=0)
            
            # Filter for likely key combos (e.g., "Ctrl", "Alt", single chars)
            current_keys = self._filter_keys(results)
            
            if current_keys and current_keys != last_text:
                timestamp = i / fps
                print(f"   [{timestamp:.1f}s] Detected Action: {current_keys}")
                
                actions.append({
                    "timestamp": timestamp,
                    "action_type": "keypress",
                    "keys": current_keys,
                    "context": f"Frame {i}" # In future, add visual context embedding
                })
                last_text = current_keys
                
        cap.release()
        
        # Save to Memory
        memory_entry = self._save_motor_memory(task_name, actions, duration)
        return memory_entry

    def _filter_keys(self, text_list: List[str]) -> str:
        """
        Heuristic to identify key overlays from random text.
        Carnac usually shows: "Ctrl + C", "Enter", "Alt + Tab"
        """
        # Simple heuristic: look for modifiers or short strings
        modifiers = ["Ctrl", "Alt", "Shift", "Win", "Enter", "Esc", "Tab"]
        
        for text in text_list:
            # If text contains a modifier
            if any(mod in text for mod in modifiers):
                return text
            # If text is very short and uppercase (e.g., "A", "S") - might be noise though
            if len(text) < 3 and text.isupper():
                return text
                
        return ""

    def _save_motor_memory(self, task_name: str, actions: List[Dict], duration: float) -> Dict:
        """Save the learned pattern to Resonance Ledger."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "motor_memory",
            "summary": f"Motor Pattern: {task_name}",
            "narrative": f"Learned execution pattern for '{task_name}' from video observation.",
            "vector": None, # TODO: Add semantic embedding
            "metadata": {
                "duration": duration,
                "action_count": len(actions),
                "actions": actions
            }
        }
        
        try:
            with open(LEDGER_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            print(f"💾 Saved Motor Memory to {LEDGER_FILE}")
        except Exception as e:
            print(f"❌ Failed to save memory: {e}")
            
        return entry

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python motor_learner.py <video_path> <task_name>")
        sys.exit(1)
        
    learner = MotorLearner()
    learner.learn_from_video(sys.argv[1], sys.argv[2])
