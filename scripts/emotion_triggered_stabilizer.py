#!/usr/bin/env python3
"""
Emotion-Triggered Stabilizer: Realtime Pipeline + Auto-Stabilizer 통합

Phase 5: Auto-Stabilizer Integration
- Realtime Pipeline에서 Lumen 감정 신호 모니터링
- Fear 레벨별 자동 안정화 트리거
- Resonance simulation + Emotion signals = Smart maintenance

Usage:
    python scripts/emotion_triggered_stabilizer.py --check-interval 300
    python scripts/emotion_triggered_stabilizer.py --check-interval 300 --auto-execute
    python scripts/emotion_triggered_stabilizer.py --once
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Constants
WORKSPACE_ROOT = Path(__file__).parent.parent
REALTIME_STATUS_JSON = WORKSPACE_ROOT / "outputs" / "realtime_pipeline_status.json"
LUMEN_STATE_PATH = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "lumen_state.json"
OUTPUT_DIR = WORKSPACE_ROOT / "outputs"
LOG_PATH = OUTPUT_DIR / "emotion_stabilizer.log"
STABILIZER_STATE_PATH = OUTPUT_DIR / "stabilizer_state.json"

# Thresholds (from AI_REST_INFORMATION_THEORY.md)
MICRO_RESET_THRESHOLD = 0.5
ACTIVE_COOLDOWN_THRESHOLD = 0.7
DEEP_MAINTENANCE_THRESHOLD = 0.9

# Cooldown periods (seconds)
MICRO_RESET_COOLDOWN = 600  # 10 minutes
ACTIVE_COOLDOWN_COOLDOWN = 1800  # 30 minutes
DEEP_MAINTENANCE_COOLDOWN = 3600  # 1 hour


def log(msg: str, level: str = "INFO") -> None:
    """로그 출력 및 파일 저장"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {msg}"
    print(log_line)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    """JSON 파일 읽기"""
    try:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        log(f"Error reading {path}: {e}", "ERROR")
        return None


def write_json(path: Path, data: Dict[str, Any]) -> None:
    """JSON 파일 쓰기"""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Error writing {path}: {e}", "ERROR")


def run_realtime_pipeline() -> bool:
    """Realtime Pipeline 실행하여 최신 상태 업데이트"""
    log("Running Realtime Pipeline to update emotion signals...", "INFO")
    
    try:
        script = WORKSPACE_ROOT / "scripts" / "realtime_resonance_pipeline.py"
        python_exe = WORKSPACE_ROOT / "fdo_agi_repo" / ".venv" / "Scripts" / "python.exe"
        
        if not python_exe.exists():
            python_exe = "python"
        
        cmd = [
            str(python_exe),
            str(script),
            "--metrics", "outputs/monitoring_metrics_latest.json",
            "--hours", "24",
            "--output-json", "outputs/realtime_pipeline_status.json",
            "--output-md", "outputs/realtime_pipeline_status.md",
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=WORKSPACE_ROOT)
        if result.returncode == 0:
            log("  Realtime Pipeline updated successfully", "SUCCESS")
            return True
        else:
            log(f"  Realtime Pipeline failed: {result.stderr}", "ERROR")
            return False
    except Exception as e:
        log(f"  Error running Realtime Pipeline: {e}", "ERROR")
        return False


def get_emotion_signals() -> Optional[Dict[str, Any]]:
    """Realtime Pipeline에서 감정 신호 읽기"""
    status = read_json(REALTIME_STATUS_JSON)
    if not status:
        return None
    
    lumen_state = status.get("lumen_state")
    if not lumen_state:
        log("No Lumen state in realtime status", "WARN")
        return None
    
    return lumen_state


def get_stabilizer_state() -> Dict[str, Any]:
    """안정화기 상태 읽기 (마지막 액션 시간 등)"""
    state = read_json(STABILIZER_STATE_PATH)
    if not state:
        return {
            "last_micro_reset": 0,
            "last_active_cooldown": 0,
            "last_deep_maintenance": 0,
        }
    return state


def update_stabilizer_state(action: str) -> None:
    """안정화기 상태 업데이트"""
    state = get_stabilizer_state()
    now = time.time()
    
    if action == "micro_reset":
        state["last_micro_reset"] = now
    elif action == "active_cooldown":
        state["last_active_cooldown"] = now
    elif action == "deep_maintenance":
        state["last_deep_maintenance"] = now
    
    write_json(STABILIZER_STATE_PATH, state)


def is_cooldown_active(action: str) -> bool:
    """Cooldown 기간 체크"""
    state = get_stabilizer_state()
    now = time.time()
    
    cooldowns = {
        "micro_reset": (state.get("last_micro_reset", 0), MICRO_RESET_COOLDOWN),
        "active_cooldown": (state.get("last_active_cooldown", 0), ACTIVE_COOLDOWN_COOLDOWN),
        "deep_maintenance": (state.get("last_deep_maintenance", 0), DEEP_MAINTENANCE_COOLDOWN),
    }
    
    last_time, cooldown_period = cooldowns.get(action, (0, 0))
    elapsed = now - last_time
    
    if elapsed < cooldown_period:
        remaining = int(cooldown_period - elapsed)
        log(f"  {action} cooldown active: {remaining}s remaining", "INFO")
        return True
    return False


