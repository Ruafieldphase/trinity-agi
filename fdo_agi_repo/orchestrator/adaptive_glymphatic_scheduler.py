"""
Adaptive Glymphatic Scheduler
리듬 기반 적응형 스케줄러
"""
from typing import Dict, Optional
from datetime import datetime, time
import random


class AdaptiveGlymphaticScheduler:
    """적응형 Glymphatic 스케줄러"""
    
    def __init__(self):
        # 기본 청소 시간대 (새벽 3-5시)
        self.default_window_start = time(3, 0)
        self.default_window_end = time(5, 0)
        
    def find_optimal_time(
        self, 
        workload: float,
        fatigue: float,
        current_hour: Optional[int] = None
    ) -> Dict:
        """최적 청소 시간 찾기"""
        
        if current_hour is None:
            current_hour = datetime.now().hour
        
        # 즉시 청소 필요 여부
        urgent = self._is_urgent(workload, fatigue)
        
        if urgent:
            return {
                "action": "cleanup_now",
                "reason": "high_fatigue_or_low_workload",
                "delay_minutes": 0,
                "confidence": 0.95
            }
        
        # 최적 시간 계산
        optimal_time = self._calculate_optimal_time(
            workload, fatigue, current_hour
        )
        
        return optimal_time
    
    def _is_urgent(self, workload: float, fatigue: float) -> bool:
        """긴급 청소 필요 여부"""
        # 피로도가 매우 높거나 작업량이 매우 낮을 때
        high_fatigue = fatigue > 80
        very_low_workload = workload < 20
        
        return high_fatigue or very_low_workload
    
    def _calculate_optimal_time(
        self, 
        workload: float,
        fatigue: float,
        current_hour: int
    ) -> Dict:
        """최적 시간 계산"""
        
        # 현재 시간대 평가
        if self._is_low_activity_period(current_hour):
            # 저활동 시간대면 빨리 청소
            delay = random.randint(5, 30)
            return {
                "action": "schedule_soon",
                "reason": "low_activity_period",
                "delay_minutes": delay,
                "confidence": 0.85
            }
        
        # 피로도 기반 스케줄링
        if fatigue > 60:
            # 피로도 높으면 다음 저활동 시간대까지 기다림
            next_window = self._time_until_next_window(current_hour)
            return {
                "action": "schedule_next_window",
                "reason": "moderate_fatigue",
                "delay_minutes": next_window,
                "confidence": 0.75
            }
        
        # 기본: 다음 새벽 시간대
        return {
            "action": "schedule_default",
            "reason": "normal_operation",
            "delay_minutes": self._time_until_default_window(current_hour),
            "confidence": 0.9
        }
    
    def _is_low_activity_period(self, hour: int) -> bool:
        """저활동 시간대 체크"""
        # 새벽 1-6시, 점심 12-13시, 저녁 19-20시
        low_activity_hours = [
            range(1, 7),    # 새벽
            range(12, 14),  # 점심
            range(19, 21)   # 저녁
        ]
        
        return any(hour in r for r in low_activity_hours)
    
    def _time_until_next_window(self, current_hour: int) -> int:
        """다음 저활동 시간대까지 시간 (분)"""
        if current_hour < 1:
            return (1 - current_hour) * 60
        elif current_hour < 6:
            return 30  # 이미 저활동 시간대
        elif current_hour < 12:
            return (12 - current_hour) * 60
        elif current_hour < 14:
            return 30  # 이미 저활동 시간대
        elif current_hour < 19:
            return (19 - current_hour) * 60
        elif current_hour < 21:
            return 30  # 이미 저활동 시간대
        else:
            return (25 - current_hour) * 60  # 다음날 새벽 1시
    
    def _time_until_default_window(self, current_hour: int) -> int:
        """기본 청소 시간대까지 시간 (분)"""
        if current_hour < 3:
            return (3 - current_hour) * 60
        elif current_hour < 5:
            return 30  # 이미 청소 시간대
        else:
            return (27 - current_hour) * 60  # 다음날 새벽 3시
    
    def should_cleanup_now(
        self,
        workload: float,
        fatigue: float
    ) -> bool:
        """지금 청소해야 하는가"""
        decision = self.find_optimal_time(workload, fatigue)
        return decision["action"] == "cleanup_now"
