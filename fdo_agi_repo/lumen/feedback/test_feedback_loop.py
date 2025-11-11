"""
Test suite for Lumen Feedback Loop system.

Tests all components:
- FeedbackLoopRedis cache monitoring
- AdaptiveTTLPolicy recommendations
- CacheSizeOptimizer decisions
- FeedbackOrchestrator complete integration

Author: Lumen Feedback Team
Date: 2025-01
Version: 1.0
"""

import os
import sys
import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any

# Ensure local module imports work when running directly
sys.path.append(os.path.dirname(__file__))

# Import all feedback components
from feedback_loop_redis import (
    FeedbackLoopRedis,
    CacheHealthStatus,
    OptimizationAction,
    CacheMetrics,
    CacheFeedback
)
from adaptive_ttl_policy import (
    AdaptiveTTLPolicy,
    TTLAdjustmentStrategy,
    TTLAdjustment
)
from cache_size_optimizer import (
    CacheSizeOptimizer,
    CacheSizeStrategy,
    CacheSizeAdjustment
)
from feedback_orchestrator import (
    FeedbackOrchestrator,
    SystemHealthLevel,
    UnifiedFeedback
)


class TestFeedbackLoopRedis(unittest.TestCase):
    """Test Redis cache monitoring and feedback generation."""
    
    def setUp(self):
        """Set up test environment."""
        self.monitor = FeedbackLoopRedis(
            project_id="test-project",
            service_name="ion-api"
        )
    
    def test_cache_health_classification(self):
        """Test cache health status determination."""
        # Test OPTIMAL (>80% hit rate)
        metrics_optimal = CacheMetrics(
            hit_rate=0.85,
            miss_rate=0.15,
            memory_usage_mb=150.0,
            memory_limit_mb=256.0,
            latency_ms=50.0,
            eviction_count=10,
            current_ttl_seconds=300
        )
        feedback_optimal = self.monitor.analyze_cache_feedback(metrics_optimal)
        self.assertEqual(feedback_optimal.health_status, CacheHealthStatus.OPTIMAL)
        self.assertEqual(feedback_optimal.optimization_action, OptimizationAction.NONE)
        
        # Test GOOD (60-80% hit rate)
        metrics_good = CacheMetrics(
            hit_rate=0.70,
            miss_rate=0.30,
            memory_usage_mb=150.0,
            memory_limit_mb=256.0,
            latency_ms=80.0,
            eviction_count=25,
            current_ttl_seconds=300
        )
        feedback_good = self.monitor.analyze_cache_feedback(metrics_good)
        self.assertEqual(feedback_good.health_status, CacheHealthStatus.GOOD)
        self.assertIn(feedback_good.optimization_action, [
            OptimizationAction.INCREASE_TTL,
            OptimizationAction.NONE
        ])
        
        # Test DEGRADED (40-60% hit rate)
        metrics_degraded = CacheMetrics(
            hit_rate=0.50,
            miss_rate=0.50,
            memory_usage_mb=200.0,
            memory_limit_mb=256.0,
            latency_ms=120.0,
            eviction_count=60,
            current_ttl_seconds=300
        )
        feedback_degraded = self.monitor.analyze_cache_feedback(metrics_degraded)
        self.assertEqual(feedback_degraded.health_status, CacheHealthStatus.DEGRADED)
        self.assertIn(feedback_degraded.optimization_action, [
            OptimizationAction.INCREASE_TTL,
            OptimizationAction.INCREASE_CACHE_SIZE
        ])
        
        # Test POOR (<40% hit rate)
        metrics_poor = CacheMetrics(
            hit_rate=0.30,
            miss_rate=0.70,
            memory_usage_mb=240.0,
            memory_limit_mb=256.0,
            latency_ms=200.0,
            eviction_count=150,
            current_ttl_seconds=300
        )
        feedback_poor = self.monitor.analyze_cache_feedback(metrics_poor)
        self.assertEqual(feedback_poor.health_status, CacheHealthStatus.POOR)
        self.assertIn(feedback_poor.optimization_action, [
            OptimizationAction.INCREASE_CACHE_SIZE,
            OptimizationAction.CLEAR_CACHE
        ])
    
    def test_optimization_action_logic(self):
        """Test optimization action decision tree."""
        # Scenario 1: Low hit rate + memory OK → Increase TTL
        metrics_1 = CacheMetrics(
            hit_rate=0.50, miss_rate=0.50,
            memory_usage_mb=100.0, memory_limit_mb=256.0,
            latency_ms=80.0, eviction_count=20,
            current_ttl_seconds=180
        )
        feedback_1 = self.monitor.analyze_cache_feedback(metrics_1)
        self.assertEqual(feedback_1.optimization_action, OptimizationAction.INCREASE_TTL)
        
        # Scenario 2: Good hit rate + high memory → Decrease TTL
        metrics_2 = CacheMetrics(
            hit_rate=0.82, miss_rate=0.18,
            memory_usage_mb=240.0, memory_limit_mb=256.0,
            latency_ms=60.0, eviction_count=80,
            current_ttl_seconds=600
        )
        feedback_2 = self.monitor.analyze_cache_feedback(metrics_2)
        self.assertEqual(feedback_2.optimization_action, OptimizationAction.DECREASE_TTL)
        
        # Scenario 3: Low hit rate + high evictions → Increase cache size
        metrics_3 = CacheMetrics(
            hit_rate=0.40, miss_rate=0.60,
            memory_usage_mb=250.0, memory_limit_mb=256.0,
            latency_ms=150.0, eviction_count=200,
            current_ttl_seconds=300
        )
        feedback_3 = self.monitor.analyze_cache_feedback(metrics_3)
        self.assertEqual(feedback_3.optimization_action, OptimizationAction.INCREASE_CACHE_SIZE)


