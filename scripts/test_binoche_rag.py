#!/usr/bin/env python3
"""
Test Binoche_Observer Integration with Resonance RAG
"""
import sys
from pathlib import Path
from workspace_root import get_workspace_root

# Add repo root to path
sys.path.append(str(get_workspace_root()))

from fdo_agi_repo.orchestrator.binoche_integration import BinocheDecisionEngine

def test_integration():
    print("Initializing Engine...")
    engine = BinocheDecisionEngine()
    
    test_cases = [
        "배경자아의 역할에 대해 설명해줘",
        "What is Resonance?",
        "리듬의 공리",
        "단순한 버그 수정"
    ]
    
    print("\n=== Testing Resonance Detection ===\n")
    
    for task in test_cases:
        print(f"Task: '{task}'")
        decision = engine.review_task(
            task_goal=task,
            quality=0.8,
            confidence=0.8
        )
        
        if decision.rule_applied == "OriginResonance":
            print(f"✅ RESONANCE DETECTED!")
            print(f"   Reasoning: {decision.reasoning}")
        else:
            print(f"   Result: {decision.action} (Rule: {decision.rule_applied})")
        print("-" * 50)

if __name__ == "__main__":
    test_integration()
