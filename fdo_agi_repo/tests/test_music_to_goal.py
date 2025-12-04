import time
from fdo_agi_repo.scripts.goal_tracker import GoalTracker
from scripts.music_to_goal import create_goal_from_rhythm


def test_music_to_goal_rate_limit():
    tracker = GoalTracker()
    # Use a unique title
    unique_title = f"Test Music Rule {int(time.time())}"

    # Make event: theta brainwave triggers goal creation
    event = {"data": {"brainwave_target": "theta", "tempo_bpm": 58}}

    # Create a small wrapper to use the same title
    create_goal_from_rhythm("rhythm_pulse", event)

    # Now find any in-progress goal that starts with our base title
    goals = [g for g in tracker.list_goals() if g['title'].startswith('Music-triggered Goal: Rhythmic Reset')]
    assert len(goals) >= 1

    # Now call again with same event - should not create a duplicate within short window
    before_count = len(goals)
    create_goal_from_rhythm("rhythm_pulse", event)
    goals_after = [g for g in tracker.list_goals() if g['title'].startswith('Music-triggered Goal: Rhythmic Reset')]
    assert len(goals_after) == before_count
