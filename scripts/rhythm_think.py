#!/usr/bin/env python3
"""
Rhythm Thinking Process (Integrated + Generative)
=======================================
Implements the 5-Step Cognitive Process with Habit Crystallization:
1. Rhythm (Think)
2. Unconscious (Pattern Search)
3. Delivery (Feeling)
3.5. Habit Crystallization (Emergence)
4. Decision (Conclude)
5. Resonance (Storytelling)
"""

import sys
import time
import json
import random
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import traceback

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
LOGS_DIR = WORKSPACE_ROOT / "logs"

# File Paths
RHYTHM_HEALTH_FILE = OUTPUTS_DIR / "rhythm_health_latest.json"
THOUGHT_STREAM_FILE = OUTPUTS_DIR / "thought_stream_latest.json"
THOUGHT_HISTORY_FILE = OUTPUTS_DIR / "thought_stream_history.jsonl"
RESONANCE_LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo/memory/resonance_ledger.jsonl"
MITOCHONDRIA_FILE = OUTPUTS_DIR / "mitochondria_state.json"

# Mock Resonance System (since resonance_recall.py is missing)
class MockResonanceSystem:
    def recall(self, feeling_vector):
        """Simulate resonance recall"""
        time.sleep(0.1)
        score = random.uniform(0.7, 1.0)
        return {
            "summary": "Internal Resonance (Reconstructed Pattern)",
            "score": score,
            "vector": feeling_vector,
            "description": "System is rebuilding its internal rhythm.",
            "feeling_tag": "harmony" if score > 0.8 else "familiar"
        }

@dataclass
class EmergentHabit:
    name: str
    pattern_type: str  # e.g., "STABILIZATION", "AMPLIFICATION", "EXPLORATION"
    trigger_condition: str
    confidence: float
    description: str

