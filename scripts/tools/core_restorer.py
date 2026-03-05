import os
import shutil
from pathlib import Path

SRC = r"C:\workspace\agi\scripts"
DEST = r"C:\workspace2\scripts\core"
os.makedirs(DEST, exist_ok=True)

def restore_core_scripts():
    all_files = [os.path.join(SRC, f) for f in os.listdir(SRC) if os.path.isfile(os.path.join(SRC, f)) and f.endswith(".py")]
    all_files.sort(key=os.path.getmtime, reverse=True)
    
    count = 0
    for f in all_files[:10]:
        try:
            shutil.copy2(f, DEST)
            print(f"✅ Restored: {os.path.basename(f)}")
            count += 1
        except Exception as e:
            print(f"❌ Failed to restore {f}: {e}")
            
    print(f"\n--- Total {count} core scripts restored to {DEST} ---")

if __name__ == "__main__":
    restore_core_scripts()
