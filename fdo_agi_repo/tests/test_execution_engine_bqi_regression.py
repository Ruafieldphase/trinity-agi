"""
Regression test: ExecutionEngine should preserve partial progress when the
Binoche (BQI) evaluation stage raises an exception. This ensures downstream
(best-effort) evaluation errors do not zero-out main execution results.
"""

import unittest
import sys
from pathlib import Path

# Ensure package import path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa.execution_engine import (
    ExecutionEngine,
    ExecutionConfig,
    ExecutionMode,
)


class _BoomBqiCore:
    def evaluate_and_decide(self, *args, **kwargs):
        # Simulate a failure in the BQI evaluation stage
        raise RuntimeError("simulated BQI failure")


class TestExecutionEngineBqiRegression(unittest.TestCase):
    def setUp(self):
        self.output_dir = Path("outputs/test_execution_engine_bqi")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def test_bqi_failure_does_not_zero_progress(self):
        # Dry-run for safety
        config = ExecutionConfig(
            mode=ExecutionMode.DRY_RUN,
            enable_verification=False,
            enable_failsafe=True,
            confirmation_required=False,
            output_dir=self.output_dir / "dry_run_bqi_fail",
        )
        engine = ExecutionEngine(config)

        # Force BQI evaluation stage to raise
        engine.rpa_core = _BoomBqiCore()

        tutorial_text = """
        Minimal Tutorial

        1. Type 'hello'
        """

        result = engine.execute_tutorial(
            tutorial_text=tutorial_text, tutorial_name="bqi_fail_regression"
        )

        # Core expectations: main execution results are preserved
        self.assertEqual(result.mode, ExecutionMode.DRY_RUN)
        self.assertGreater(result.total_actions, 0, "Actions should be extracted")
        self.assertEqual(
            result.executed_actions,
            result.total_actions,
            "All actions should be executed in dry-run",
        )
        self.assertEqual(result.failed_actions, 0)
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main(verbosity=2)
