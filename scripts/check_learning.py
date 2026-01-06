#!/usr/bin/env python3
"""Check learning progress"""

import json
from pathlib import Path
from datetime import datetime

workspace = Path("c:/workspace/agi")

# 학습 패턴 확인
patterns_file = workspace / "memory/learned_patterns.json"
auto_systems_file = workspace / "memory/auto_systems.json"
experience_log_file = workspace / "memory/experience_log.jsonl"

print("=" * 60)
print("📚 Learning Progress Report")
print("=" * 60)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# 경험 로그
if experience_log_file.exists():
    with open(experience_log_file, 'r', encoding='utf-8') as f:
        experiences = [json.loads(line) for line in f]
    
    total = len(experiences)
    success = sum(1 for e in experiences if e.get('success'))
    
    print(f"📊 Experiences: {total} total, {success} successful ({success/total*100:.1f}%)")
else:
    print("⚠️ No experiences yet")

print()

# 학습된 패턴
if patterns_file.exists():
    with open(patterns_file, 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    
    print(f"🧠 Learned Patterns: {len(patterns)}")
    
    for key, pattern in sorted(patterns.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"\n  📌 {key}")
        print(f"     Count: {pattern['count']}")
        print(f"     Success Rate: {pattern['success_rate']:.1%}")
        print(f"     Progress: {'■' * pattern['count']}{'□' * (5 - pattern['count'])} ({pattern['count']}/5)")
        
        if pattern['count'] >= 5 and pattern['success_rate'] > 0.8:
            print(f"     Status: ✅ READY FOR AUTO-SYSTEM")
else:
    print("⚠️ No patterns learned yet")

print()

# 자동 시스템
if auto_systems_file.exists():
    with open(auto_systems_file, 'r', encoding='utf-8') as f:
        auto_systems = json.load(f)
    
    print(f"🌟 Auto-Systems: {len(auto_systems)}")
    
    for key, system in auto_systems.items():
        print(f"\n  ⚡ {key}")
        print(f"     Confidence: {system['confidence']:.1%}")
        print(f"     Learned from: {system['learned_from_experiences']} experiences")
        print(f"     Promoted: {system['promoted_at']}")
        print(f"     Status: ✅ FULLY AUTOMATED")
else:
    print("⚠️ No auto-systems yet")

print()
print("=" * 60)
