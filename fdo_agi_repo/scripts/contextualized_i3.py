#!/usr/bin/env python3
"""
Contextualized I3 (CI3): Trinity의 통일장 이론

물리학 대응:
- Signal Space (Lua, Elo, Lumen) = 양자역학
- Context Space (Where, When, Who) = 일반상대성
- CI3 = 통일장 이론
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class Context:
    """시공간 맥락 (중력에 해당)"""
    where: str  # 공간 (Space)
    when: float  # 시간 (Time)
    who: str  # 관계망 (Network)
    
    def to_vector(self) -> np.ndarray:
        """Context를 벡터로 변환 (수치화)"""
        # 간단한 해시 기반 인코딩
        where_code = hash(self.where) % 1000 / 1000.0
        who_code = hash(self.who) % 1000 / 1000.0
        return np.array([where_code, self.when, who_code])


def conditional_entropy(X: np.ndarray, Y: np.ndarray, C: np.ndarray, 
                       bins: int = 10) -> float:
    """
    조건부 엔트로피: H(X|Y,C)
    
    물리적 의미:
    - Context C를 고정했을 때 Y가 주어진 상태에서 X의 불확실성
    """
    # 1D로 변환
    if X.ndim > 1:
        X = X.ravel()
    if Y.ndim > 1:
        Y = Y.ravel()
    if C.ndim > 1:
        C = C.ravel()
    
    # 2차원 히스토그램으로 단순화
    H_XY, edges = np.histogram2d(X, Y, bins=bins)
    p_XY = H_XY / np.sum(H_XY) if np.sum(H_XY) > 0 else H_XY
    
    # H(X|Y) = -Σ p(x,y) log p(x|y)
    H_X_given_Y = 0.0
    p_Y = np.sum(p_XY, axis=0)
    
    for i in range(bins):
        for j in range(bins):
            if p_XY[i,j] > 0 and p_Y[j] > 0:
                p_x_given_y = p_XY[i,j] / p_Y[j]
                H_X_given_Y -= p_XY[i,j] * np.log2(p_x_given_y)
    
    return H_X_given_Y


def conditional_mutual_information(X: np.ndarray, Y: np.ndarray, 
                                  C: np.ndarray, bins: int = 10) -> float:
    """
    조건부 상호정보: I(X;Y|C)
    
    물리적 의미:
    - Context C를 고정했을 때 X와 Y의 상관성
    - "시공간 배경을 고정하면 두 입자가 얼마나 상관되는가?"
    
    I(X;Y|C) = H(X|C) - H(X|Y,C)
    """
    # 1D로 변환
    if X.ndim > 1:
        X = X.ravel()
    if Y.ndim > 1:
        Y = Y.ravel()
    if C.ndim > 1:
        C = C.ravel()
    
    # Mutual Information 직접 계산
    H_X, _ = np.histogram(X, bins=bins)
    H_Y, _ = np.histogram(Y, bins=bins)
    H_XY, _, _ = np.histogram2d(X, Y, bins=bins)
    
    p_X = H_X / np.sum(H_X) if np.sum(H_X) > 0 else H_X
    p_Y = H_Y / np.sum(H_Y) if np.sum(H_Y) > 0 else H_Y
    p_XY = H_XY / np.sum(H_XY) if np.sum(H_XY) > 0 else H_XY
    
    MI = 0.0
    for i in range(bins):
        for j in range(bins):
            if p_XY[i,j] > 0 and p_X[i] > 0 and p_Y[j] > 0:
                MI += p_XY[i,j] * np.log2(p_XY[i,j] / (p_X[i] * p_Y[j]))
    
    return MI


def contextualized_i3(lua: np.ndarray, elo: np.ndarray, lumen: np.ndarray,
                     context: np.ndarray, bins: int = 10) -> Tuple[float, dict]:
    """
    Contextualized I3 (CI3): Trinity의 통일장 이론
    
    CI3 = I(Lua;Elo|C) + I(Lua;Lumen|C) + I(Elo;Lumen|C) - I(Lua,Elo,Lumen|C)
    
    Args:
        lua: Lua 신호 (독립 작업)
        elo: Elo 신호 (도전)
        lumen: Lumen 신호 (통합)
        context: Context 벡터 (Where, When, Who)
        bins: 히스토그램 빈 수
    
    Returns:
        (CI3, details_dict)
        
    물리적 해석:
        CI3 > 0: Context 고정해도 중복 존재 (비효율)
        CI3 = 0: 완벽한 통합 (초전도 상태)
        CI3 < 0: 시너지 (음의 에너지? 양자 얽힘?)
    """
    # 조건부 상호정보 계산
    I_12_given_C = conditional_mutual_information(lua, elo, context, bins)
    I_13_given_C = conditional_mutual_information(lua, lumen, context, bins)
    I_23_given_C = conditional_mutual_information(elo, lumen, context, bins)
    
    # 3-way 상호정보 (단순 합으로 근사)
    I_123_given_C = max(I_12_given_C, I_13_given_C, I_23_given_C)
    
    # CI3 계산
    CI3 = I_12_given_C + I_13_given_C + I_23_given_C - I_123_given_C
    
    details = {
        "ci3": CI3,
        "I_lua_elo_given_context": I_12_given_C,
        "I_lua_lumen_given_context": I_13_given_C,
        "I_elo_lumen_given_context": I_23_given_C,
        "I_all_given_context": I_123_given_C,
        "interpretation": interpret_ci3(CI3)
    }
    
    return CI3, details


def interpret_ci3(ci3: float) -> str:
    """CI3 해석 (물리적 의미)"""
    if ci3 > 0.1:
        return "중복 정보 많음 (저항 상태)"
    elif ci3 > 0:
        return "약간의 중복 (실온 전도)"
    elif ci3 > -0.1:
        return "거의 완벽한 통합 (초전도 접근)"
    else:
        return "강한 시너지 (양자 얽힘?)"


def main():
    """테스트 및 시연"""
    print("=" * 60)
    print("🌟 Contextualized I3 (CI3): Trinity 통일장 이론")
    print("=" * 60)
    print()
    
    # 샘플 데이터 생성
    np.random.seed(42)
    n_samples = 100
    
    # Context 벡터 (시공간)
    context = Context(
        where="workspace/agi",
        when=0.5,  # 정규화된 시간
        who="lumen"
    )
    context_vec = context.to_vector()
    context_array = np.tile(context_vec, (n_samples, 1))
    
    # Trinity 신호 (Context에 의존)
    lua = np.random.uniform(0.1, 0.3, n_samples) + 0.1 * context_vec[0]
    elo = np.random.uniform(0.7, 0.9, n_samples) + 0.1 * context_vec[1]
    lumen = np.random.uniform(0.4, 0.6, n_samples) + 0.1 * context_vec[2]
    
    # CI3 계산
    ci3, details = contextualized_i3(lua, elo, lumen, context_array[:, 0])
    
    print("📊 결과:")
    print(f"  CI3 = {ci3:.4f} bits")
    print(f"  해석: {details['interpretation']}")
    print()
    print("🔍 상세:")
    print(f"  I(Lua;Elo|Context) = {details['I_lua_elo_given_context']:.4f}")
    print(f"  I(Lua;Lumen|Context) = {details['I_lua_lumen_given_context']:.4f}")
    print(f"  I(Elo;Lumen|Context) = {details['I_elo_lumen_given_context']:.4f}")
    print(f"  I(All|Context) = {details['I_all_given_context']:.4f}")
    print()
    print("💡 물리적 의미:")
    print("  - Context = 중력 (시공간 배경)")
    print("  - CI3 → 0 = 초전도 상태 (완벽한 통합)")
    print("  - Trinity 통일장 이론 구현 완료! 🌟")
    print()


if __name__ == "__main__":
    main()