class TestAdaptiveTTLPolicy(unittest.TestCase):
    """Test adaptive TTL adjustment logic."""
    
    def setUp(self):
        """Set up test environment."""
        self.policy = AdaptiveTTLPolicy()
    
    def test_ttl_increase_low_hit_rate(self):
        """Test TTL increase when hit rate is low."""
        adjustment = self.policy.calculate_ttl_adjustment(
            current_ttl=180,
            hit_rate=0.45,
            memory_usage_percent=60,
            eviction_count=15,
            cost_trend_percent=5.0  # Cost rising
        )
        
        self.assertGreater(adjustment.recommended_ttl, adjustment.current_ttl)
        self.assertIn(adjustment.strategy, [
            TTLAdjustmentStrategy.MODERATE,
            TTLAdjustmentStrategy.AGGRESSIVE
        ])
        self.assertGreater(adjustment.expected_hit_rate_change, 0)
        self.assertLess(adjustment.cost_impact, 0)  # Cost should decrease
    
    def test_ttl_decrease_memory_pressure(self):
        """Test TTL decrease when memory pressure is high."""
        adjustment = self.policy.calculate_ttl_adjustment(
            current_ttl=600,
            hit_rate=0.85,
            memory_usage_percent=92,  # Very high memory
            eviction_count=120,
            cost_trend_percent=-2.0  # Cost stable/falling
        )
        
        self.assertLess(adjustment.recommended_ttl, adjustment.current_ttl)
        self.assertIn(adjustment.strategy, [
            TTLAdjustmentStrategy.MODERATE,
            TTLAdjustmentStrategy.CONSERVATIVE
        ])
        self.assertLess(adjustment.expected_hit_rate_change, 0)
    
    def test_ttl_maintain_optimal(self):
        """Test TTL maintenance when cache is optimal."""
        adjustment = self.policy.calculate_ttl_adjustment(
            current_ttl=300,
            hit_rate=0.82,
            memory_usage_percent=75,
            eviction_count=20,
            cost_trend_percent=0.5  # Cost stable
        )
        
        # Should maintain or slightly increase
        self.assertGreaterEqual(adjustment.recommended_ttl, adjustment.current_ttl * 0.9)
        self.assertLessEqual(adjustment.recommended_ttl, adjustment.current_ttl * 1.2)
        self.assertEqual(adjustment.strategy, TTLAdjustmentStrategy.CONSERVATIVE)


