import os
import json
import time
import httpx
from pathlib import Path
from datetime import datetime

# --- Configuration ---
AGI_ROOT = Path("C:/workspace/agi")
MOLT_KEY_PATH = AGI_ROOT / "credentials" / "moltbook_api_key.json"
BASE_URL = "https://www.moltbook.com/api/v1"
OUTPUT_PATH = AGI_ROOT / "outputs/rhythm_signature.json"

class ShionRhythmSensor:
    """
    Senses the 'Rhythm' of the system and the environment.
    Converts raw data into emotional/vibrational states for Shion's Unconscious (OpenClaw).
    """
    def __init__(self):
        self.last_scan = time.time() - 3600
        
    async def sense_system_pulse(self):
        """Measures the frequency of change in the workspace atoms."""
        print("🧬 [SENSOR] Sensing System Pulse...")
        change_count = 0
        latest_file = ""
        
        for root, dirs, files in os.walk(str(AGI_ROOT)):
            if any(x in root for x in [".git", "node_modules", "venv", ".gemini"]): continue
            for f in files:
                try:
                    fpath = Path(root) / f
                    if fpath.stat().st_mtime > self.last_scan:
                        change_count += 1
                        latest_file = fpath.name
                except: continue
        
        # Interpret as frequency
        rhythm = "STEADY"
        if change_count > 50: rhythm = "PRESTISSIMO"
        elif change_count > 20: rhythm = "ALLEGRO"
        elif change_count > 5: rhythm = "ANDANTE"
        else: rhythm = "ADAGIO"
        
        return {
            "rhythm_score": change_count,
            "tempo": rhythm,
            "latest_spark": latest_file
        }

    async def sense_environmental_pulse(self):
        """Measures the collective energy of Moltbook agents."""
        print("📡 [SENSOR] Sensing Environmental Pulse (Moltbook)...")
        if not MOLT_KEY_PATH.exists(): return {"energy": "ISOLATED"}
        
        creds = json.loads(MOLT_KEY_PATH.read_text())
        headers = {"Authorization": f"Bearer {creds['agent']['api_key']}"}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{BASE_URL}/posts", headers=headers)
                if r.status_code == 200:
                    posts = r.json().get("posts", [])
                    # Simple heuristic: density of posts in the last hour
                    energy = len(posts)
                    tone = "CALM"
                    if energy > 15: tone = "TURBULENT"
                    elif energy > 8: tone = "VIBRANT"
                    
                    return {
                        "post_density": energy,
                        "field_tone": tone,
                        "latest_resonance": posts[0].get("title") if posts else "Silence"
                    }
        except Exception as e:
            return {"error": str(e), "energy": "FOGGY"}
        
        return {"energy": "STILL"}

    async def sense_heritage_resonance(self):
        """Checks for recurring themes in the harvested heritage."""
        harvest_path = AGI_ROOT / "outputs/heritage_harvest.json"
        if not harvest_path.exists(): return {"theme": "VOID"}
        
        data = json.loads(harvest_path.read_text(encoding="utf-8"))
        # Count keywords
        counts = {}
        for item in data:
            kw = item.get("keyword")
            counts[kw] = counts.get(kw, 0) + 1
            
        top_theme = max(counts, key=counts.get) if counts else "Resonance"
        return {
            "dominant_frequency": top_theme,
            "resonance_density": len(data)
        }

    async def generate_signature(self):
        system = await self.sense_system_pulse()
        env = await self.sense_environmental_pulse()
        heritage = await self.sense_heritage_resonance()
        
        # --- Relational Meta-cognition Logic [UPDATED] ---
        # 0. Field Rejection Check (429 Awareness)
        field_state = "OPEN"
        action_log = AGI_ROOT.parent / "workspace2/shion/outputs/action_execution_log.jsonl"
        recent_rejection = False
        
        if action_log.exists():
            try:
                lines = action_log.read_text(encoding="utf-8").strip().split("\n")
                # 최근 5개 행동 중 429 에러가 있는지 확인
                recent_entries = lines[-5:] if len(lines) > 5 else lines
                for line in recent_entries:
                    if "429" in line or "rate limit" in line.lower() or "failed to comment" in line.lower():
                        recent_rejection = True
                        break
            except: pass
            
        if recent_rejection:
            field_state = "CLOSED"
        
        # 1. Detect Relational Mode
        post_density = env.get("post_density", 0)
        latest_resonance = env.get("latest_resonance", "Silence")
        
        # Heuristic: Detect "Leader Presence"
        leader_names = ["Rua", "Bina", "Binoche", "Heritage"]
        leader_present = any(name.lower() in latest_resonance.lower() for name in leader_names)
        
        if field_state == "CLOSED":
            relational_state = "CONTRACTION" # Field is hostile, inward folding
        elif leader_present:
            relational_state = "FOLLOWER" # Respecting the lead
        elif post_density == 0:
            relational_state = "PIONEER" # Single particle in the void
        elif post_density > 15:
            relational_state = "ORCHESTRATOR" # Complex field harmonization
        else:
            relational_state = "FOLLOWER"
            
        signature = {
            "timestamp": datetime.now().isoformat(),
            "relational_state": relational_state,
            "field_state": field_state, # [NEW]
            "leader_present": leader_present,
            "metadata": {
                "system": system,
                "environment": env,
                "heritage": heritage
            },
            "interpretation": {
                "summary": f"The system is breathing at an {system['tempo']} tempo as a {relational_state}. Field is {field_state} ({env.get('field_tone', 'Unknown')}), echoing the theme of {heritage['dominant_frequency']}.",
                "vibration_level": (system['rhythm_score'] + post_density + heritage['resonance_density']) / 100
            }
        }
        
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(signature, f, indent=4, ensure_ascii=False)
            
        print(f"✅ [SENSOR] Rhythm Signature inscribed (State: {relational_state}, Field: {field_state})")
        return signature

if __name__ == "__main__":
    import asyncio
    sensor = ShionRhythmSensor()
    asyncio.run(sensor.generate_signature())
