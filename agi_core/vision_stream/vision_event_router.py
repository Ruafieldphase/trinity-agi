"""
Vision Event Router
Vision 분석 결과를 Self-Acquisition Loop로 라우팅

개별 이벤트 + 절차(Procedure) 학습 통합
"""

import logging
from typing import Any, Dict, List
from datetime import datetime, timezone

logger = logging.getLogger("VisionEventRouter")

# 외부 이벤트 버퍼 (Self-Acquisition Loop에서 소비)
_external_events: List[Dict[str, Any]] = []

# Procedure 시스템 인스턴스 (lazy init)
_sequence_detector = None
_procedure_encoder = None
_procedure_memory = None


def _init_procedure_system():
    """Procedure 시스템 lazy 초기화"""
    global _sequence_detector, _procedure_encoder, _procedure_memory
    
    if _sequence_detector is None:
        try:
            from agi_core.procedures.sequence_detector import SequenceDetector
            from agi_core.procedures.procedure_encoder import ProcedureEncoder
            from agi_core.procedures.procedure_memory import ProcedureMemory
            
            _sequence_detector = SequenceDetector(max_gap=2.0)
            _procedure_encoder = ProcedureEncoder(min_events=3)
            _procedure_memory = ProcedureMemory()
            logger.info("✅ Procedure system initialized")
        except ImportError as e:
            logger.warning(f"Procedure system not available: {e}")


class VisionEventRouter:
    """Vision 분석 결과를 Self-Acquisition Loop로 전달"""
    
    @staticmethod
    def route(vision_result: Dict[str, Any]) -> None:
        """
        Vision 분석 결과를 외부 이벤트로 등록하고,
        절차(Procedure) 학습까지 진행
        
        Args:
            vision_result: 프레임 분석 결과 (actions, objects, patterns 등)
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # 1. 개별 이벤트 등록
        event = {
            "source": "vision",
            "type": "VISION_EVENT",
            "timestamp": timestamp,
            "data": vision_result,
        }
        _external_events.append(event)
        logger.debug(f"Vision event routed: {len(_external_events)} pending events")
        
        # 2. Procedure 학습 시도
        handle_vision_event(vision_result)
    
    @staticmethod
    def get_pending_events() -> List[Dict[str, Any]]:
        """대기 중인 이벤트 목록 반환 (소비하지 않음)"""
        return _external_events.copy()
    
    @staticmethod
    def consume_events() -> List[Dict[str, Any]]:
        """대기 중인 이벤트 모두 소비 (큐 비움)"""
        global _external_events
        events = _external_events.copy()
        _external_events.clear()
        logger.info(f"Consumed {len(events)} vision events")
        return events
    
    @staticmethod
    def clear() -> None:
        """이벤트 큐 초기화"""
        global _external_events
        _external_events.clear()


def handle_vision_event(event: Dict[str, Any]) -> None:
    """
    Vision 모델이 해석한 단일 이벤트를 받아,
    절차(Procedure) 단위까지 연결하고,
    Self-Acquisition Loop에 전달
    """
    _init_procedure_system()
    
    if _sequence_detector is None:
        return
    
    # 1. 시퀀스 감지
    sequence = _sequence_detector.add_event(event)
    if not sequence:
        return
    
    # 2. 절차 인코딩
    procedure = _procedure_encoder.encode(sequence)
    if not procedure:
        return
    
    # 3. 절차 메모리에 저장
    _procedure_memory.save(procedure)
    
    # 4. Self-Acquisition에 절차 학습 이벤트 등록
    register_external_event({
        "type": "PROCEDURE_LEARNED",
        "source": "vision",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": procedure,
    })
    
    logger.info(f"🔄 Procedure learned: {procedure.get('procedure_name')} (freq: {procedure.get('frequency', 1)})")


def register_external_event(event: Dict[str, Any]) -> None:
    """
    외부 시스템에서 이벤트 등록 (Self-Acquisition Loop 호환)
    """
    _external_events.append(event)
    logger.debug(f"External event registered: type={event.get('type', 'unknown')}, source={event.get('source', 'unknown')}")


def get_external_events() -> List[Dict[str, Any]]:
    """외부 이벤트 목록 반환"""
    return _external_events.copy()


def consume_external_events() -> List[Dict[str, Any]]:
    """외부 이벤트 소비"""
    global _external_events
    events = _external_events.copy()
    _external_events.clear()
    return events


def get_procedure_stats() -> Dict[str, Any]:
    """절차 시스템 통계"""
    _init_procedure_system()
    
    if _procedure_memory is None:
        return {"error": "Procedure system not available"}
    
    return {
        "memory": _procedure_memory.get_stats(),
        "detector": {
            "sequence_count": _sequence_detector.sequence_count if _sequence_detector else 0,
            "pending_events": _sequence_detector.pending_events if _sequence_detector else 0,
        },
        "encoder": {
            "encoded_count": _procedure_encoder.encoded_count if _procedure_encoder else 0,
        },
    }