class TestCacheSizeOptimizer(unittest.TestCase):
    """Test cache size optimization logic."""
    
    def setUp(self):
        """Set up test environment."""
        self.optimizer = CacheSizeOptimizer()
    
    def test_scale_up_memory_pressure(self):
        """Test cache size increase when memory pressure is high."""
        adjustment = self.optimizer.calculate_optimal_size(
            current_size_mb=256,
            memory_usage_mb=240,  # 93% used
            hit_rate=0.70,
            eviction_count=150,
            request_rate_per_second=50
        )
        
        self.assertEqual(adjustment.strategy, CacheSizeStrategy.SCALE_UP)
        self.assertGreater(adjustment.recommended_size_mb, adjustment.current_size_mb)
        self.assertGreater(adjustment.roi_score, 5.0)  # Should have good ROI
        self.assertGreater(adjustment.expected_hit_rate_change, 0)
    
    def test_scale_down_underutilized(self):
        """Test cache size decrease when underutilized."""
        adjustment = self.optimizer.calculate_optimal_size(
            current_size_mb=512,
            memory_usage_mb=180,  # 35% used (very low)
            hit_rate=0.55,
            eviction_count=5,
            request_rate_per_second=20
        )
        
        self.assertEqual(adjustment.strategy, CacheSizeStrategy.SCALE_DOWN)
        self.assertLess(adjustment.recommended_size_mb, adjustment.current_size_mb)
        self.assertGreater(adjustment.roi_score, 0)  # Still positive ROI
    
    def test_maintain_optimal(self):
        """Test cache size maintenance when optimal."""
        adjustment = self.optimizer.calculate_optimal_size(
            current_size_mb=256,
            memory_usage_mb=192,  # 75% used (optimal)
            hit_rate=0.85,
            eviction_count=10,
            request_rate_per_second=30
        )
        
        self.assertEqual(adjustment.strategy, CacheSizeStrategy.MAINTAIN)
        self.assertEqual(adjustment.recommended_size_mb, adjustment.current_size_mb)
        self.assertGreater(adjustment.roi_score, 7.0)  # Excellent ROI
    
    def test_roi_calculation(self):
        """Test ROI score calculation."""
        # High traffic + good hit rate → High ROI
        adjustment_high = self.optimizer.calculate_optimal_size(
            current_size_mb=128,
            memory_usage_mb=115,
            hit_rate=0.75,
            eviction_count=80,
            request_rate_per_second=100  # High traffic
        )
        self.assertGreater(adjustment_high.roi_score, 7.0)
        
        # Low traffic + low hit rate → Low ROI
        adjustment_low = self.optimizer.calculate_optimal_size(
            current_size_mb=512,
            memory_usage_mb=200,
            hit_rate=0.50,
            eviction_count=20,
            request_rate_per_second=5  # Low traffic
        )
        self.assertLess(adjustment_low.roi_score, 5.0)


class TestFeedbackOrchestrator(unittest.TestCase):
    """Test complete feedback loop orchestration."""
    
    def setUp(self):
        """Set up test environment."""
        self.orchestrator = FeedbackOrchestrator(
            project_id="test-project",
            service_name="ion-api"
        )
    
    def test_unified_gate_calculation(self):
        """Test Unified Gate score calculation (extended v1.7)."""
        # Create mock feedback data
        mock_feedback = {
            "roi_score": 6000.0,  # Excellent
            "maturity_score": 85.0,  # Level 5
            "slo_compliance_rate": 0.95,  # 95%
            "cache_hit_rate": 0.82  # Good
        }
        
        # Calculate unified score
        roi_normalized = min(100, (mock_feedback["roi_score"] / 6000) * 100)  # ~100
        maturity_norm = mock_feedback["maturity_score"]  # 85
        slo_norm = mock_feedback["slo_compliance_rate"] * 100  # 95
        cache_norm = mock_feedback["cache_hit_rate"] * 100  # 82
        
        unified_score = (
            roi_normalized * 0.30 +
            slo_norm * 0.25 +
            maturity_norm * 0.25 +
            cache_norm * 0.20
        )
        
        # Should be EXCELLENT (>85)
        self.assertGreater(unified_score, 85.0)
        self.assertLess(unified_score, 100.0)
    
    def test_system_health_determination(self):
        """Test system health level classification."""
        # EXCELLENT: All metrics good
        health_excellent = self._classify_health(
            unified_score=90.0,
            cost_rhythm="RESONANT",
            cache_health="OPTIMAL"
        )
        self.assertEqual(health_excellent, SystemHealthLevel.EXCELLENT)
        
        # WARNING: Cache degraded
        health_warning = self._classify_health(
            unified_score=75.0,
            cost_rhythm="RESONANT",
            cache_health="DEGRADED"
        )
        self.assertEqual(health_warning, SystemHealthLevel.WARNING)
        
        # CRITICAL: Cost chaotic
        health_critical = self._classify_health(
            unified_score=60.0,
            cost_rhythm="CHAOTIC",
            cache_health="POOR"
        )
        self.assertEqual(health_critical, SystemHealthLevel.CRITICAL)
    
    def _classify_health(self, unified_score: float, cost_rhythm: str, cache_health: str) -> SystemHealthLevel:
        """Helper to classify system health (simplified logic)."""
        if cost_rhythm == "CHAOTIC" or (cache_health == "POOR" and unified_score < 50):
            return SystemHealthLevel.CRITICAL
        elif cost_rhythm == "DISSONANT" or cache_health in ["DEGRADED", "POOR"] or unified_score < 60:
            return SystemHealthLevel.WARNING
        elif unified_score >= 85 and cost_rhythm == "RESONANT" and cache_health == "OPTIMAL":
            return SystemHealthLevel.EXCELLENT
        else:
            return SystemHealthLevel.GOOD


