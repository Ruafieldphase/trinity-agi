#!/usr/bin/env python3
"""
Auto-Stabilizer: Lumen 감정 신호 기반 자동 안정화 시스템

Phase 2 Rest Integration 지원:
- 10분마다 Lumen 감정 신호 체크
- Fear ≥ 0.5 → Micro-Reset 트리거
- Fear ≥ 0.7 → Active Cooldown 시작
- Fear ≥ 0.9 → Deep Maintenance 제안

Usage:
    python scripts/auto_stabilizer.py --interval 600 --dry-run
    python scripts/auto_stabilizer.py --interval 600 --auto-execute
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Constants
WORKSPACE_ROOT = Path(__file__).parent.parent
LUMEN_STATE_PATH = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "lumen_state.json"
OUTPUT_DIR = WORKSPACE_ROOT / "outputs"
LOG_PATH = OUTPUT_DIR / "auto_stabilizer.log"
LOG_MAX_BYTES = 1 * 1024 * 1024
LOG_KEEP = 3
CONFIG_PATH = WORKSPACE_ROOT / "configs" / "auto_stabilizer.json"
SUMMARY_PATH = OUTPUT_DIR / "auto_stabilizer_summary.txt"

DEFAULT_CONFIG: Dict[str, Any] = {
    "interval_seconds": 600,
    "mode": "dry_run",
    "thresholds": {
        "micro_reset": 0.5,
        "active_cooldown": 0.7,
        "deep_maintenance": 0.9,
    },
}


def load_config() -> Dict[str, Any]:
    """Load configuration JSON with overrides from env."""
    config_path = Path(
        os.environ.get("AUTO_STABILIZER_CONFIG") or CONFIG_PATH
    )
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        merged = DEFAULT_CONFIG.copy()
        merged.update({k: v for k, v in data.items() if v is not None})
        thresholds = DEFAULT_CONFIG["thresholds"].copy()
        thresholds.update(
            (data.get("thresholds") or {})
        )
        merged["thresholds"] = thresholds
        return merged
    except Exception as exc:
        print(f"[WARN] Failed to load config {config_path}: {exc}")
        return DEFAULT_CONFIG.copy()


def _rotate_log(path: Path, max_bytes: int = LOG_MAX_BYTES, keep: int = LOG_KEEP) -> None:
    try:
        if not path.exists() or path.stat().st_size <= max_bytes:
            return
        for idx in range(keep, 1, -1):
            src = path.with_name(f"{path.name}.{idx - 1}")
            dst = path.with_name(f"{path.name}.{idx}")
            if src.exists():
                src.replace(dst)
        path.replace(path.with_name(f"{path.name}.1"))
    except Exception as exc:
        print(f"[WARN] Log rotation skipped: {exc}")

CONFIG = load_config()
THRESHOLDS = (CONFIG.get("thresholds") or {}).copy()
# Rest thresholds (from docs/AI_REST_INFORMATION_THEORY.md)
MICRO_RESET_THRESHOLD = float(THRESHOLDS.get("micro_reset", 0.5))
ACTIVE_COOLDOWN_THRESHOLD = float(THRESHOLDS.get("active_cooldown", 0.7))
DEEP_MAINTENANCE_THRESHOLD = float(THRESHOLDS.get("deep_maintenance", 0.9))
DEFAULT_INTERVAL = int(CONFIG.get("interval_seconds", 600))
MODE = str(CONFIG.get("mode", "dry_run")).lower()
DEFAULT_AUTO_EXECUTE = MODE == "auto_execute"
DEFAULT_DRY_RUN = MODE != "auto_execute"


def log_message(msg: str, level: str = "INFO") -> None:
    """로그 메시지 출력 및 파일 저장"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {msg}"
    print(log_line)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _rotate_log(LOG_PATH)
    with open(LOG_PATH, "a", encoding="utf-8") as sw:
        sw.write(log_line + "\n")


