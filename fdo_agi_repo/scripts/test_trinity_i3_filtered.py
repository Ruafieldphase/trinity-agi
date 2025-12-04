#!/usr/bin/env python3
"""
Trinity I3 측정 (소스 필터링 버전)

특정 소스의 이벤트만 필터링하여 I3 계산
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import argparse

import numpy as np
from scipy.stats import entropy

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO_ROOT / "memory" / "resonance_ledger.jsonl"


def load_events_by_source(source_filter: str, hours: int = 24):
    """특정 소스의 이벤트만 로드"""
    events = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    if not LEDGER_PATH.exists():
        return events
    
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                
                # timestamp 파싱
                ts_str = event.get("ts") or event.get("timestamp", "")
                if not ts_str:
                    continue
                
                # UTC 파싱
                if ts_str.endswith("Z"):
                    ts = datetime.fromisoformat(ts_str[:-1]).replace(tzinfo=timezone.utc)
                elif "+" in ts_str or ts_str.count("-") > 2:
                    ts = datetime.fromisoformat(ts_str)
                else:
                    ts = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
                
                if ts < cutoff:
                    continue
                
                # 소스 필터링
                metadata = event.get("metadata", {})
                source = metadata.get("source", "")
                if source_filter and source != source_filter:
                    continue
                
                events.append(event)
                
            except Exception as e:
                continue
    
    return events


def extract_signals_by_persona(events):
    """페르소나별 신호 추출"""
    signals = defaultdict(list)
    
    for event in events:
        persona = event.get("persona_id", "")
        if not persona:
            continue
        
        score = event.get("resonance_score")
        if score is None:
            outcome = event.get("outcome", {})
            score = outcome.get("quality")
        
        if score is not None:
            signals[persona].append(float(score))
    
    return signals


def discretize_signal(signal, bins=10):
    """신호를 이산화 (히스토그램)"""
    hist, _ = np.histogram(signal, bins=bins, range=(0, 1))
    # 0 방지
    hist = hist + 1e-10
    return hist / hist.sum()


def mutual_information(X, Y, bins=10):
    """상호정보량 I(X;Y) 계산"""
    p_x = discretize_signal(X, bins)
    p_y = discretize_signal(Y, bins)
    
    # 2D histogram for joint distribution
    hist_xy, _, _ = np.histogram2d(X, Y, bins=bins, range=[[0, 1], [0, 1]])
    hist_xy = hist_xy + 1e-10
    p_xy = hist_xy / hist_xy.sum()
    
    # I(X;Y) = H(X) + H(Y) - H(X,Y)
    h_x = entropy(p_x, base=2)
    h_y = entropy(p_y, base=2)
    h_xy = entropy(p_xy.flatten(), base=2)
    
    return h_x + h_y - h_xy


def mutual_information_3way(X, Y, Z, bins=10):
    """3변수 상호정보량 I(X;Y,Z) 계산"""
    p_x = discretize_signal(X, bins)
    
    # 3D histogram for joint distribution
    hist_xyz, _ = np.histogramdd(
        np.column_stack([X, Y, Z]),
        bins=bins,
        range=[[0, 1], [0, 1], [0, 1]]
    )
    hist_xyz = hist_xyz + 1e-10
    p_xyz = hist_xyz / hist_xyz.sum()
    
    # 2D histogram for Y, Z
    hist_yz, _, _ = np.histogram2d(Y, Z, bins=bins, range=[[0, 1], [0, 1]])
    hist_yz = hist_yz + 1e-10
    p_yz = hist_yz / hist_yz.sum()
    
    # I(X;Y,Z) = H(X) + H(Y,Z) - H(X,Y,Z)
    h_x = entropy(p_x, base=2)
    h_yz = entropy(p_yz.flatten(), base=2)
    h_xyz = entropy(p_xyz.flatten(), base=2)
    
    return h_x + h_yz - h_xyz


def compute_i3(signals, personas, bins=10):
    """Integration Information (I3) 계산"""
    if len(personas) != 3:
        raise ValueError("I3는 정확히 3개의 페르소나가 필요합니다")
    
    X1 = np.array(signals[personas[0]])
    X2 = np.array(signals[personas[1]])
    X3 = np.array(signals[personas[2]])
    
    # 길이 맞추기
    min_len = min(len(X1), len(X2), len(X3))
    X1, X2, X3 = X1[:min_len], X2[:min_len], X3[:min_len]
    
    if min_len < 3:
        raise ValueError(f"신호 길이가 너무 짧습니다: {min_len}")
    
    # I3 = I(X1;X2) + I(X1;X3) + I(X2;X3) - I(X1;X2,X3)
    i_12 = mutual_information(X1, X2, bins)
    i_13 = mutual_information(X1, X3, bins)
    i_23 = mutual_information(X2, X3, bins)
    i_1_23 = mutual_information_3way(X1, X2, X3, bins)
    
    i3 = i_12 + i_13 + i_23 - i_1_23
    
    return {
        "i3": i3,
        "i_12": i_12,
        "i_13": i_13,
        "i_23": i_23,
        "i_1_23": i_1_23,
        "signal_length": min_len,
        "personas": personas
    }


def main():
    parser = argparse.ArgumentParser(description="Trinity I3 측정 (소스 필터링)")
    parser.add_argument("--source", type=str, required=True, help="필터링할 소스명")
    parser.add_argument("--hours", type=int, default=24, help="분석 시간 범위 (시간)")
    parser.add_argument("--personas", nargs=3, default=["lua", "elo", "lumen"], help="분석할 3개 페르소나")
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"🔺 Trinity I3 측정 (소스: {args.source})")
    print("=" * 60)
    
    # 이벤트 로드
    events = load_events_by_source(args.source, args.hours)
    print(f"✓ 소스 '{args.source}' 이벤트: {len(events)}개 (최근 {args.hours}시간)")
    
    if len(events) < 3:
        print(f"❌ 이벤트가 너무 적습니다: {len(events)}개")
        return 1
    
    # 신호 추출
    signals = extract_signals_by_persona(events)
    
    print(f"\n📋 페르소나 분포:")
    for persona, sig in signals.items():
        print(f"  {persona}: {len(sig)}개")
    
    # 신호 통계
    print(f"\n🎵 신호 추출:")
    for persona in args.personas:
        if persona in signals and signals[persona]:
            avg = np.mean(signals[persona])
            print(f"  ✓ {persona}: {len(signals[persona])}개 신호 (평균: {avg:.3f})")
        else:
            print(f"  ⚠️  {persona}: 이벤트 없음")
            return 1
    
    # I3 계산
    try:
        print(f"\n📊 I3 계산 중...")
        result = compute_i3(signals, args.personas, bins=10)
        
        print(f"  신호 길이: {result['signal_length']}")
        print(f"  페르소나: {', '.join(result['personas'])}")
        
        print("\n" + "=" * 60)
        print("📊 Trinity I3 결과")
        print("=" * 60)
        print(f"  I3 = {result['i3']:.4f} bits")
        print(f"  페르소나: {', '.join(result['personas'])}")
        print(f"  신호 길이: {result['signal_length']}")
        print()
        print(f"  I(X1;X2) = {result['i_12']:.4f}")
        print(f"  I(X1;X3) = {result['i_13']:.4f}")
        print(f"  I(X2;X3) = {result['i_23']:.4f}")
        print(f"  I(X1;X2,X3) = {result['i_1_23']:.4f}")
        print()
        
        if result['i3'] < 0:
            print("✅ 정보 시너지 (I3 < 0)")
            print("   전체 > 부분의 합 → Trinity 협업이 추가 정보를 생성합니다")
        else:
            print("⚠️  정보 중복 (I3 > 0)")
            print("   부분의 합 > 전체 → 페르소나들이 독립적으로 작동합니다")
        
        print("=" * 60)
        
        # 결과 저장
        output_path = REPO_ROOT / "outputs" / f"trinity_i3_{args.source}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                **result,
                "source": args.source,
                "hours": args.hours,
                "event_count": len(events),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 결과 저장: {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"❌ I3 계산 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
