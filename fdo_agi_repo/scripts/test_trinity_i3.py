#!/usr/bin/env python3
"""
Trinity I3 (Integration Information) 측정 스크립트

Ello-Luon-Core 삼위일체가 만드는 시너지를 정량화합니다.
I3 < 0 이면 시너지가 있음 (전체 > 부분의 합)
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
from scipy.stats import entropy

# 프로젝트 루트 경로 추가
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT))


def load_resonance_ledger(hours: int = 24) -> List[Dict]:
    """레저에서 최근 N시간의 이벤트 로드"""
    ledger_path = REPO_ROOT / "memory" / "resonance_ledger.jsonl"
    
    if not ledger_path.exists():
        print(f"❌ 레저 없음: {ledger_path}")
        return []
    
    from datetime import timezone
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    events = []
    
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                # 타임스탬프 파싱 (ts 필드 우선, 없으면 timestamp)
                ts_str = event.get("ts") or event.get("timestamp", "")
                if ts_str:
                    # ISO 8601 파싱 (Z 제거 후 +00:00 추가)
                    ts_clean = ts_str.replace("Z", "+00:00")
                    ts = datetime.fromisoformat(ts_clean)
                    # timezone-naive라면 UTC로 가정
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if ts >= cutoff:
                        events.append(event)
            except Exception as e:
                # 타임스탬프 파싱 실패 시 조용히 스킵 (너무 많은 경고 방지)
                continue
    
    print(f"✓ 레저 로드: {len(events)}개 이벤트 (최근 {hours}시간)")
    return events


def extract_signals(events: List[Dict], personas: List[str]) -> Dict[str, np.ndarray]:
    """각 페르소나의 신호 추출 - 레저 필드 구조 반영"""
    signals = {}
    
    for persona in personas:
        # 해당 페르소나의 이벤트만 필터링
        persona_events = [e for e in events if e.get("persona_id") == persona]
        
        if not persona_events:
            print(f"  ⚠️  {persona}: 이벤트 없음")
            continue
        
        # 시간순 정렬
        persona_events.sort(key=lambda x: x.get("timestamp", ""))
        
        # 신호 추출 (다양한 필드 활용)
        scores = []
        for event in persona_events:
            score = None
            
            # 1. resonance_score 직접 확인
            if "resonance_score" in event:
                score = event["resonance_score"]
            
            # 2. outcome 내부 확인
            elif "outcome" in event and isinstance(event["outcome"], dict):
                outcome = event["outcome"]
                score = (
                    outcome.get("resonance_score") or
                    outcome.get("quality") or
                    outcome.get("score")
                )
            
            # 3. decision 내부 확인
            elif "decision" in event and isinstance(event["decision"], dict):
                decision = event["decision"]
                score = decision.get("confidence")
            
            # 4. metadata 내부 확인
            elif "metadata" in event and isinstance(event["metadata"], dict):
                metadata = event["metadata"]
                score = (
                    metadata.get("quality_score") or
                    metadata.get("confidence") or
                    metadata.get("score")
                )
            
            # 5. action이 있으면 성공으로 간주 (0.7)
            elif "action" in event:
                score = 0.7
            
            # 6. 기본값
            if score is None:
                score = 0.5
            
            scores.append(float(score))
        
        if scores:
            signals[persona] = np.array(scores)
            print(f"  ✓ {persona}: {len(scores)}개 신호 추출 (평균: {np.mean(scores):.3f})")
        else:
            print(f"  ⚠️  {persona}: 점수 추출 실패")
    
    return signals


def calculate_entropy(signal: np.ndarray, bins: int = 10) -> float:
    """신호의 엔트로피 계산 (정보량)"""
    hist, _ = np.histogram(signal, bins=bins, density=True)
    hist = hist + 1e-10  # 0 방지
    return entropy(hist, base=2)


def calculate_mutual_information(X: np.ndarray, Y: np.ndarray, bins: int = 10) -> float:
    """두 신호 간 상호정보량 I(X;Y) 계산"""
    # 2D 히스토그램
    hist_2d, _, _ = np.histogram2d(X, Y, bins=bins, density=True)
    hist_2d = hist_2d + 1e-10
    
    # 1D 히스토그램
    hist_x, _ = np.histogram(X, bins=bins, density=True)
    hist_y, _ = np.histogram(Y, bins=bins, density=True)
    hist_x = hist_x + 1e-10
    hist_y = hist_y + 1e-10
    
    # I(X;Y) = H(X) + H(Y) - H(X,Y)
    H_X = entropy(hist_x, base=2)
    H_Y = entropy(hist_y, base=2)
    H_XY = entropy(hist_2d.flatten(), base=2)
    
    return H_X + H_Y - H_XY


def calculate_i3(signals: Dict[str, np.ndarray]) -> Tuple[float, Dict]:
    """
    Integration Information I3 계산
    
    I3 = I(X1; X2; X3) = I(X1; X2) + I(X1; X3) - I(X1; X2, X3)
    
    I3 < 0: 시너지 (전체 정보 > 부분의 합)
    I3 > 0: 중복 (부분의 합 > 전체 정보)
    I3 = 0: 독립
    """
    personas = list(signals.keys())
    if len(personas) < 3:
        print(f"❌ 최소 3개 페르소나 필요 (현재: {len(personas)})")
        return 0.0, {}
    
    # 신호 길이 맞추기 (가장 짧은 것에 맞춤)
    min_len = min(len(s) for s in signals.values())
    X1 = signals[personas[0]][:min_len]
    X2 = signals[personas[1]][:min_len]
    X3 = signals[personas[2]][:min_len]
    
    print(f"\n📊 I3 계산 중...")
    print(f"  신호 길이: {min_len}")
    print(f"  페르소나: {personas[0]}, {personas[1]}, {personas[2]}")
    
    # 상호정보량 계산
    I_12 = calculate_mutual_information(X1, X2)
    I_13 = calculate_mutual_information(X1, X3)
    I_23 = calculate_mutual_information(X2, X3)
    
    # 3변수 상호정보량 근사 (간소화)
    # I(X1; X2, X3) ≈ I(X1; X2) + I(X1; X3) - I(X2; X3)
    I_123 = I_12 + I_13 - I_23
    
    # I3 = 쌍별 합 - 3변수 정보
    I3 = (I_12 + I_13 + I_23) - I_123
    
    details = {
        "I_12": I_12,
        "I_13": I_13,
        "I_23": I_23,
        "I_123": I_123,
        "I3": I3,
        "personas": personas[:3],
        "signal_length": min_len
    }
    
    return I3, details


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Trinity I3 측정")
    parser.add_argument("--hours", type=int, default=24, help="분석 기간 (시간)")
    parser.add_argument("--personas", nargs="+", default=["lua", "elo", "Core", "thesis", "antithesis", "synthesis"],
                      help="분석할 페르소나들")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔺 Trinity I3 (Integration Information) 측정")
    print("=" * 60)
    
    # 1. 레저 로드
    events = load_resonance_ledger(hours=args.hours)
    if not events:
        print("❌ 분석할 이벤트 없음")
        return 1
    
    # 페르소나 분포 확인
    persona_counts = {}
    for e in events:
        p = e.get("persona_id")
        if p:
            persona_counts[p] = persona_counts.get(p, 0) + 1
    
    print(f"\n📋 페르소나 분포:")
    for p, count in sorted(persona_counts.items(), key=lambda x: -x[1]):
        print(f"  {p}: {count}개")
    
    # 2. 신호 추출
    print(f"\n🎵 신호 추출 중...")
    signals = extract_signals(events, args.personas)
    
    if len(signals) < 3:
        print(f"❌ 최소 3개 페르소나 필요 (현재: {len(signals)})")
        return 1
    
    # 3. I3 계산
    I3, details = calculate_i3(signals)
    
    # 4. 결과 출력
    print("\n" + "=" * 60)
    print("📊 Trinity I3 결과")
    print("=" * 60)
    print(f"  I3 = {I3:.4f} bits")
    print(f"  페르소나: {', '.join(details['personas'])}")
    print(f"  신호 길이: {details['signal_length']}")
    print()
    print(f"  I(X1;X2) = {details['I_12']:.4f}")
    print(f"  I(X1;X3) = {details['I_13']:.4f}")
    print(f"  I(X2;X3) = {details['I_23']:.4f}")
    print(f"  I(X1;X2,X3) = {details['I_123']:.4f}")
    print()
    
    # 해석
    if I3 < -0.01:
        print("✨ 시너지 발견! (I3 < 0)")
        print("   전체 > 부분의 합 → Trinity가 창발적 지능을 만듭니다")
    elif I3 > 0.01:
        print("⚠️  정보 중복 (I3 > 0)")
        print("   부분의 합 > 전체 → 페르소나들이 독립적으로 작동합니다")
    else:
        print("➖ 중립 (I3 ≈ 0)")
        print("   독립적 작동 중")
    
    print("=" * 60)
    
    # 5. 결과 저장
    output_path = REPO_ROOT / "outputs" / "trinity_i3_latest.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "I3": I3,
            "details": details,
            "interpretation": "synergy" if I3 < -0.01 else "redundancy" if I3 > 0.01 else "neutral"
        }, f, indent=2)
    
    print(f"\n✓ 결과 저장: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
