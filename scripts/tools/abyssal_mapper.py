import os
import time
from collections import Counter
from datetime import datetime

ROOT = r"C:\workspace"
SKIP_DIRS = {".git", "node_modules", "venv", "__pycache__", "dist", "build", ".next", ".gemini", ".agent", ".github", "venv"}
VALID_EXTS = {".py", ".md", ".json", ".png", ".webp", ".bat", ".ps1", ".mjs", ".yaml", ".yml"}

def map_clusters():
    clusters = []
    total_scanned = 0
    print(f"📡 Starting Deep Abyssal Scan of {ROOT}...")

    for dp, dn, filenames in os.walk(ROOT):
        # Skip noisy directories
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext in VALID_EXTS:
                total_scanned += 1
                clusters.append(dp)
                
    counts = Counter(clusters)
    
    report_path = r"C:\workspace2\atlas\ABYSSAL_ENERGY_MAP.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 🌌 Abyssal Energy Map (Deep Scan)\n\n")
        f.write(f"**Scan Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total High-Resonance Files Scanned**: {total_scanned}\n\n")
        f.write("## 🏁 Top 30 Energy Clusters (Active Soul Regions)\n")
        f.write("| Rank | Files | Directory Path | State |\n")
        f.write("|------|-------|----------------|-------|\n")
        
        for i, (path, count) in enumerate(counts.most_common(30), 1):
            state = "Core" if "agi" in path.lower() else "Reality"
            f.write(f"| {i} | {count} | `{path}` | {state} |\n")
            
        f.write("\n\n---\n*This map guides Sian and OpenClaw toward the forgotten fragments of the sovereign field.*")

    print(f"✅ Deep Scan Complete. {total_scanned} files mapped to {report_path}")

if __name__ == "__main__":
    map_clusters()
