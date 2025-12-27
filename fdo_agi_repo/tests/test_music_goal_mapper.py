from fdo_agi_repo.utils.music_goal_mapper import map_rhythm_event_to_goal, ensure_goal_from_event
from fdo_agi_repo.scripts.goal_tracker import GoalTracker


def test_map_delta_event():
    ev = {"data": {"brainwave_target": "delta", "tempo_bpm": 50}}
    spec = map_rhythm_event_to_goal(ev)
    assert spec is not None
    assert "Rhythmic Reset" in spec["title"]


def test_ensure_goal_rate_limit():
    tracker = GoalTracker()
    ev = {"data": {"brainwave_target": "theta", "tempo_bpm": 58}}
    gid = ensure_goal_from_event(ev, window_minutes=5)
    assert gid is not None

    # calling again should return the same id or at least not create more
    gid2 = ensure_goal_from_event(ev, window_minutes=5)
    assert gid2 is not None
    assert gid2 == gid


def test_music_daemon_auto_goal_once(monkeypatch):
    # Run a minimal instantiation of MusicDaemon with auto_goal enabled
    from pathlib import Path
<<<<<<< HEAD
    from scripts.music_daemon import MusicDaemon
=======
from scripts.music_daemon import MusicDaemon
>>>>>>> origin/main

    class DummyEventBus:
        def publish(self, topic, data):
            # simulate immediate rhythm pulse usage
            pass

    daemon = MusicDaemon(workspace_root=Path('.'), interval=1, flow_threshold=0.3)
    daemon.event_bus = DummyEventBus()
    daemon.auto_goal = True

    # Simulate a rhythm pulse being published
    from fdo_agi_repo.utils.music_goal_mapper import ensure_goal_from_event
    ensure_goal_from_event({'data': {'brainwave_target': 'theta', 'tempo_bpm': 58}})
    # Check goal existence
    tracker = GoalTracker()
    g = [x for x in tracker.list_goals() if 'theta' in x['title']]
    assert len(g) >= 1
