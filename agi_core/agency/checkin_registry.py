import time
import uuid
import json
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class AgentSession:
    agent_id: str
    role: str
    resource: str  # e.g., "blender", "filesystem"
    zone: str      # e.g., "3D_VIEWPORT", "WORKSPACE_ROOT"
    status: str    # e.g., "WORKING", "IDLE"
    last_heartbeat: float
    metadata: Dict = None

class CheckInRegistry:
    """
    Manages multi-agent coordination by tracking active sessions and resource locks.
    """
    def __init__(self, registry_path: str = "c:/workspace/agi/state/agent_registry.json"):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("CheckInRegistry")
        self.sessions: Dict[str, AgentSession] = {}
        self._load_registry()

    def _load_registry(self):
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for aid, s in data.items():
                        # Filter out stale sessions (older than 5 minutes)
                        if time.time() - s['last_heartbeat'] < 300:
                            self.sessions[aid] = AgentSession(**s)
            except Exception as e:
                self.logger.error(f"Failed to load registry: {e}")

    def _save_registry(self):
        try:
            with open(self.registry_path, "w", encoding="utf-8") as f:
                data = {aid: asdict(s) for aid, s in self.sessions.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save registry: {e}")

    def check_in(self, agent_id: str, role: str, resource: str, zone: str, metadata: Optional[Dict] = None) -> bool:
        """
        Agent registers its presence. If the resource/zone is locked by another agent, returns False.
        """
        # Check for conflicts
        for aid, session in self.sessions.items():
            if aid != agent_id and session.resource == resource and session.zone == zone:
                if time.time() - session.last_heartbeat < 30: # 30s grace period
                    self.logger.warning(f"Conflict: {resource}/{zone} is already occupied by {aid}")
                    return False

        self.sessions[agent_id] = AgentSession(
            agent_id=agent_id,
            role=role,
            resource=resource,
            zone=zone,
            status="WORKING",
            last_heartbeat=time.time(),
            metadata=metadata or {}
        )
        self._save_registry()
        self.logger.info(f"Agent {agent_id} ({role}) checked in for {resource}/{zone}")
        return True

    def heartbeat(self, agent_id: str):
        if agent_id in self.sessions:
            self.sessions[agent_id].last_heartbeat = time.time()
            self._save_registry()

    def check_out(self, agent_id: str):
        if agent_id in self.sessions:
            del self.sessions[agent_id]
            self._save_registry()
            self.logger.info(f"Agent {agent_id} checked out")

    def get_active_agents(self) -> List[AgentSession]:
        return list(self.sessions.values())

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    reg = CheckInRegistry()
    success = reg.check_in("shion_task_1", "ActionLayer", "blender", "3D_VIEWPORT")
    print(f"Check-in result: {success}")
    time.sleep(1)
    reg.heartbeat("shion_task_1")
    print(f"Active agents: {reg.get_active_agents()}")
    reg.check_out("shion_task_1")
