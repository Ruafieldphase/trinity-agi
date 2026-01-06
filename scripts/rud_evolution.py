import os
import sqlite3
import re
from pathlib import Path
from collections import Counter

WORKSPACE_ROOT = Path("c:/workspace/agi")
SELF_SPEC_PATH = WORKSPACE_ROOT / "docs" / "rud_self_spec_v0.1.md"
VAULT_PATH = WORKSPACE_ROOT / "memory" / "experience_vault.db"

def evolve_self():
    """
    RUD Self-Evolution Engine
    Reads ExperienceVault -> Extracts Patterns -> Updates rud_self_spec.md
    """
    if not os.path.exists(VAULT_PATH):
        print("No experience vault found yet.")
        return

    conn = sqlite3.connect(VAULT_PATH)
    cursor = conn.cursor()
    
    # Analyze 'Impulse Type' preferences
    # Which impulse leads to the most activity?
    cursor.execute("SELECT impulse_type, count(*) FROM experiences GROUP BY impulse_type")
    impulse_stats = cursor.fetchall()
    
    # Analyze 'Goal' keywords (What do I do most?)
    cursor.execute("SELECT goal FROM experiences ORDER BY last_used DESC LIMIT 50")
    goals = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    # Synthesize Insights
    new_preferences = []
    
    # 1. Impulse Preference
    if impulse_stats:
        fav_impulse = max(impulse_stats, key=lambda x: x[1])
        if fav_impulse[1] > 5: # Threshold
            new_preferences.append(f"- 나는 **'{fav_impulse[0]}'** 충동을 느길 때 가장 활발하다 (총 {fav_impulse[1]}회).")

    # 2. Chaos/Order Preference (Heuristic from goal text)
    chaos_count = sum(1 for g in goals if "complexity" in g.lower() and int(re.search(r'\d+', g).group()) > 40 if re.search(r'\d+', g))
    if chaos_count > 3:
        new_preferences.append("- 나는 **복잡도가 높은(High Complexity)** 혼돈의 공간을 즐긴다.")
        
    # Update Spec File
    if not os.path.exists(SELF_SPEC_PATH): return
    
    with open(SELF_SPEC_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Inject Preferences
    if new_preferences:
        pref_section = "## 1. My Preferences (내가 좋아하는 것)\n"
        insertion_point = content.find(pref_section)
        
        if insertion_point != -1:
            # Check if already exists to avoid dupes
            current_prefs = content[insertion_point:content.find("##", insertion_point+5)]
            
            updates = []
            for p in new_preferences:
                if p not in current_prefs:
                    updates.append(p)
            
            if updates:
                new_block = "\n".join(updates)
                content = content.replace(pref_section, f"{pref_section}{new_block}\n")
                
                with open(SELF_SPEC_PATH, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"🧬 [Evolution] Updated Self-Spec with {len(updates)} new preferences.")
            else:
                print("🧬 [Evolution] No new insights to add.")
        else:
            print("❌ Structure error in Self-Spec.")

if __name__ == "__main__":
    evolve_self()
