#!/usr/bin/env python3
"""
Test concurrent Phase 6l learning execution to verify FileLock prevents corruption.
Spawns 3 worker processes that all try to run binoche_online_learner.py simultaneously.
"""

import subprocess
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
VENV_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
LEARNER_SCRIPT = REPO_ROOT / "scripts" / "rune" / "binoche_online_learner.py"
WEIGHTS_FILE = REPO_ROOT / "outputs" / "ensemble_weights.json"
LOG_FILE = REPO_ROOT / "outputs" / "online_learning_log.jsonl"


def run_learner(worker_id: int) -> dict:
    """Run binoche_online_learner.py and return result."""
    print(f"Worker {worker_id}: Starting Phase 6l...")
    start_time = time.time()
    
    cmd = [
        str(VENV_PYTHON) if VENV_PYTHON.exists() else "python",
        str(LEARNER_SCRIPT),
        "--window-hours", "24",
        "--learning-rate", "0.01"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8'
        )
        elapsed = time.time() - start_time
        
        success = result.returncode == 0
        status_emoji = "OK" if success else "FAIL"
        print(f"Worker {worker_id}: {status_emoji} ({elapsed:.1f}s)")
        
        # Show stderr on failure for debugging
        if not success:
            if result.stderr:
                print(f"  STDERR: {result.stderr[:500]}")
            if result.stdout:
                print(f"  STDOUT: {result.stdout[:500]}")
        
        return {
            'worker_id': worker_id,
            'success': success,
            'elapsed': elapsed,
            'stdout': result.stdout[-500:] if result.stdout else "",
            'stderr': result.stderr[-500:] if result.stderr else ""
        }
    except Exception as e:
        print(f"Worker {worker_id}: ❌ Exception: {e}")
        return {
            'worker_id': worker_id,
            'success': False,
            'elapsed': time.time() - start_time,
            'error': str(e)
        }


def validate_weights_file() -> bool:
    """Check if ensemble_weights.json is valid JSON and not corrupted."""
    try:
        with open(WEIGHTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check required keys
        if 'weights' not in data or 'timestamp' not in data:
            print("Weights file missing required keys")
            return False
        
        # Check weights sum to ~1.0
        weights = data['weights']
        total = sum(weights.values())
        if not (0.99 <= total <= 1.01):
            print(f"Weights sum to {total:.4f}, expected ~1.0")
            return False
        
        print(f"Weights file valid: {weights}")
        return True
    except json.JSONDecodeError as e:
        print(f"Weights file corrupted (JSON decode error): {e}")
        return False
    except Exception as e:
        print(f"Weights file validation error: {e}")
        return False


def validate_log_file() -> bool:
    """Check if online_learning_log.jsonl has no corrupted lines."""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        valid_count = 0
        for i, line in enumerate(lines):
            try:
                json.loads(line)
                valid_count += 1
            except json.JSONDecodeError:
                print(f"Log file line {i+1} corrupted: {line[:50]}...")
                return False
        
        print(f"Log file valid: {valid_count} entries")
        return True
    except Exception as e:
        print(f"Log file validation error: {e}")
        return False


def main():
    print("=" * 60)
    print("Testing Concurrent Phase 6l Learning")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Workers: 3")
    print(f"Target: {WEIGHTS_FILE.name}, {LOG_FILE.name}")
    print()
    
    # Backup current weights
    backup_path = WEIGHTS_FILE.with_suffix('.json.backup')
    if WEIGHTS_FILE.exists():
        import shutil
        shutil.copy2(WEIGHTS_FILE, backup_path)
        print(f"Backed up weights to {backup_path.name}")
    
    # Run 3 workers concurrently
    print("\nLaunching 3 concurrent workers...")
    with ProcessPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_learner, i) for i in range(3)]
        results = [future.result() for future in as_completed(futures)]
    
    # Analyze results
    print("\n" + "=" * 60)
    print("Results:")
    success_count = sum(1 for r in results if r['success'])
    print(f"  Success: {success_count}/3")
    print(f"  Failed: {3 - success_count}/3")
    
    for r in sorted(results, key=lambda x: x['worker_id']):
        status = "OK" if r['success'] else "FAIL"
        print(f"  Worker {r['worker_id']}: {status} ({r['elapsed']:.1f}s)")
    
    # Validate files
    print("\nValidating output files...")
    weights_ok = validate_weights_file()
    log_ok = validate_log_file()
    
    # Final verdict
    print("\n" + "=" * 60)
    if success_count >= 2 and weights_ok and log_ok:
        print("Concurrent test PASSED!")
        print("   - Multiple workers executed successfully")
        print("   - No file corruption detected")
        print("   - FileLock working correctly")
    else:
        print("Concurrent test FAILED!")
        if not weights_ok:
            print("   - Weights file corrupted")
        if not log_ok:
            print("   - Log file corrupted")
        if success_count < 2:
            print(f"   - Only {success_count}/3 workers succeeded")
    print("=" * 60)


if __name__ == '__main__':
    main()