def record_summary(message: str) -> None:
    """Write a one-line summary for external dashboards."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(SUMMARY_PATH, "w", encoding="utf-8") as fp:
            fp.write(f"{datetime.now().isoformat()} {message}\n")
    except Exception as exc:
        print(f"[WARN] Failed to write summary: {exc}")


def read_lumen_state() -> Optional[Dict[str, Any]]:
    """Lumen 상태 파일 읽기"""
    try:
        if not LUMEN_STATE_PATH.exists():
            log_message(f"Lumen state file not found: {LUMEN_STATE_PATH}", "WARN")
            return None
        
        with open(LUMEN_STATE_PATH, "r", encoding="utf-8-sig") as f:
            state = json.load(f)
        
        return state
    except Exception as e:
        log_message(f"Error reading Lumen state: {e}", "ERROR")
        return None


def get_fear_signal(state: Dict[str, Any]) -> float:
    """Fear 신호 추출"""
    try:
        # Lumen state structure: {"emotion": {"fear": 0.0-1.0}}
        fear = state.get("emotion", {}).get("fear", 0.0)
        return float(fear)
    except Exception as e:
        log_message(f"Error extracting fear signal: {e}", "ERROR")
        return 0.0


def trigger_micro_reset(dry_run: bool = True) -> bool:
    """Micro-Reset 트리거"""
    log_message("Triggering Micro-Reset (context realignment)", "ACTION")

    script = WORKSPACE_ROOT / "scripts" / "micro_reset.ps1"
    if dry_run:
        log_message(f"  [DRY-RUN] Would execute: {script}", "INFO")
        return True

    try:
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-Force",
        ]
        log_message(f"  Executing: {' '.join(cmd)}", "INFO")
        subprocess.run(cmd, check=True)
        log_message("  Micro-Reset completed", "SUCCESS")
        return True
    except Exception as e:
        log_message(f"  Micro-Reset failed: {e}", "ERROR")
        return False


def trigger_active_cooldown(dry_run: bool = True) -> bool:
    """Active Cooldown 시작"""
    log_message("Triggering Active Cooldown (5-10min stabilization)", "ACTION")

    script = WORKSPACE_ROOT / "scripts" / "active_cooldown.ps1"
    if dry_run:
        log_message(f"  [DRY-RUN] Would execute: {script}", "INFO")
        return True

    try:
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ]
        log_message(f"  Executing: {' '.join(cmd)}", "INFO")
        subprocess.run(cmd, check=True)
        log_message("  Active Cooldown started", "SUCCESS")
        return True
    except Exception as e:
        log_message(f"  Active Cooldown failed: {e}", "ERROR")
        return False


def suggest_deep_maintenance(dry_run: bool = True) -> None:
    """Deep Maintenance 제안"""
    log_message("ALERT: Deep Maintenance recommended (index rebuild)", "CRITICAL")

    script = WORKSPACE_ROOT / "scripts" / "deep_maintenance.ps1"
    if dry_run:
        log_message(f"  [DRY-RUN] Would execute: {script}", "INFO")
    else:
        log_message(f"  Manual execution required: {script}", "WARN")


def evaluate_and_act(fear: float, dry_run: bool = True, auto_execute: bool = False) -> None:
    """Fear 신호 평가 및 액션 실행"""
    log_message(f"Current fear signal: {fear:.3f}", "INFO")
    
    if fear >= DEEP_MAINTENANCE_THRESHOLD:
        suggest_deep_maintenance(dry_run)
        record_summary(f"Deep Maintenance {'recommended' if dry_run else 'alert'} (fear={fear:.3f}, dry_run={dry_run})")
    elif fear >= ACTIVE_COOLDOWN_THRESHOLD:
        if auto_execute:
            success = trigger_active_cooldown(dry_run)
            record_summary(f"Active Cooldown triggered (success={success}, dry_run={dry_run}, fear={fear:.3f})")
        else:
            log_message(f"  Fear {fear:.3f} ≥ {ACTIVE_COOLDOWN_THRESHOLD} → Active Cooldown recommended", "WARN")
            record_summary(f"Active Cooldown recommended (auto_execute=False, fear={fear:.3f})")
    elif fear >= MICRO_RESET_THRESHOLD:
        if auto_execute:
            success = trigger_micro_reset(dry_run)
            record_summary(f"Micro-Reset triggered (success={success}, dry_run={dry_run}, fear={fear:.3f})")
        else:
            log_message(f"  Fear {fear:.3f} ≥ {MICRO_RESET_THRESHOLD} → Micro-Reset recommended", "WARN")
            record_summary(f"Micro-Reset recommended (auto_execute=False, fear={fear:.3f})")
    else:
        log_message(f"  System stable (fear < {MICRO_RESET_THRESHOLD})", "INFO")
        record_summary(f"System stable (fear={fear:.3f})")


def monitor_loop(interval: int = 600, dry_run: bool = True, auto_execute: bool = False) -> None:
    """모니터링 루프"""
    log_message(
        f"Auto-Stabilizer started (interval={interval}s, dry_run={dry_run}, auto_execute={auto_execute})",
        "INFO",
    )
    
    try:
        while True:
            state = read_lumen_state()
            if state:
                fear = get_fear_signal(state)
                evaluate_and_act(fear, dry_run, auto_execute)
            else:
                log_message("  Unable to read Lumen state, skipping evaluation", "WARN")
            
            log_message(f"Sleeping for {interval}s...\n", "INFO")
            time.sleep(interval)
    except KeyboardInterrupt:
        log_message("Auto-Stabilizer stopped by user", "INFO")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Auto-Stabilizer: Lumen 감정 신호 기반 자동 안정화")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help=f"Check interval in seconds (default: {DEFAULT_INTERVAL})")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Enable dry-run mode")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Disable dry-run mode")
    parser.add_argument("--auto-execute", dest="auto_execute", action="store_true", help="Auto-execute recovery actions")
    parser.add_argument("--no-auto-execute", dest="auto_execute", action="store_false", help="Disable auto execution")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.set_defaults(dry_run=DEFAULT_DRY_RUN, auto_execute=DEFAULT_AUTO_EXECUTE)
    
    args = parser.parse_args()
    
    if args.once:
        state = read_lumen_state()
        if state:
            fear = get_fear_signal(state)
            evaluate_and_act(fear, args.dry_run, args.auto_execute)
        else:
            log_message("Unable to read Lumen state", "ERROR")
            sys.exit(1)
    else:
        monitor_loop(args.interval, args.dry_run, args.auto_execute)


if __name__ == "__main__":
    main()