def execute_micro_reset(dry_run: bool = True) -> bool:
    """Micro-Reset 실행"""
    log("🔄 Executing Micro-Reset (context realignment)...", "ACTION")
    
    if is_cooldown_active("micro_reset"):
        return False
    
    script = WORKSPACE_ROOT / "scripts" / "micro_reset.ps1"
    if dry_run:
        log(f"  [DRY-RUN] Would execute: {script}", "INFO")
        return True
    
    try:
        cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-Force"]
        subprocess.run(cmd, check=True, cwd=WORKSPACE_ROOT)
        log("  ✅ Micro-Reset completed", "SUCCESS")
        update_stabilizer_state("micro_reset")
        return True
    except Exception as e:
        log(f"  ❌ Micro-Reset failed: {e}", "ERROR")
        return False


def execute_active_cooldown(dry_run: bool = True) -> bool:
    """Active Cooldown 실행"""
    log("❄️ Executing Active Cooldown (5-10min stabilization)...", "ACTION")
    
    if is_cooldown_active("active_cooldown"):
        return False
    
    script = WORKSPACE_ROOT / "scripts" / "active_cooldown.ps1"
    if dry_run:
        log(f"  [DRY-RUN] Would execute: {script}", "INFO")
        return True
    
    try:
        cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)]
        subprocess.run(cmd, check=True, cwd=WORKSPACE_ROOT)
        log("  ✅ Active Cooldown started", "SUCCESS")
        update_stabilizer_state("active_cooldown")
        return True
    except Exception as e:
        log(f"  ❌ Active Cooldown failed: {e}", "ERROR")
        return False


def suggest_deep_maintenance() -> None:
    """Deep Maintenance 제안"""
    log("⚠️ CRITICAL: Deep Maintenance recommended (index rebuild)", "CRITICAL")
    
    if is_cooldown_active("deep_maintenance"):
        return
    
    script = WORKSPACE_ROOT / "scripts" / "deep_maintenance.ps1"
    log(f"  💡 Manual execution required: {script}", "WARN")
    log(f"  📋 Or use: python scripts/deep_maintenance.py", "WARN")
    update_stabilizer_state("deep_maintenance")


def evaluate_and_stabilize(
    fear: float,
    joy: float,
    trust: float,
    dry_run: bool = True,
    auto_execute: bool = False,
) -> None:
    """감정 신호 평가 및 안정화 액션"""
    log(f"Emotion signals: Fear={fear:.3f}, Joy={joy:.3f}, Trust={trust:.3f}", "INFO")
    
    # Fear-based stabilization
    if fear >= DEEP_MAINTENANCE_THRESHOLD:
        suggest_deep_maintenance()
    elif fear >= ACTIVE_COOLDOWN_THRESHOLD:
        if auto_execute:
            execute_active_cooldown(dry_run)
        else:
            log(f"  💡 Fear {fear:.3f} ≥ {ACTIVE_COOLDOWN_THRESHOLD} → Active Cooldown recommended", "WARN")
    elif fear >= MICRO_RESET_THRESHOLD:
        if auto_execute:
            execute_micro_reset(dry_run)
        else:
            log(f"  💡 Fear {fear:.3f} ≥ {MICRO_RESET_THRESHOLD} → Micro-Reset recommended", "WARN")
    else:
        log(f"  ✅ System stable (Fear < {MICRO_RESET_THRESHOLD})", "INFO")
    
    # Joy/Trust-based insights
    if joy < 0.5:
        log(f"  ⚠️ Low Joy ({joy:.3f}) detected - consider positive reinforcement", "INFO")
    if trust < 0.5:
        log(f"  ⚠️ Low Trust ({trust:.3f}) detected - verify system integrity", "INFO")


def check_and_stabilize(dry_run: bool = True, auto_execute: bool = False) -> bool:
    """Realtime Pipeline 체크 및 안정화 실행"""
    # Update realtime pipeline
    if not run_realtime_pipeline():
        log("Failed to update Realtime Pipeline", "ERROR")
        return False
    
    # Read emotion signals
    emotion = get_emotion_signals()
    if not emotion:
        log("No emotion signals available", "WARN")
        return False
    
    fear = emotion.get("fear", 0.0)
    joy = emotion.get("joy", 0.5)
    trust = emotion.get("trust", 0.5)
    
    # Evaluate and stabilize
    evaluate_and_stabilize(fear, joy, trust, dry_run, auto_execute)
    return True


def monitor_loop(interval: int = 300, dry_run: bool = True, auto_execute: bool = False) -> None:
    """모니터링 루프"""
    log(
        f"Emotion-Triggered Stabilizer started (interval={interval}s, dry_run={dry_run}, auto={auto_execute})",
        "INFO",
    )
    
    try:
        while True:
            log("=" * 60, "INFO")
            check_and_stabilize(dry_run, auto_execute)
            log(f"Sleeping for {interval}s...\n", "INFO")
            time.sleep(interval)
    except KeyboardInterrupt:
        log("Emotion-Triggered Stabilizer stopped by user", "INFO")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Emotion-Triggered Stabilizer")
    parser.add_argument("--check-interval", type=int, default=300, help="Check interval in seconds (default: 300)")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode (no actual execution)")
    parser.add_argument("--auto-execute", action="store_true", help="Auto-execute stabilization actions")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    if args.once:
        success = check_and_stabilize(args.dry_run, args.auto_execute)
        sys.exit(0 if success else 1)
    else:
        monitor_loop(args.check_interval, args.dry_run, args.auto_execute)


if __name__ == "__main__":
    main()
