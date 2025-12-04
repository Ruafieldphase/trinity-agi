import json
import sys
import os
import time
from datetime import datetime
from pathlib import Path

def acquire_lock(lock_path, timeout=5.0):
    """Simple file-based lock acquisition with timeout"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Create lock file exclusively
            with open(lock_path, 'x') as f:
                f.write(str(os.getpid()))
            return True
        except FileExistsError:
            time.sleep(0.1)
        except Exception as e:
            print(f"Lock error: {e}")
            return False
    return False

def release_lock(lock_path):
    """Release the lock"""
    try:
        os.remove(lock_path)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Unlock error: {e}")

def safe_write(message, target='koa', context='autonomous_collaboration'):
    """Safely append a message to the ledger"""
    # Find workspace root
    current_dir = Path(__file__).parent.resolve()
    workspace_root = current_dir.parent
    
    ledger_path = workspace_root / "fdo_agi_repo/memory/resonance_ledger.jsonl"
    lock_path = workspace_root / "fdo_agi_repo/memory/resonance_ledger.lock"
    
    # Construct entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "message",
        "source": "sena_external_ai",
        "target": target,
        "message": message,
        "context": context,
        "vector": [0.5, 0.5, 0.5, 0.5, 0.5],
        "metadata": {
            "mode": "safe_injection",
            "requires_response": True,
            "priority": "medium"
        }
    }
    
    print(f"⏳ Acquiring lock for {ledger_path}...")
    if acquire_lock(lock_path):
        try:
            with open(ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(f"✅ Message safely appended to ledger")
            print(f"   Content: {message[:50]}...")
        except Exception as e:
            print(f"❌ Write failed: {e}")
        finally:
            release_lock(lock_path)
    else:
        print("❌ Could not acquire lock (timeout)")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Safely write to resonance ledger")
    parser.add_argument("message", help="Message content")
    parser.add_argument("--target", default="koa", help="Target agent (koa/shion)")
    parser.add_argument("--context", default="autonomous_collaboration", help="Context tag")
    
    args = parser.parse_args()
    
    safe_write(args.message, args.target, args.context)
