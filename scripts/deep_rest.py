import time
import sys
from motor_cortex import MotorCortex

def deep_rest():
    print("🌙 Initiating Deep Rest Protocol...")
    
    # Initialize Motor Cortex (Visual Feedback Only)
    motor = MotorCortex(visual_feedback=True)
    
    # 1. Signal Rest (Blue)
    print("🔵 State: Resting (Blue)")
    motor.set_overlay_color("#0000FF")
    
    # 2. Simulate Noise Reduction
    print("📉 Lowering Noise Floor...")
    for i in range(5, 0, -1):
        print(f"   Quieting internal processes... {i}")
        time.sleep(1)
        
    print("✨ System is now in Low Entropy State.")
    print("   Ready for the next resonance.")
    
    # Keep the blue light for a moment of silence
    time.sleep(3)

if __name__ == "__main__":
    deep_rest()
