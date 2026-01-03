#!/usr/bin/env python3
"""
Listen for music daemon rhythm events and create/update goals accordingly.

This PoC subscribes to the EventBus topic `rhythm_pulse` and when it sees
low-tempo or restorative brainwave targets (e.g., delta/theta), it creates a
goal using `dream_to_goal.py` with a default priority mapping.

It runs for a short time by default (poll_loop_count) and then exits — good for
CI or manual test runs.
"""
import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

import sys
from pathlib import Path
from workspace_root import get_workspace_root

# Ensure workspace packages can be imported
workspace_root = get_workspace_root()
sys.path.insert(0, str(workspace_root))
sys.path.insert(0, str(workspace_root / 'fdo_agi_repo'))

from fdo_agi_repo.utils.event_bus import EventBus

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def run_cmd(cmd: str):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if p.returncode != 0:
        logger.error(p.stderr)
        raise SystemExit(p.returncode)
    return p.stdout


def create_goal_from_rhythm(topic, event):
    data = event.get("data", {})
    brainwave = data.get("brainwave_target") or data.get("brainwave") or data.get("brainwave_target")
    tempo = data.get("tempo_bpm") or data.get("tempo") or 60

    # Rule: If deep-rest (delta) or creative (theta) or slow tempo, create restorative goal
    if brainwave in ("delta", "theta") or int(float(tempo)) < 60:
        title = f"Music-triggered Goal: Rhythmic Reset ({brainwave} @ {tempo}BPM)"
        desc = f"Auto-generated from rhythm event: brainwave={brainwave}, tempo={tempo}."
        priority = 11 if brainwave == "theta" else 12

        cmd = f'py -3 scripts/dream_to_goal.py --title "{title}" --priority {priority} --days 1 --description "{desc}" --start'
        logger.info(f"Creating goal because of rhythm: {brainwave} {tempo} -> {title}")

        # Use GoalTracker directly (avoid duplicate-problem from CLI) and start the goal
        try:
            from fdo_agi_repo.scripts.goal_tracker import GoalTracker
            tracker = GoalTracker()
            # Rate-limit: do not create duplicate goals with same title within short window
            now = __import__('datetime').datetime.now()
            window_minutes = 5
            goals = tracker.list_goals()
            normalized = title.strip().lower()
            recent = [g for g in goals if g.get('title','').strip().lower() == normalized]
            if recent:
                # If any recent goal is in proposed/in_progress or created within window, skip
                for g in recent:
                    created_at = g.get('created_at')
                    if g.get('status') in ('proposed','in_progress'):
                        logger.info(f"⚠️ Skipping creation: existing active goal {g.get('id')} status={g.get('status')}")
                        return
                    if created_at:
                        created = __import__('datetime').datetime.fromisoformat(created_at)
                        if (now - created).total_seconds() < window_minutes * 60:
                            logger.info(f"⚠️ Skipping creation: recent goal {g.get('id')} created {created_at}")
                            return

            goal_id = tracker.add_goal(title, priority, 1.0, desc)
            if goal_id:
                tracker.start_goal(goal_id)
        except Exception as e:
            logger.error(f"Failed to add/start goal directly: {e}")
            # Fall back to CLI call
            out = run_cmd(cmd)
            logger.info(out)
    else:
        logger.info(f"No goal rule matched for rhythm: {brainwave}@{tempo}BPM")


def main():
    parser = argparse.ArgumentParser(description="PoC: Music → Goal Trigger")
    parser.add_argument("--loops", type=int, default=5, help="How many poll loops to run")
    parser.add_argument("--interval", type=int, default=2, help="Polling interval (s)")
    args = parser.parse_args()

    bus = EventBus()

    # Subscribe to 'rhythm_pulse'
    def on_pulse(event):
        logger.info("Pulse event received: %s", event.get("data"))
        create_goal_from_rhythm("rhythm_pulse", event)

    bus.subscribe("rhythm_pulse", on_pulse)

    logger.info("🔭 Listening to music rhythm pulses (PoC). Polling...")

    for i in range(args.loops):
        results = bus.poll_all_subscribed()
        if results:
            logger.info("Polled events: %s", {k: len(v) for k, v in results.items()})
        time.sleep(args.interval)

    logger.info("🛑 PoC finished")


if __name__ == '__main__':
    main()
