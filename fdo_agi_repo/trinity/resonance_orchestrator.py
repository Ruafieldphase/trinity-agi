"""
Trinity Resonance Orchestrator - Event Bus Integration
Monitors rhythm/flow events and provides resonance oracle for autonomous systems
"""
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from workspace_utils import find_workspace_root
from utils.event_bus import EventBus


@dataclass
class ResonanceState:
    """Current resonance state from trinity perspective"""
    timestamp: str
    rhythm_pulse: Optional[float] = None  # BPM-like from music
    flow_state: Optional[str] = None      # flow, distracted, etc
    energy_level: float = 0.5             # 0-1 scale
    coherence: float = 0.5                # How aligned are the signals
    recommendation: str = "neutral"       # rest, focus, create, etc
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ResonanceOrchestrator:
    """
    Listens to Event Bus for rhythm/flow events
    Synthesizes trinity perspective
    Publishes resonance state
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        if workspace_root is None:
            workspace_root = find_workspace_root(Path(__file__).parent)
        
        self.workspace_root = Path(workspace_root)
        self.event_bus = EventBus(self.workspace_root / "outputs" / "events")
        self.state = ResonanceState(timestamp=datetime.now().isoformat())
        
        # State file for persistence
        self.state_file = self.workspace_root / "outputs" / "resonance_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load previous state if exists
        self._load_state()
    
    def _load_state(self):
        """Load previous resonance state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Reconstruct dataclass
                    self.state = ResonanceState(**data)
            except Exception as e:
                print(f"⚠️ Could not load previous state: {e}")
    
    def _save_state(self):
        """Persist current resonance state"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state.to_dict(), f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save state: {e}")
    
    def _process_rhythm_event(self, event: Dict[str, Any]):
        """Update state from rhythm pulse"""
        data = event.get("data", {})
        self.state.rhythm_pulse = data.get("bpm")
        self.state.energy_level = data.get("energy", 0.5)
        self._update_recommendation()
    
    def _process_flow_event(self, event: Dict[str, Any]):
        """Update state from flow observation"""
        data = event.get("data", {})
        self.state.flow_state = data.get("state", "unknown")
        # Adjust coherence based on flow state
        if self.state.flow_state == "flow":
            self.state.coherence = min(1.0, self.state.coherence + 0.1)
        elif self.state.flow_state == "distracted":
            self.state.coherence = max(0.0, self.state.coherence - 0.1)
        self._update_recommendation()
    
    def _update_recommendation(self):
        """Synthesize trinity recommendation"""
        # Simple heuristic - can be made more sophisticated
        if self.state.flow_state == "distracted":
            self.state.recommendation = "rest"
        elif self.state.energy_level > 0.7 and self.state.coherence > 0.6:
            self.state.recommendation = "create"
        elif self.state.energy_level > 0.5:
            self.state.recommendation = "focus"
        else:
            self.state.recommendation = "rest"
        
        self.state.timestamp = datetime.now().isoformat()
        
        # Publish updated resonance state
        self.event_bus.publish("resonance", {
            "state": self.state.to_dict()
        })
        
        # Save state
        self._save_state()
    
    def listen(self, interval: float = 5.0, duration: Optional[float] = None):
        """
        Main event loop - listen to Event Bus and update resonance
        
        Args:
            interval: How often to check for events (seconds)
            duration: How long to run (seconds), None = indefinite
        """
        print("🌀 Trinity Resonance Orchestrator started")
        print(f"📡 Listening to Event Bus at: {self.event_bus.event_dir}")
        print(f"💾 State file: {self.state_file}")
        
        # Subscribe to topics with callbacks
        self.event_bus.subscribe("rhythm.pulse", self._process_rhythm_event)
        self.event_bus.subscribe("flow.state_changed", self._process_flow_event)
        
        start_time = time.time()
        event_count = 0
        
        try:
            while True:
                # Poll all subscribed topics
                results = self.event_bus.poll_all_subscribed()
                
                # Count events
                total_events = sum(len(events) for events in results.values())
                event_count += total_events
                
                # Print current state if events received
                if total_events > 0:
                    print(f"\n🌊 Resonance State Update (processed {event_count} events):")
                    print(f"  Rhythm: {self.state.rhythm_pulse} BPM")
                    print(f"  Flow: {self.state.flow_state}")
                    print(f"  Energy: {self.state.energy_level:.2f}")
                    print(f"  Coherence: {self.state.coherence:.2f}")
                    print(f"  → {self.state.recommendation.upper()}")
                
                # Check duration
                if duration and (time.time() - start_time) > duration:
                    print(f"\n✅ Completed {duration}s listening cycle")
                    break
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n⏹️ Resonance Orchestrator stopped by user")
        
        finally:
            self._save_state()
            print(f"💾 Final state saved to: {self.state_file}")


def main():
    """Run resonance orchestrator as standalone daemon"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Trinity Resonance Orchestrator")
    parser.add_argument("--interval", type=float, default=5.0, help="Event check interval (seconds)")
    parser.add_argument("--duration", type=float, default=None, help="Run duration (seconds), None=indefinite")
    parser.add_argument("--workspace", type=str, default=None, help="Workspace root path")
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace) if args.workspace else None
    orchestrator = ResonanceOrchestrator(workspace_root=workspace)
    orchestrator.listen(interval=args.interval, duration=args.duration)


if __name__ == "__main__":
    main()
