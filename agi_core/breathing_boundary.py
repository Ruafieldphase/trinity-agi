import time
import json
from typing import Dict, Optional, List

class BreathingBoundary:
    """
    맥락에 따라 유연하게 변하는 경계 (Breathing Boundary)
    - Hysteresis: 경계 근처에서의 진동 방지
    - Rhythm-aware: 리듬 모드(EXPANSION/CONTRACTION)에 따른 완화/강화
    - Trend-aware: 추세(velocity)에 따른 선제적 조정
    - Context-aware: 외부 맥락(신뢰도 등) 반영
    """
    def __init__(self, base: float, name: str, behavior: str = "higher_is_safer"):
        self.base = base
        self.name = name
        self.behavior = behavior # "higher_is_safer" (e.g. score) or "lower_is_safer" (e.g. error rate)
        self.last_threshold = base
        self.evolution_history: List[float] = [base]

    def get_threshold(self, context: dict) -> float:
        """
        맥락 기반 adaptive threshold 계산
        
        Args:
            context = {
                "rhythm_mode": "EXPANSION" | "CONTRACTION" | "NEUTRAL",
                "current_state": "inside" | "outside", # Hysteresis용
                "velocity": float, # 변화율
                "trust": float, # 0.0 ~ 1.0 (신뢰도)
                "domain_risk": float, # 0.0 ~ 1.0 (영역 위험도)
            }
        """
        threshold = self.base
        
        # 1. 리듬 조정 (EXPANSION 시에는 경계를 완화하여 탐색 허용)
        rhythm_mode = context.get("rhythm_mode", "NEUTRAL")
        rhythm_factor = 1.0
        if rhythm_mode == "EXPANSION":
            rhythm_factor = 0.8 if self.behavior == "higher_is_safer" else 1.2
        elif rhythm_mode == "CONTRACTION":
            rhythm_factor = 1.2 if self.behavior == "higher_is_safer" else 0.8
        
        threshold *= rhythm_factor

        # 2. Hysteresis (떨림 방지)
        current_state = context.get("current_state")
        hysteresis = 1.0
        if current_state == "inside": # 이미 안전 구역 안에 있음
            hysteresis = 0.9 if self.behavior == "higher_is_safer" else 1.1 # 유지하기 쉽게 (임계값 낮춤/높임)
        elif current_state == "outside": # 위험 구역에 있음
            hysteresis = 1.1 if self.behavior == "higher_is_safer" else 0.9 # 진입하기 어렵게 (임계값 높임/낮춤)
        
        threshold *= hysteresis

        # 3. 추세 고려 (급격한 변화 시 선제적 대응)
        velocity = context.get("velocity", 0.0)
        trend_factor = 1.0
        if self.behavior == "higher_is_safer":
            if velocity < -5: trend_factor = 1.2 # 급락 중이면 경계 높임 (민감하게)
            elif velocity > 5: trend_factor = 0.8 # 급등 중이면 경계 낮춤 (여유있게)
        else:
            if velocity > 5: trend_factor = 1.2 # 위협이 급격히 증가 중이면 경계 낮춤 (민감하게)
            elif velocity < -5: trend_factor = 0.8 # 위협이 급격히 감소 중이면 경계 높임 (여유있게)
            
        threshold *= trend_factor

        # 4. 신뢰도/위험도 조정
        trust = context.get("trust", 0.5)
        risk = context.get("domain_risk", 0.5)
        # 신뢰도가 높고 위험도가 낮을수록 완화
        safety_margin = (trust * 0.4) - (risk * 0.4) # -0.4 ~ +0.4
        adjust_factor = 1.0 - safety_margin if self.behavior == "higher_is_safer" else 1.0 + safety_margin
        
        threshold *= adjust_factor

        self.last_threshold = threshold
        return threshold

    def tune(self, adjustment_factor: float):
        """
        경험에 기반하여 기저 임계값(Base)을 직접 조정함. 
        계산 방식: new_base = current_base * (1 + adjustment_factor)
        """
        old_base = self.base
        self.base *= (1.0 + adjustment_factor)
        self.evolution_history.append(self.base)
        print(f"🧬 [{self.name}] Boundary Evolved: {old_base:.2f} -> {self.base:.2f} (factor: {adjustment_factor:+.4f})")

    def save_state(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "name": self.name,
                "base": self.base,
                "history": self.evolution_history
            }, f, indent=2)

    def load_state(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.base = data.get("base", self.base)
                self.evolution_history = data.get("history", [self.base])
        except:
            pass
