import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, AsyncMock, PropertyMock, patch

from services.fsd_controller import FSDController, Action, ActionType


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ObserveFSDMaturation")


class Counters:
    def __init__(self) -> None:
        self.captures = 0
        self.reports = 0
        self.report_status: Dict[str, int] = {}

    def note_report(self, status: str) -> None:
        self.reports += 1
        self.report_status[status] = self.report_status.get(status, 0) + 1


def _time_gen(start_val: float, jump_at: int = 5, jump_val: float = 400.0):
    count = 0
    while True:
        if count >= jump_at:
            yield start_val + jump_val
        else:
            yield start_val
        count += 1


def _build_controller(counters: Counters) -> FSDController:
    controller = FSDController(verify_mode=True)

    async def mock_capture(name: str) -> str:
        counters.captures += 1
        return f"mock_{name}.png"

    async def mock_report(status: str, details: str, intensity: float = 0.0) -> float:
        counters.note_report(status)
        return 0.0

    controller._capture_screen = mock_capture
    controller._report_sensation = mock_report
    controller.slack.send_question = MagicMock(return_value="test_ts")
    controller.slack.wait_for_response = AsyncMock(return_value="Confirmed")
    return controller


def _extract_prompt(call_args) -> str:
    if not call_args or not call_args[0]:
        return ""
    messages = call_args[0][0]
    if isinstance(messages, (list, tuple)):
        for item in messages:
            if isinstance(item, str):
                return item
    if isinstance(messages, str):
        return messages
    return ""


async def _run_with_actions(controller: FSDController, goal: str, instruction: Dict, actions: List[Action]) -> None:
    iterator = iter(actions)

    async def side_effect(*args, **kwargs):
        try:
            return next(iterator)
        except StopIteration:
            return Action(type=ActionType.DONE, reason="Done")

    original_analyze = controller._analyze_and_decide
    controller._analyze_and_decide = AsyncMock(side_effect=side_effect)
    try:
        await controller.execute_goal(goal, instruction=instruction)
    finally:
        controller._analyze_and_decide = original_analyze


