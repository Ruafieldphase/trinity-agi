#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hippocampus Quantum Observation Test
Tests wave-particle duality in memory formation
"""

import sys
from pathlib import Path
from workspace_root import get_workspace_root
sys.path.insert(0, str(get_workspace_root() / "fdo_agi_repo"))

from copilot.hippocampus import Hippocampus
from datetime import datetime, timedelta
import json

def main():
    print("=" * 60)
    print("🌊⚛️ Hippocampus Quantum Observation Test")
    print("=" * 60)
    print()
    
    # Initialize hippocampus
    print("📍 Initializing hippocampus...")
    h = Hippocampus()
    
    # Simulate a sequence of related events (wave pattern)
    print("\n🌊 Creating wave-like event sequence...")
    base_time = datetime.now() - timedelta(hours=1)
    
    events = [
        {
            "event": "user_query",
            "query": "Tell me about quantum computing",
            "timestamp": (base_time + timedelta(minutes=0)).isoformat(),
            "confidence": 0.9
        },
        {
            "event": "llm_response",
            "content": "Quantum computing uses qubits...",
            "timestamp": (base_time + timedelta(minutes=1)).isoformat(),
            "latency_ms": 450
        },
        {
            "event": "user_query",
            "query": "What is quantum entanglement?",
            "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
            "confidence": 0.95
        },
        {
            "event": "llm_response",
            "content": "Quantum entanglement is a phenomenon...",
            "timestamp": (base_time + timedelta(minutes=6)).isoformat(),
            "latency_ms": 380
        },
        {
            "event": "user_query",
            "query": "Explain superposition",
            "timestamp": (base_time + timedelta(minutes=10)).isoformat(),
            "confidence": 0.88
        },
    ]
    
    # Store events
    for event in events:
        h.store_event(event)
    
    print(f"✅ Stored {len(events)} events")
    
    # Test wave detection
    print("\n🌊 Testing wave pattern detection...")
    wave_query = {
        "topic": "quantum",
        "time_window_minutes": 30
    }
    
    wave_result = h.observe_wave(wave_query)
    print(f"   Wave confidence: {wave_result.get('confidence', 0):.2f}")
    print(f"   Pattern: {wave_result.get('pattern_type', 'none')}")
    print(f"   Events in wave: {len(wave_result.get('events', []))}")
    
    # Test particle detection (specific event)
    print("\n⚛️ Testing particle detection...")
    particle_query = {
        "event_type": "user_query",
        "keywords": ["quantum", "entanglement"]
    }
    
    particle_result = h.observe_particle(particle_query)
    print(f"   Found particles: {len(particle_result.get('events', []))}")
    for idx, event in enumerate(particle_result.get('events', [])[:3], 1):
        print(f"   {idx}. {event.get('event', 'unknown')} - {event.get('query', 'N/A')[:50]}")
    
    # Test unified observation (wave-particle duality)
    print("\n🌊⚛️ Testing unified observation (wave-particle duality)...")
    unified_query = {
        "topic": "quantum",
        "min_confidence": 0.8,
        "time_window_minutes": 30
    }
    
    unified_result = h.observe(unified_query)
    print(f"   Observer effect detected: {unified_result.get('observer_effect', False)}")
    print(f"   Wave component confidence: {unified_result.get('wave_confidence', 0):.2f}")
    print(f"   Particle count: {unified_result.get('particle_count', 0)}")
    print(f"   Coherence: {unified_result.get('coherence', 0):.2f}")
    print(f"   Interpretation: {unified_result.get('interpretation', 'unknown')}")
    
    # Show memory consolidation status
    print("\n💾 Memory consolidation status...")
    stm_count = len(h.short_term_memory)
    ltm_count = sum(1 for _ in h.long_term_memory.iterdir() if _.suffix == '.json')
    print(f"   Short-term memory: {stm_count} events")
    print(f"   Long-term memory: {ltm_count} files")
    
    # Test retrieval
    print("\n🔍 Testing contextual retrieval...")
    context = h.get_context({"topic": "quantum", "limit": 3})
    print(f"   Retrieved {len(context.get('relevant_memories', []))} memories")
    
    print("\n" + "=" * 60)
    print("✅ Quantum observation test complete!")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
