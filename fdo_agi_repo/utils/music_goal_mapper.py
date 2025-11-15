from datetime import datetime
from typing import Dict, Optional

from fdo_agi_repo.scripts.goal_tracker import GoalTracker


def map_rhythm_event_to_goal(event: Dict) -> Optional[Dict]:
    """Map a rhythm event to a goal spec.

    Returns dict with keys: title, priority, days, description or None if no rule matches.
    """
    data = event.get("data", {})
    brainwave = data.get("brainwave_target") or data.get("brainwave")
    tempo = data.get("tempo_bpm") or data.get("tempo")

    if not brainwave and not tempo:
        return None

    # Normalize
    bw = (brainwave or "").lower()
    t = None
    try:
        if tempo is not None:
            t = int(float(tempo))
    except Exception:
        t = None

    # Rules: delta/theta are restorative -> create goal
    if bw in ("delta", "theta") or (t is not None and t < 60):
        if bw == "theta":
            priority = 11
        elif bw == "delta":
            priority = 12
        else:
            priority = 12

        title = f"Music-triggered Goal: Rhythmic Reset ({bw or 'tempo'} @ {t or '?'}BPM)"
        description = f"Auto-generated from rhythm event: brainwave={bw}, tempo={t}."
        return {
            "title": title,
            "priority": priority,
            "days": 1.0,
            "description": description,
            "source": "music_daemon",
            "trigger": "rhythm",
            "metadata": {
                "brainwave": bw,
                "tempo_bpm": t,
                "timestamp": event.get("timestamp")
            }
        }

    return None


def ensure_goal_from_event(event: Dict, window_minutes: int = 5) -> Optional[str]:
    """Ensure a goal exists for this event, with rate-limit.

    Returns the goal id if created or found; otherwise None.
    """
    spec = map_rhythm_event_to_goal(event)
    if not spec:
        return None

    tracker = GoalTracker()
    title = spec["title"].strip()
    now = datetime.now()

    # Find recent goals with same normalized title
    for g in tracker.list_goals():
        if g.get("title", "").strip().lower() == title.lower():
            # active
            if g.get("status") in ("proposed", "in_progress"):
                return g.get("id")
            # recent
            created_at = g.get("created_at")
            if created_at:
                created = datetime.fromisoformat(created_at)
                if (now - created).total_seconds() < window_minutes * 60:
                    return g.get("id")

    # Not found; create and start
    gid = tracker.add_goal(
        spec["title"], 
        spec["priority"], 
        spec["days"], 
        spec["description"],
        tags=[
            f"source:{spec.get('source', 'unknown')}",
            f"trigger:{spec.get('trigger', 'unknown')}",
            f"brainwave:{spec.get('metadata', {}).get('brainwave', 'unknown')}",
            f"tempo:{spec.get('metadata', {}).get('tempo_bpm', 0)}"
        ]
    )
    if gid:
        tracker.start_goal(gid)
    return gid
