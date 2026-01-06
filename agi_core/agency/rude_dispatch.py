#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rude Dispatcher
===============
Allows Rude (the Mind) to send mission requests to Shion (the Body).
Missions are dropped into Shion's inbox for the MissionCoordinator to handle.
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Workspace discovery
WORKSPACE = Path(__file__).resolve().parents[2]
INBOX = WORKSPACE / "inputs" / "agent_inbox" / "antigravity_shion"

class RudeDispatcher:
    def __init__(self, agent_id: str = "antigravity_rude"):
        self.agent_id = agent_id
        self.inbox_path = INBOX
        self.inbox_path.mkdir(parents=True, exist_ok=True)

    def send_mission(self, task_name: str, actions: List[Dict[str, Any]], priority: int = 2) -> Optional[Path]:
        """
        Send a mission to Shion's inbox.
        :param task_name: Name of the mission
        :param actions: List of action dictionaries
        :param priority: Mission priority (1-5, lower is higher)
        :return: Path to the created mission file
        """
        timestamp = int(time.time())
        filename = f"MISSION_{timestamp}_{task_name.replace(' ', '_')}.json"
        dest_path = self.inbox_path / filename

        mission = {
            "mission_id": f"mission_{timestamp}",
            "origin": self.agent_id,
            "target": "antigravity_shion",
            "name": task_name,
            "priority": priority,
            "timestamp": timestamp,
            "actions": actions
        }

        try:
            with open(dest_path, "w", encoding="utf-8") as f:
                json.dump(mission, f, indent=2, ensure_ascii=False)
            print(f"✓ Mission '{task_name}' dispatched to Shion's inbox.")
            return dest_path
        except Exception as e:
            print(f"✗ Failed to dispatch mission: {e}")
            return None

def quick_dispatch(task_name: str, actions: List[Dict[str, Any]]):
    """Convenience function for quick mission dispatch."""
    dispatcher = RudeDispatcher()
    return dispatcher.send_mission(task_name, actions)

if __name__ == "__main__":
    # Example usage
    example_actions = [
        {"type": "ping", "message": "Initial connection from Rude"},
        {"type": "log", "content": "Rude is now orchestrating the body."}
    ]
    quick_dispatch("Identity Synchronization", example_actions)
