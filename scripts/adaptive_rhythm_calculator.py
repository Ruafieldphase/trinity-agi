#!/usr/bin/env python3
"""
Adaptive Rhythm Calculator for Autonomous Goal Execution

자연스러운 리듬 기반 간격 계산:
- 시스템 활동도
- 시간대 (집중 시간 vs 휴식 시간)
- 최근 실행 성공률
- CPU/메모리 사용률
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from workspace_root import get_workspace_root

WORKSPACE_ROOT = get_workspace_root()
TRACKER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "goal_tracker.json"
RHYTHM_STATE_FILE = WORKSPACE_ROOT / "outputs" / "rhythm_state.json"


class AdaptiveRhythmCalculator:
    """적응형 리듬 계산기"""
    
    # 기본 간격 (분)
    BASE_INTERVAL = 15
    MIN_INTERVAL = 5
    MAX_INTERVAL = 60
    
    # 시간대별 가중치
    HOUR_WEIGHTS = {
        # 아침 집중 시간 (09:00-12:00) - 짧은 간격
        9: 0.7, 10: 0.7, 11: 0.7,
        
        # 점심 (12:00-14:00) - 긴 간격
        12: 1.5, 13: 1.5,
        
        # 오후 집중 시간 (14:00-18:00) - 짧은 간격
        14: 0.8, 15: 0.8, 16: 0.8, 17: 0.8,
        
        # 저녁 (18:00-21:00) - 중간 간격
        18: 1.2, 19: 1.2, 20: 1.2,
        
        # 야간 (21:00-06:00) - 긴 간격
        21: 1.8, 22: 2.0, 23: 2.5,
        0: 3.0, 1: 3.0, 2: 3.0, 3: 3.0, 4: 3.0, 5: 3.0,
        
        # 새벽 (06:00-09:00) - 중간-짧은 간격
        6: 1.3, 7: 1.0, 8: 0.9
    }
    
    def __init__(self):
        self.now = datetime.now()
        self.tracker_data = self._load_tracker()
        self.rhythm_state = self._load_rhythm_state()
    
    def _load_tracker(self) -> Dict:
        """Goal Tracker 로드"""
        if TRACKER_FILE.exists():
            try:
                with open(TRACKER_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"goals": []}
    
    def _load_rhythm_state(self) -> Dict:
        """이전 리듬 상태 로드"""
        if RHYTHM_STATE_FILE.exists():
            try:
                with open(RHYTHM_STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_execution": None,
            "consecutive_successes": 0,
            "consecutive_failures": 0,
            "last_interval": self.BASE_INTERVAL
        }
    
    def _save_rhythm_state(self, new_state: Dict):
        """리듬 상태 저장"""
        RHYTHM_STATE_FILE.parent.mkdir(exist_ok=True)
        with open(RHYTHM_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_state, f, indent=2, ensure_ascii=False)
    
    def calculate_next_interval(self) -> int:
        """다음 실행 간격 계산 (분)"""
        
        # 1. 시간대 가중치
        hour = self.now.hour
        time_weight = self.HOUR_WEIGHTS.get(hour, 1.0)
        
        # 2. 최근 성공률 분석
        success_weight = self._calculate_success_weight()
        
        # 3. 시스템 활동도 (간단 버전)
        activity_weight = self._calculate_activity_weight()
        
        # 4. 종합 계산
        base = self.BASE_INTERVAL
        adjusted = base * time_weight * success_weight * activity_weight
        
        # 5. 범위 제한 + 랜덤 지터 (±10%)
        import random
        jitter = random.uniform(0.9, 1.1)
        final = int(adjusted * jitter)
        final = max(self.MIN_INTERVAL, min(self.MAX_INTERVAL, final))
        
        return final
    
    def _calculate_success_weight(self) -> float:
        """최근 성공률 기반 가중치"""
        successes = self.rhythm_state.get("consecutive_successes", 0)
        failures = self.rhythm_state.get("consecutive_failures", 0)
        
        # 연속 성공 → 더 자주 실행 (신뢰도 높음)
        if successes >= 3:
            return 0.8
        elif successes >= 2:
            return 0.9
        
        # 연속 실패 → 덜 자주 실행 (시스템 부담 줄임)
        if failures >= 3:
            return 1.5
        elif failures >= 2:
            return 1.3
        
        return 1.0
    
    def _calculate_activity_weight(self) -> float:
        """시스템 활동도 기반 가중치"""
        # 최근 1시간 내 실행 횟수
        recent_executions = self._count_recent_executions(hours=1)
        
        # 많이 실행됐으면 간격 늘림
        if recent_executions >= 5:
            return 1.4
        elif recent_executions >= 3:
            return 1.2
        
        # 실행이 적으면 간격 줄임
        if recent_executions == 0:
            return 0.9
        
        return 1.0
    
    def _count_recent_executions(self, hours: int) -> int:
        """최근 N시간 내 실행 횟수"""
        cutoff = self.now - timedelta(hours=hours)
        count = 0
        
        for goal in self.tracker_data.get("goals", []):
            started = goal.get("started_at")
            if started:
                try:
                    started_dt = datetime.fromisoformat(started)
                    if started_dt >= cutoff:
                        count += 1
                except:
                    pass
        
        return count
    
    def get_next_execution_time(self) -> str:
        """다음 실행 예정 시각 (ISO format)"""
        interval = self.calculate_next_interval()
        next_time = self.now + timedelta(minutes=interval)
        return next_time.isoformat()
    
    def explain_rhythm(self) -> Dict:
        """리듬 계산 설명"""
        interval = self.calculate_next_interval()
        hour = self.now.hour
        time_weight = self.HOUR_WEIGHTS.get(hour, 1.0)
        success_weight = self._calculate_success_weight()
        activity_weight = self._calculate_activity_weight()
        
        return {
            "next_interval_minutes": interval,
            "next_execution_time": self.get_next_execution_time(),
            "factors": {
                "time_of_day": {
                    "hour": hour,
                    "weight": time_weight,
                    "reason": self._explain_time_weight(hour)
                },
                "success_rate": {
                    "consecutive_successes": self.rhythm_state.get("consecutive_successes", 0),
                    "consecutive_failures": self.rhythm_state.get("consecutive_failures", 0),
                    "weight": success_weight,
                    "reason": self._explain_success_weight(success_weight)
                },
                "activity": {
                    "recent_executions": self._count_recent_executions(1),
                    "weight": activity_weight,
                    "reason": self._explain_activity_weight(activity_weight)
                }
            },
            "base_interval": self.BASE_INTERVAL,
            "rhythm_philosophy": "자연스러운 흐름, 강제하지 않는 리듬"
        }
    
    def _explain_time_weight(self, hour: int) -> str:
        """시간대 가중치 설명"""
        if 9 <= hour < 12 or 14 <= hour < 18:
            return "집중 시간대 - 짧은 간격"
        elif 12 <= hour < 14:
            return "점심 시간 - 긴 간격"
        elif 21 <= hour or hour < 6:
            return "휴식 시간 - 긴 간격"
        else:
            return "전환 시간대 - 중간 간격"
    
    def _explain_success_weight(self, weight: float) -> str:
        """성공률 가중치 설명"""
        if weight < 1.0:
            return "연속 성공 - 더 자주 실행"
        elif weight > 1.0:
            return "연속 실패 - 시스템 부담 줄이기"
        else:
            return "정상 상태"
    
    def _explain_activity_weight(self, weight: float) -> str:
        """활동도 가중치 설명"""
        if weight > 1.0:
            return "최근 활동 많음 - 간격 늘림"
        elif weight < 1.0:
            return "최근 활동 적음 - 간격 줄임"
        else:
            return "정상 활동"


def main():
    """메인 함수"""
    calc = AdaptiveRhythmCalculator()
    
    # JSON 출력
    result = calc.explain_rhythm()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 간격만 필요한 경우
    if "--interval-only" in sys.argv:
        print(result["next_interval_minutes"])
        sys.exit(0)


if __name__ == "__main__":
    main()
