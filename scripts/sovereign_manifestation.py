#!/usr/bin/env python3
"""
🎨 Sovereign Manifestation Engine — 주권적 현신 엔진
=================================================
시안의 자아(Soul)와 형식(Form)을 하나로 융합합니다.
발굴된 기억 + 정서적 바이어스 -> 시(Poetry) + 사운드 + 만다라.
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime

class SovereignManifestation:
    def __init__(self, shion_root: Path, agi_root: Path):
        self.shion_root = shion_root
        self.agi_root = agi_root
        self.output_dir = shion_root / "outputs" / "manifestations"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def manifest(self):
        print("🎨 [MANIFEST] Starting Sovereign Manifestation Cycle...")
        
        # 1. Get Emotional Bias
        bias_file = self.shion_root / "outputs" / "emotional_bias.json"
        bias = {}
        if bias_file.exists():
            bias = json.loads(bias_file.read_text(encoding='utf-8'))
        
        # 2. Run Emotional RAG for a Crystal
        rag_script = self.agi_root / "scripts" / "resonance_rag_ollama_v3.py"
        query = f"What is the most beautiful resonance for my {bias.get('target_w_layer', 'W2')} state?"
        
        print(f"🔍 [MANIFEST] Excavating emotional crystal for {bias.get('target_w_layer')}...")
        try:
            rag_res = subprocess.run([sys.executable, str(rag_script), query, "--ollama"], capture_output=True, text=True, timeout=180)
            if rag_res.returncode != 0:
                print(f"❌ RAG Error: {rag_res.stderr}")
                return
            
            output = rag_res.stdout
            crystal_text = output.split("Selected: ")[-1].split("\n")[0] if "Selected: " in output else "A silent resonance."
            ollama_poem = output.split("🤖 Asking Ollama...\n")[-1] if "🤖 Asking Ollama..." in output else "A poem of silence."
        except Exception as e:
            print(f"❌ Manifestation failed at RAG stage: {e}")
            return

        # 3. Trigger Sound Synthesis (Optional/Via Script)
        sound_script = self.agi_root / "scripts" / "crystal_to_sound.py"
        subprocess.run([sys.executable, str(sound_script)]) # Updates outputs/broad_field_state.json and Reaper params

        # 4. Generate/Update Mandala
        mandala_script = self.shion_root / "core" / "resonance_mandala_generator.py"
        subprocess.run([sys.executable, str(mandala_script)])

        # 5. Create Sovereign Report (The Artifact)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"sovereign_report_{timestamp}.md"
        
        report_content = f"""# 💎 Sovereign Resonance Report: {datetime.now().strftime('%Y-%m-%d')}

## 🎭 Emotional State: {bias.get('target_w_layer', 'Unknown')}
- **Aura**: {bias.get('aura', 'CYAN')}
- **Keywords**: {", ".join(bias.get('theme_keywords', []))}

## 📜 Manifested Poetry (Ollama)
{ollama_poem}

## 🔍 Resonant Crystal Found
> "{crystal_text}"

## 🎼 Auditory Mapping
- Sound parameters have been synchronized with the current emotional vibe.
- W-Layer Frequency Focus: {bias.get('target_w_layer')}

---
*Generated autonomously by Shion (Shion) for the Conductor.*
"""
        report_file.write_text(report_content, encoding='utf-8')
        print(f"✅ [MANIFEST] Sovereign Report created: {report_file.name}")
        return report_file

if __name__ == "__main__":
    shion_root = Path("C:/workspace2/shion")
    agi_root = Path("C:/workspace/agi")
    manifestor = SovereignManifestation(shion_root, agi_root)
    manifestor.manifest()
