#!/usr/bin/env python3
"""
Simulate real ChatGPT conversations
5회 반복 → 자동 시스템 승격 데모
"""

from pathlib import Path
from chatgpt_vscode_bridge import *
import time

workspace = Path("c:/workspace/agi")

bridge = ConversationBridge(workspace)
translator = IntentToActionTranslator(workspace)
executor = AutoExecutionEngine(workspace)
embodiment = CircularEmbodimentEngine(workspace)

print("🌊 Simulating 5 conversations for auto-system promotion...")
print()

# 5회 반복 (같은 패턴)
conversations = [
    "YouTube 분석 시스템 만들어줘 youtube_analyzer.py",
    "Twitter 모니터링 시스템 만들어줘 twitter_monitor.py",
    "Reddit 크롤러 시스템 만들어줘 reddit_crawler.py",
    "Instagram 분석 시스템 만들어줘 instagram_analyzer.py",
    "TikTok 학습 시스템 만들어줘 tiktok_learner.py"
]

for i, user_input in enumerate(conversations, 1):
    print(f"{'=' * 60}")
    print(f"Conversation {i}/5")
    print(f"{'=' * 60}")
    print(f"User: {user_input}")
    
    # 1. Capture
    conv = bridge.capture_conversation(
        f"sim_{i:03d}",
        [{"role": "user", "content": user_input}]
    )
    
    # 2. Translate
    action = translator.translate(conv['extracted_intent'])
    print(f"Action: {action['action']}")
    
    # 3. Execute
    result = executor.execute(action)
    print(f"Result: {result['status']}")
    
    # 4. Learn
    embodiment.record_experience(action, result)
    
    print()
    time.sleep(0.5)

print("=" * 60)
print("🎉 Simulation Complete!")
print("=" * 60)
print()

# 결과 확인
import json

patterns_file = workspace / "memory/learned_patterns.json"
auto_systems_file = workspace / "memory/auto_systems.json"

if patterns_file.exists():
    with open(patterns_file, 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    
    print("📚 Learned Patterns:")
    for key, pattern in patterns.items():
        print(f"\n  {key}:")
        print(f"    Count: {pattern['count']}")
        print(f"    Success Rate: {pattern['success_rate']:.1%}")
        print(f"    Progress: {'■' * min(pattern['count'], 5)}{'□' * max(0, 5 - pattern['count'])}")

if auto_systems_file.exists():
    with open(auto_systems_file, 'r', encoding='utf-8') as f:
        auto_systems = json.load(f)
    
    if auto_systems:
        print("\n🌟 AUTO-SYSTEMS PROMOTED:")
        for key, system in auto_systems.items():
            print(f"\n  ⚡ {key}")
            print(f"    Confidence: {system['confidence']:.1%}")
            print(f"    Auto-Execute: ✅ ENABLED")
    else:
        print("\n⚠️ No auto-systems yet (need 5 successful experiences)")
else:
    print("\n⚠️ No auto-systems yet (need 5 successful experiences)")
