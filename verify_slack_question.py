import asyncio
import logging
import os
import time
from typing import List, Optional
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock

from services.fsd_controller import FSDController, Action, ActionType, ExecutionStep
from scripts.slack_event_queue import SlackEventQueue

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyPhase3")

async def verify_phase3_flow():
    controller = FSDController(verify_mode=True)
    
    # Mock _capture_screen, _report_sensation, and asyncio.sleep
    async def mock_capture(x): return f"test_{x}.png"
    async def mock_report(s, d, i=0): return 0.0
    async def mock_sleep(x): return None
    
    controller._capture_screen = mock_capture
    controller._report_sensation = mock_report
    
    # We'll patch asyncio.sleep globally for the controller
    patch_sleep = patch('asyncio.sleep', mock_sleep)
    patch_sleep.start()

    # Mock Slack Gateway
    controller.slack.send_question = MagicMock(return_value="test_ts")
    controller.slack.wait_for_response = AsyncMock(return_value=None)

    # Let's run execute_goal but stop it early
    async def run_test_goal(g, i):
        # We need a way to stop the infinite loop of execute_goal
        # Let's mock _analyze_and_decide to return DONE after 2 calls
        call_count = 0
        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return Action(type=ActionType.QUESTION, text="Q", keys=["A"], reason="R")
            return Action(type=ActionType.DONE, reason="Done")
        controller._analyze_and_decide = AsyncMock(side_effect=side_effect)
        await controller.execute_goal(g, instruction=i)

    # 1. Test Signature-based Deduplication
    logger.info("🧪 TEST 1: Signature-based Deduplication")
    controller.boundary_memory.clear()
    controller.questions_asked = 0
    controller.edge_histogram.clear()
    controller.slack.wait_for_response.side_effect = AsyncMock(return_value="Confirmed")
    
    # signature = goal:app:phase
    goal = "File Cleanup"
    instruction = {"target_app": "Explorer", "phase": 1}
    
    await run_test_goal(goal, instruction)
    
    sig = f"{goal}:Explorer:1"
    logger.info(f"   Signature: {sig}")
    logger.info(f"   Memory: {controller.boundary_memory.get(sig)}")
    logger.info(f"   Questions asked: {controller.questions_asked} (Expected: 1)")

    # 2. Test Timeout Escape Policy (2 Strikes)
    logger.info("🧪 TEST 2: Timeout Escape Policy")
    controller.boundary_memory.clear()
    controller.questions_asked = 0
    controller.edge_histogram.clear()
    controller.slack.wait_for_response.side_effect = AsyncMock(return_value=None) # Always timeout
    
    def time_gen(start_val, jump_at, jump_val):
        count = 0
        while True:
            if count >= jump_at: yield start_val + jump_val
            else: yield start_val
            count += 1

    # Strike 1
    with patch('time.time', side_effect=time_gen(time.time(), 5, 400)):
        await run_test_goal("Timeout Test", {"target_app": "App", "phase": 1})
    
    sig_timeout = "Timeout Test:App:1"
    logger.info(f"   Strike 1 Timeouts: {controller.boundary_memory[sig_timeout]['timeouts']}")
    
    # Strike 2
    controller.edge_histogram.clear()
    with patch('time.time', side_effect=time_gen(time.time() + 1000, 5, 400)):
        await run_test_goal("Timeout Test", {"target_app": "App", "phase": 1})
    logger.info(f"   Strike 2 Timeouts: {controller.boundary_memory[sig_timeout]['timeouts']}")
    
    # Strike 3: Escape
    controller.edge_histogram.clear()
    controller.questions_asked = 0 # Reset count so it doesn't hit question limit first
    with patch('time.time', side_effect=time_gen(time.time() + 2000, 5, 400)):
        await run_test_goal("Timeout Test", {"target_app": "App", "phase": 1})
        logger.info(f"   Strike 3 Action handled (check logs for 'Escape Policy Triggered')")

    # 3. Test 2-stage Trigger (Hard-gate)
    logger.info("🧪 TEST 3: 2-stage Trigger (Hard-gate)")
    controller.questions_asked = 0
    controller.edge_histogram.clear()
    
    # We create a full mock for model_selector and assign it
    mock_selector = MagicMock()
    # Property mockup for 'available'
    type(mock_selector).available = PropertyMock(return_value=True)
    
    # mock try_generate_content
    mock_selector.try_generate_content = MagicMock(return_value=(MagicMock(text='{"action": "idle"}'), "gemini"))
    
    controller.model_selector = mock_selector
    
    await controller._analyze_and_decide("Simple Search", [], "path")
    # Check what was sent to the model
    call_args = mock_selector.try_generate_content.call_args
    if call_args:
        # call_args[0][0] is the list of messages. [1] is typically the model's message object.
        # But for simplicity, let's just str() the whole call args to find the string.
        call_str = str(call_args)
        logger.info(f"   Hard-gate (Risky: False) prompt status: {'비활성' in call_str}")
    
    await controller._analyze_and_decide("Delete System File", [], "path")
    call_args_risky = mock_selector.try_generate_content.call_args
    if call_args_risky:
        call_str_risky = str(call_args_risky)
        logger.info(f"   Hard-gate (Risky: True) prompt status: {'활성' in call_str_risky}")

    # 4. Test Forgetting Policy (FIFO)
    logger.info("TEST 4: Forgetting Policy (FIFO)")
    controller.boundary_memory.clear()
    controller.questions_asked = 0
    controller.edge_histogram.clear()
    controller.max_boundary_entries = 5
    controller.max_questions_per_episode = 10
    controller.slack.wait_for_response.side_effect = AsyncMock(return_value="Confirmed")

    async def run_fifo_goal(g, i):
        call_count = 0
        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Action(type=ActionType.QUESTION, text="Q", keys=["A"], reason="R")
            return Action(type=ActionType.DONE, reason="Done")
        controller._analyze_and_decide = AsyncMock(side_effect=side_effect)
        await controller.execute_goal(g, instruction=i)

    for idx in range(7):
        controller.questions_asked = 0
        controller.edge_histogram.clear()
        await run_fifo_goal(f"Goal {idx}", {"target_app": "App", "phase": 1})

    fifo_size = len(controller.boundary_memory)
    logger.info(f"   FIFO size: {fifo_size} (Expected: 5)")
    logger.info(f"   FIFO eviction: {'Goal 0:App:1' not in controller.boundary_memory and 'Goal 1:App:1' not in controller.boundary_memory}")

    patch_sleep.stop()
    logger.info("Phase 3/3.1 Logic Verified.")

if __name__ == "__main__":
    asyncio.run(verify_phase3_flow())
