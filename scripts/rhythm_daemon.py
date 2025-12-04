#!/usr/bin/env python3
"""
Rhythm Daemon Wrapper
=====================
Wraps rhythm_think.py to run continuously as a daemon.
"""
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent
RHYTHM_SCRIPT = WORKSPACE / "scripts" / "rhythm_think.py"
INTERVAL = 60  # Run every 60 seconds

def main():
    print(f"🎵 Rhythm Daemon started at {datetime.now()}")
    print(f"   Executing: {RHYTHM_SCRIPT}")
    print(f"   Interval: {INTERVAL}s")
    print("=" * 60)
    
    cycle = 0
    while True:
        cycle += 1
        try:
            print(f"\n[Cycle {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            result = subprocess.run(
                [sys.executable, str(RHYTHM_SCRIPT)], 
                check=True,
                capture_output=False
            )
            print(f"✅ Cycle {cycle} completed successfully")
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Rhythm cycle {cycle} failed with exit code {e.returncode}")
            
        except KeyboardInterrupt:
            print(f"\n👋 Rhythm daemon stopped after {cycle} cycles")
            break
            
        except Exception as e:
            print(f"❌ Unexpected error in cycle {cycle}: {e}")
            
        # Sleep until next cycle
        print(f"💤 Sleeping {INTERVAL}s until next cycle...")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
