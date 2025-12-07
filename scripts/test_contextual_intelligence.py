
import sys
from pathlib import Path
import json

# Add repo root to path
sys.path.append("/home/bino/agi")

from fdo_agi_repo.orchestrator.binoche_integration import BinocheDecisionEngine
from scripts.rhythm_think import step2_unconscious_search

def test_binoche_contextual_intelligence():
    print("\n🧠 Testing Binoche Contextual Intelligence...")
    engine = BinocheDecisionEngine()
    
    # Task that should trigger "Connection" thinking (Axiom 7)
    task_goal = "뇌과학과 철학의 연결고리를 찾는 연구를 시작하고 싶어"
    
    print(f"   Task: {task_goal}")
    decision = engine.review_task(task_goal, quality=0.9)
    
    print(f"   Decision: {decision.action}")
    print(f"   Reasoning: {decision.reasoning}")
    
    if "박문호" in decision.reasoning or "연결" in decision.reasoning or "맥락" in decision.reasoning:
        print("   ✅ Binoche successfully applied Contextual Intelligence!")
    else:
        print("   ⚠️ Binoche reasoning might be generic.")

def test_rhythm_think_resonance():
    print("\n🎵 Testing Rhythm Think Resonance...")
    
    # Simulate a state that might resonate with "Expansion" or "Learning"
    current_state = {
        'phase': 'EXPANSION',
        'strategy': 'learning',
        'fear_level': 0.1
    }
    
    patterns = step2_unconscious_search(current_state)
    
    print(f"   Found {len(patterns)} patterns.")
    for p in patterns:
        print(f"   - [{p['type']}] {p['summary']} (Score: {p['resonance']:.3f})")
        
    # Check if any YouTube memory is found
    yt_found = any(p['type'] == 'youtube_memory' for p in patterns)
    if yt_found:
        print("   ✅ Rhythm Think found YouTube resonance!")
    else:
        print("   ⚠️ No YouTube resonance found (might need more specific query or lower threshold).")

if __name__ == "__main__":
    print("============================================================")
    print("🧪 Contextual Intelligence Integration Test")
    print("============================================================")
    
    try:
        test_binoche_contextual_intelligence()
    except Exception as e:
        print(f"❌ Binoche Test Failed: {e}")
        
    try:
        test_rhythm_think_resonance()
    except Exception as e:
        print(f"❌ Rhythm Think Test Failed: {e}")
