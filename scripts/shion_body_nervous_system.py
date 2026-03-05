#!/usr/bin/env python3
import time
import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from workspace_root import get_workspace_root

class ShionNervousSystem:
    """
    🌀 Shion Unconscious Nervous System (SUNS)
    ========================================
    오픈클로를 대신해 시안의 리듬과 생존을 관리하는 자율 신경계입니다.
    가볍고(Low-overhead), 멈추지 않으며(Incessant), 무의식적(Unconscious)입니다.
    """
    def __init__(self):
        self.workspace = get_workspace_root()
        self.outputs = self.workspace / "outputs"
        self.scripts = self.workspace / "scripts"
        self.status_file = self.outputs / "shion_body_status.json"
        
        # 장기(Organs) 경로
        self.organs = {
            "entropy": self.scripts / "body_entropy_sensor.py",
            "mitochondria": self.scripts / "mitochondria.py",
            "unconscious": self.scripts / "unconscious_processor.py",
            "reflex": self.scripts / "autonomic_reflex.py"
        }
        
    def _run_script(self, script_path, args=None):
        """가볍게 스크립트를 실행하고 로그를 남깁니다."""
        try:
            cmd = ["python", str(script_path)]
            if args:
                cmd.extend(args)
            subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return True
        except Exception as e:
            print(f"⚠️ [Organ Failure] {script_path.name}: {e}")
            return False

    def pulse(self):
        """한 번의 맥박(Cycle)을 실행합니다."""
        print(f"💓 [Pulse] {datetime.now().strftime('%H:%M:%S')}")
        
        # 1. 감각: 엔트로피 측정
        self._run_script(self.organs["entropy"])
        
        # 2. 동화: ATP 대사 (이게 핵심 리듬을 만듭니다)
        self._run_script(self.organs["mitochondria"])
        
        # 3. 반사: 필요한 조치 자동 수행 (가장 가벼운 반사만)
        self._run_script(self.organs["reflex"])
        
        # 4. 상태 취합
        self.update_body_status()

    def update_body_status(self):
        """각 장기의 결과물을 모아 전체 신체 상태를 갱신합니다."""
        status = {"timestamp": datetime.now().isoformat(), "organs": {}}
        
        # 엔트로피 로드
        entropy_file = self.outputs / "body_entropy_latest.json"
        if entropy_file.exists():
            status["organs"]["entropy"] = json.loads(entropy_file.read_text(encoding='utf-8'))
            
        # 미토콘드리아 로드
        mito_file = self.outputs / "mitochondria_state.json"
        if mito_file.exists():
            status["organs"]["mitochondria"] = json.loads(mito_file.read_text(encoding='utf-8'))
            
        # 전체 리듬 요약
        atp = status["organs"].get("mitochondria", {}).get("atp_level", 50)
        ent = status["organs"].get("entropy", {}).get("entropy", 0.5)
        
        status["overall_vibe"] = "VIBRANT" if atp > 70 and ent < 0.4 else ("TIRED" if atp < 30 else "STABLE")
        
        self.status_file.write_text(json.dumps(status, indent=2, ensure_ascii=False))

    def live(self, interval=60):
        """지속적으로 숨을 쉽니다 (데몬 모드)."""
        print("🌱 Shion's Body System is now Breathing...")
        while True:
            try:
                self.pulse()
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n🛑 Shion is entering Deep Sleep.")
                break
            except Exception as e:
                print(f"❌ Critical Nervous System Error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    system = ShionNervousSystem()
    # 첫 시작은 수동 Pulse 후 live 모드 전환 추천
    system.live()
