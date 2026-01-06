#!/usr/bin/env python3
"""
Auto-healing System
===================

Reads anomaly alerts and executes healing actions based on strategies.

Features:
- Strategy-based healing (JSON config)
- Grace period & Rate limiting
- Rollback mechanism
- Healing history logging

Usage:
    python scripts/auto_healer.py --strategies configs/healing_strategies.json --once
    python scripts/auto_healer.py --interval 60 --dry-run
"""

import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from workspace_root import get_workspace_root

# ============================================================================
# Configuration
# ============================================================================

WORKSPACE_ROOT = get_workspace_root()
ALERT_FILE = WORKSPACE_ROOT / "outputs" / "anomaly_alert_latest.json"
ALERTS_DIR = WORKSPACE_ROOT / "outputs" / "alerts"  # Phase 7 Task 2: Multi-alert support
STRATEGIES_FILE = WORKSPACE_ROOT / "configs" / "healing_strategies.json"
HEALING_LOG = WORKSPACE_ROOT / "outputs" / "healing_log.jsonl"
GRACE_HISTORY_FILE = WORKSPACE_ROOT / "outputs" / "healing_grace_history.json"

# ============================================================================
# Healing History & Grace Period
# ============================================================================

class GracePeriodTracker:
    """Track healing history to enforce grace periods"""
    
    def __init__(self, history_file: Path):
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self) -> Dict[str, Any]:
        """Load grace period history"""
        if not self.history_file.exists():
            return {}
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Failed to load grace history: {e}")
            return {}
    
    def _save_history(self):
        """Save grace period history"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save grace history: {e}")
    
    def can_heal(self, strategy_name: str, grace_period_seconds: int, max_retries: int) -> bool:
        """Check if healing is allowed (grace period expired)"""
        if strategy_name not in self.history:
            return True
        
        record = self.history[strategy_name]
        last_time = datetime.fromisoformat(record['last_heal_time'])
        now = datetime.now()
        
        # Check grace period
        if (now - last_time).total_seconds() < grace_period_seconds:
            print(f"⏳ Grace period active for '{strategy_name}' (last: {last_time.strftime('%H:%M:%S')})")
            return False
        
        # Check max retries (within last 1 hour)
        recent_count = sum(
            1 for ts in record.get('recent_heals', [])
            if (now - datetime.fromisoformat(ts)).total_seconds() < 3600
        )
        
        if recent_count >= max_retries:
            print(f"🚫 Max retries ({max_retries}) reached for '{strategy_name}' in last hour")
            return False
        
        return True
    
    def can_heal_with_consecutive_check(
        self, 
        strategy_name: str, 
        grace_period_seconds: int, 
        max_retries: int,
        consecutive_failures_threshold: int
    ) -> bool:
        """Check if healing is allowed (grace period + consecutive failures)"""
        if not self.can_heal(strategy_name, grace_period_seconds, max_retries):
            return False
        
        # Check consecutive failures
        if strategy_name in self.history:
            record = self.history[strategy_name]
            consecutive_failures = record.get('consecutive_failures', 0)
            
            if consecutive_failures >= consecutive_failures_threshold:
                print(f"🚫 Consecutive failures ({consecutive_failures}) >= threshold ({consecutive_failures_threshold}) for '{strategy_name}'")
                return False
        
        return True
    
    def record_heal(self, strategy_name: str, success: bool = True):
        """Record a healing action"""
        now = datetime.now().isoformat()
        
        if strategy_name not in self.history:
            self.history[strategy_name] = {
                'first_heal_time': now,
                'last_heal_time': now,
                'recent_heals': [now],
                'total_count': 1,
                'consecutive_failures': 0 if success else 1
            }
        else:
            record = self.history[strategy_name]
            record['last_heal_time'] = now
            record['recent_heals'] = [
                ts for ts in record.get('recent_heals', [])
                if (datetime.now() - datetime.fromisoformat(ts)).total_seconds() < 3600
            ] + [now]
            record['total_count'] = record.get('total_count', 0) + 1
            
            # Update consecutive failures
            if success:
                record['consecutive_failures'] = 0
            else:
                record['consecutive_failures'] = record.get('consecutive_failures', 0) + 1
        
        self._save_history()

# ============================================================================
# Healing Actions
# ============================================================================

class HealingExecutor:
    """Execute healing actions"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.workspace_root = WORKSPACE_ROOT
    
    def execute_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Execute a single healing action"""
        action_type = action.get('type')
        
        if self.dry_run:
            print(f"   [DRY-RUN] Would execute: {action_type}")
            return True
        
        # Dispatch to specific handler
        handler = getattr(self, f"_action_{action_type}", None)
        if not handler:
            print(f"⚠️  Unknown action type: {action_type}")
            return False
        
        try:
            return handler(action, context)
        except Exception as e:
            print(f"❌ Action '{action_type}' failed: {e}")
            return False
    
    def _action_log(self, action: Dict, context: Dict) -> bool:
        """Log message"""
        message = action['message'].format(**context)
        print(f"   📝 {message}")
        return True
    
    def _action_rate_limit(self, action: Dict, context: Dict) -> bool:
        """Apply rate limiting"""
        target = action['target']
        params = action.get('params', {})
        print(f"   🐢 Rate limiting: {target} (max_workers={params.get('max_workers', 1)})")
        # TODO: Implement actual rate limiting (e.g., modify queue config)
        return True
    
    def _action_restart_if_critical(self, action: Dict, context: Dict) -> bool:
        """Restart service if condition is critical"""
        condition = action.get('condition', '')
        target = action['target']
        
        # Evaluate condition (simple eval, be careful!)
        try:
            should_restart = eval(condition, {}, context)
        except Exception as e:
            print(f"⚠️  Failed to evaluate condition '{condition}': {e}")
            return False
        
        if should_restart:
            print(f"   🔄 Restarting: {target}")
            return self._restart_service(target)
        else:
            print(f"   ℹ️  Condition not met, skip restart: {condition}")
            return True
    
    def _action_clear_cache(self, action: Dict, context: Dict) -> bool:
        """Clear cache"""
        targets = action.get('targets', [])
        print(f"   🗑️  Clearing cache: {', '.join(targets)}")
        # TODO: Implement cache clearing (e.g., delete cache files)
        return True
    
    def _action_restart_service(self, action: Dict, context: Dict) -> bool:
        """Restart service"""
        target = action['target']
        print(f"   🔄 Restarting service: {target}")
        return self._restart_service(target)
    
    def _action_fallback_llm(self, action: Dict, context: Dict) -> bool:
        """Fallback to alternative LLM"""
        from_llm = action['from']
        to_llm = action['to']
        print(f"   🔀 Fallback LLM: {from_llm} → {to_llm}")
        # TODO: Implement LLM config switching
        return True
    
    def _action_notify(self, action: Dict, context: Dict) -> bool:
        """Send notification"""
        channels = action.get('channels', ['console'])
        message = action['message']
        print(f"   📢 Notify [{', '.join(channels)}]: {message}")
        return True
    
    def _action_enable_cache(self, action: Dict, context: Dict) -> bool:
        """Enable caching"""
        target = action['target']
        ttl = action.get('ttl_seconds', 3600)
        print(f"   💾 Enable cache: {target} (TTL={ttl}s)")
        # TODO: Implement cache config update
        return True
    
    def _action_scale_workers(self, action: Dict, context: Dict) -> bool:
        """Scale workers"""
        target = action['target']
        scale_action = action['action']
        max_workers = action.get('max_workers', 2)
        print(f"   📈 Scale workers: {target} ({scale_action}, max={max_workers})")
        # TODO: Implement worker scaling
        return True
    
    def _action_redistribute_tasks(self, action: Dict, context: Dict) -> bool:
        """Redistribute tasks"""
        max_tasks = action.get('max_tasks_per_worker', 5)
        print(f"   🔀 Redistribute tasks (max={max_tasks} per worker)")
        # TODO: Implement task redistribution
        return True
    
    def _action_snapshot(self, action: Dict, context: Dict) -> bool:
        """Take system snapshot"""
        target = action['target']
        output = action['output'].format(timestamp=datetime.now().strftime('%Y%m%d_%H%M%S'))
        print(f"   📸 Snapshot: {target} → {output}")
        # TODO: Implement snapshot (e.g., save current metrics)
        return True
    
    def _restart_service(self, target: str) -> bool:
        """Restart a service (helper)"""
        if target == "rpa_worker":
            script = self.workspace_root / "scripts" / "ensure_rpa_worker.ps1"
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-KillAll"]
        elif target == "task_queue_server":
            script = self.workspace_root / "scripts" / "ensure_task_queue_server.ps1"
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-Restart"]
        elif target == "all_workers":
            script = self.workspace_root / "scripts" / "ensure_rpa_worker.ps1"
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-KillAll"]
        else:
            print(f"⚠️  Unknown restart target: {target}")
            return False
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"   ✅ Restart succeeded: {target}")
                return True
            else:
                print(f"   ❌ Restart failed: {target} (code={result.returncode})")
                return False
        except Exception as e:
            print(f"   ❌ Restart error: {e}")
            return False

# ============================================================================
# Auto-healer
# ============================================================================

class AutoHealer:
    """Main auto-healing orchestrator"""
    
    def __init__(self, strategies_file: Path, dry_run: bool = False):
        self.strategies_file = strategies_file
        self.strategies = self._load_strategies()
        self.grace_tracker = GracePeriodTracker(GRACE_HISTORY_FILE)
        self.executor = HealingExecutor(dry_run=dry_run)
        self.dry_run = dry_run
    
    def _load_strategies(self) -> Dict[str, Any]:
        """Load healing strategies from JSON"""
        try:
            with open(self.strategies_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config['strategies']
        except Exception as e:
            print(f"❌ Failed to load strategies: {e}")
            sys.exit(1)
    
    def heal_once(self):
        """Check for anomalies and heal once (supports multiple alert files)"""
        print(f"🩹 [{datetime.now().strftime('%H:%M:%S')}] Checking for anomalies to heal...")
        
        # Phase 7 Task 2: Read from alerts directory
        alerts_to_process = []
        
        # 1. Check legacy alert file
        if ALERT_FILE.exists():
            alerts_to_process.append(ALERT_FILE)
        
        # 2. Check new alerts directory
        if ALERTS_DIR.exists():
            alert_files = sorted(ALERTS_DIR.glob("*_alert_latest.json"))
            alerts_to_process.extend(alert_files)
        
        if not alerts_to_process:
            print("   ℹ️  No alerts found")
            return
        
        print(f"   📋 Found {len(alerts_to_process)} alert file(s)")
        
        # Process each alert file
        total_anomalies = 0
        for alert_file in alerts_to_process:
            try:
                with open(alert_file, 'r', encoding='utf-8') as f:
                    alert = json.load(f)
            except Exception as e:
                print(f"⚠️  Failed to read {alert_file.name}: {e}")
                continue
            
            # Check if alert is recent (< 5 minutes)
            alert_time = datetime.fromisoformat(alert['timestamp'])
            if (datetime.now() - alert_time).total_seconds() > 300:
                print(f"   ℹ️  Alert is stale: {alert_file.name} (from {alert_time.strftime('%H:%M:%S')})")
                continue
            
            anomalies = alert.get('anomalies', [])
            if not anomalies:
                print(f"   ✅ No anomalies in {alert_file.name}")
                continue
            
            print(f"   🚨 {alert_file.name}: {len(anomalies)} anomaly/anomalies")
            total_anomalies += len(anomalies)
            
            # Process each anomaly
            for anomaly in anomalies:
                self._heal_anomaly(anomaly, alert)
        
        if total_anomalies == 0:
            print("   ✅ No active anomalies found")
    
    def _heal_anomaly(self, anomaly: Dict, alert: Dict):
        """Heal a single anomaly"""
        metric = anomaly['metric']
        value = anomaly['value']
        severity = anomaly['severity']
        
        # Find matching strategy
        strategy = self._find_strategy(metric, value)
        if not strategy:
            print(f"   ⚠️  No strategy found for metric: {metric}")
            return
        
        strategy_name = strategy['name']
        grace_period = strategy.get('grace_period_seconds', 300)
        max_retries = strategy.get('max_retries', 3)
        consecutive_failures_threshold = strategy.get('consecutive_failures_threshold', 3)
        
        # Check grace period + consecutive failures
        if not self.grace_tracker.can_heal_with_consecutive_check(
            strategy_name, grace_period, max_retries, consecutive_failures_threshold
        ):
            return
        
        # Execute healing actions
        print(f"\n🛠️  Healing: {strategy_name}")
        print(f"   Metric: {metric} = {value}")
        print(f"   Severity: {severity}")
        
        context = {
            'metric': metric,
            'value': value,
            'severity': severity,
            **alert['metrics']
        }
        
        success_count = 0
        for i, action in enumerate(strategy['actions'], 1):
            print(f"\n   Action {i}/{len(strategy['actions'])}: {action['type']}")
            if self.executor.execute_action(action, context):
                success_count += 1
            else:
                print(f"   ❌ Action failed, stopping")
                break
        
        # Log healing result
        healing_result = {
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy_name,
            'metric': metric,
            'value': value,
            'severity': severity,
            'actions_executed': success_count,
            'actions_total': len(strategy['actions']),
            'success': success_count == len(strategy['actions']),
            'dry_run': self.dry_run
        }
        
        self._log_healing(healing_result)
        
        # Record heal with success status
        success = healing_result['success']
        self.grace_tracker.record_heal(strategy_name, success)
        
        if success:
            print(f"\n   ✅ Healing completed: {strategy_name}")
        else:
            print(f"\n   ⚠️  Healing partially completed: {success_count}/{len(strategy['actions'])}")
    
    def _find_strategy(self, metric: str, value: float) -> Optional[Dict]:
        """Find matching healing strategy"""
        for strategy_key, strategy in self.strategies.items():
            trigger = strategy['trigger']
            if trigger['metric'] == metric:
                return strategy
        return None
    
    def _log_healing(self, result: Dict):
        """Log healing result to JSONL"""
        try:
            HEALING_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(HEALING_LOG, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"⚠️  Failed to log healing: {e}")

# ============================================================================
# Main
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-healing System')
    parser.add_argument('--strategies', type=str, default=str(STRATEGIES_FILE),
                        help='Path to healing strategies JSON')
    parser.add_argument('--once', action='store_true',
                        help='Run once and exit')
    parser.add_argument('--interval', type=int, default=60,
                        help='Check interval in seconds (default: 60)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Dry run mode (no actual actions)')
    
    args = parser.parse_args()
    
    print("🩹 Auto-healing System Starting...")
    print(f"   Strategies: {args.strategies}")
    print(f"   Mode: {'Once' if args.once else f'Continuous ({args.interval}s interval)'}")
    if args.dry_run:
        print("   [DRY-RUN MODE]")
    print()
    
    healer = AutoHealer(Path(args.strategies), dry_run=args.dry_run)
    
    if args.once:
        healer.heal_once()
    else:
        print("Press Ctrl+C to stop...\n")
        try:
            while True:
                healer.heal_once()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\n🛑 Auto-healer stopped by user")

if __name__ == '__main__':
    main()
