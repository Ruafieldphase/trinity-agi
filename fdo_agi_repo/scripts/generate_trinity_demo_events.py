#!/usr/bin/env python3
"""
Trinity 데모 이벤트 생성기

lua(정), elo(반), Core(합) 페르소나의 샘플 이벤트를 레저에 기록합니다.
I3 계산을 위한 시연용 데이터입니다.
"""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO_ROOT / "memory" / "resonance_ledger.jsonl"


def generate_trinity_events(count: int = 30, hours_back: int = 24):
    """Trinity 이벤트 생성"""
    
    personas = ["lua", "elo", "Core"]
    events = []
    
    # 시간 범위
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours_back)
    
    for i in range(count):
        # 시간 분산
        event_time = start_time + timedelta(
            seconds=random.uniform(0, hours_back * 3600)
        )
        
        # 페르소나 선택 (균등 분포)
        persona = personas[i % len(personas)]
        
        # 페르소나별 특성
        if persona == "lua":
            # 정(Thesis): 완전히 낮은 구간 (0.1~0.3)
            base_score = 0.2
            variance = 0.05
            event_type = "thesis_generation"
        elif persona == "Core":
            # 합(Synthesis): 중간, 조화로움 (0.4~0.6)
            base_score = 0.5
            variance = 0.05
            event_type = "synthesis_integration"
        else:  # elo
            # 반(Antithesis): 완전히 높은 구간 (0.7~0.9)
            base_score = 0.8
            variance = 0.05
            event_type = "antithesis_challenge"
        
        # 점수 생성 (각 페르소나별로 구간 제한)
        if persona == "lua":
            score = max(0.1, min(0.3, random.gauss(base_score, variance)))
        elif persona == "Core":
            score = max(0.4, min(0.6, random.gauss(base_score, variance)))
        else:
            score = max(0.7, min(0.9, random.gauss(base_score, variance)))
        
        # 이벤트 구조
        event = {
            "ts": event_time.isoformat(),
            "timestamp": event_time.isoformat(),
            "event": event_type,
            "persona_id": persona,
            "resonance_score": round(score, 3),
            "outcome": {
                "quality": round(score, 3),
                "confidence": round(random.uniform(0.6, 0.95), 3),
            },
            "metadata": {
                "source": "trinity_demo",
                "iteration": i + 1,
            }
        }
        
        events.append(event)
    
    # 시간순 정렬
    events.sort(key=lambda x: x["ts"])
    
    # 레저에 추가
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    print(f"✓ {len(events)}개 Trinity 이벤트 생성 완료")
    print(f"  - lua:   {sum(1 for e in events if e['persona_id'] == 'lua')}개")
    print(f"  - elo:   {sum(1 for e in events if e['persona_id'] == 'elo')}개")
    print(f"  - Core: {sum(1 for e in events if e['persona_id'] == 'Core')}개")
    print(f"  - 시간 범위: {hours_back}시간")
    print(f"  - 저장 경로: {LEDGER_PATH}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Trinity 데모 이벤트 생성")
    parser.add_argument("--count", type=int, default=30, help="생성할 이벤트 수")
    parser.add_argument("--hours", type=int, default=24, help="시간 범위 (시간)")
    
    args = parser.parse_args()
    
    generate_trinity_events(count=args.count, hours_back=args.hours)
