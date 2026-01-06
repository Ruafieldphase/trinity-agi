"""
Procedure Encoder
감지된 sequence를 의미 있는 절차(Procedure) 개념으로 인코딩

"이건 어떤 절차다"라는 레이블과 구조를 부여
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ProcedureEncoder")


class ProcedureEncoder:
    """
    SequenceDetector가 반환한 sequence를
    의미 있는 절차(Procedure) 블록으로 인코딩
    """
    
    def __init__(self, min_events: int = 3):
        """
        Args:
            min_events: 절차로 인정하기 위한 최소 이벤트 수
        """
        self.min_events = min_events
        self._encoded_count = 0
    
    def encode(self, sequence: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        시퀀스를 받아 절차(Procedure)로 인코딩합니다.
        절차로 보기 애매하면 None을 반환합니다.
        
        Returns:
            인코딩된 Procedure dict or None
        """
        events = sequence.get("events", [])
        
        if len(events) < self.min_events:
            logger.debug(f"Sequence too short ({len(events)} < {self.min_events}), skipping")
            return None
        
        name = self._infer_name(events)
        if not name:
            logger.debug("Could not infer procedure name, skipping")
            return None
        
        self._encoded_count += 1
        
        procedure = {
            "procedure_id": self._encoded_count,
            "procedure_name": name,
            "steps": self._extract_steps(events),
            "start": sequence.get("start"),
            "end": sequence.get("end"),
            "duration_sec": self._calculate_duration(sequence),
            "event_count": len(events),
            "confidence": self._estimate_confidence(events),
            "binoche_signature": True,  # 비노체 관찰 기반임을 표시
            "activity_types": self._extract_activity_types(events),
        }
        
        logger.info(f"Encoded procedure: {name} ({len(events)} events, {procedure['confidence']:.0%} confidence)")
        return procedure
    
    def _infer_name(self, events: List[Dict[str, Any]]) -> str:
        """
        규칙 기반 이름 추론:
        - 활성 앱/윈도우 타이틀
        - 반복되는 UI 요소
        - 메뉴/설정 패턴
        """
        app = None
        activity = None
        keywords = []
        
        for e in events:
            # 앱 이름 찾기
            if not app:
                app = e.get("current_app") or e.get("app")
            
            # 활동 유형 찾기
            if not activity:
                activity = e.get("activity_type")
            
            # 행동 키워드 수집
            if e.get("action"):
                keywords.append(e["action"])
            if e.get("user_actions"):
                if isinstance(e["user_actions"], list):
                    keywords.extend(e["user_actions"])
        
        # 이름 조합
        parts = []
        if app:
            parts.append(app.lower().replace(" ", "_"))
        if activity:
            parts.append(activity.lower())
        
        if keywords:
            # 상위 3개 고유 키워드
            unique_keywords = list(dict.fromkeys(keywords))[:3]
            parts.extend([k.lower().replace(" ", "_") for k in unique_keywords])
        
        if not parts:
            return ""
        
        return "_".join(parts[:4])  # 최대 4개 파트
    
    def _extract_steps(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """이벤트에서 핵심 스텝 정보만 추출"""
        steps = []
        for i, e in enumerate(events):
            step = {
                "order": i + 1,
                "timestamp": e.get("timestamp"),
                "action": e.get("action") or e.get("summary", "")[:50],
                "app": e.get("current_app") or e.get("app"),
            }
            if e.get("ui_elements"):
                step["ui_elements"] = e["ui_elements"][:3]  # 상위 3개
            steps.append(step)
        return steps
    
    def _extract_activity_types(self, events: List[Dict[str, Any]]) -> List[str]:
        """이벤트에서 활동 유형 추출"""
        types = set()
        for e in events:
            if e.get("activity_type"):
                types.add(e["activity_type"])
        return list(types)
    
    def _calculate_duration(self, sequence: Dict[str, Any]) -> Optional[float]:
        """시퀀스 지속 시간 계산"""
        start = sequence.get("start")
        end = sequence.get("end")
        
        if start is None or end is None:
            return None
        
        # timestamp를 float로 변환
        def to_float(ts):
            if isinstance(ts, (int, float)):
                return float(ts)
            if isinstance(ts, str):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    return dt.timestamp()
                except (ValueError, TypeError):
                    return None
            return None
        
        start_f = to_float(start)
        end_f = to_float(end)
        
        if start_f and end_f:
            return round(end_f - start_f, 2)
        return None
    
    def _estimate_confidence(self, events: List[Dict[str, Any]]) -> float:
        """
        Confidence 추정:
        - 이벤트 수
        - 앱 일관성
        - 패턴 밀도
        """
        n = len(events)
        
        # 기본 점수 (이벤트 수 기반)
        if n >= 10:
            base = 0.9
        elif n >= 5:
            base = 0.75
        else:
            base = 0.6
        
        # 앱 일관성 보너스
        apps = [e.get("current_app") or e.get("app") for e in events]
        apps = [a for a in apps if a]
        if apps:
            unique_apps = len(set(apps))
            if unique_apps == 1:
                base += 0.05  # 단일 앱이면 보너스
            elif unique_apps > 3:
                base -= 0.05  # 너무 많은 앱 전환이면 패널티
        
        return min(max(base, 0.3), 1.0)
    
    @property
    def encoded_count(self) -> int:
        """인코딩된 절차 총 수"""
        return self._encoded_count
