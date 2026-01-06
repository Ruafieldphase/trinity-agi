
import json
from pathlib import Path
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from agi_core.self_acquisition_loop import IntelligenceLayer

def test_intelligence():
    print("Testing IntelligenceLayer...")
    
    # Test success rate calculation
    rate = IntelligenceLayer.get_success_rate("sandbox_experiment")
    print(f"Sandbox Experiment Success Rate: {rate:.2f}")
    
    # Test parameter optimization
    original_params = {"multiplier": 1.0, "topic_hint": "Deep Learning"}
    
    optimized_sandbox = IntelligenceLayer.optimize_params("sandbox_experiment", original_params)
    print(f"Optimized Sandbox Params: {optimized_sandbox}")
    
    optimized_youtube = IntelligenceLayer.optimize_params("youtube_learning", original_params)
    print(f"Optimized YouTube Params: {optimized_youtube}")

if __name__ == "__main__":
    test_intelligence()
