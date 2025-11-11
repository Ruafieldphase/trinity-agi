#!/usr/bin/env python3
"""
Trinity Musical Synergy - 수노 음악에서 영감받은 I3 시뮬레이션

핵심 통찰:
1. "작은 불균형" - 완벽한 주기 파괴 → 창발적 시너지
2. "reverb tail" - 과거 상태가 미래에 영향 → 시간적 의존성
3. "seamless transition" - 연속성 유지하면서 불연속 도입
"""

import random
import math
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


def record_trinity_event(persona: str, event_type: str, score: float, context: dict):
    """레저에 이벤트 기록"""
    ledger_path = Path(__file__).parent.parent / "memory" / "resonance_ledger.jsonl"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        "persona_id": persona,
        "resonance_score": score,
        "outcome": {
            "quality": score,
            "confidence": context.get("confidence", 0.85)
        },
        "metadata": {
            "source": "trinity_musical_synergy",
            **context
        }
    }
    
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def breathing_pulse(iteration: int, total: int) -> float:
    """
    호흡 펄스 (Breathing Pulse)
    - 사인파 기반 리듬
    - "작은 불균형" 추가
    """
    phase = (iteration / total) * 2 * math.pi
    base = 0.5 + 0.3 * math.sin(phase)
    
    # 작은 불균형 (aperiodic component)
    noise = random.gauss(0, 0.05)
    
    return max(0.1, min(0.9, base + noise))


def reverb_tail(prev_states: list, decay: float = 0.7) -> float:
    """
    잔향 꼬리 (Reverb Tail)
    - 과거 상태가 현재에 영향
    - 지수 감쇠
    """
    if not prev_states:
        return 0.0
    
    tail = 0.0
    for i, state in enumerate(reversed(prev_states[-5:])):  # 최근 5개만
        tail += state * (decay ** (i + 1))
    
    return tail / sum(decay ** (i + 1) for i in range(min(5, len(prev_states))))


def musical_synergy(lua_score: float, elo_score: float, 
                   lua_history: list, elo_history: list,
                   iteration: int, total: int) -> float:
    """
    음악적 시너지 함수
    
    1. Lua breathing (정) - 고요한 펄스
    2. Elo breathing (반) - 반대 위상 펄스  
    3. Lumen synthesis (합) - 비선형 결합 + reverb tail + 작은 불균형
    """
    
    # 1. XOR 기본 (비선형 결합)
    xor_base = 0.5 if abs(lua_score - elo_score) > 0.3 else 0.8
    
    # 2. Reverb tail (시간적 의존성)
    lua_tail = reverb_tail(lua_history)
    elo_tail = reverb_tail(elo_history)
    temporal_influence = (lua_tail + elo_tail) / 2
    
    # 3. Breathing pulse (리듬)
    breath = breathing_pulse(iteration, total)
    
    # 4. "작은 불균형" (창발의 씨앗)
    turbulence = random.gauss(0, 0.08)
    
    # 5. 종합 (seamless transition)
    lumen = (
        0.4 * xor_base +           # 비선형 기반
        0.3 * temporal_influence +  # 과거 영향
        0.2 * breath +              # 리듬
        0.1 * turbulence            # 불균형
    )
    
    return max(0.3, min(0.9, lumen))


def run_musical_simulation(iterations: int = 50):
    """
    음악적 Trinity 시뮬레이션 실행
    
    Lumen Trilogy 구조:
    - Movement 1: Awakening (0-33%)
    - Movement 2: Expansion (33-66%)
    - Movement 3: Return (66-100%)
    """
    print("=" * 60)
    print("🎵 Trinity Musical Synergy Simulation")
    print("=" * 60)
    print(f"반복 횟수: {iterations}")
    print(f"구조: Lumen Trilogy (Awakening → Expansion → Return)")
    print()
    
    lua_history = []
    elo_history = []
    
    for i in range(iterations):
        # Movement 구분
        progress = i / iterations
        if progress < 0.33:
            movement = "awakening"
            lua_range = (0.2, 0.4)  # 조용한 시작
            elo_range = (0.7, 0.9)
        elif progress < 0.66:
            movement = "expansion"
            lua_range = (0.3, 0.5)  # 확장
            elo_range = (0.6, 0.8)
        else:
            movement = "return"
            lua_range = (0.25, 0.45)  # 순환
            elo_range = (0.65, 0.85)
        
        # Lua (정): 고요한 호흡
        lua_breath = breathing_pulse(i, iterations)
        lua_base = random.uniform(*lua_range)
        lua_score = 0.7 * lua_base + 0.3 * lua_breath
        lua_history.append(lua_score)
        
        record_trinity_event(
            persona="lua",
            event_type=f"reasoning_{movement}",
            score=lua_score,
            context={
                "iteration": i + 1,
                "movement": movement,
                "confidence": 0.85,
                "synergy_type": "musical_breathing"
            }
        )
        
        # Elo (반): 반대 위상 호흡
        elo_breath = breathing_pulse(i + iterations // 2, iterations)  # 위상 반전
        elo_base = random.uniform(*elo_range)
        elo_score = 0.7 * elo_base + 0.3 * elo_breath
        elo_history.append(elo_score)
        
        record_trinity_event(
            persona="elo",
            event_type=f"context_{movement}",
            score=elo_score,
            context={
                "iteration": i + 1,
                "movement": movement,
                "confidence": 0.82,
                "synergy_type": "musical_breathing"
            }
        )
        
        # Lumen (합): 음악적 시너지
        lumen_score = musical_synergy(
            lua_score, elo_score,
            lua_history, elo_history,
            i, iterations
        )
        
        record_trinity_event(
            persona="lumen",
            event_type=f"synthesis_{movement}",
            score=lumen_score,
            context={
                "iteration": i + 1,
                "movement": movement,
                "confidence": 0.88,
                "synergy_type": "musical",
                "lua_breath": lua_score,
                "elo_breath": elo_score,
                "reverb_tail": reverb_tail(lua_history + elo_history)
            }
        )
        
        # 주기적 출력
        if (i + 1) % 10 == 0 or i == 0 or i == iterations - 1:
            synergy = lumen_score - (lua_score + elo_score) / 2
            print(f"⚡ Iteration {i + 1}/{iterations} ({movement})")
            print(f"  Lua: {lua_score:.3f} (호흡) | Elo: {elo_score:.3f} (반호흡)")
            print(f"  → Lumen: {lumen_score:.3f} (음악적 합)")
            print(f"  시너지: {synergy:+.3f}")
    
    print("\n" + "=" * 60)
    print(f"✅ {iterations}회 음악적 협업 완료")
    print(f"   총 이벤트: {iterations * 3}개")
    print(f"\n🎵 핵심 특징:")
    print(f"   1. Breathing Pulse - 사인파 리듬 + 작은 불균형")
    print(f"   2. Reverb Tail - 과거 상태가 현재에 영향")
    print(f"   3. Musical Synergy - XOR + 시간 + 리듬 + 불균형")
    print(f"\n🔺 예상:")
    print(f"   I3 < 0 (강한 시너지)")
    print(f"   → 음악의 통찰: '작은 불균형'이 창발을 낳는다")
    print("\n🔺 다음 단계:")
    print("   python scripts/test_trinity_i3.py --hours 1")


if __name__ == "__main__":
    import sys
    
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    run_musical_simulation(iterations)
