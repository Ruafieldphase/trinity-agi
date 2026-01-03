#!/usr/bin/env python3
"""
Test Auto Dream Pipeline
========================

Tests for the full automated dream pipeline.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from workspace_root import get_workspace_root

# Add project root to path
project_root = get_workspace_root()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from auto_dream_pipeline import DreamPipelineAutomation


class TestDreamPipelineAutomation(unittest.TestCase):
    """Test cases for DreamPipelineAutomation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = DreamPipelineAutomation(dry_run=True, verbose=False)
    
    def test_initialization(self):
        """Test pipeline initialization."""
        self.assertTrue(self.pipeline.dry_run)
        self.assertFalse(self.pipeline.verbose)
        self.assertIsNotNone(self.pipeline.stats)
        self.assertEqual(self.pipeline.stats["resonance_events_processed"], 0)
    
    def test_log_levels(self):
        """Test different log levels."""
        # Should not raise
        self.pipeline.log("Info message", "INFO")
        self.pipeline.log("Warning message", "WARN")
        self.pipeline.log("Error message", "ERROR")
        self.pipeline.log("Success message", "SUCCESS")
    
    @patch('auto_dream_pipeline.consolidate_to_hippocampus')
    def test_step1_consolidate_resonance_dryrun(self, mock_consolidate):
        """Test Step 1 in dry-run mode."""
        count, status = self.pipeline.step_1_consolidate_resonance()
        
        self.assertEqual(count, 0)
        self.assertEqual(status, "dry-run")
        mock_consolidate.assert_not_called()
    
    @patch('auto_dream_pipeline.consolidate_to_hippocampus')
    def test_step1_consolidate_resonance_success(self, mock_consolidate):
        """Test Step 1 with successful consolidation."""
        # Setup non-dry-run pipeline
        pipeline = DreamPipelineAutomation(dry_run=False, verbose=False)
        
        # Mock successful consolidation
        mock_consolidate.return_value = {
            "events_read": 10,
            "memories_added": 5
        }
        
        count, status = pipeline.step_1_consolidate_resonance()
        
        self.assertEqual(count, 5)
        self.assertEqual(status, "success")
        self.assertEqual(pipeline.stats["resonance_events_processed"], 10)
        mock_consolidate.assert_called_once()
    
    @patch('auto_dream_pipeline.consolidate_to_hippocampus')
    def test_step1_consolidate_resonance_error(self, mock_consolidate):
        """Test Step 1 with error."""
        pipeline = DreamPipelineAutomation(dry_run=False, verbose=False)
        
        # Mock error
        mock_consolidate.side_effect = Exception("Test error")
        
        count, status = pipeline.step_1_consolidate_resonance()
        
        self.assertEqual(count, 0)
        self.assertEqual(status, "error")
        self.assertEqual(len(pipeline.stats["errors"]), 1)
    
    def test_step2_generate_dreams_dryrun(self):
        """Test Step 2 in dry-run mode."""
        count, status = self.pipeline.step_2_generate_dreams()
        
        self.assertEqual(count, 0)
        self.assertEqual(status, "dry-run")
    
    def test_step3_glymphatic_cleanup_dryrun(self):
        """Test Step 3 in dry-run mode."""
        cleanup_mb, status = self.pipeline.step_3_glymphatic_cleanup()
        
        self.assertEqual(cleanup_mb, 0.0)
        self.assertEqual(status, "dry-run")
    
    def test_step4_consolidate_longterm_dryrun(self):
        """Test Step 4 in dry-run mode."""
        count, status = self.pipeline.step_4_consolidate_to_longterm()
        
        self.assertEqual(count, 0)
        self.assertEqual(status, "dry-run")
    
    def test_extract_patterns_empty(self):
        """Test pattern extraction with empty memory."""
        patterns = self.pipeline._extract_patterns_from_memory()
        
        # Should return empty or handle gracefully
        self.assertIsInstance(patterns, list)
    
    def test_run_pipeline_dryrun(self):
        """Test full pipeline in dry-run mode."""
        stats = self.pipeline.run_pipeline()
        
        self.assertIsNotNone(stats)
        self.assertIn("start_time", stats)
        self.assertIn("end_time", stats)
        self.assertIn("duration_seconds", stats)
        self.assertTrue(stats["success"])
    
    def test_generate_report(self):
        """Test report generation."""
        report = self.pipeline._generate_report(success=True)
        
        self.assertIn("start_time", report)
        self.assertIn("end_time", report)
        self.assertIn("duration_seconds", report)
        self.assertIn("success", report)
        self.assertTrue(report["success"])


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for the full pipeline."""
    
    @patch('auto_dream_pipeline.consolidate_to_hippocampus')
    def test_full_pipeline_mock(self, mock_consolidate):
        """Test full pipeline with mocked dependencies."""
        # Setup mocks
        mock_consolidate.return_value = {
            "events_read": 10,
            "memories_added": 5
        }
        
        # Run pipeline
        pipeline = DreamPipelineAutomation(dry_run=False, verbose=False)
        
        # Mock hippocampus methods
        pipeline.hippocampus.retrieve_memories = Mock(return_value=[
            {"content": "test", "importance": 0.8, "id": "1", "timestamp": "2025-11-05"}
        ])
        pipeline.hippocampus.generate_dream = Mock(return_value={
            "content": "test dream",
            "quality": 0.9
        })
        pipeline.hippocampus.working_memory = {
            "short_term": [
                {"content": "test", "importance": 0.9}
            ]
        }
        
        # Mock glymphatic
        pipeline.glymphatic.cleanup_cycle = Mock(return_value={
            "cleared_mb": 1.5
        })
        
        stats = pipeline.run_pipeline()
        
        self.assertTrue(stats["success"])
        self.assertGreater(stats["duration_seconds"], 0)


def run_tests():
    """Run all tests."""
    print("🧪 Running Auto Dream Pipeline Tests...\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestDreamPipelineAutomation))
    suite.addTests(loader.loadTestsFromTestCase(TestPipelineIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print(f"{'='*60}\n")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
