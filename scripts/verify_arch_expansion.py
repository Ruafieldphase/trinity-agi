import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.arch_fsd_strategy import ArchFSDStrategy
import logging

def test_material_awareness():
    logging.basicConfig(level=logging.INFO)
    strategy = ArchFSDStrategy(constant_c=250.0)
    
    print("--- Testing Material Awareness ---")
    
    # Test case 1: RC Wall
    action_rc = {"type": "extrude", "text": "RC Wall", "depth": None}
    refined_rc = strategy.apply_strategy(action_rc, {})
    print(f"RC Wall: {refined_rc['depth']}mm (Reason: {refined_rc.get('reason')})")
    assert refined_rc["depth"] == 200.0
    
    # Test case 2: Glass Partition
    action_glass = {"type": "shell", "text": "Glass Partition", "depth": None}
    refined_glass = strategy.apply_strategy(action_glass, {})
    print(f"Glass Partition: {refined_glass['depth']}mm (Reason: {refined_glass.get('reason')})")
    assert refined_glass["depth"] == 12.0
    
    # Test case 3: Unknown material (should default to Constant C)
    action_unknown = {"type": "extrude", "text": "Floating Wall", "depth": None}
    refined_unknown = strategy.apply_strategy(action_unknown, {})
    print(f"Unknown Wall: {refined_unknown['depth']}mm (Default Constant C)")
    assert refined_unknown["depth"] == 250.0
    
    print("\n--- Testing Adaptive Folding Placeholder ---")
    matrix = strategy.calculate_adaptive_fold([], [])
    print(f"Adaptive Fold Matrix shape: {matrix.shape}")
    assert matrix.shape == (4, 4)
    
    print("\nVerification SUCCESSFUL!")

if __name__ == "__main__":
    test_material_awareness()
