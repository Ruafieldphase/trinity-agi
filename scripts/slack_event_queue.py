#!/usr/bin/env python3
"""
Slack Event Queue for Autonomous Agent
Phase 5.3: Bridge between Slack listener and Autonomous Agent

Purpose: Store unprocessed Slack events for autonomous agent to pick up
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional


class SlackEventQueue:
    """
    Queue system for Slack events
    
    Flow:
    1. chatgpt_slack_listener.py → save event to queue
    2. autonomous_agent.py → check queue → process → mark processed
    """
    
    def __init__(self, queue_dir: str = None):
        self.queue_dir = Path(queue_dir or Path.home() / "agi" / "outputs" / "slack_queue")
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        self.pending_file = self.queue_dir / "pending_events.jsonl"
        self.processed_file = self.queue_dir / "processed_events.jsonl"
    
    def add_event(self, event: Dict) -> str:
        """
        Add a new Slack event to the queue
        
        Args:
            event: Slack event dict with keys:
                - text: message text
                - channel: channel ID
                - user: user ID
                - thread_ts: thread timestamp
                - ts: event timestamp
                
        Returns:
            Event ID
        """
        # Generate event ID
        timestamp = event.get("ts")
        if timestamp:
            # Slack ts is already a float string
            event_id = f"slack_{timestamp.replace('.', '_')}"
        else:
            # Generate from current time
            event_id = f"slack_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        
        # Add metadata
        enriched_event = {
            "id": event_id,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "processed": False,
            **event
        }
        
        # Append to pending queue
        with open(self.pending_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(enriched_event, ensure_ascii=False) + '\n')
        
        print(f"📥 Slack event queued: {event_id}")
        return event_id
    
    def get_pending_events(self, limit: int = 10) -> List[Dict]:
        """
        Get unprocessed events
        
        Returns:
            List of pending events (oldest first)
        """
        if not self.pending_file.exists():
            return []
        
        pending = []
        with open(self.pending_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    event = json.loads(line)
                    if not event.get("processed", False):
                        pending.append(event)
        
        return pending[:limit]
    
    def mark_processed(self, event_id: str, result: str = "success"):
        """
        Mark an event as processed
        
        Args:
            event_id: Event ID
            result: Processing result
        """
        # Read all pending events
        if not self.pending_file.exists():
            return
        
        events = []
        with open(self.pending_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        
        # Update the specific event
        updated = False
        for event in events:
            if event.get("id") == event_id:
                event["processed"] = True
                event["processed_at"] = datetime.now(timezone.utc).isoformat()
                event["result"] = result
                updated = True
                
                # Log to processed file
                with open(self.processed_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        # Rewrite pending file (without processed events)
        if updated:
            with open(self.pending_file, 'w', encoding='utf-8') as f:
                for event in events:
                    if not event.get("processed", False):
                        f.write(json.dumps(event, ensure_ascii=False) + '\n')
            
            print(f"✓ Marked processed: {event_id} ({result})")
    
    def clear_old_processed(self, days: int = 7):
        """Clear processed events older than N days"""
        # TODO: Implement if needed
        pass


def test_queue():
    """Test the event queue"""
    queue = SlackEventQueue()
    
    # Simulate adding events
    event1 = {
        "text": "Hello AGI",
        "channel": "C123456",
        "user": "U789012",
        "ts": "1234567890.123456"
    }
    
    event2 = {
        "text": "Alpha 상태는?",
        "channel": "C123456",
        "user": "U789012",
        "ts": "1234567891.123456"
    }
    
    # Add to queue
    id1 = queue.add_event(event1)
    id2 = queue.add_event(event2)
    
    # Get pending
    pending = queue.get_pending_events()
    print(f"\n📋 Pending events: {len(pending)}")
    for event in pending:
        print(f"   - {event['id']}: {event['text']}")
    
    # Mark first as processed
    queue.mark_processed(id1, "success")
    
    # Check again
    pending = queue.get_pending_events()
    print(f"\n📋 After processing 1st event: {len(pending)} pending")
    for event in pending:
        print(f"   - {event['id']}: {event['text']}")


if __name__ == "__main__":
    test_queue()
