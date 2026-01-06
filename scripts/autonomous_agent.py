#!/usr/bin/env python3
"""
Autonomous Agent - Phase 5.2
Self-operating AGI loop

Purpose: Run continuously, monitor events, make decisions, execute autonomously
Goal: Free 비노체님 from manual triggers (프롬프트 입력 + Accept 클릭)
"""

import os
import sys
import time
import json
import signal
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from workspace_root import get_workspace_root
from decision_engine import DecisionEngine, Decision
from context_bridge import ContextBridge, Context

# Slack API for posting responses
try:
    from slack_sdk import WebClient
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    print("⚠️ slack_sdk not installed. Slack responses will be disabled.")


class AutonomousAgent:
    """
    Self-operating AGI agent
    
    Loop:
    1. Check for events (Slack, Alpha, Scheduled)
    2. Make decision (DecisionEngine)
    3. Execute if allowed
    4. Log and report
    """
    
    def __init__(self, dry_run: bool = True):
        """
        Args:
            dry_run: If True, don't actually execute (safe mode)
        """
        self.dry_run = dry_run
        self.running = False
        
        # Paths (must be set first)
        self.base_dir = get_workspace_root()
        self.state_file = self.base_dir / "outputs" / "autonomous_agent_state.json"
        self.kill_switch_file = self.base_dir / "KILL_SWITCH"
        self.rhythm_tempo_file = self.base_dir / "outputs" / "rhythm_tempo.json"
        
        # Core components
        self.decision_engine = DecisionEngine()
        self.context_bridge = ContextBridge()
        
        # Slack client
        self.slack_client = None
        if SLACK_AVAILABLE:
            self._init_slack_client()
        
        # State
        
        # State
        self.state = self._load_state()
        
        # Signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _init_slack_client(self):
        """Initialize Slack client from config"""
        config_path = self.base_dir / "config" / "slack_config.json"
        
        if not config_path.exists():
            print("⚠️ Slack config not found, responses disabled")
            return
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Use CHATGPT specific token or fallback
            token = config.get("CHATGPT_SLACK_BOT_TOKEN") or config.get("SLACK_BOT_TOKEN")
            
            if not token or token.startswith("xoxb-your"):
                print("⚠️ Invalid Slack token, responses disabled")
                return
            
            self.slack_client = WebClient(token=token)
            print("✓ Slack client initialized")
            
        except Exception as e:
            print(f"⚠️ Failed to init Slack client: {e}")
    
    def _load_state(self) -> Dict:
        """Load agent state"""
        if not self.state_file.exists():
            return {
                "started_at": None,
                "cycles": 0,
                "actions_executed": 0,
                "last_event_check": None
            }
        
        with open(self.state_file, 'r') as f:
            return json.load(f)
    
    def _save_state(self):
        """Save agent state"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def _signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {sig}, shutting down gracefully...")
        self.stop()
    
    def check_kill_switch(self) -> bool:
        """Check if kill switch is activated"""
        if self.kill_switch_file.exists():
            print("🛑 KILL SWITCH ACTIVATED")
            with open(self.kill_switch_file, 'r') as f:
                reason = f.read().strip() or "Manual activation"
            print(f"   Reason: {reason}")
            self.report_to_slack(f"🛑 Kill Switch: {reason}")
            return True
        return False
    
    def check_slack_events(self) -> list:
        """
        Check for new Slack events from queue
        
        Returns:
            List of unprocessed events
        """
        from slack_event_queue import SlackEventQueue
        
        queue = SlackEventQueue()
        events = queue.get_pending_events(limit=5)
        
        if events:
            print(f"   📩 Found {len(events)} pending Slack events")
        
        return events
    
    def check_alpha_state(self) -> Optional[Dict]:
        """Check Alpha Background Self state"""
        alpha_state_file = self.base_dir / "outputs" / "alpha_background_self_state.json"
        
        if not alpha_state_file.exists():
            return None
        
        try:
            with open(alpha_state_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def execute_decision(self, decision: Decision) -> str:
        """
        Execute a decision
        
        Args:
            decision: Decision to execute
            
        Returns:
            Result string ("success", "failed", "skipped")
        """
        print(f"\n⚙️ Executing: {decision.action}")
        print(f"   Confidence: {decision.confidence:.2f}")
        print(f"   Reason: {decision.reason}")
        
        if self.dry_run:
            print("   [DRY RUN] Would execute but dry_run=True")
            return "dry_run"
        
        # Check whitelist
        allowed, reason = self.decision_engine.is_allowed(decision)
        if not allowed:
            print(f"   ❌ Blocked: {reason}")
            return "blocked"
        
        # Execute based on action type
        try:
            if decision.action == "respond_to_slack":
                return self._execute_slack_response(decision)
            
            elif decision.action == "save_context":
                return self._execute_save_context(decision)
            
            elif decision.action == "run_diagnostic":
                return self._execute_diagnostic(decision)
            
            elif decision.action == "execute_emergency_protocol":
                return self._execute_emergency(decision)
            
            else:
                print(f"   ⚠️ Unknown action: {decision.action}")
                return "unknown_action"
                
        except Exception as e:
            print(f"   ❌ Execution error: {e}")
            return f"error: {e}"
    
    def _execute_slack_response(self, decision: Decision) -> str:
        """Execute Slack response"""
        text = decision.params.get("text", "")
        channel = decision.params.get("channel")
        thread_ts = decision.params.get("thread_ts")
        
        print(f"   📤 [SLACK] {text[:80]}...")
        
        if self.dry_run:
            print(f"   [DRY RUN] Would post to channel {channel}")
            return "dry_run"
        
        if not self.slack_client:
            print(f"   ⚠️ Slack client not available")
            return "client_unavailable"
        
        try:
            # Actually post to Slack
            response = self.slack_client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts
            )
            
            print(f"   ✓ Posted to Slack: {response['ts']}")
            return "success"
            
        except Exception as e:
            print(f"   ❌ Slack post failed: {e}")
            return f"error: {e}"
    
    def _execute_save_context(self, decision: Decision) -> str:
        """Save context to Context Bridge"""
        content = decision.params.get("content", "")
        layer = decision.params.get("layer", "system")
        
        ctx = Context.create(
            layer=layer,
            speaker="autonomous_agent",
            content=content,
            tags=["auto_saved"],
            importance=0.7
        )
        
        self.context_bridge.save(ctx)
        print(f"   💾 Saved context: {ctx.id}")
        return "success"
    
    def _execute_diagnostic(self, decision: Decision) -> str:
        """Run system diagnostic"""
        component = decision.params.get("component", "system")
        print(f"   🔍 Running diagnostic: {component}")
        
        if component == "alpha":
            alpha_state = self.check_alpha_state()
            if alpha_state:
                state = alpha_state.get("state", "UNKNOWN")
                drift = alpha_state.get("drift_score", 0.0)
                result = f"Alpha: {state}, Drift: {drift:.2f}"
                print(f"   📊 {result}")
                return "success"
        
        return "success"
    
    def _execute_emergency(self, decision: Decision) -> str:
        """Execute emergency protocol"""
        protocol_type = decision.params.get("protocol_type", "UNKNOWN")
        print(f"   🚨 Emergency: {protocol_type}")
        
        # TODO: Call actual emergency_protocol.py
        self.report_to_slack(f"🚨 Alpha Emergency: {protocol_type}")
        return "success"
    
    def report_to_slack(self, message: str):
        """Report to Slack (통지만, 비개입)"""
        print(f"   📢 [SLACK REPORT] {message}")
        # TODO: Implement actual Slack notification
    
    def read_tempo_signal(self, system_name: str = "autonomous_agent", default: int = 30) -> int:
        """
        Read tempo signal from RhythmConductor
        
        Args:
            system_name: Name of this system
            default: Default interval if tempo file doesn't exist
            
        Returns:
            Interval in seconds
        """
        if not self.rhythm_tempo_file.exists():
            return default
        
        try:
            with open(self.rhythm_tempo_file, 'r') as f:
                tempos = json.load(f)
            
            tempo_info = tempos.get(system_name)
            if isinstance(tempo_info, dict):
                interval = tempo_info.get("interval", default)
                reason = tempo_info.get("reason", "unknown")
                print(f"   🎵 Tempo from RhythmConductor: {interval}s ({reason})")
                return interval
            elif isinstance(tempo_info, int):
                # Legacy format
                return tempo_info
            else:
                return default
        except Exception as e:
            print(f"   ⚠️  Failed to read tempo: {e}")
            return default
    
    def run_cycle(self):
        """Run one cycle of the autonomous loop"""
        self.state["cycles"] += 1
        cycle_num = self.state["cycles"]
        
        print(f"\n{'='*60}")
        print(f"🔄 Cycle {cycle_num} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        # 1. Check kill switch
        if self.check_kill_switch():
            self.stop()
            return
        
        # 2. Check Slack events
        slack_events = self.check_slack_events()
        for event in slack_events:
            event_id = event.get("id")
            event_text = event.get("text", "")
            
            print(f"\n📩 Slack Event: {event_text[:60]}...")
            
            decision = self.decision_engine.decide(
                input_text=event_text,
                layer="Shion"
            )
            
            result = self.execute_decision(decision)
            self.decision_engine.log_action(decision, result)
            
            # Mark as processed
            from slack_event_queue import SlackEventQueue
            queue = SlackEventQueue()
            queue.mark_processed(event_id, result)
            
            if result in ["success", "dry_run"]:
                self.state["actions_executed"] += 1
        
        # 3. Check Alpha state
        alpha_state = self.check_alpha_state()
        if alpha_state and alpha_state.get("state") == "INTERVENTION":
            print(f"\n🚨 Alpha INTERVENTION detected")
            print(f"   Drift: {alpha_state.get('drift_score', 0):.2f}")
            print(f"   Anomaly: {alpha_state.get('anomaly', 'UNKNOWN')}")
            
            decision = self.decision_engine.decide(
                input_text="Alpha intervention required",
                layer="system",
                alpha_state=alpha_state
            )
            
            result = self.execute_decision(decision)
            self.decision_engine.log_action(decision, result)
            
            if result in ["success", "dry_run"]:
                self.state["actions_executed"] += 1
        
        # 4. Save state
        self.state["last_event_check"] = datetime.now(timezone.utc).isoformat()
        self._save_state()
        
        print(f"\n✓ Cycle complete. Actions: {self.state['actions_executed']}")
    
    def start(self, interval: int = 10):
        """
        Start the autonomous loop
        
        Args:
            interval: Seconds between cycles
        """
        self.running = True
        self.state["started_at"] = datetime.now(timezone.utc).isoformat()
        
        mode_str = "DRY RUN" if self.dry_run else "LIVE"
        print("=" * 60)
        print(f"🤖 Autonomous Agent Starting ({mode_str})")
        print("=" * 60)
        print(f"Interval: {interval}s")
        print(f"Kill switch: {self.kill_switch_file}")
        print("=" * 60)
        
        if self.dry_run:
            print("⚠️ Running in DRY RUN mode (no actual execution)")
        else:
            print("⚠️ LIVE MODE - Will execute actions autonomously!")
        
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while self.running:
                self.run_cycle()
                
                # Read tempo from RhythmConductor (dynamic interval)
                current_interval = self.read_tempo_signal("autonomous_agent", default=interval)
                time.sleep(current_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Keyboard interrupt received")
            self.stop()
        
        print("\n✓ Autonomous Agent stopped")
    
    def stop(self):
        """Stop the agent"""
        self.running = False
        self._save_state()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous AGI Agent")
    parser.add_argument("--live", action="store_true", help="Run in LIVE mode (actually execute)")
    parser.add_argument("--interval", type=int, default=10, help="Cycle interval in seconds")
    parser.add_argument("--kill-switch", action="store_true", help="Activate kill switch")
    
    args = parser.parse_args()
    
    # Handle kill switch activation
    if args.kill_switch:
        kill_file = Path.home() / "agi" / "KILL_SWITCH"
        kill_file.parent.mkdir(parents=True, exist_ok=True)
        with open(kill_file, 'w') as f:
            f.write("Manual activation via --kill-switch flag\n")
        print(f"🛑 Kill switch activated: {kill_file}")
        return
    
    # Start agent
    agent = AutonomousAgent(dry_run=not args.live)
    agent.start(interval=args.interval)


if __name__ == "__main__":
    main()
