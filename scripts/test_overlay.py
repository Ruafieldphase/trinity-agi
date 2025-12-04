import time
from motor_cortex import MotorCortex

def test_overlay():
    print("🎨 Testing Visual Overlay...")
    motor = MotorCortex(visual_feedback=True)
    
    print("   Color: Cyan (Pulse)")
    motor.set_overlay_color("#00FFFF")
    time.sleep(2)
    
    print("   Color: Red (Stop)")
    motor.set_overlay_color("#FF0000")
    time.sleep(2)
    
    print("   Color: Blue (Rest)")
    motor.set_overlay_color("#0000FF")
    time.sleep(2)
    
    print("✅ Overlay Test Complete.")

if __name__ == "__main__":
    test_overlay()
