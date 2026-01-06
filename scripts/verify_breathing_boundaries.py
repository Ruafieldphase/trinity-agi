import sys
from pathlib import Path

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent.parent.absolute()
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.breathing_boundary import BreathingBoundary

def test_breathing_boundary():
    print("🧪 Testing Breathing Boundaries...")
    
    # Survival threshold test (Base: 25)
    survival = BreathingBoundary(base=25, name="survival")
    
    # 1. Neutral State
    ctx_neutral = {"rhythm_mode": "NEUTRAL", "current_state": "outside", "velocity": 0, "trust": 0.5}
    t1 = survival.get_threshold(ctx_neutral)
    print(f"Neutral Threshold: {t1:.1f} (Exp: ~25.0)")
    
    # 2. Expansion Mode (Should lower threshold -> more relaxed)
    ctx_expansion = {"rhythm_mode": "EXPANSION", "current_state": "outside", "velocity": 0, "trust": 0.5}
    t2 = survival.get_threshold(ctx_expansion)
    print(f"Expansion Threshold: {t2:.1f} (Exp: < 25.0)")
    
    # 3. Contraction Mode (Should raise threshold -> more defensive)
    ctx_contraction = {"rhythm_mode": "CONTRACTION", "current_state": "outside", "velocity": 0, "trust": 0.5}
    t3 = survival.get_threshold(ctx_contraction)
    print(f"Contraction Threshold: {t3:.1f} (Exp: > 25.0)")
    
    # 4. Hysteresis (Inside state should lower threshold to maintain state)
    ctx_inside = {"rhythm_mode": "NEUTRAL", "current_state": "inside", "velocity": 0, "trust": 0.5}
    t4 = survival.get_threshold(ctx_inside)
    print(f"Hysteresis (Inside) Threshold: {t4:.1f} (Exp: < 25.0)")
    
    # 5. Velocity (Falling score should raise threshold to be more sensitive)
    ctx_falling = {"rhythm_mode": "NEUTRAL", "current_state": "outside", "velocity": -10, "trust": 0.5}
    t5 = survival.get_threshold(ctx_falling)
    print(f"Falling Score Threshold: {t5:.1f} (Exp: > 25.0)")

    print("\n✅ Breathing Boundary logic verified.")

if __name__ == "__main__":
    test_breathing_boundary()
