#!/usr/bin/env python3
"""
Goal Tracker - Simple goal state management
Tracks goal lifecycle: proposed → in_progress → completed → archived
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

class GoalTracker:
    def __init__(self, tracker_file: Optional[str] = None):
        self.tracker_file = tracker_file or os.path.join(
            os.path.dirname(__file__), "..", "memory", "goal_tracker.json"
        )
        self._ensure_tracker_file()
    
    def _ensure_tracker_file(self):
        """Ensure tracker file exists"""
        os.makedirs(os.path.dirname(self.tracker_file), exist_ok=True)
        if not os.path.exists(self.tracker_file):
            self._save_data({"goals": [], "version": "1.0"})
    
    def _load_data(self) -> Dict:
        """Load tracker data"""
        with open(self.tracker_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_data(self, data: Dict):
        """Save tracker data"""
        with open(self.tracker_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_goal(self, title: str, priority: int, estimated_days: float, 
                 description: str = "", tags: List[str] = None) -> str:
        """Add a new goal"""
        data = self._load_data()

        # Prevent duplicate active goals with exact same title
        normalized = title.strip().lower()
        for g in data.get("goals", []):
            if g.get("title", "").strip().lower() == normalized and g.get("status") in ("proposed","in_progress"):
                print(f"⚠️ Goal with title already exists (status={g.get('status')}): {g.get('id', '<no-id>')} - {title}")
                return g.get("id")
        
        # Generate ID
        goal_id = f"goal_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        goal = {
            "id": goal_id,
            "title": title,
            "description": description,
            "status": "proposed",
            "priority": priority,
            "estimated_days": estimated_days,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "actual_days": None,
            "outcome": None
        }
        
        data["goals"].append(goal)
        self._save_data(data)
        
        print(f"✅ Goal added: {goal_id} - {title}")
        return goal_id
    
    def start_goal(self, goal_id: str):
        """Mark goal as in progress"""
        data = self._load_data()
        
        for goal in data["goals"]:
            # Some older goals may not have an 'id' field; compare safely
            if goal.get("id") == goal_id:
                goal["status"] = "in_progress"
                goal["started_at"] = datetime.now().isoformat()
                goal["updated_at"] = datetime.now().isoformat()
                self._save_data(data)
                print(f"🚀 Goal started: {goal_id} - {goal['title']}")
                return
        
        print(f"❌ Goal not found: {goal_id}")
    
    def complete_goal(self, goal_id: str, outcome: str, actual_days: Optional[float] = None):
        """Mark goal as completed"""
        data = self._load_data()
        
        for goal in data["goals"]:
            # Use .get to avoid KeyError for older entries without 'id'
            if goal.get("id") == goal_id:
                goal["status"] = "completed"
                goal["completed_at"] = datetime.now().isoformat()
                goal["updated_at"] = datetime.now().isoformat()
                goal["outcome"] = outcome
                
                # Calculate actual days if not provided
                if actual_days is not None:
                    goal["actual_days"] = actual_days
                elif goal["started_at"]:
                    started = datetime.fromisoformat(goal["started_at"])
                    completed = datetime.now()
                    goal["actual_days"] = (completed - started).total_seconds() / 86400
                
                self._save_data(data)
                print(f"✅ Goal completed: {goal_id} - {goal['title']}")
                print(f"   Outcome: {outcome}")
                if goal["actual_days"]:
                    print(f"   Time: {goal['actual_days']:.2f} days (estimated: {goal['estimated_days']})")
                return
        
        print(f"❌ Goal not found: {goal_id}")
    
    def list_goals(self, status: Optional[str] = None) -> List[Dict]:
        """List goals, optionally filtered by status"""
        data = self._load_data()
        goals = data["goals"]
        
        if status:
            goals = [g for g in goals if g["status"] == status]
        
        return goals
    
    def get_goal(self, goal_id: str) -> Optional[Dict]:
        """Get a specific goal"""
        data = self._load_data()
        
        for goal in data["goals"]:
            if goal.get("id") == goal_id:
                return goal
        
        return None
    
    def print_summary(self):
        """Print summary of all goals"""
        data = self._load_data()
        
        by_status = {}
        for goal in data["goals"]:
            status = goal["status"]
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(goal)
        
        print("\n📊 Goal Tracker Summary")
        print("=" * 60)
        
        for status in ["proposed", "in_progress", "completed", "archived"]:
            goals = by_status.get(status, [])
            if goals:
                print(f"\n{status.upper()} ({len(goals)} goals):")
                for goal in sorted(goals, key=lambda x: x.get("priority", 0), reverse=True):
                    priority_str = f"[P{goal['priority']}]"
                    days_str = f"{goal.get('estimated_days','?')}d"
                    goal_id = goal.get('id', '<no-id>')
                    print(f"  {priority_str:6} {days_str:5} {goal_id:20} {goal['title']}")
                    if goal.get("outcome"):
                        print(f"         → {goal['outcome']}")
        
        print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Goal Tracker CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Add goal
    add_parser = subparsers.add_parser("add", help="Add a new goal")
    add_parser.add_argument("title", help="Goal title")
    add_parser.add_argument("--priority", type=int, required=True, help="Priority (1-20)")
    add_parser.add_argument("--days", type=float, required=True, help="Estimated days")
    add_parser.add_argument("--description", default="", help="Goal description")
    add_parser.add_argument("--tags", nargs="*", default=[], help="Tags")
    
    # Start goal
    start_parser = subparsers.add_parser("start", help="Start a goal")
    start_parser.add_argument("goal_id", help="Goal ID")
    
    # Complete goal
    complete_parser = subparsers.add_parser("complete", help="Complete a goal")
    complete_parser.add_argument("goal_id", help="Goal ID")
    complete_parser.add_argument("outcome", help="Outcome description")
    complete_parser.add_argument("--actual-days", type=float, help="Actual days taken")
    
    # List goals
    list_parser = subparsers.add_parser("list", help="List goals")
    list_parser.add_argument("--status", choices=["proposed", "in_progress", "completed", "archived"], 
                            help="Filter by status")
    
    # Get goal
    get_parser = subparsers.add_parser("get", help="Get a specific goal")
    get_parser.add_argument("goal_id", help="Goal ID")
    
    # Summary
    subparsers.add_parser("summary", help="Print summary")
    
    args = parser.parse_args()
    
    tracker = GoalTracker()
    
    if args.command == "add":
        tracker.add_goal(args.title, args.priority, args.days, args.description, args.tags)
    elif args.command == "start":
        tracker.start_goal(args.goal_id)
    elif args.command == "complete":
        tracker.complete_goal(args.goal_id, args.outcome, args.actual_days)
    elif args.command == "list":
        goals = tracker.list_goals(args.status)
        for goal in goals:
            print(json.dumps(goal, indent=2, ensure_ascii=False))
    elif args.command == "get":
        goal = tracker.get_goal(args.goal_id)
        if goal:
            print(json.dumps(goal, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Goal not found: {args.goal_id}")
    elif args.command == "summary":
        tracker.print_summary()
    else:
        parser.print_help()
