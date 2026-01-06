"""
Procedures 시스템 테스트
"""
import pytest
import time
from unittest.mock import patch


class TestSequenceDetector:
    """sequence_detector.py 테스트"""
    
    def test_add_event_no_boundary(self):
        """경계 없이 이벤트 추가"""
        from agi_core.procedures.sequence_detector import SequenceDetector
        
        detector = SequenceDetector(max_gap=2.0)
        
        event1 = {"timestamp": time.time(), "action": "click"}
        result = detector.add_event(event1)
        
        assert result is None  # 첫 이벤트는 시퀀스 미완성
        assert detector.pending_events == 1
    
    def test_add_event_time_boundary(self):
        """시간 간격으로 경계 감지"""
        from agi_core.procedures.sequence_detector import SequenceDetector
        
        detector = SequenceDetector(max_gap=1.0)
        
        now = time.time()
        
        # 첫 번째 이벤트
        detector.add_event({"timestamp": now, "action": "click1"})
        
        # 두 번째 이벤트 (간격 내)
        detector.add_event({"timestamp": now + 0.5, "action": "click2"})
        
        # 세 번째 이벤트 (간격 초과 - 경계)
        result = detector.add_event({"timestamp": now + 2.5, "action": "click3"})
        
        assert result is not None
        assert result["event_count"] == 2
        assert len(result["events"]) == 2
    
    def test_context_change_boundary(self):
        """컨텍스트 변화로 경계 감지"""
        from agi_core.procedures.sequence_detector import SequenceDetector
        
        detector = SequenceDetector(max_gap=5.0)
        
        now = time.time()
        
        detector.add_event({"timestamp": now, "app": "VSCode"})
        detector.add_event({"timestamp": now + 0.1, "app": "VSCode"})
        
        # 앱 전환
        result = detector.add_event({"timestamp": now + 0.2, "app": "Chrome"})
        
        assert result is not None
        assert result["event_count"] == 2
    
    def test_flush(self):
        """강제 플러시"""
        from agi_core.procedures.sequence_detector import SequenceDetector
        
        detector = SequenceDetector()
        
        detector.add_event({"action": "a"})
        detector.add_event({"action": "b"})
        
        result = detector.flush()
        
        assert result is not None
        assert result["event_count"] == 2
        assert detector.pending_events == 0


class TestProcedureEncoder:
    """procedure_encoder.py 테스트"""
    
    def test_encode_short_sequence(self):
        """짧은 시퀀스 - 절차로 인정 안 함"""
        from agi_core.procedures.procedure_encoder import ProcedureEncoder
        
        encoder = ProcedureEncoder(min_events=3)
        
        sequence = {
            "events": [{"action": "a"}, {"action": "b"}],
            "start": 1.0,
            "end": 2.0,
        }
        
        result = encoder.encode(sequence)
        assert result is None
    
    def test_encode_valid_sequence(self):
        """유효한 시퀀스 인코딩"""
        from agi_core.procedures.procedure_encoder import ProcedureEncoder
        
        encoder = ProcedureEncoder(min_events=3)
        
        sequence = {
            "events": [
                {"app": "VSCode", "action": "type", "activity_type": "coding"},
                {"app": "VSCode", "action": "save"},
                {"app": "VSCode", "action": "run"},
            ],
            "start": 1.0,
            "end": 3.0,
        }
        
        result = encoder.encode(sequence)
        
        assert result is not None
        assert "procedure_name" in result
        assert result["binoche_signature"] is True
        assert result["event_count"] == 3
        assert "confidence" in result
    
    def test_confidence_based_on_events(self):
        """이벤트 수에 따른 confidence"""
        from agi_core.procedures.procedure_encoder import ProcedureEncoder
        
        encoder = ProcedureEncoder(min_events=3)
        
        # 5개 이벤트
        seq5 = {
            "events": [{"app": "App", "action": f"a{i}"} for i in range(5)],
            "start": 1.0,
            "end": 5.0,
        }
        
        # 10개 이벤트
        seq10 = {
            "events": [{"app": "App", "action": f"a{i}"} for i in range(10)],
            "start": 1.0,
            "end": 10.0,
        }
        
        result5 = encoder.encode(seq5)
        result10 = encoder.encode(seq10)
        
        assert result10["confidence"] > result5["confidence"]


class TestProcedureMemory:
    """procedure_memory.py 테스트"""
    
    def test_save_new_procedure(self, tmp_path):
        """새 절차 저장"""
        from agi_core.procedures.procedure_memory import ProcedureMemory
        
        path = str(tmp_path / "procedures.json")
        memory = ProcedureMemory(path=path)
        
        procedure = {
            "procedure_name": "test_proc",
            "confidence": 0.8,
        }
        
        memory.save(procedure)
        
        assert len(memory) == 1
        assert memory.procedures[0]["frequency"] == 1
    
    def test_save_duplicate_procedure(self, tmp_path):
        """중복 절차 - frequency 증가"""
        from agi_core.procedures.procedure_memory import ProcedureMemory
        
        path = str(tmp_path / "procedures.json")
        memory = ProcedureMemory(path=path)
        
        procedure = {"procedure_name": "test_proc", "confidence": 0.8}
        
        memory.save(procedure)
        memory.save(procedure)
        memory.save(procedure)
        
        assert len(memory) == 1
        assert memory.procedures[0]["frequency"] == 3
    
    def test_get_frequent(self, tmp_path):
        """자주 사용된 절차 조회"""
        from agi_core.procedures.procedure_memory import ProcedureMemory
        
        path = str(tmp_path / "procedures.json")
        memory = ProcedureMemory(path=path)
        
        # 여러 절차 저장 (다른 frequency)
        for i in range(5):
            proc = {"procedure_name": f"proc_{i}", "confidence": 0.5}
            for _ in range(i + 1):  # i+1 번 저장
                memory.save(proc)
        
        frequent = memory.get_frequent(top_k=3)
        
        assert len(frequent) == 3
        assert frequent[0]["procedure_name"] == "proc_4"  # 5번
        assert frequent[1]["procedure_name"] == "proc_3"  # 4번


class TestIntegration:
    """통합 테스트"""
    
    def test_full_pipeline(self, tmp_path):
        """전체 파이프라인 테스트"""
        from agi_core.procedures.sequence_detector import SequenceDetector
        from agi_core.procedures.procedure_encoder import ProcedureEncoder
        from agi_core.procedures.procedure_memory import ProcedureMemory
        
        detector = SequenceDetector(max_gap=1.0)
        encoder = ProcedureEncoder(min_events=3)
        memory = ProcedureMemory(path=str(tmp_path / "procedures.json"))
        
        now = time.time()
        
        # 이벤트 시뮬레이션
        events = [
            {"timestamp": now, "app": "VSCode", "action": "open"},
            {"timestamp": now + 0.1, "app": "VSCode", "action": "type"},
            {"timestamp": now + 0.2, "app": "VSCode", "action": "save"},
            {"timestamp": now + 0.3, "app": "VSCode", "action": "run"},
        ]
        
        for e in events:
            detector.add_event(e)
        
        # 간격 후 새 이벤트 (경계 트리거)
        sequence = detector.add_event({"timestamp": now + 3, "action": "new"})
        
        assert sequence is not None
        
        procedure = encoder.encode(sequence)
        assert procedure is not None
        
        memory.save(procedure)
        assert len(memory) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
