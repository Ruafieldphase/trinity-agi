import sys
import os
import sqlite3
import time
sys.path.append("c:/workspace/agi")
from services.experience_vault import ExperienceVault

def test_pruning():
    print("--- Simulating Memory Pruning (Ephemeral Minimalism) ---")
    vault = ExperienceVault()
    conn = sqlite3.connect(vault.db_path)
    cursor = conn.cursor()
    
    # 1. Inject old memory (60 days ago)
    old_time = time.time() - (60 * 24 * 3600)
    cursor.execute("INSERT INTO experiences (goal, last_used) VALUES (?, ?)", ("Old Memory", old_time))
    conn.commit()
    print(f"Inserted 'Old Memory' dated {time.ctime(old_time)}")
    
    # 2. Inject fresh memory (1 day ago)
    fresh_time = time.time() - (1 * 24 * 3600)
    cursor.execute("INSERT INTO experiences (goal, last_used) VALUES (?, ?)", ("Fresh Memory", fresh_time))
    conn.commit()
    print(f"Inserted 'Fresh Memory' dated {time.ctime(fresh_time)}")
    
    conn.close()
    
    # 3. Execute Pruning (Keep 30 days)
    print("\nAction: Pruning memories older than 30 days...")
    vault.prune_old_experiences(days_to_keep=30)
    
    # 4. Verify
    conn = sqlite3.connect(vault.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT goal FROM experiences")
    remaining = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print(f"\nRemaining Memories: {remaining}")
    
    if "Old Memory" not in remaining and "Fresh Memory" in remaining:
        print("✅ SUCCESS: Old memory faded away, fresh memory remains.")
    else:
        print("❌ FAILURE: Pruning logic incorrect.")

if __name__ == "__main__":
    test_pruning()