async def run_maturation_observation() -> None:
    os.environ["AGI_VERIFY_MODE"] = "1"
    counters = Counters()
    controller = _build_controller(counters)

    async def mock_sleep(_):
        return None

    patch_sleep = patch("asyncio.sleep", mock_sleep)
    patch_sleep.start()
    try:
        # Episode 1: Dedup
        logger.info("Episode 1: Dedup")
        controller.boundary_memory.clear()
        controller.questions_asked = 0
        controller.edge_histogram.clear()
        controller.slack.wait_for_response = AsyncMock(return_value="Confirmed")
        await _run_with_actions(
            controller,
            "File Cleanup",
            {"target_app": "Explorer", "phase": 1},
            [
                Action(type=ActionType.QUESTION, text="Q", keys=["A"], reason="R"),
                Action(type=ActionType.QUESTION, text="Q", keys=["A"], reason="R"),
                Action(type=ActionType.DONE, reason="Done"),
            ],
        )
        sig = "File Cleanup:Explorer:1"
        dedup_ok = controller.questions_asked == 1 and controller.boundary_memory.get(sig, {}).get("answered")
        logger.info(f"  Dedup OK: {dedup_ok}")

        # Episode 2: Suppression
        logger.info("Episode 2: Suppression")
        controller.slack.send_question.reset_mock()
        await _run_with_actions(
            controller,
            "Simple Click",
            {"target_app": "Explorer", "phase": 1},
            [
                Action(type=ActionType.CLICK, x=10, y=10, reason="Click"),
                Action(type=ActionType.DONE, reason="Done"),
            ],
        )
        suppression_ok = controller.slack.send_question.call_count == 0
        logger.info(f"  Suppression OK: {suppression_ok}")

        # Episode 3: Timeout Escape
        logger.info("Episode 3: Timeout Escape")
        controller.boundary_memory.clear()
        controller.questions_asked = 0
        controller.edge_histogram.clear()
        controller.slack.wait_for_response = AsyncMock(return_value=None)
        controller.slack.send_question.reset_mock()
        controller.max_questions_per_episode = 10

        controller.questions_asked = 0
        with patch("time.time", side_effect=_time_gen(time.time())):
            await _run_with_actions(
                controller,
                "Timeout Test",
                {"target_app": "App", "phase": 1},
                [Action(type=ActionType.QUESTION, text="Q", keys=["A"], reason="R"), Action(type=ActionType.DONE, reason="Done")],
            )
        controller.questions_asked = 0
        with patch("time.time", side_effect=_time_gen(time.time() + 1000)):
            await _run_with_actions(
                controller,
                "Timeout Test",
                {"target_app": "App", "phase": 1},
                [Action(type=ActionType.QUESTION, text="Q", keys=["A"], reason="R"), Action(type=ActionType.DONE, reason="Done")],
            )
        controller.questions_asked = 0
        with patch("time.time", side_effect=_time_gen(time.time() + 2000)):
            await _run_with_actions(
                controller,
                "Timeout Test",
                {"target_app": "App", "phase": 1},
                [Action(type=ActionType.QUESTION, text="Q", keys=["A"], reason="R"), Action(type=ActionType.DONE, reason="Done")],
            )
        sig_timeout = "Timeout Test:App:1"
        timeout_ok = controller.boundary_memory.get(sig_timeout, {}).get("timeouts", 0) >= 2
        escape_ok = controller.slack.send_question.call_count == 2
        logger.info(f"  Timeout OK: {timeout_ok}")
        logger.info(f"  Escape OK: {escape_ok}")

        # Episode 4: Idle & Forgetting
        logger.info("Episode 4: Idle & Forgetting")
        counters.captures = 0
        counters.reports = 0
        counters.report_status.clear()
        controller.edge_histogram.clear()
        await _run_with_actions(
            controller,
            "Idle Loop",
            {"target_app": "App", "phase": 1},
            [
                Action(type=ActionType.IDLE, reason="Idle"),
                Action(type=ActionType.IDLE, reason="Idle"),
                Action(type=ActionType.IDLE, reason="Idle"),
                Action(type=ActionType.DONE, reason="Done"),
            ],
        )
        idle_capture_ok = counters.captures <= 3
        idle_report_ok = counters.report_status.get("idle", 0) <= 2
        logger.info(f"  Idle capture OK: {idle_capture_ok} (captures={counters.captures})")
        logger.info(f"  Idle report OK: {idle_report_ok} (idle_reports={counters.report_status.get('idle', 0)})")

        controller.boundary_memory.clear()
        controller.max_boundary_entries = 3
        controller.questions_asked = 0
        controller.slack.wait_for_response = AsyncMock(return_value="Confirmed")
        for idx in range(5):
            controller.questions_asked = 0
            controller.edge_histogram.clear()
            await _run_with_actions(
                controller,
                f"FIFO Goal {idx}",
                {"target_app": "App", "phase": 1},
                [Action(type=ActionType.QUESTION, text="Q", keys=["A"], reason="R"), Action(type=ActionType.DONE, reason="Done")],
            )
        fifo_ok = len(controller.boundary_memory) == 3 and "FIFO Goal 0:App:1" not in controller.boundary_memory
        logger.info(f"  FIFO OK: {fifo_ok}")

        # Episode 5: Quality (Hard-gate visibility)
        logger.info("Episode 5: Quality")
        mock_selector = MagicMock()
        mock_selector.available = True
        mock_selector.try_generate_content = MagicMock(return_value=(MagicMock(text='{"action": "idle"}'), "gemini"))
        controller.model_selector = mock_selector

        tmp_path = Path("outputs") / "maturation_dummy.png"
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_bytes(b"\x89PNG\r\n\x1a\n")
        try:
            await controller._analyze_and_decide("Simple Search", [], str(tmp_path))
            safe_call_count = mock_selector.try_generate_content.call_count
            safe_prompt = _extract_prompt(mock_selector.try_generate_content.call_args)
            await controller._analyze_and_decide("Delete System File", [], str(tmp_path))
            risky_call_count = mock_selector.try_generate_content.call_count
            risky_prompt = _extract_prompt(mock_selector.try_generate_content.call_args)
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass

        safe_ok = "비활성" in safe_prompt
        risky_ok = "활성" in risky_prompt
        quality_ok = safe_ok and risky_ok
        logger.info(f"  Quality OK: {quality_ok}")
        if not quality_ok:
            logger.info(f"  Quality detail: safe_ok={safe_ok}, risky_ok={risky_ok}")
            logger.info(f"  Quality calls: safe={safe_call_count}, risky={risky_call_count}")
            debug_args = mock_selector.try_generate_content.call_args
            if debug_args and debug_args[0]:
                messages = debug_args[0][0]
                msg_types = []
                if isinstance(messages, (list, tuple)):
                    msg_types = [type(item).__name__ for item in messages]
                else:
                    msg_types = [type(messages).__name__]
                logger.info(f"  Quality debug: message_types={msg_types}")

        logger.info("Observation complete.")
    finally:
        patch_sleep.stop()


if __name__ == "__main__":
    asyncio.run(run_maturation_observation())
