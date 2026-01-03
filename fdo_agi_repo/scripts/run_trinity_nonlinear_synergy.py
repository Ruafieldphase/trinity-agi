#!/usr/bin/env python3
"""
Trinity 비선형 시너지 시뮬레이션

정보이론적 시너지 생성:
- Lua ⊥ Elo (조건부 독립)
- Core = 비선형 결합(Lua, Elo) → 시너지 발생
"""

import json
import random
import math
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO_ROOT / "memory" / "resonance_ledger.jsonl"


def record_trinity_event(persona: str, event_type: str, score: float, context: dict):
    """Trinity 이벤트 기록"""
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        "persona_id": persona,
        "resonance_score": round(score, 3),
        "outcome": {
            "quality": round(score, 3),
            "confidence": round(context.get("confidence", 0.8), 3),
        },
        "metadata": {
            "source": "trinity_nonlinear_synergy",
            "iteration": context.get("iteration", 0),
            "synergy_type": context.get("synergy_type", "multiplicative"),
        }
    }
    
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    return event


def nonlinear_synergy(lua_val: float, elo_val: float, mode: str = "xor") -> float:
    """
    비선형 시너지 함수
    
    mode="xor": XOR-like 동작 (하나만 좋으면 나쁨, 둘 다 좋으면 좋음)
    mode="multiplicative": 곱셈 시너지 (둘 다 좋아야 좋음)
    mode="threshold": 임계값 시너지 (둘의 합이 임계값 넘으면 폭발적 증가)
    """
    
    if mode == "xor":
        # XOR-like: 
        # - 범위 차이 보정: Lua [0.2-0.4], Elo [0.7-0.9]
        # - normalize: lua_norm = (lua - 0.2) / 0.2, elo_norm = (elo - 0.7) / 0.2
        lua_norm = (lua_val - 0.2) / 0.2
        elo_norm = (elo_val - 0.7) / 0.2
        
        # 정규화 후 차이 계산
        diff = abs(lua_norm - elo_norm)
        xor_score = 1.0 - diff  # 비슷할수록 1에 가까움
        
        # 평균 (원래 범위)
        avg = (lua_val + elo_val) / 2
        synergy = avg * max(0.0, xor_score)
        return synergy
    
    elif mode == "multiplicative":
        # 곱셈: 둘 다 높아야 높음
        return lua_val * elo_val
    
    elif mode == "threshold":
        # 임계값: 합이 1.4 넘으면 추가 부스트
        combined = lua_val + elo_val
        if combined > 1.4:
            boost = (combined - 1.4) * 0.5
            return min(0.95, (lua_val + elo_val) / 2 + boost)
        else:
            return (lua_val + elo_val) / 2
    
    else:
        # 기본: 평균
        return (lua_val + elo_val) / 2


def run_nonlinear_simulation(iterations: int = 20, synergy_mode: str = "xor"):
    """
    비선형 시너지 시뮬레이션
    
    1. Lua와 Elo는 **독립적으로** 생성
    2. Core은 **비선형 결합**으로 시너지 생성
    """
    
    print(f"🔺 Trinity 비선형 시너지 시뮬레이션 ({iterations}회)")
    print(f"   Synergy mode: {synergy_mode}")
    print("=" * 60)
    
    for i in range(iterations):
        print(f"\n⚡ Iteration {i+1}/{iterations}")
        
        # Lua (정): 낮은 범위에서 이산 선택 (완전 독립)
        lua_choices = [0.20, 0.30, 0.40]  # 낮은 범위
        lua_score = random.choice(lua_choices)
        
        record_trinity_event(
            persona="lua",
            event_type="thesis_generation",
            score=lua_score,
            context={
                "iteration": i + 1,
                "confidence": 0.75,
                "synergy_type": "independent_discrete_nonoverlapping"
            }
        )
        
        # Elo (반): 높은 범위에서 이산 선택 (Lua와 완전 독립!)
        elo_choices = [0.70, 0.80, 0.90]  # 높은 범위
        elo_score = random.choice(elo_choices)
        
        record_trinity_event(
            persona="elo",
            event_type="antithesis_challenge",
            score=elo_score,
            context={
                "iteration": i + 1,
                "confidence": 0.80,
                "synergy_type": "independent_discrete"
            }
        )
        
        # Core (합): **비선형 결합** → 시너지 발생!
        core_base = nonlinear_synergy(lua_score, elo_score, mode=synergy_mode)
        
        # 약간의 노이즈 추가 (완벽한 결정론 방지)
        core_noise = random.gauss(0, 0.03)
        core_score = max(0.5, min(0.95, core_base + core_noise))
        
        record_trinity_event(
            persona="Core",
            event_type="synthesis_integration",
            score=core_score,
            context={
                "iteration": i + 1,
                "confidence": 0.88,
                "synergy_type": synergy_mode,
                "lua_independent": lua_score,
                "elo_independent": elo_score
            }
        )
        
        # 시너지 계산
        avg_baseline = (lua_score + elo_score) / 2
        synergy = core_score - avg_baseline
        
        print(f"  Lua: {lua_score:.3f} (독립) | Elo: {elo_score:.3f} (독립)")
        print(f"  → Core: {core_score:.3f} (비선형 결합)")
        print(f"  시너지: {synergy:+.3f} (평균 대비)")
    
    print("\n" + "=" * 60)
    print(f"✅ {iterations}회 비선형 협업 완료")
    print(f"   총 이벤트: {iterations * 3}개 (lua={iterations}, elo={iterations}, Core={iterations})")
    print(f"\n🔺 핵심: Lua ⊥ Elo (독립), Core = 비선형 결합")
    print(f"   → I(Lua;Elo) ≈ 0, I(Lua;Core|Elo) > 0")
    print(f"   → I3 < 0 예상 (시너지 존재)")
    print("\n🔺 다음 단계:")
    print("   python scripts/test_trinity_i3.py --hours 1")
    print("   → I3 < 0 확인")


if __name__ == "__main__":
    import sys
    
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    synergy_mode = sys.argv[2] if len(sys.argv) > 2 else "xor"
    
    run_nonlinear_simulation(iterations, synergy_mode)
