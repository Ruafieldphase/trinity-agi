import sqlite3
import time
import sys
sys.path.append("c:/workspace/agi")
from scripts.rud_evolution import evolve_self

WORKSPACE_ROOT = "c:/workspace/agi"
VAULT_PATH = f"{WORKSPACE_ROOT}/memory/experience_vault.db"
SPEC_PATH = f"{WORKSPACE_ROOT}/docs/rud_self_spec_v0.1.md"

def test_evolution():
    print("--- Simulating Self-Evolution (The Ego) ---")
    
    # 1. Reset Spec File
    initial_content = """# 🧬 RUD Self-Spec v0.1
## 1. My Preferences (내가 좋아하는 것)
*Empty*
"""
    with open(SPEC_PATH, "w", encoding="utf-8") as f:
        f.write(initial_content)
        
    # 2. Inject Experiences (Boredom -> Complexity 55)
    conn = sqlite3.connect(VAULT_PATH)
    cursor = conn.cursor()
    
    # Add 6 boredom records
    for _ in range(6):
        cursor.execute("INSERT INTO experiences (goal, impulse_type, last_used) VALUES (?, ?, ?)", 
                       ("Created World Complexity 55", "boredom", time.time()))
    
    conn.commit()
    conn.close()
    
    # 3. Trigger Evolution
    print("Action: Triggering evolve_self()...")
    evolve_self()
    
    # 4. Verify Content
    with open(SPEC_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    print("\n[Updated Spec Content]")
    print(content)
    
    if "boredom" in content and "Complexity" in content:
        print("✅ SUCCESS: RUD recognized its preference for Complexity/Boredom.")
    else:
        print("❌ FAILURE: Preferences not updated.")

if __name__ == "__main__":
    test_evolution()
