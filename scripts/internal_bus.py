import os
import json
import time
import glob
from typing import Dict, List, Optional, Callable

class InternalBus:
    """
    A file-based internal message bus for high-speed AI-to-AI communication.
    Messages are stored in `outputs/internal_bus/` as JSON files.
    """
    def __init__(self, bus_dir: str = "outputs/internal_bus"):
        self.bus_dir = bus_dir
        self._ensure_bus_dir()

    def _ensure_bus_dir(self):
        if not os.path.exists(self.bus_dir):
            os.makedirs(self.bus_dir)

    def publish(self, topic: str, message: Dict, source: str, target: str, priority: str = "normal") -> str:
        """
        Publishes a message to the bus.
        Returns the message ID (filename).
        """
        timestamp = time.time()
        message_id = f"{timestamp}_{source}_to_{target}_{topic}.json"
        
        payload = {
            "id": message_id,
            "timestamp": timestamp,
            "topic": topic,
            "source": source,
            "target": target,
            "priority": priority,  # 'normal' or 'critical'
            "content": message,
            "read": False
        }
        
        file_path = os.path.join(self.bus_dir, message_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            print(f"🚌 [InternalBus] Published: {message_id} ({priority})")
            return message_id
        except Exception as e:
            print(f"❌ [InternalBus] Failed to publish: {e}")
            return ""

    def poll(self, target: str, topic: Optional[str] = None) -> List[Dict]:
        """
        Retrieves unread messages targeted at a specific agent.
        Optionally filters by topic.
        """
        messages = []
        pattern = os.path.join(self.bus_dir, "*.json")
        files = sorted(glob.glob(pattern)) # Process oldest first

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Filter logic
                if data.get("target") != target:
                    continue
                if data.get("read"):
                    continue
                if topic and data.get("topic") != topic:
                    continue
                
                # Mark as read (or move to processed folder in future)
                # For now, we'll just return it. The consumer should handle 'ack'.
                messages.append(data)
                
            except Exception as e:
                print(f"⚠️ [InternalBus] Error reading {file_path}: {e}")
                continue
                
        return messages

    def ack(self, message_id: str):
        """
        Acknowledges a message (marks as read/deletes).
        For this simple version, we delete the file to keep the bus clean.
        """
        file_path = os.path.join(self.bus_dir, message_id)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                # print(f"✅ [InternalBus] Acknowledged: {message_id}")
        except Exception as e:
            print(f"❌ [InternalBus] Failed to ack {message_id}: {e}")

# Singleton instance for easy import
bus = InternalBus()

if __name__ == "__main__":
    # Simple test
    print("Testing Internal Bus...")
    bus.publish("test_topic", {"hello": "world"}, "Tester", "Gitko")
    msgs = bus.poll("Gitko")
    print(f"Found {len(msgs)} messages for Gitko.")
    for msg in msgs:
        print(f"Message: {msg}")
        bus.ack(msg['id'])
