import sys
from pathlib import Path
import json
import unittest
from unittest.mock import MagicMock

# Add workspace to path
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(WORKSPACE_ROOT))

from scripts.rhythm_think import LogResonanceSystem
from agi_core.self_trigger import compute_mimesis_stall_trigger, TriggerType

class TestResonanceRecovery(unittest.TestCase):
    def setUp(self):
        self.temp_ledger = WORKSPACE_ROOT / "temp_test_ledger.jsonl"
        self.temp_history = WORKSPACE_ROOT / "temp_test_history.jsonl"
        
    def tearDown(self):
        if self.temp_ledger.exists(): self.temp_ledger.unlink()
        if self.temp_history.exists(): self.temp_history.unlink()

    def test_resonance_fallback(self):
        """기억이 없을 때 'Primordial Silence'를 반환하는지 테스트"""
        system = LogResonanceSystem(self.temp_ledger)
        feeling_vector = [0.5, 0.5, 0.5, 0, 0]
        resonance = system.recall(feeling_vector)
        
        self.assertEqual(resonance['summary'], "Primordial Silence (Ready for First Expression).")
        self.assertEqual(resonance['feeling_tag'], "neutral")

    def test_mimesis_stall_trigger(self):
        """연속된 정체 상태에서 MIMESIS_STALL 트리거가 발생하는지 테스트"""
        # Create 10 stall entries
        with open(self.temp_history, 'w', encoding='utf-8') as f:
            for _ in range(10):
                entry = {
                    "state": {"score": 50},
                    "resonance": {"summary": "Unknown Memory"}
                }
                f.write(json.dumps(entry) + "\n")
        
        trigger = compute_mimesis_stall_trigger(str(self.temp_history), threshold_consecutive_neutral=5)
        
        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.type, TriggerType.MIMESIS_STALL)
        self.assertTrue(trigger.score >= 0.5)
        self.assertIn("리듬 정체 감지", trigger.reason)

if __name__ == "__main__":
    unittest.main()
