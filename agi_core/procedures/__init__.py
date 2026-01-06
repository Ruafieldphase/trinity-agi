"""
Procedures Package
Vision → Event → 절차 패턴(Procedure) → Self-Acquisition Loop

비노체의 작업 방식을 "절차 기억"으로 학습하는 시스템
"""

from .sequence_detector import SequenceDetector
from .procedure_encoder import ProcedureEncoder
from .procedure_memory import ProcedureMemory

__all__ = [
    "SequenceDetector",
    "ProcedureEncoder", 
    "ProcedureMemory",
]
