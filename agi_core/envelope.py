"""
Behavior Envelope - 행동량 규제 모듈
AGI의 행동 총량을 조절하여 과열을 방지

구조:
1. Per-Heartbeat Action Limit: 심장박동당 1개 행동만 허용
2. Daily Action Budget: 하루 행동 총량 제한
3. Surge Protection: 연속 행동 3회 이상 시 자동 휴식
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, date
from typing import Tuple

logger = logging.getLogger("BehaviorEnvelope")

# 행동량 설정
MAX_ACTION_PER_HEARTBEAT = 1
DAILY_BUDGET = 100  # 하루 총 에너지

# 레벨별 비용
LEVEL_COST = {
    1: 3,   # 내부 탐색 (가벼움)
    2: 12,  # 중간 작업
    3: 30,  # 외부/위험 작업
}

# 연속 실행 보호
SURGE_LIMIT = 3       # 연속 행동 허용치
SURGE_COOLDOWN = 30   # 냉각 시간 (초)


@dataclass
class EnvelopeState:
    """Envelope 상태"""
    daily_used: int = 0
    recent_actions: int = 0
    last_date: str = ""
    total_actions_today: int = 0


class ActionEnvelope:
    """
    행동량 규제 시스템
    
    - 하루 예산 관리
    - 연속 실행 방지 (Surge Protection)
    - 레벨별 비용 계산
    """
    
    def __init__(self):
        self.daily_used = 0
        self.recent_actions = 0
        self.last_date = self._get_today()
        self.total_actions_today = 0
    
    def _get_today(self) -> str:
        return date.today().isoformat()
    
    def reset_daily_if_needed(self) -> None:
        """새로운 날이면 리셋"""
        today = self._get_today()
        if today != self.last_date:
            logger.info(f"🌅 새로운 날 시작 - 예산 리셋 (어제 사용량: {self.daily_used})")
            self.daily_used = 0
            self.total_actions_today = 0
            self.last_date = today
    
    def check(self, action_level: int) -> Tuple[bool, str]:
        """
        행동 실행 가능 여부 확인
        
        Returns:
            (ok, reason): 실행 가능 여부와 이유
        """
        self.reset_daily_if_needed()
        
        # 1) Daily Budget 체크
        cost = LEVEL_COST.get(action_level, LEVEL_COST[2])
        if self.daily_used + cost > DAILY_BUDGET:
            remaining = DAILY_BUDGET - self.daily_used
            logger.warning(f"⛔ 하루 예산 초과 (사용: {self.daily_used}, 남음: {remaining}, 필요: {cost})")
            return False, "DAILY_BUDGET_EXCEEDED"
        
        # 2) Surge Protection 체크
        if self.recent_actions >= SURGE_LIMIT:
            logger.warning(f"⛔ 연속 행동 제한 ({self.recent_actions}회 연속)")
            return False, "SURGE_PROTECTION"
        
        # 통과 - 비용 차감 및 카운트 증가
        self.daily_used += cost
        self.recent_actions += 1
        self.total_actions_today += 1
        
        logger.info(f"✅ 행동 허용 (Level {action_level}, 비용: {cost}, "
                   f"오늘 사용: {self.daily_used}/{DAILY_BUDGET}, "
                   f"연속: {self.recent_actions})")
        
        return True, "OK"
    
    def on_cooldown(self) -> None:
        """Surge 냉각 완료"""
        self.recent_actions = 0
        logger.info("❄️ 냉각 완료 - 연속 카운트 리셋")
    
    def on_idle(self) -> None:
        """행동 없이 heartbeat가 지나갔을 때 - 연속 카운트 감소"""
        if self.recent_actions > 0:
            self.recent_actions -= 1
    
    def get_status(self) -> dict:
        """현재 상태 반환"""
        return {
            "daily_used": self.daily_used,
            "daily_remaining": DAILY_BUDGET - self.daily_used,
            "recent_actions": self.recent_actions,
            "surge_limit": SURGE_LIMIT,
            "total_actions_today": self.total_actions_today,
        }


# 전역 인스턴스
_envelope: ActionEnvelope | None = None


def get_envelope() -> ActionEnvelope:
    """Envelope 싱글톤"""
    global _envelope
    if _envelope is None:
        _envelope = ActionEnvelope()
    return _envelope


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    env = get_envelope()
    
    # 테스트
    for i in range(5):
        ok, reason = env.check(1)
        print(f"Action {i+1}: {ok} - {reason}")
    
    print(f"\nStatus: {env.get_status()}")
