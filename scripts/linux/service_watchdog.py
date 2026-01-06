#!/usr/bin/env python3
"""
AGI Service Watchdog
====================
Monitors all agi-* systemd services and automatically restarts failed ones.
Escalates to Sena on repeated failures.

Usage:
    python scripts/linux/service_watchdog.py [--interval SECONDS] [--max-retries N]
"""

import subprocess
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import argparse

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent.parent
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
STATE_FILE = WORKSPACE_ROOT / "outputs" / "watchdog_state.json"
LOG_DIR = WORKSPACE_ROOT / "outputs"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "service_watchdog.log")
    ]
)
logger = logging.getLogger("ServiceWatchdog")

@dataclass
class ServiceStatus:
    """Service status information"""
    name: str
    active: bool
    status: str  # "running", "failed", "inactive", "unknown"
    uptime_seconds: Optional[int] = None
    restart_count: int = 0

class ServiceWatchdog:
    """Monitors and recovers systemd services"""
    
    def __init__(self, max_restart_attempts: int = 3, check_interval: int = 10):
        self.max_restart_attempts = max_restart_attempts
        self.check_interval = check_interval
        self.recovery_state = self._load_state()
        
    def _load_state(self) -> Dict:
        """Load watchdog state from disk"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
        return {}
    
    def _save_state(self):
        """Save watchdog state to disk"""
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATE_FILE, 'w') as f:
                json.dump(self.recovery_state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def discover_services(self) -> List[str]:
        """Discover all agi-* systemd services (including stopped ones)"""
        try:
            # Use list-unit-files to get ALL registered services, not just loaded ones
            result = subprocess.run(
                ["systemctl", "--user", "list-unit-files", "agi-*.service", "--no-pager", "--plain"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            services = []
            for line in result.stdout.split('\n'):
                if line.strip() and 'agi-' in line and '.service' in line:
                    # Parse: "agi-Core.service  enabled  enabled"
                    parts = line.split()
                    if parts and parts[0].startswith('agi-') and parts[0].endswith('.service'):
                        services.append(parts[0])
            
            logger.info(f"Discovered {len(services)} services: {services}")
            return services
            
        except Exception as e:
            logger.error(f"Failed to discover services: {e}")
            return []
    
    def check_service(self, name: str) -> ServiceStatus:
        """Check status of a single service"""
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            status_text = result.stdout.strip()
            active = (status_text == "active")
            
            # Get detailed status for uptime
            uptime = None
            try:
                status_result = subprocess.run(
                    ["systemctl", "--user", "show", name, "--property=ActiveEnterTimestamp"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # Parse timestamp if service is running
                if active and "ActiveEnterTimestamp=" in status_result.stdout:
                    timestamp_str = status_result.stdout.split("=", 1)[1].strip()
                    if timestamp_str and timestamp_str != "n/a":
                        # Calculate uptime (simplified)
                        uptime = 1  # placeholder
            except:
                pass
            
            return ServiceStatus(
                name=name,
                active=active,
                status=status_text if status_text in ["active", "inactive", "failed"] else "unknown",
                uptime_seconds=uptime
            )
            
        except Exception as e:
            logger.error(f"Failed to check service {name}: {e}")
            return ServiceStatus(name=name, active=False, status="unknown")
    
    def restart_service(self, name: str) -> bool:
        """Attempt to restart a service"""
        try:
            logger.info(f"Attempting to restart {name}...")
            result = subprocess.run(
                ["systemctl", "--user", "restart", name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Wait a moment and verify
            time.sleep(2)
            status = self.check_service(name)
            
            if status.active:
                logger.info(f"✅ Successfully restarted {name}")
                return True
            else:
                logger.warning(f"⚠️ Restart command succeeded but {name} is not active")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to restart {name}: {e}")
            return False
    
    def alert_user(self, name: str, reason: str, metadata: Dict):
        """
        Alert user of repeated service failure (AUTONOMY: No automatic external AI call)
        
        Philosophy: Internal Background Self must handle decisions.
        External mentors (Sena) are called ONLY when user explicitly requests.
        See: docs/AGI_SELF_ARCHITECTURE.md - Layer 1 vs Layer 2
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "service_failure_alert",
            "source": "service_watchdog",
            "target": "user",  # ← Changed from "sena" to "user"
            "priority": "critical",
            "message": f"⚠️ Service {name} failed repeatedly: {reason}",
            "details": {
                "service_name": name,
                "failure_reason": reason,
                "restart_attempts": metadata.get("restart_attempts", 0),
                "last_status": metadata.get("last_status", "unknown"),
                "watchdog_recommendation": "Manual intervention recommended. Check logs for root cause.",
                "internal_diagnosis": self._diagnose_failure(name, metadata)
            },
            "user_actions": [
                f"Check logs: journalctl --user -u {name} -n 50",
                f"Manual restart: systemctl --user restart {name}",
                "Review recent system changes",
                "[OPTIONAL] Ask Sena for advice if needed"
            ]
        }
        
        try:
            LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LEDGER_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            logger.critical(f"🚨 USER ALERT: {name} - {reason}")
            logger.info(f"   Recommendation: {entry['details']['watchdog_recommendation']}")
            logger.info(f"   Internal Diagnosis: {entry['details']['internal_diagnosis']}")
        except Exception as e:
            logger.error(f"Failed to alert user: {e}")
    
    def _diagnose_failure(self, name: str, metadata: Dict) -> str:
        """
        Internal diagnostic attempt (Layer 1: Background Self)
        Analyze failure pattern without external help
        """
        attempts = metadata.get("restart_attempts", 0)
        status = metadata.get("last_status", "unknown")
        
        # Simple pattern matching (can be expanded with ML later)
        if status == "failed":
            return f"Service crashed {attempts} times. Check service logs for exceptions."
        elif status == "inactive":
            return f"Service stopped unexpectedly {attempts} times. Possible dependency issue."
        else:
            return f"Unknown failure pattern (status={status}). Deep investigation needed."
    
    def handle_service(self, status: ServiceStatus):
        """Handle a single service status"""
        name = status.name
        
        # Initialize state if needed
        if name not in self.recovery_state:
            self.recovery_state[name] = {
                "restart_attempts": 0,
                "last_check": None,
                "last_status": None,
                "escalated": False
            }
        
        state = self.recovery_state[name]
        state["last_check"] = datetime.now().isoformat()
        state["last_status"] = status.status
        
        # Service is healthy
        if status.active:
            # Reset attempt counter on successful recovery
            if state["restart_attempts"] > 0:
                logger.info(f"✅ {name} recovered after {state['restart_attempts']} restart(s)")
                state["restart_attempts"] = 0
                state["escalated"] = False
            return
        
        # Service is down
        logger.warning(f"⚠️ {name} is {status.status}")
        
        # Check if already escalated
        if state.get("escalated", False):
            logger.info(f"ℹ️ {name} already escalated, waiting for manual intervention")
            return
        
        # Attempt restart
        if state["restart_attempts"] < self.max_restart_attempts:
            state["restart_attempts"] += 1
            logger.info(f"🔄 Restart attempt {state['restart_attempts']}/{self.max_restart_attempts} for {name}")
            
            if self.restart_service(name):
                state["restart_attempts"] = 0
            else:
                logger.warning(f"⚠️ Restart {state['restart_attempts']}/{self.max_restart_attempts} failed for {name}")
        else:
            # Max retries exceeded, alert user (NOT external AI)
            logger.critical(f"🚨 {name} exceeded max restart attempts ({self.max_restart_attempts})")
            self.alert_user(
                name,
                f"Failed to recover after {self.max_restart_attempts} restart attempts",
                state
            )
            state["escalated"] = True
        
        self._save_state()
    
    def run_loop(self):
        """Main monitoring loop"""
        logger.info(f"🔍 Service Watchdog started (interval={self.check_interval}s, max_retries={self.max_restart_attempts})")
        
        try:
            while True:
                services = self.discover_services()
                
                for service_name in services:
                    status = self.check_service(service_name)
                    self.handle_service(status)
                
                logger.debug(f"Check cycle complete. Sleeping {self.check_interval}s...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Watchdog stopped by user")
        except Exception as e:
            logger.critical(f"Watchdog crashed: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description="AGI Service Watchdog")
    parser.add_argument("--interval", type=int, default=10, help="Check interval in seconds")
    parser.add_argument("--max-retries", type=int, default=3, help="Max restart attempts before escalation")
    args = parser.parse_args()
    
    watchdog = ServiceWatchdog(
        max_restart_attempts=args.max_retries,
        check_interval=args.interval
    )
    watchdog.run_loop()

if __name__ == "__main__":
    main()
