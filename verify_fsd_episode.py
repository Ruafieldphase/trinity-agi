import asyncio
import sys
from pathlib import Path

# Add workspace to path
WORKSPACE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKSPACE_ROOT))

# Mock some dependencies if needed or import them
try:
    from services.fsd_controller import FSDController, ActionType, Action
    from agi_core.internal_state import get_internal_state, update_internal_state
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def test_episode_logic():
    print("🚀 Testing FSD Episode Logic...")
    
    # Initialize Controller
    controller = FSDController(max_steps=10)
    
    # Mock _analyze_and_decide to return IDLE then DONE
    original_analyze = controller._analyze_and_decide
    
    # Test 1: IDLE Progression
    print("\n--- Test 1: IDLE Progression ---")
    step_calls = 0
    async def mock_analyze_idle(goal, steps, screenshot, instruction, panic):
        nonlocal step_calls
        step_calls += 1
        if step_calls < 3:
            return Action(type=ActionType.IDLE, reason="Rhythmic Wait")
        return Action(type=ActionType.DONE, reason="Goal Met")
    
    controller._analyze_and_decide = mock_analyze_idle
    result = await controller.execute_goal("Test Idle")
    print(f"Result Result: {result.success}, Message: {result.message}, Steps: {len(result.steps)}")
    for s in result.steps:
        print(f"  Step {s.step_number}: {s.action.type.value}")

    # Test 2: Energy Termination
    print("\n--- Test 2: Energy Termination ---")
    state = get_internal_state()
    state.energy = 0.1 # Force low energy
    
    result = await controller.execute_goal("Test Energy")
    print(f"Result Result (Expect success=True but stopped early): {result.success}, Message: {result.message}")
    
    # Reset Energy
    state.energy = 1.0
    
    # Test 3: Repetition Termination
    print("\n--- Test 3: Repetition Termination ---")
    controller.edge_histogram.clear()
    async def mock_analyze_repeat(goal, steps, screenshot, instruction, panic):
        return Action(type=ActionType.CLICK, x=100, y=100, reason="Clicking same button")
    
    controller._analyze_and_decide = mock_analyze_repeat
    result = await controller.execute_goal("Test Repeat")
    print(f"Result Result: {result.success}, Message: {result.message}")
    print(f"Final Histogram: {list(controller.edge_histogram)}")

if __name__ == "__main__":
    asyncio.run(test_episode_logic())
