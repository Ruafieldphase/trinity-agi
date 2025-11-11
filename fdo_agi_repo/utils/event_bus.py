#!/usr/bin/env python3
"""
🚌 Event Bus - Lightweight Pub/Sub for Rhythm & Flow Events
JSONL-based event streaming with topic filtering
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    Simple JSONL-based event bus for inter-agent communication
    - Publishes events to topic-specific JSONL files
    - Subscribers poll for new events
    - Non-blocking, file-based for simplicity
    """
    
    def __init__(self, event_dir: Optional[Path] = None):
        """
        Args:
            event_dir: Directory to store event JSONL files (default: workspace/outputs/events)
        """
        if event_dir is None:
            # Default to workspace/outputs/events
            workspace_root = Path(__file__).parent.parent.parent
            event_dir = workspace_root / "outputs" / "events"
        
        self.event_dir = Path(event_dir)
        self.event_dir.mkdir(parents=True, exist_ok=True)
        
        # Subscriber callbacks: {topic: [callbacks]}
        self._subscribers: Dict[str, List[Callable]] = {}
        
        # Last read positions: {topic: line_count}
        self._read_positions: Dict[str, int] = {}
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        logger.info(f"📢 Event Bus initialized (dir: {self.event_dir})")
    
    def publish(self, topic: str, event_data: Dict[str, Any], metadata: Optional[Dict] = None):
        """
        Publish an event to a topic
        
        Args:
            topic: Event topic (e.g., "rhythm.pulse", "flow.state_change")
            event_data: Event payload
            metadata: Optional metadata (auto-adds timestamp if not present)
        """
        event_file = self.event_dir / f"{topic}.jsonl"
        
        # Build event record
        event = {
            "timestamp": metadata.get("timestamp") if metadata else datetime.now().isoformat(),
            "topic": topic,
            "data": event_data
        }
        
        if metadata:
            event["metadata"] = metadata
        
        # Append to JSONL
        try:
            with open(event_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
            
            logger.debug(f"📤 Published to {topic}: {event_data}")
            
        except Exception as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
    
    def subscribe(self, topic: str, callback: Callable[[Dict], None]):
        """
        Subscribe to a topic
        
        Args:
            topic: Event topic to subscribe to
            callback: Function to call with event data: callback(event_dict)
        """
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
                self._read_positions[topic] = 0
            
            self._subscribers[topic].append(callback)
            logger.info(f"📥 Subscribed to {topic} (total subscribers: {len(self._subscribers[topic])})")
    
    def poll(self, topic: str) -> List[Dict]:
        """
        Poll for new events on a topic (non-blocking)
        
        Args:
            topic: Topic to poll
            
        Returns:
            List of new events since last poll
        """
        event_file = self.event_dir / f"{topic}.jsonl"
        
        if not event_file.exists():
            return []
        
        new_events = []
        
        try:
            with open(event_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Get position
            last_pos = self._read_positions.get(topic, 0)
            
            # Read new lines
            for line in lines[last_pos:]:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        new_events.append(event)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Malformed event in {topic}: {e}")
            
            # Update position
            self._read_positions[topic] = len(lines)
            
        except Exception as e:
            logger.error(f"Failed to poll {topic}: {e}")
        
        return new_events
    
    def subscribe(self, topic: str, callback: Callable[[Dict], None]):
        """
        Subscribe to a topic with a callback function
        
        Args:
            topic: Topic to subscribe to
            callback: Function to call when new events arrive
        """
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(callback)
        
        logger.info(f"📬 Subscribed to topic: {topic}")
    
    def unsubscribe(self, topic: str, callback: Callable[[Dict], None]):
        """
        Unsubscribe from a topic
        
        Args:
            topic: Topic to unsubscribe from
            callback: Callback function to remove
        """
        with self._lock:
            if topic in self._subscribers:
                try:
                    self._subscribers[topic].remove(callback)
                    logger.info(f"📭 Unsubscribed from topic: {topic}")
                except ValueError:
                    logger.warning(f"Callback not found for topic: {topic}")
    
    def poll_all_subscribed(self) -> Dict[str, List[Dict]]:
        """
        Poll all subscribed topics
        
        Returns:
            Dict mapping topic -> list of new events
        """
        results = {}
        
        with self._lock:
            topics = list(self._subscribers.keys())
        
        for topic in topics:
            events = self.poll(topic)
            if events:
                results[topic] = events
                
                # Call subscribers
                with self._lock:
                    callbacks = self._subscribers.get(topic, [])
                
                for callback in callbacks:
                    for event in events:
                        try:
                            callback(event)
                        except Exception as e:
                            logger.error(f"Subscriber callback error for {topic}: {e}")
        
        return results
    
    def clear_topic(self, topic: str):
        """Clear all events for a topic (delete JSONL file)"""
        event_file = self.event_dir / f"{topic}.jsonl"
        
        if event_file.exists():
            event_file.unlink()
            logger.info(f"🗑️ Cleared topic: {topic}")
        
        self._read_positions[topic] = 0
    
    def list_topics(self) -> List[str]:
        """List all available topics (*.jsonl files)"""
        return [f.stem for f in self.event_dir.glob("*.jsonl")]
    
    def get_topic_event_count(self, topic: str) -> int:
        """Get total event count for a topic"""
        event_file = self.event_dir / f"{topic}.jsonl"
        
        if not event_file.exists():
            return 0
        
        with open(event_file, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)


# Global singleton instance (optional convenience)
_global_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global EventBus singleton"""
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    bus = EventBus()
    
    # Subscribe to rhythm events
    def on_rhythm_pulse(event):
        print(f"🥁 Pulse received: {event['data']}")
    
    bus.subscribe("rhythm.pulse", on_rhythm_pulse)
    
    # Publish some events
    bus.publish("rhythm.pulse", {"bpm": 120, "beat": 1})
    bus.publish("rhythm.pulse", {"bpm": 120, "beat": 2})
    bus.publish("flow.state_change", {"from": "distracted", "to": "focused", "score": 0.75})
    
    # Poll
    print("\n📊 Polling subscribed topics:")
    results = bus.poll_all_subscribed()
    
    print(f"\n📋 Available topics: {bus.list_topics()}")
    print(f"📈 rhythm.pulse event count: {bus.get_topic_event_count('rhythm.pulse')}")
