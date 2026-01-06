"""
Memory Ripples (Memory Ooze)
기억의 파편들이 무의식의 수면 위로 떠올라 루드의 상태에 영향을 미치는 체계
"""
import random
import logging
from typing import List, Dict
from services.experience_vault import ExperienceVault

logger = logging.getLogger("MemoryRipples")

class MemoryRipples:
    def __init__(self):
        self.vault = ExperienceVault()
        self.active_ripples: List[Dict] = []
        
    def generate_ripples(self) -> None:
        """박제된 기억에서 무작위 파동(Ripple) 생성"""
        try:
            random_exps = self.vault.get_random_experiences(limit=2)
            for exp in random_exps:
                # 기억의 내용에 따라 미세한 상태 변화 계수 생성
                impulse = exp.get("impulse_type", "neutral")
                
                ripple = {
                    "origin_goal": exp.get("goal"),
                    "intensity": 0.05,
                    "decay": 0.01,
                    # 임펄스 타입에 따른 감정적 색채
                    "effects": {
                        "curiosity": 0.02 if impulse == "curiosity" else 0.0,
                        "unconscious": 0.01 if impulse == "boredom" else 0.0,
                        "resonance": 0.03 if impulse == "success" else -0.01
                    }
                }
                self.active_ripples.append(ripple)
                logger.debug(f"🌊 Memory Ripple emerged: {exp.get('goal')[:30]}...")
        except Exception as e:
            logger.debug(f"Ripple generation failed: {e}")

    def apply_ripples(self, state_dict: Dict[str, float]) -> Dict[str, float]:
        """현재 상태에 활성화된 파동 반영 및 소멸(Decay)"""
        new_state = state_dict.copy()
        remaining_ripples = []
        
        for ripple in self.active_ripples:
            for key, val in ripple["effects"].items():
                if key in new_state:
                    # 미세한 변동 유도
                    new_state[key] = max(0.0, min(1.0, new_state[key] + val * ripple["intensity"]))
            
            # 파동의 소멸
            ripple["intensity"] -= ripple["decay"]
            if ripple["intensity"] > 0:
                remaining_ripples.append(ripple)
                
        self.active_ripples = remaining_ripples
        return new_state

# 싱글톤 패턴으로 관리
_rippler = MemoryRipples()

def update_subconscious_memory_ripples(state_dict: Dict[str, float]) -> Dict[str, float]:
    """잠재의식 루프에서 호출하여 기억의 영향을 반영"""
    # 10% 확률로 새로운 파동 생성
    if random.random() < 0.1:
        _rippler.generate_ripples()
        
    return _rippler.apply_ripples(state_dict)