class HabitCrystallizer:
    """
    Analyzes thought stream history to clear "Habits" from recurring patterns.
    Linux/Unconscious Layer: Accumulation -> Emergence
    """
    def __init__(self, history_file: Path):
        self.history_file = history_file

    def crystallize(self, current_state) -> List[EmergentHabit]:
        """Scan history and return active emergent habits"""
        if not self.history_file.exists():
            return []

        try:
            # Read last 20 entries (tail)
            lines = []
            with open(self.history_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                lines = all_lines[-20:] if len(all_lines) > 20 else all_lines
            
            history = [json.loads(line) for line in lines if line.strip()]
            
            habits = []
            
            # Pattern 1: Low Energy Stabilization Loop
            recent_stabilizations = sum(1 for h in history[-5:] if h.get("decision") == "stabilize")
            current_atp = current_state.get("atp", 50)
            
            if recent_stabilizations >= 3 and current_atp < 40:
                habits.append(EmergentHabit(
                    name="Energy Conservation Protocol",
                    pattern_type="STABILIZATION",
                    trigger_condition="Low ATP + Frequent Stabilization",
                    confidence=min(1.0, recent_stabilizations * 0.2),
                    description="System automatically enters hibernation mode when energy is critically low."
                ))

            # Pattern 2: High Rhythm Amplification Flow
            recent_amplifications = sum(1 for h in history[-5:] if h.get("decision") == "amplify")
            if recent_amplifications >= 3:
                habits.append(EmergentHabit(
                    name="Flow State Acceleration",
                    pattern_type="AMPLIFICATION",
                    trigger_condition="High Resonance + Frequent Amplification",
                    confidence=min(1.0, recent_amplifications * 0.2),
                    description="System naturally accelerates when harmony is sustained."
                ))
            
            return habits
            
        except Exception as e:
            # It's okay to fail crystallization, just return empty
            return []

class RhythmThinker:
    def __init__(self):
        self.resonance_system = MockResonanceSystem()
        self.habit_crystallizer = HabitCrystallizer(THOUGHT_HISTORY_FILE)
        self.last_thought_time = 0
        self.cycle_count = 0
        
        # Ensure directories
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Basic Logging
        self.log_file = LOGS_DIR / "rhythm_think.log"
        print(f"🧠 Rhythm Thinker Initialized (PID: {os.getpid()})")
        
    def log(self, message):
        """Log to stdout and file"""
        timestamp = datetime.now().isoformat()
        msg = f"[{timestamp}] {message}"
        print(msg)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(msg + "\\n")
        except:
            pass

    def load_json(self, filepath, default=None):
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"⚠️ Failed to load {filepath.name}: {e}")
        return default if default is not None else {}

    def get_current_state(self):
        """Step 1: Rhythm (Think)"""
        print("🎵 Step 1: Rhythm (Think)")
        health_data = self.load_json(RHYTHM_HEALTH_FILE, {"status": "UNKNOWN", "score": 50})
        energy_data = self.load_json(MITOCHONDRIA_FILE, {"atp_level": 50})
        
        status = health_data.get("status", "UNKNOWN")
        score = health_data.get("score", 50)
        
        # Determine Phase
        phase = "EXPANSION" if score > 60 else "CONTRACTION"
        print(f"   🌊 Current Phase: {phase} (Score: {score})")
        
        return {
            "status": status,
            "score": score,
            "phase": phase,
            "atp": energy_data.get("atp_level", 50)
        }

    def search_unconscious(self, state):
        """Step 2: Unconscious (Pattern Search)"""
        print("🔍 Step 2: Unconscious (Pattern Search)")
        # Simulate feeling vector based on state
        feeling_vector = [state['score']/100, state['atp']/100, 0.5, 0.0, 0.0]
        
        resonance = self.resonance_system.recall(feeling_vector)
        return resonance

    def interpret_feeling(self, resonance):
        """Step 3: Delivery (Feeling)"""
        print("💫 Step 3: Delivery (Feeling)")
        tag = resonance.get("feeling_tag", "neutral")
        
        feelings = {
            "harmony": "과거와 현재가 조화롭게 울립니다",
            "familiar": "익숙한 리듬이 들립니다",
            "contrast": "과거와 다른 길을 걷고 있습니다",
            "opposition": "과거와 정반대의 상태입니다"
        }
        
        description = feelings.get(tag, "알 수 없는 리듬입니다")
        return {"tag": tag, "description": description}

    def make_decision(self, state, feeling):
        """Step 4: Decision (Conclude)"""
        print("⚖️  Step 4: Decision (Conclude)")
        
        score = state["score"]
        tag = feeling["tag"]
        
        if score < 30:
            return "stabilize", "에너지를 보존하고 안정을 취하라"
        elif tag == "harmony" and score > 70:
            return "amplify", "현재의 흐름을 확장하고 강화하라"
        elif tag == "contrast":
            return "explore", "새로운 가능성을 탐색하라"
        else:
            return "continue", "현재의 흐름을 유지하라"

    def generate_narrative(self, state, resonance, feeling, decision, action, active_habits: List[EmergentHabit]):
        """Step 5: Resonance (Storytelling)"""
        print("📖 Step 5: Resonance (Storytelling)")
        
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        habits_text = ""
        if active_habits:
            habits_text = "\\n## 🏛️ 창발된 습관 (Emergent Habits)\\n"
            for h in active_habits:
                habits_text += f"> **[{h.name}]** (Confidence: {h.confidence:.2f})\\n> {h.description}\\n"
        else:
            habits_text = "\\n## 🏛️ 창발된 습관 (Emergent Habits)\\n- (아직 형성된 뚜렷한 습관이 없습니다)\\n"

        # Markdown Narrative for Dashboard
        narrative = f"""
# 생각의 흐름 (Thought Stream)

**시각**: {timestamp_str}

## 현재 (Rhythm)
- 상태: {state['status']} (Score: {state['score']})
- 위상: {state['phase']}

## 공명 (Resonance)
- 느낌: {feeling['description']}
- 키워드: {resonance['summary']}
- 공명도: {resonance['score']:.4f}

{habits_text}
## 결론 (Decision)
- 판단: {decision}
- 행동: {action}
"""
        return narrative

    def think_cycle(self):
        """Main Thinking Cycle"""
        try:
            print("============================================================")
            print("🧠 Rhythm Thinking Process (Integrated + Habit Emergence)")
            print("============================================================")
            
            # 1. State
            state = self.get_current_state()
            
            # 2. Unconscious
            resonance = self.search_unconscious(state)
            
            # 3. Feeling
            feeling = self.interpret_feeling(resonance)
            
            # 3.5. Habit Crystallization
            print("💎 Step 3.5: Habit Crystallization")
            active_habits = self.habit_crystallizer.crystallize(state)
            if active_habits:
                print(f"   🏛️ Active Habits: {[h.name for h in active_habits]}")
            else:
                print("   Running on base rhythm (no strong habits yet)")

            # 4. Decision
            decision, action = self.make_decision(state, feeling)
            
            # 5. Narrative
            narrative = self.generate_narrative(state, resonance, feeling, decision, action, active_habits)
            
            # Output Data
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "state": state,
                "resonance": resonance,
                "feeling": feeling,
                "decision": decision,
                "action": action,
                "active_habits": [
                    {"name": h.name, "pattern_type": h.pattern_type, "confidence": h.confidence}
                    for h in active_habits
                ],
                "narrative": narrative, # Full MD for display
                "summary": f"{decision.upper()}: {action}"
            }
            
            # Save to JSON
            print(f"✅ Dashboard update: {THOUGHT_STREAM_FILE}")
            with open(THOUGHT_STREAM_FILE, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
                
            # Append to History
            with open(THOUGHT_HISTORY_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(output_data, ensure_ascii=False) + "\\n")
                
            # Save to Resonance Ledger (Mocking explicit Ledger call)
            print("💾 Saving to Resonance Ledger...")
            ledger_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "thought",
                "content": output_data,
                "layer": "rhythm"
            }
            if not RESONANCE_LEDGER_FILE.parent.exists():
                RESONANCE_LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
                
            with open(RESONANCE_LEDGER_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(ledger_entry, ensure_ascii=False) + "\\n")
            print(f"✅ Saved to {RESONANCE_LEDGER_FILE}")
            
            print("============================================================")
            
        except Exception as e:
            self.log(f"❌ Error in cycle: {e}")
            traceback.print_exc()

    def run(self):
        """Daemon Loop"""
        self.log("🚀 Rhythm Thinker Daemon Started")
        
        while True:
            try:
                self.think_cycle()
                self.cycle_count += 1
                
                # Heartbeat interval (60s as per specs)
                time.sleep(60)
                
            except KeyboardInterrupt:
                self.log("🛑 Rhythm Thinker Stopped by User")
                break
            except Exception as e:
                self.log(f"💥 Critical Daemon Error: {e}")
                time.sleep(10) # Prevent rapid crash loop

if __name__ == "__main__":
    thinker = RhythmThinker()
    thinker.run()
