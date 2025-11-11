"""
Rhythm-Aware Glymphatic System
리듬 인식 통합 시스템
"""
from typing import Dict, Optional
from pathlib import Path
import json
from datetime import datetime


class RhythmAwareGlymphaticSystem:
    """리듬 인식 Glymphatic 시스템"""
    
    def __init__(self, rhythm_file: str = "outputs/RHYTHM_SYSTEM_STATUS_REPORT.md"):
        self.rhythm_file = Path(rhythm_file)
        
    def read_rhythm_state(self) -> Optional[Dict]:
        """리듬 상태 읽기"""
        if not self.rhythm_file.exists():
            return None
        
        try:
            content = self.rhythm_file.read_text(encoding='utf-8')
            
            # 파일에서 핵심 정보 추출
            state = {
                "phase": self._extract_phase(content),
                "health": self._extract_health(content),
                "energy": self._extract_energy(content),
                "timestamp": datetime.now().isoformat()
            }
            
            return state
            
        except Exception as e:
            print(f"⚠️ 리듬 파일 읽기 실패: {e}")
            return None
    
    def _extract_phase(self, content: str) -> str:
        """Phase 추출"""
        if "REST_PHASE" in content or "휴식" in content:
            return "rest"
        elif "WORK_PHASE" in content or "집중" in content:
            return "work"
        elif "FLOW_PHASE" in content or "몰입" in content:
            return "flow"
        else:
            return "unknown"
    
    def _extract_health(self, content: str) -> str:
        """건강도 추출"""
        if "EXCELLENT" in content or "우수" in content:
            return "excellent"
        elif "GOOD" in content or "양호" in content:
            return "good"
        elif "DEGRADED" in content or "저하" in content:
            return "degraded"
        else:
            return "unknown"
    
    def _extract_energy(self, content: str) -> float:
        """에너지 레벨 추출 (추정)"""
        # 간단한 휴리스틱
        if "EXCELLENT" in content:
            return 90.0
        elif "GOOD" in content:
            return 70.0
        elif "DEGRADED" in content:
            return 40.0
        else:
            return 50.0
    
    def adjust_cleanup_urgency(
        self,
        base_fatigue: float,
        workload: float
    ) -> Dict:
        """리듬 기반 청소 긴급도 조정"""
        
        rhythm = self.read_rhythm_state()
        
        if not rhythm:
            return {
                "adjusted_fatigue": base_fatigue,
                "urgency_multiplier": 1.0,
                "reason": "no_rhythm_data"
            }
        
        # Phase별 조정
        if rhythm["phase"] == "rest":
            # 휴식 중이면 청소 좋은 타이밍
            multiplier = 1.5
            reason = "optimal_rest_phase"
            
        elif rhythm["phase"] == "work":
            # 작업 중이면 청소 미룸
            multiplier = 0.7
            reason = "active_work_phase"
            
        elif rhythm["phase"] == "flow":
            # 몰입 중이면 절대 방해 안 함
            multiplier = 0.3
            reason = "flow_state_protection"
            
        else:
            multiplier = 1.0
            reason = "unknown_phase"
        
        # 건강도 고려
        if rhythm["health"] == "degraded":
            # 건강도 나쁘면 청소 더 시급
            multiplier *= 1.3
            reason += "_plus_low_health"
        
        adjusted = min(100.0, base_fatigue * multiplier)
        
        return {
            "adjusted_fatigue": adjusted,
            "urgency_multiplier": multiplier,
            "reason": reason,
            "rhythm_phase": rhythm["phase"],
            "rhythm_health": rhythm["health"]
        }
    
    def should_cleanup_now_with_rhythm(
        self,
        base_fatigue: float,
        workload: float,
        threshold: float = 60.0
    ) -> bool:
        """리듬 고려한 청소 결정"""
        
        adjustment = self.adjust_cleanup_urgency(base_fatigue, workload)
        
        return adjustment["adjusted_fatigue"] >= threshold
