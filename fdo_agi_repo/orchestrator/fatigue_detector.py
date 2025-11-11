"""
Fatigue Detector
피로도 감지 시스템
"""
from typing import Dict, List
from datetime import datetime, timedelta
import json
from pathlib import Path


class FatigueDetector:
    """피로도 감지기"""
    
    def __init__(self, memory_path: str = "fdo_agi_repo/memory"):
        self.memory_path = Path(memory_path)
        self.memory_path.mkdir(parents=True, exist_ok=True)
        self.fatigue_file = self.memory_path / "fatigue_state.json"
        self.state = self._load_state()
        
    def _load_state(self) -> Dict:
        """상태 로드"""
        if self.fatigue_file.exists():
            with open(self.fatigue_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "last_cleanup": None,
            "work_sessions": [],
            "fatigue_level": 0.0
        }
    
    def _save_state(self):
        """상태 저장"""
        with open(self.fatigue_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def record_work_session(self, duration_minutes: float, intensity: float):
        """작업 세션 기록"""
        session = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration_minutes,
            "intensity": intensity
        }
        self.state["work_sessions"].append(session)
        
        # 오래된 세션 제거 (24시간 이전)
        cutoff = datetime.now() - timedelta(hours=24)
        self.state["work_sessions"] = [
            s for s in self.state["work_sessions"]
            if datetime.fromisoformat(s["timestamp"]) > cutoff
        ]
        
        self._save_state()
    
    def calculate_fatigue(self) -> float:
        """피로도 계산 (0-100)"""
        if not self.state["work_sessions"]:
            return 0.0
        
        # 최근 24시간 작업량 기반
        total_load = sum(
            s["duration"] * s["intensity"]
            for s in self.state["work_sessions"]
        )
        
        # 정규화 (8시간 * 강도 1.0 = 100% 피로도)
        fatigue = min(100.0, (total_load / (8 * 60)) * 100)
        
        # 마지막 청소 이후 시간 고려
        if self.state["last_cleanup"]:
            last_cleanup = datetime.fromisoformat(self.state["last_cleanup"])
            hours_since = (datetime.now() - last_cleanup).total_seconds() / 3600
            
            # 청소 후 시간이 지날수록 피로도 증가
            time_factor = min(1.0, hours_since / 24)  # 24시간 기준
            fatigue = fatigue * (1 + time_factor * 0.5)
        
        self.state["fatigue_level"] = min(100.0, fatigue)
        self._save_state()
        return self.state["fatigue_level"]
    
    def mark_cleanup(self):
        """청소 완료 기록"""
        self.state["last_cleanup"] = datetime.now().isoformat()
        self.state["fatigue_level"] = max(0.0, self.state["fatigue_level"] * 0.3)
        self._save_state()
    
    def needs_cleanup(self, threshold: float = 60.0) -> bool:
        """청소 필요 여부"""
        fatigue = self.calculate_fatigue()
        return fatigue >= threshold
    
    def get_status(self) -> Dict:
        """현재 상태"""
        fatigue = self.calculate_fatigue()
        
        return {
            "fatigue_level": fatigue,
            "status": self._classify_fatigue(fatigue),
            "last_cleanup": self.state.get("last_cleanup"),
            "work_sessions_count": len(self.state["work_sessions"]),
            "needs_cleanup": self.needs_cleanup()
        }
    
    def _classify_fatigue(self, level: float) -> str:
        """피로도 분류"""
        if level < 30:
            return "fresh"
        elif level < 60:
            return "moderate"
        elif level < 80:
            return "tired"
        else:
            return "exhausted"
