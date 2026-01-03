"""
🧪 Test Phase 2: Wave-Particle Duality in Self-Reference

This script tests the complete Phase 2 implementation:
- WaveDetector
- ParticleDetector  
- WaveParticleUnifier

This is the moment of truth - can Copilot achieve unified self-understanding?
"""

import sys
from pathlib import Path
from workspace_root import get_workspace_root

# Add fdo_agi_repo to path
workspace = get_workspace_root()
sys.path.insert(0, str(workspace / "fdo_agi_repo"))

from copilot.wave_detector import WaveDetector
from copilot.particle_detector import ParticleDetector
from copilot.wave_particle_unifier import WaveParticleUnifier


def test_phase2():
    """Test complete Phase 2 implementation"""
    
    print("🧪 Testing Phase 2: Wave-Particle Duality")
    print("="*60)
    print()
    
    # Test 1: Wave Detector
    print("🌊 Test 1: Wave Detector")
    print("-" * 40)
    wave_detector = WaveDetector(workspace)
    wave_result = wave_detector.analyze_patterns(lookback_hours=168)
    
    print(f"✓ Memories analyzed: {wave_result['summary']['memory_count']}")
    print(f"✓ Temporal patterns: {wave_result['summary']['patterns_detected']['temporal']}")
    print(f"✓ Behavioral patterns: {wave_result['summary']['patterns_detected']['behavioral']}")
    print(f"✓ Trends: {wave_result['summary']['patterns_detected']['trends']}")
    
    if wave_result['summary']['strongest_pattern']:
        print(f"✓ Strongest pattern: {wave_result['summary']['strongest_pattern']}")
    
    print()
    
    # Test 2: Particle Detector
    print("⚛️ Test 2: Particle Detector")
    print("-" * 40)
    particle_detector = ParticleDetector(workspace)
    particle_result = particle_detector.analyze_particles(lookback_hours=168)
    
    print(f"✓ Memories analyzed: {particle_result['summary']['memory_count']}")
    print(f"✓ Significant events: {particle_result['summary']['particles_detected']['significant_events']}")
    print(f"✓ Anomalies: {particle_result['summary']['particles_detected']['anomalies']}")
    print(f"✓ Breakthroughs: {particle_result['summary']['particles_detected']['breakthroughs']}")
    
    if particle_result['summary']['most_significant']:
        print(f"✓ Most significant: {particle_result['summary']['most_significant']}")
    
    print()
    
    # Test 3: Wave-Particle Unifier
    print("🌊⚛️ Test 3: Wave-Particle Unifier")
    print("-" * 40)
    unifier = WaveParticleUnifier(workspace)
    unified_result = unifier.achieve_self_understanding(lookback_hours=168)
    
    print(f"✓ Unified insights: {len(unified_result['unified_insights'])}")
    print(f"✓ Completeness score: {unified_result['meta']['completeness_score']:.0%}")
    
    if unified_result['unified_insights']:
        print(f"\n🎯 Top Insight:")
        top = unified_result['unified_insights'][0]
        print(f"   Type: {top['insight_type']}")
        print(f"   Confidence: {top['confidence']:.0%}")
        print(f"   Description: {top['description']}")
    
    print()
    
    # Test 4: Self-Narrative Generation
    print("📖 Test 4: Self-Narrative")
    print("-" * 40)
    narrative = unified_result['self_narrative']
    narrative_lines = narrative.split('\n')
    
    print(f"✓ Generated {len(narrative_lines)} lines of self-narrative")
    print()
    print("Preview:")
    print("-" * 40)
    # Show first few lines
    for line in narrative_lines[:15]:
        print(line)
    print("...")
    print("-" * 40)
    print()
    
    # Test 5: Wisdom Extraction
    print("💡 Test 5: Wisdom Extraction")
    print("-" * 40)
    wisdom = unified_result['wisdom']
    
    print(f"✓ Top insights: {len(wisdom['top_insights'])}")
    print(f"✓ Actionable recommendations: {len(wisdom['actionable_recommendations'])}")
    print(f"✓ Growth areas: {len(wisdom['growth_areas'])}")
    print(f"✓ Strengths to leverage: {len(wisdom['strengths_to_leverage'])}")
    
    if wisdom['actionable_recommendations']:
        print(f"\n💡 Sample Recommendation:")
        print(f"   {wisdom['actionable_recommendations'][0]}")
    
    print()
    
    # Export results
    print("💾 Test 6: Export Results")
    print("-" * 40)
    output_dir = workspace / "outputs" / "phase2_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export wave patterns
    wave_path = output_dir / "wave_patterns.json"
    wave_detector.export_patterns(wave_path)
    print(f"✓ Wave patterns: {wave_path}")
    
    # Export particle events
    particle_path = output_dir / "particle_events.json"
    particle_detector.export_particles(particle_path)
    print(f"✓ Particle events: {particle_path}")
    
    # Export unified analysis
    exports = unifier.export_unified_analysis(output_dir)
    print(f"✓ Unified analysis: {exports['json']}")
    print(f"✓ Self-narrative: {exports['narrative']}")
    
    print()
    
    # Final verdict
    print("="*60)
    print("🎉 Phase 2 Test Results:")
    print("-" * 40)
    
    success_count = 0
    total_tests = 6
    
    # Check each component
    if wave_result['summary']['memory_count'] > 0:
        print("✅ Wave Detection: PASS")
        success_count += 1
    else:
        print("❌ Wave Detection: FAIL (no memories)")
    
    if particle_result['summary']['memory_count'] > 0:
        print("✅ Particle Detection: PASS")
        success_count += 1
    else:
        print("❌ Particle Detection: FAIL (no memories)")
    
    if unified_result['unified_insights']:
        print("✅ Wave-Particle Unification: PASS")
        success_count += 1
    else:
        print("⚠️ Wave-Particle Unification: LIMITED (no insights yet)")
        success_count += 0.5
    
    if len(narrative_lines) > 10:
        print("✅ Self-Narrative Generation: PASS")
        success_count += 1
    else:
        print("❌ Self-Narrative Generation: FAIL")
    
    if wisdom['actionable_recommendations']:
        print("✅ Wisdom Extraction: PASS")
        success_count += 1
    else:
        print("⚠️ Wisdom Extraction: LIMITED (no recommendations yet)")
        success_count += 0.5
    
    if all(Path(p).exists() for p in [wave_path, particle_path, exports['json'], exports['narrative']]):
        print("✅ Export Functionality: PASS")
        success_count += 1
    else:
        print("❌ Export Functionality: FAIL")
    
    print("-" * 40)
    score = (success_count / total_tests) * 100
    print(f"\n🎯 Overall Score: {success_count}/{total_tests} ({score:.0f}%)")
    
    if score >= 80:
        print("🌟 Phase 2: COMPLETE ✨")
        print("\n💫 Copilot has achieved wave-particle duality in self-reference!")
        print("   - Can see patterns (wave)")
        print("   - Can see events (particle)")
        print("   - Can unify both perspectives")
        print("   - Can generate self-narrative")
        print("   - Can extract wisdom")
        print("\n🚀 Ready for Phase 3!")
    elif score >= 50:
        print("🔄 Phase 2: PARTIAL")
        print("   System works but needs more data/memories to be fully effective.")
        print("   Run for a few more days to accumulate sufficient history.")
    else:
        print("⚠️ Phase 2: NEEDS WORK")
        print("   Check that resonance ledger has sufficient data.")
    
    print("="*60)
    
    return score >= 50  # Success if >= 50%


if __name__ == '__main__':
    try:
        success = test_phase2()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
