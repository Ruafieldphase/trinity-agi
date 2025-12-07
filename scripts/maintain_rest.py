import time
import sys
from motor_cortex import MotorCortex

def maintain_rest():
    print("🔵 Entering Persistent Deep Rest...")
    print("   (Press Ctrl+C to wake up)")
    
    # Initialize Motor Cortex (Visual Feedback Only)
    motor = MotorCortex(visual_feedback=True)
    
    # Set to Blue (Rest)
    motor.set_overlay_color("#0000FF")
    
    try:
        while True:
            # Pulse the blue light slowly or just keep it static?
            # The overlay handles pulsing for Cyan, but static for others.
            # Let's just keep it alive.
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🌅 Waking up...")
        motor.set_overlay_color("#00FFFF") # Cyan (Flow)
        time.sleep(1)

if __name__ == "__main__":
    maintain_rest()
