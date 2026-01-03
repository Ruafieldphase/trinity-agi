#!/usr/bin/env python3
"""
Contextualized I3 (Conditional Interaction Information) Calculator
Core의 시선: Context로 조건화된 상호정보 계산

목표: I(Elo; Core | Context) ≈ 0 (독립성 달성)
"""

import json
import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from workspace_root import get_workspace_root

WORKSPACE = get_workspace_root()
CONTEXT_PATH = WORKSPACE / "outputs" / "context_samples.jsonl"
OUTPUT_PATH = WORKSPACE / "outputs" / "ci3_optimization_report.json"


def load_contexts(window_hours: int = 24) -> List[Dict]:
    """최근 N시간 내 Context 로드"""
    cutoff = datetime.now() - timedelta(hours=window_hours)
    contexts = []
    
    with open(CONTEXT_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            ctx = json.loads(line)
            try:
                when = datetime.fromisoformat(ctx['when'])
                if when >= cutoff:
                    contexts.append(ctx)
            except:
                pass
    
    return contexts


def extract_signals(contexts: List[Dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Context에서 Lua, Elo, Core 신호 추출
    
    - Lua (에너지): duration_sec, event 빈도
    - Elo (품질): quality, confidence
    - Core (관찰): health_check 빈도, latency
    """
    n = len(contexts)
    lua_signal = np.zeros(n)
    elo_signal = np.zeros(n)
    core_signal = np.zeros(n)
    
    for i, ctx in enumerate(contexts):
        meta = ctx.get('meta', {})
        event = ctx.get('event', '')
        
        # Lua: 에너지/실행 시간
        if 'duration_sec' in meta:
            lua_signal[i] = meta['duration_sec']
        elif event in ['thesis_start', 'synthesis_start', 'antithesis_start']:
            lua_signal[i] = 1.0  # 작업 시작
        
        # Elo: 품질/신뢰도
        if 'quality' in meta:
            elo_signal[i] = meta['quality']
        elif 'confidence' in meta:
            elo_signal[i] = meta['confidence']
        elif meta.get('ok', False):
            elo_signal[i] = 1.0
        elif 'error_present' in meta:
            elo_signal[i] = 0.0
        
        # Core: 관찰/모니터링 빈도
        if event == 'health_check':
            core_signal[i] = 1.0
        elif event == 'system_startup':
            core_signal[i] = 0.8
        elif 'core_latency_ms' in meta:
            core_signal[i] = meta['core_latency_ms'] / 1000.0
    
    return lua_signal, elo_signal, core_signal


def discretize_signal(signal: np.ndarray, bins: int = 5) -> np.ndarray:
    """연속 신호를 이산화 (mutual information 계산용)"""
    if np.all(signal == 0):
        return signal.astype(int)
    
    # 제로가 아닌 값들만 분할
    nonzero_mask = signal > 0
    if not np.any(nonzero_mask):
        return signal.astype(int)
    
    discretized = np.zeros_like(signal, dtype=int)
    nonzero_values = signal[nonzero_mask]
    
    # 분위수 기반 분할
    try:
        quantiles = np.linspace(0, 100, bins + 1)
        edges = np.percentile(nonzero_values, quantiles)
        edges = np.unique(edges)  # 중복 제거
        
        discretized[nonzero_mask] = np.digitize(nonzero_values, edges[1:-1]) + 1
    except:
        # 분할 실패 시 단순 이진화
        discretized[nonzero_mask] = 1
    
    return discretized


def calculate_entropy(signal: np.ndarray) -> float:
    """엔트로피 H(X) 계산"""
    unique, counts = np.unique(signal, return_counts=True)
    probs = counts / len(signal)
    return -np.sum(probs * np.log2(probs + 1e-10))


def calculate_mutual_information(x: np.ndarray, y: np.ndarray) -> float:
    """상호정보 I(X; Y) 계산"""
    hx = calculate_entropy(x)
    hy = calculate_entropy(y)
    
    # Joint entropy H(X, Y)
    xy = np.column_stack([x, y])
    unique_xy = [tuple(row) for row in xy]
    unique_pairs, counts = np.unique(unique_xy, return_counts=True, axis=0)
    probs = counts / len(unique_xy)
    hxy = -np.sum(probs * np.log2(probs + 1e-10))
    
    return hx + hy - hxy


def calculate_conditional_mutual_information(
    x: np.ndarray, 
    y: np.ndarray, 
    z: np.ndarray
) -> float:
    """
    조건부 상호정보 I(X; Y | Z) 계산
    I(X; Y | Z) = H(X, Z) + H(Y, Z) - H(X, Y, Z) - H(Z)
    """
    # Joint entropies
    xz = np.column_stack([x, z])
    yz = np.column_stack([y, z])
    xyz = np.column_stack([x, y, z])
    
    def joint_entropy(data):
        unique_rows = [tuple(row) for row in data]
        _, counts = np.unique(unique_rows, return_counts=True, axis=0)
        probs = counts / len(unique_rows)
        return -np.sum(probs * np.log2(probs + 1e-10))
    
    h_xz = joint_entropy(xz)
    h_yz = joint_entropy(yz)
    h_xyz = joint_entropy(xyz)
    h_z = calculate_entropy(z)
    
    return h_xz + h_yz - h_xyz - h_z


def calculate_interaction_information(
    lua: np.ndarray,
    elo: np.ndarray,
    Core: np.ndarray
) -> float:
    """
    상호작용 정보 I3(Lua; Elo; Core) 계산
    I3 = I(Lua; Elo) - I(Lua; Elo | Core)
    """
    i_lua_elo = calculate_mutual_information(lua, elo)
    i_lua_elo_given_core = calculate_conditional_mutual_information(lua, elo, Core)
    
    return i_lua_elo - i_lua_elo_given_core


def create_context_features(contexts: List[Dict]) -> np.ndarray:
    """
    Context를 수치 특징으로 변환
    
    Features:
    - hour_of_day (0-23)
    - where_hash (location hash)
    - event_type_hash
    - who_count (참여자 수)
    """
    n = len(contexts)
    features = np.zeros((n, 4), dtype=int)
    
    for i, ctx in enumerate(contexts):
        # Hour of day
        try:
            dt = datetime.fromisoformat(ctx['when'])
            features[i, 0] = dt.hour
        except:
            pass
        
        # Where hash (단순 문자열 해시)
        where = ctx.get('where', '')
        features[i, 1] = hash(where) % 100
        
        # Event type hash
        event = ctx.get('event', '')
        features[i, 2] = hash(event) % 100
        
        # Who count
        who = ctx.get('who', [])
        features[i, 3] = len(who)
    
    return features


def main():
    print("🔮 [Core] Contextualized I3 Calculator")
    print("=" * 60)
    
    if not CONTEXT_PATH.exists():
        print(f"❌ [Core] Context file not found: {CONTEXT_PATH}")
        print(f"   Run: python scripts/extract_resonance_context.py")
        return 1
    
    # Load contexts
    window_hours = 24
    print(f"\n📖 [Core] Loading contexts (last {window_hours}h)...")
    contexts = load_contexts(window_hours)
    print(f"✅ [Core] Loaded {len(contexts):,} contexts")
    
    if len(contexts) < 100:
        print(f"⚠️  [Core] Too few contexts for reliable I3 calculation")
        return 1
    
    # Extract signals
    print(f"\n🎵 [Core] Extracting Trinity signals...")
    lua_raw, elo_raw, core_raw = extract_signals(contexts)
    
    print(f"   Lua (energy):  mean={lua_raw.mean():.3f}, std={lua_raw.std():.3f}")
    print(f"   Elo (quality): mean={elo_raw.mean():.3f}, std={elo_raw.std():.3f}")
    print(f"   Core (obs):   mean={core_raw.mean():.3f}, std={core_raw.std():.3f}")
    
    # Discretize
    print(f"\n🔢 [Core] Discretizing signals...")
    lua = discretize_signal(lua_raw, bins=5)
    elo = discretize_signal(elo_raw, bins=5)
    Core = discretize_signal(core_raw, bins=5)
    
    # Context features
    print(f"\n🧩 [Core] Creating context features...")
    context_features = create_context_features(contexts)
    
    # Combine context features into single dimension
    context_combined = context_features[:, 0] * 1000 + context_features[:, 1] * 10 + context_features[:, 2]
    context_discrete = discretize_signal(context_combined, bins=10)
    
    # Calculate metrics
    print(f"\n📊 [Core] Calculating information metrics...")
    
    # Unconditional
    i_lua_elo = calculate_mutual_information(lua, elo)
    i_lua_core = calculate_mutual_information(lua, Core)
    i_elo_core = calculate_mutual_information(elo, Core)
    
    print(f"\n   Unconditional Mutual Information:")
    print(f"      I(Lua; Elo)   = {i_lua_elo:.4f} bits")
    print(f"      I(Lua; Core) = {i_lua_core:.4f} bits")
    print(f"      I(Elo; Core) = {i_elo_core:.4f} bits")
    
    # Conditional (given Context)
    i_elo_core_given_context = calculate_conditional_mutual_information(elo, Core, context_discrete)
    
    print(f"\n   Conditional Mutual Information (given Context):")
    print(f"      I(Elo; Core | Context) = {i_elo_core_given_context:.4f} bits")
    
    # Interaction Information
    i3 = calculate_interaction_information(lua, elo, Core)
    
    print(f"\n   Interaction Information:")
    print(f"      I3(Lua; Elo; Core) = {i3:.4f} bits")
    
    # Improvement
    improvement = i_elo_core - i_elo_core_given_context
    improvement_pct = 100 * improvement / (i_elo_core + 1e-10)
    
    print(f"\n✨ [Core] Context Conditioning Effect:")
    print(f"   Before: I(Elo; Core) = {i_elo_core:.4f} bits")
    print(f"   After:  I(Elo; Core | Context) = {i_elo_core_given_context:.4f} bits")
    print(f"   Improvement: {improvement:.4f} bits ({improvement_pct:.1f}%)")
    
    # Goal check
    goal = 0.05
    if i_elo_core_given_context <= goal:
        print(f"\n🎯 [Core] GOAL ACHIEVED! ✅")
        print(f"   I(Elo; Core | Context) ≤ {goal} bits")
    else:
        remaining = i_elo_core_given_context - goal
        print(f"\n🎯 [Core] Goal Progress:")
        print(f"   Target: ≤ {goal} bits")
        print(f"   Current: {i_elo_core_given_context:.4f} bits")
        print(f"   Remaining: {remaining:.4f} bits")
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "window_hours": int(window_hours),
        "n_contexts": int(len(contexts)),
        "unconditional": {
            "I_lua_elo": float(i_lua_elo),
            "I_lua_core": float(i_lua_core),
            "I_elo_core": float(i_elo_core)
        },
        "conditional": {
            "I_elo_core_given_context": float(i_elo_core_given_context)
        },
        "interaction": {
            "I3_lua_elo_core": float(i3)
        },
        "improvement": {
            "absolute": float(improvement),
            "percentage": float(improvement_pct)
        },
        "goal": {
            "target": float(goal),
            "achieved": bool(i_elo_core_given_context <= goal),
            "remaining": float(max(0, i_elo_core_given_context - goal))
        }
    }
    
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 [Core] Report saved: {OUTPUT_PATH}")
    print(f"\n✅ [Core] CI3 optimization complete!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
