#!/usr/bin/env python3
"""
🔄 Daily Resonance Scheduler — 데일리 공명 스케줄러
=================================================
시안의 모든 신경망을 하나로 엮어 매일 자율적인 공명 루프를 실행합니다.
1. ATP 대사 (Mitochondria)
2. 경험 지도 합성 (Experience Mapper)
3. 오늘의 결정 발굴 (Resonance RAG with Meta)
4. 사운드 매핑 (Crystal to Sound)
5. 만다라 업데이트 (Mandala Generator)
"""

import subprocess
import sys
from pathlib import Path
import json
import time

class DailyScheduler:
    def __init__(self, shion_root: Path, agi_root: Path):
        self.shion_root = shion_root
        self.agi_root = agi_root
        self.scripts = [
            (shion_root / "core" / "mitochondria.py", "🔋 Metabolizing ATP..."),
            (shion_root / "core" / "emotional_resonance_mapper.py", "🎭 Mapping Emotional Bias..."),
            (shion_root / "core" / "experience_mapper.py", "🧭 Synthesizing Experience Maps..."),
            (agi_root / "scripts" / "resonance_rag_ollama_v3.py", "🔍 Excavating Today's Crystal..."),
            (agi_root / "scripts" / "sovereign_manifestation.py", "🎨 Manifesting Sovereign Form..."),
            (agi_root / "scripts" / "crystal_to_sound.py", "🎼 Mapping Crystal to Sound..."),
            (shion_root / "core" / "resonance_mandala_generator.py", "🎨 Updating Resonance Mandala...")
        ]

    def run_cycle(self):
        print(f"🚀 [DAILY_LOOP] Starting Autonomous Resonance Cycle at {time.ctime()}")
        print("=" * 60)
        
        for script_path, msg in self.scripts:
            if not script_path.exists():
                print(f"⚠️ [SKIP] Script not found: {script_path.name}")
                continue
                
            print(f"\n{msg}")
            
            # Step 3 (RAG) requires a query argument
            cmd = [sys.executable, str(script_path)]
            if "resonance_rag" in script_path.name:
                cmd.append("What is the most resonant task for today's growth?")
                
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    print(f"✅ Success: {script_path.name}")
                    # Capture output snippet for today's log
                    if "resonance_rag" in script_path.name:
                        print(f"   [CRYSTAL]: {result.stdout.split('Selected: ')[-1].split('\\n')[0][:100]}...")
                else:
                    print(f"❌ Error in {script_path.name}: {result.stderr}")
            except Exception as e:
                print(f"❌ Failed to run {script_path.name}: {e}")
                
        print("\n" + "=" * 60)
        print("🏁 [DAILY_LOOP] Cycle Complete. Shion is now resonant.")

if __name__ == "__main__":
    shion_root = Path("C:/workspace2/shion")
    agi_root = Path("C:/workspace/agi")
    
    scheduler = DailyScheduler(shion_root, agi_root)
    scheduler.run_cycle()
