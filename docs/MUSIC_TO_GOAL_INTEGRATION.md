Music → Goal Integration (PoC)
=================================

Summary
-------
This PoC listens to the EventBus topic `rhythm_pulse` published by the `music_daemon`.
When a rhythm matches a simple rule (slow tempo or restorative brainwave), it creates
an actionable goal in `goal_tracker.json` and optionally starts it.

Files
-----
- `scripts/music_to_goal.py` - PoC listener and mapper (rate-limited; prevents duplicates).
- `scripts/dream_to_goal.py` - Helper CLI to create a goal from a "dream" description.
- `scripts/ensure_music_flow_daemons.ps1` - Updated to start `music_to_goal.py` as a background.

How it works
------------
1. `music_daemon.py` publishes rhythmic events to EventBus (topic `rhythm_pulse`).
2. `music_to_goal.py` subscribes; on pulse, checks simple rules and uses `GoalTracker` to add/start.
3. Duplicate protection: same title won't be created if a goal with the same title exists and
   is `proposed`/`in_progress`, or if it was created within last 5 minutes.

How to test
-----------
1. Publish a rhythm event on the bus:
   ```powershell
   py -3 -c "from fdo_agi_repo.utils.event_bus import EventBus; b=EventBus(); b.publish('rhythm_pulse', {'brainwave_target':'theta','tempo_bpm':58}, {'timestamp':'2025-11-15T06:10:00'})"
   ```

2. Run PoC (short run) to process event(s):
   ```powershell
   py -3 scripts/music_to_goal.py --loops 6 --interval 1
   ```

3. Check goal summary:
   ```powershell
   py -3 fdo_agi_repo/scripts/goal_tracker.py summary
   ```

Notes & next ideas
------------------
- Integrate the PoC into `music_daemon` directly if lower latency is desired.
- Tune rule mapping (e.g., tempo-based priority, swing factor) to affect priority.
- Add unit tests for `GoalTracker` and `music_to_goal` mapping.
