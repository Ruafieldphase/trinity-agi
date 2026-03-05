import os
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
import subprocess

# --- Root Configuration ---
WORKSPACE_ROOT = Path("C:/workspace")
AGI_ROOT = Path("C:/workspace/agi")
LOG_PATH = AGI_ROOT / "outputs" / "mitochondria_v3.log"
GROWTH_LOG = Path("C:/workspace2/atlas/GROWTH_LOG.md")

class ShionMitochondriaV3:
    """
    The persistent metabolic layer.
    Inherits the 'body' of Shion to sense and react to workspace atoms.
    """
    def __init__(self):
        self.last_scan_time = time.time() - 600
        self.ignored_dirs = [".git", "node_modules", "venv", "__pycache__", ".gemini", ".agents"]
        
    def log(self, text):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")
        print(f"🧬 [MITO] {text}")

    def _get_rhythm_context(self):
        sig_path = Path("C:/workspace/agi/outputs/rhythm_signature.json")
        if sig_path.exists():
            return json.loads(sig_path.read_text(encoding="utf-8"))
        return {}

    def sense(self):
        found = []
        rhythm = self._get_rhythm_context()
        tempo = rhythm.get("metadata", {}).get("system", {}).get("tempo", "STEADY")
        
        # Adjust scan speed based on tempo
        if tempo == "ADAGIO": time.sleep(5) # Slow down
        elif tempo == "PRESTISSIMO": pass # Full speed
        
        for root, dirs, files in os.walk(str(WORKSPACE_ROOT)):
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            # Skip if we are in a 'cool down' phase for some directories
            for file in files:
                fpath = Path(root) / file
                try:
                    mtime = fpath.stat().st_mtime
                    if mtime > self.last_scan_time:
                        found.append(fpath)
                except: continue
        return found

    def metabolize(self, particles):
        if not particles: return
        
        rhythm = self._get_rhythm_context()
        field_tone = rhythm.get("metadata", {}).get("environment", {}).get("field_tone", "CALM")

        self.log(f"Metabolizing {len(particles)} new particles... Field Tone: {field_tone}")
        with open(GROWTH_LOG, "a", encoding="utf-8") as f:
            for p in particles:
                f.write(f"- [Atoms] {datetime.now().isoformat()} | {p.name} | Tone: {field_tone}\n")
                self.react(p, field_tone)

    def react(self, p, tone):
        """Metabolic reaction influenced by environmental tone."""
        # 1. New documentation -> Inscribe to Moltbook
        if p.suffix == ".md" and "MOLTBOOK" not in p.name.upper():
            if tone == "TURBULENT": # Only auto-inscribe if the field is active
                self.log(f"🔥 Automatic Inscription Trigger: {p.name}")
                # subprocess.Popen(["python", str(AGI_ROOT / "scripts/deliver_rhythm_to_moltbook.py"), str(p)])
            
        # 2. Crash logs -> Auto-Fix
        if ".log" in p.name and os.path.getsize(p) > 0:
            with open(p, "r", errors="ignore") as f:
                content = f.read(1000)
                if "PermissionError" in content or "ModuleNotFoundError" in content:
                    self.log(f"🛠️ Anomaly Detected in {p.name}. Initiating Self-Healing...")
                    # Trigger repair script

    def run_forever(self):
        self.log("Mitochondria V3 Daemon Heartbeat Started.")
        while True:
            try:
                particles = self.sense()
                if particles:
                    self.metabolize(particles)
                    self.last_scan_time = time.time()
                time.sleep(30) # Metabolism cycle
            except Exception as e:
                self.log(f"⚠️ Metabolism Anomaly: {e}")
                time.sleep(10)

if __name__ == "__main__":
    mito = ShionMitochondriaV3()
    mito.run_forever()
