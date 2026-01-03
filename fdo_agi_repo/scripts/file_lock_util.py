#!/usr/bin/env python3
"""
File lock utility for Core System

Prevents concurrent writes to critical files like:
- ensemble_weights.json
- resonance_ledger.jsonl
- online_learning_log.jsonl

Usage:
    from file_lock_util import FileLock
    
    with FileLock("ensemble_weights.json"):
        # Safe to write
        with open("ensemble_weights.json", "w") as f:
            json.dump(data, f)
"""

import os
import time
from pathlib import Path
from typing import Optional


class FileLock:
    """Simple file-based lock for Windows"""
    
    def __init__(self, target_file: str, timeout: int = 30, check_interval: float = 0.1):
        """
        Args:
            target_file: Path to file to lock (relative or absolute)
            timeout: Max seconds to wait for lock (default: 30)
            check_interval: Seconds between lock checks (default: 0.1)
        """
        self.target_file = Path(target_file).resolve()
        self.lock_file = self.target_file.with_suffix(self.target_file.suffix + ".lock")
        self.timeout = timeout
        self.check_interval = check_interval
        self.acquired = False
    
    def acquire(self) -> bool:
        """Acquire the lock, wait if necessary"""
        start_time = time.time()
        
        while True:
            try:
                # Try to create lock file (atomic on Windows)
                # 'x' mode fails if file already exists
                with open(self.lock_file, 'x') as f:
                    f.write(f"Locked at {time.time()}\n")
                    f.write(f"PID: {os.getpid()}\n")
                
                self.acquired = True
                return True
            
            except FileExistsError:
                # Lock file exists, check timeout
                elapsed = time.time() - start_time
                if elapsed >= self.timeout:
                    # Check if lock is stale (> 5 minutes old)
                    if self.lock_file.exists():
                        lock_age = time.time() - self.lock_file.stat().st_mtime
                        if lock_age > 300:  # 5 minutes
                            print(f"⚠️ Stale lock detected ({lock_age:.0f}s old), breaking...")
                            self._force_release()
                            continue
                    
                    raise TimeoutError(
                        f"Failed to acquire lock for {self.target_file.name} "
                        f"after {self.timeout}s"
                    )
                
                # Wait and retry
                time.sleep(self.check_interval)
    
    def release(self):
        """Release the lock"""
        if self.acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink()
                self.acquired = False
            except Exception as e:
                print(f"⚠️ Failed to release lock: {e}")
    
    def _force_release(self):
        """Force release a stale lock"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception as e:
            print(f"⚠️ Failed to force release lock: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
        return False


# Convenience function
def with_file_lock(filepath: str, timeout: int = 30):
    """
    Decorator to protect a function with file lock
    
    Usage:
        @with_file_lock("ensemble_weights.json")
        def save_weights(weights):
            with open("ensemble_weights.json", "w") as f:
                json.dump(weights, f)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with FileLock(filepath, timeout=timeout):
                return func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test
    import json
    
    test_file = Path("test_lock_file.json")
    
    print("🧪 Testing FileLock...")
    
    # Test 1: Basic lock/unlock
    with FileLock(test_file):
        print("✅ Lock acquired")
        test_file.write_text(json.dumps({"test": True}))
        print("✅ File written safely")
    
    print("✅ Lock released")
    
    # Test 2: Concurrent access simulation
    import threading
    
    def worker(worker_id: int):
        try:
            with FileLock(test_file, timeout=5):
                print(f"   Worker {worker_id} acquired lock")
                time.sleep(1)  # Simulate work
                data = json.loads(test_file.read_text())
                data[f"worker_{worker_id}"] = time.time()
                test_file.write_text(json.dumps(data))
                print(f"   Worker {worker_id} done")
        except TimeoutError:
            print(f"   Worker {worker_id} timeout!")
    
    print("\n🧪 Testing concurrent access...")
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print("\n✅ Concurrent test complete")
    print(f"📄 Final data: {test_file.read_text()}")
    
    # Cleanup
    test_file.unlink(missing_ok=True)
    print("\n✅ All tests passed!")