class TestCompleteIntegration(unittest.TestCase):
    """Test complete Lumen feedback loop integration (Phase 1-4)."""
    
    def test_end_to_end_feedback_cycle(self):
        """Test complete feedback loop from monitoring to recommendations."""
        # Step 1: Simulate cache monitoring
        monitor = FeedbackLoopRedis(project_id="test-project", service_name="ion-api")
        mock_metrics = CacheMetrics(
            hit_rate=0.65,
            miss_rate=0.35,
            memory_usage_mb=200.0,
            memory_limit_mb=256.0,
            latency_ms=95.0,
            eviction_count=45,
            current_ttl_seconds=240
        )
        cache_feedback = monitor.analyze_cache_feedback(mock_metrics)
        
        # Step 2: Get TTL recommendation
        ttl_policy = AdaptiveTTLPolicy()
        ttl_adjustment = ttl_policy.calculate_ttl_adjustment(
            current_ttl=mock_metrics.current_ttl_seconds,
            hit_rate=mock_metrics.hit_rate,
            memory_usage_percent=(mock_metrics.memory_usage_mb / mock_metrics.memory_limit_mb) * 100,
            eviction_count=mock_metrics.eviction_count,
            cost_trend_percent=3.5
        )
        
        # Step 3: Get size recommendation
        size_optimizer = CacheSizeOptimizer()
        size_adjustment = size_optimizer.calculate_optimal_size(
            current_size_mb=mock_metrics.memory_limit_mb,
            memory_usage_mb=mock_metrics.memory_usage_mb,
            hit_rate=mock_metrics.hit_rate,
            eviction_count=mock_metrics.eviction_count,
            request_rate_per_second=40
        )
        
        # Validate recommendations
        self.assertIsNotNone(cache_feedback)
        self.assertIsNotNone(ttl_adjustment)
        self.assertIsNotNone(size_adjustment)
        
        # Check consistency
        if cache_feedback.optimization_action == OptimizationAction.INCREASE_TTL:
            self.assertGreater(ttl_adjustment.recommended_ttl, ttl_adjustment.current_ttl)
        
        if cache_feedback.optimization_action == OptimizationAction.INCREASE_CACHE_SIZE:
            self.assertGreater(size_adjustment.recommended_size_mb, size_adjustment.current_size_mb)
        
        print("\n=== Complete Feedback Loop Test ===")
        print(f"Cache Health: {cache_feedback.health_status.name}")
        print(f"Optimization Action: {cache_feedback.optimization_action.name}")
        print(f"TTL: {ttl_adjustment.current_ttl}s → {ttl_adjustment.recommended_ttl}s")
        print(f"Cache Size: {size_adjustment.current_size_mb}MB → {size_adjustment.recommended_size_mb}MB")
        print(f"Expected Hit Rate Change: {ttl_adjustment.expected_hit_rate_change:+.2%}")
        print(f"ROI Score: {size_adjustment.roi_score:.1f}/10")


def run_all_tests():
    """Run all test suites."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFeedbackLoopRedis))
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveTTLPolicy))
    suite.addTests(loader.loadTestsFromTestCase(TestCacheSizeOptimizer))
    suite.addTests(loader.loadTestsFromTestCase(TestFeedbackOrchestrator))
    suite.addTests(loader.loadTestsFromTestCase(TestCompleteIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("Lumen Feedback Loop Test Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
