#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Coordinator
===================
Monitors inputs/agent_inbox/antigravity_shion/ for mission requests from other agents.
Converts these requests into body_task.json for execution.
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Constants
WORKSPACE = Path(__file__).resolve().parents[2]
INBOX = WORKSPACE / "inputs" / "agent_inbox" / "antigravity_shion"
TASK_FILE = WORKSPACE / "signals" / "body_task.json"
HISTORY_DIR = WORKSPACE / "outputs" / "agency" / "mission_history"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("MissionCoordinator")

class MissionCoordinator:
    def __init__(self):
        self.inbox_path = INBOX
        self.task_file = TASK_FILE
        self.history_dir = HISTORY_DIR
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def scan_inbox(self) -> List[Path]:
        """Scan inbox for new mission files."""
        if not self.inbox_path.exists():
            return []
        
        # Support both .json and .md (with frontmatter or embedded json)
        missions = list(self.inbox_path.glob("MISSION_*.json"))
        missions.extend(self.inbox_path.glob("MISSION_*.md"))
        missions.extend(self.inbox_path.glob("TASK_*.json"))
        
        # Sort by creation time
        missions.sort(key=lambda x: x.stat().st_mtime)
        return missions

    def parse_mission(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse mission file content."""
        logger.info(f"Parsing mission: {file_path.name}")
        try:
            # Windows PowerShell의 Set-Content는 UTF-8 BOM을 붙일 수 있어 utf-8-sig로 읽는다.
            content = file_path.read_text(encoding="utf-8-sig", errors="replace")
            if file_path.suffix == ".json":
                return json.loads(content)
            elif file_path.suffix == ".md":
                # Basic markdown parsing: look for json block
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0]
                    return json.loads(json_str)
                # Or look for YAML-like frontmatter if we want to be fancy
                # For now, let's keep it simple: assume mission is JSON or MD with JSON block
        except Exception as e:
            logger.error(f"Failed to parse mission {file_path.name}: {e}")
        return None

    def archive_mission(self, file_path: Path, status: str):
        """Move mission file to history with status prefix."""
        timestamp = int(time.time())
        dest = self.history_dir / f"{status}_{timestamp}_{file_path.name}"
        try:
            os.replace(file_path, dest)
            logger.info(f"Archived mission to {dest.name}")
        except Exception as e:
            logger.error(f"Failed to archive mission: {e}")

    def run_once(self):
        """Check inbox and trigger task if possible."""
        if self.task_file.exists():
            # Already has a task, wait for it to be consumed
            logger.debug("Task file exists, skipping mission scan.")
            return

        missions = self.scan_inbox()
        if not missions:
            return

        for mission_file in missions:
            mission_data = self.parse_mission(mission_file)
            if not mission_data:
                self.archive_mission(mission_file, "INVALID")
                continue

            # Check if it has required fields
            if "actions" not in mission_data:
                # If it's a single action, wrap it
                if "action" in mission_data:
                    mission_data = {"actions": [mission_data]}
                else:
                    logger.warning(f"Mission {mission_file.name} missing 'actions'")
                    self.archive_mission(mission_file, "MALFORMED")
                    continue

            # Normalize action schema for supervised_body_controller:
            # - body controller expects action dicts with key "type"
            # - some missions use "action" instead (Phase 5 walkthrough example)
            try:
                actions = mission_data.get("actions") if isinstance(mission_data, dict) else None
                if isinstance(actions, list):
                    norm: list[dict[str, Any]] = []
                    for a in actions[:50]:
                        if not isinstance(a, dict):
                            continue
                        if "type" not in a and "action" in a:
                            a = dict(a)
                            a["type"] = a.get("action")
                        norm.append(a)
                    mission_data["actions"] = norm
            except Exception:
                pass

            # Inject source if missing
            if "origin" not in mission_data:
                mission_data["origin"] = f"agency_{mission_file.name}"

            # Write to body_task.json
            try:
                with open(self.task_file, "w", encoding="utf-8") as f:
                    json.dump(mission_data, f, indent=2, ensure_ascii=False)
                logger.info(f"🚀 Mission from {mission_file.name} promoted to body_task.json")
                self.archive_mission(mission_file, "PROMOTED")
                break # Only one mission at a time to prevent overload
            except Exception as e:
                logger.error(f"Failed to write task file: {e}")

def main():
    coordinator = MissionCoordinator()
    logger.info("Mission Coordinator started (Agency Layer)")
    # Normally this would run in a loop or be called by another daemon
    coordinator.run_once()

if __name__ == "__main__":
    main()
