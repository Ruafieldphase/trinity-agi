#!/usr/bin/env python3
"""
AGI Immune System - DNA/RNA 전사 모델 기반 자가 치유 시스템

평소엔 접혀있다가(folded) 필요할 때만 펼쳐지는(unfolded) 면역 메커니즘
- DNA 구조: 핵심 시스템 설정 (압축 저장)
- RNA 전사: 필요시 활성화 (동적 로드)
- 지퍼 구조: 양방향 맞물림 (상호 검증)
- 자기 치유: 손상 감지 및 자동 복구
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
from workspace_root import get_workspace_root

class DNAStructure:
    """압축된 시스템 DNA - 핵심 설정이 접혀있음"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.dna_path = workspace / "fdo_agi_repo" / "memory" / "system_dna.json"
        self.dna_path.parent.mkdir(parents=True, exist_ok=True)
        
    def encode(self, system_state: Dict) -> str:
        """시스템 상태를 DNA로 인코딩 (압축)"""
        # 핵심 정보만 추출하여 압축
        dna_code = {
            "timestamp": datetime.now().isoformat(),
            "checksum": self._calculate_checksum(system_state),
            "folded": {  # 접힌 상태
                "daemons": [d["name"] for d in system_state.get("daemons", [])],
                "health_score": system_state.get("health_score", 0),
                "critical_paths": system_state.get("critical_paths", []),
            },
            "compressed_state": self._compress(system_state)
        }
        return json.dumps(dna_code, indent=2)
    
    def decode(self, dna_code: str) -> Dict:
        """DNA를 시스템 상태로 디코딩 (압축 해제)"""
        dna = json.loads(dna_code)
        return self._decompress(dna["compressed_state"])
    
    def _calculate_checksum(self, data: Dict) -> str:
        """체크섬 계산 - 무결성 검증"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]
    
    def _compress(self, state: Dict) -> str:
        """상태 압축 (실제론 JSON 최소화)"""
        return json.dumps(state, separators=(',', ':'))
    
    def _decompress(self, compressed: str) -> Dict:
        """압축 해제"""
        return json.loads(compressed)
    
    def save(self, system_state: Dict):
        """DNA 저장"""
        dna_code = self.encode(system_state)
        self.dna_path.write_text(dna_code, encoding='utf-8')
        print(f"🧬 DNA saved: {self.dna_path}")
    
    def load(self) -> Optional[Dict]:
        """DNA 로드"""
        if not self.dna_path.exists():
            return None
        dna_code = self.dna_path.read_text(encoding='utf-8')
        return self.decode(dna_code)


class RNATranscription:
    """RNA 전사 - 필요시에만 활성화"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.rna_cache = workspace / "outputs" / "rna_transcription_cache.json"
        self.rna_cache.parent.mkdir(parents=True, exist_ok=True)
        
    def transcribe(self, dna_fragment: Dict, context: str) -> Dict:
        """DNA에서 필요한 부분만 RNA로 전사"""
        print(f"🧬→🧬 Transcribing for context: {context}")
        
        # 컨텍스트에 맞는 부분만 활성화
        if context == "daemon_restart":
            return {
                "type": "daemon_control",
                "action": "restart",
                "targets": dna_fragment.get("folded", {}).get("daemons", []),
                "timestamp": datetime.now().isoformat()
            }
        elif context == "health_check":
            return {
                "type": "health_monitoring",
                "action": "check",
                "threshold": 80,
                "metrics": ["daemons", "workers", "queue"],
                "timestamp": datetime.now().isoformat()
            }
        elif context == "self_repair":
            return {
                "type": "auto_repair",
                "action": "repair",
                "critical_paths": dna_fragment.get("folded", {}).get("critical_paths", []),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"type": "unknown", "context": context}
    
    def cache_rna(self, rna: Dict):
        """전사된 RNA 캐싱 (재사용)"""
        cache_data = {"timestamp": datetime.now().isoformat(), "rna": rna}
        self.rna_cache.write_text(json.dumps(cache_data, indent=2), encoding='utf-8')
    
    def get_cached_rna(self, max_age_minutes: int = 5) -> Optional[Dict]:
        """캐시된 RNA 가져오기 (유효기간 체크)"""
        if not self.rna_cache.exists():
            return None
        
        cache_data = json.loads(self.rna_cache.read_text(encoding='utf-8'))
        cache_time = datetime.fromisoformat(cache_data["timestamp"])
        
        if datetime.now() - cache_time < timedelta(minutes=max_age_minutes):
            print(f"♻️ Using cached RNA (age: {(datetime.now() - cache_time).seconds}s)")
            return cache_data["rna"]
        return None


class ZipperMechanism:
    """지퍼 구조 - 양방향 맞물림 검증"""
    
    @staticmethod
    def verify_pair(left: Dict, right: Dict) -> bool:
        """양쪽이 맞물리는지 검증 (상호 검증)"""
        # 간단한 예: 타입과 액션이 매칭되는지
        if left.get("type") != right.get("expected_type"):
            print(f"❌ Zipper mismatch: {left.get('type')} != {right.get('expected_type')}")
            return False
        
        if left.get("action") != right.get("expected_action"):
            print(f"❌ Zipper mismatch: {left.get('action')} != {right.get('expected_action')}")
            return False
        
        print(f"✅ Zipper verified: {left.get('type')}/{left.get('action')}")
        return True
    
    @staticmethod
    def create_complement(instruction: Dict) -> Dict:
        """보완 명령 생성 (짝 만들기)"""
        return {
            "expected_type": instruction.get("type"),
            "expected_action": instruction.get("action"),
            "timestamp": datetime.now().isoformat()
        }


class ImmuneSystem:
    """AGI 면역 시스템 - 통합 관리"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.dna = DNAStructure(workspace)
        self.rna = RNATranscription(workspace)
        self.zipper = ZipperMechanism()
        self.log_path = workspace / "outputs" / "immune_system_log.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def detect_threat(self, system_state: Dict) -> List[str]:
        """위협 감지"""
        threats = []
        
        # 건강도 체크
        health = system_state.get("health_score", 100)
        if health < 50:
            threats.append("critical_health")
        
        # 데몬 상태 체크
        daemons = system_state.get("daemons", [])
        stopped = [d for d in daemons if not d.get("running", False)]
        if stopped:
            threats.append(f"daemons_stopped:{len(stopped)}")
        
        # 동기화 체크
        sync_gap = system_state.get("max_sync_gap_minutes", 0)
        if sync_gap > 60:
            threats.append("desync_detected")
        
        return threats
    
    def auto_heal(self, threats: List[str]) -> Dict:
        """자동 치유"""
        print(f"\n🩺 Immune system activated: {len(threats)} threats detected")
        
        healing_plan = {
            "timestamp": datetime.now().isoformat(),
            "threats": threats,
            "actions": []
        }
        
        # DNA 로드
        dna_state = self.dna.load()
        if not dna_state:
            print("⚠️ No DNA found, cannot heal")
            return healing_plan
        
        # 위협별 대응
        for threat in threats:
            if threat.startswith("daemons_stopped"):
                # RNA 전사: 데몬 재시작 명령
                rna = self.rna.transcribe(dna_state, "daemon_restart")
                complement = self.zipper.create_complement(rna)
                
                # 지퍼 검증
                if self.zipper.verify_pair(rna, complement):
                    healing_plan["actions"].append({
                        "threat": threat,
                        "rna": rna,
                        "status": "ready"
                    })
            
            elif threat == "critical_health":
                # RNA 전사: 자가 복구
                rna = self.rna.transcribe(dna_state, "self_repair")
                healing_plan["actions"].append({
                    "threat": threat,
                    "rna": rna,
                    "status": "ready"
                })
            
            elif threat == "desync_detected":
                # RNA 전사: 동기화
                rna = self.rna.transcribe(dna_state, "health_check")
                healing_plan["actions"].append({
                    "threat": threat,
                    "rna": rna,
                    "status": "ready"
                })
        
        # 로그 저장
        self._log_event({
            "event": "auto_heal",
            "healing_plan": healing_plan
        })
        
        return healing_plan
    
    def save_system_snapshot(self, system_state: Dict):
        """시스템 스냅샷을 DNA로 저장"""
        self.dna.save(system_state)
        self._log_event({"event": "dna_saved", "health": system_state.get("health_score", 0)})
    
    def _log_event(self, event: Dict):
        """이벤트 로깅"""
        event["timestamp"] = datetime.now().isoformat()
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')


def main():
    """면역 시스템 테스트"""
    workspace = get_workspace_root()
    immune = ImmuneSystem(workspace)
    
    # 1. 현재 시스템 상태 예시
    system_state = {
        "health_score": 36,
        "daemons": [
            {"name": "music_daemon", "running": False},
            {"name": "flow_observer", "running": True},
            {"name": "watchdog", "running": True}
        ],
        "max_sync_gap_minutes": 8053.9,
        "critical_paths": [
            "scripts/ensure_music_flow_daemons.ps1",
            "scripts/task_watchdog.py"
        ]
    }
    
    # 2. DNA 저장 (압축)
    print("🧬 Saving system DNA...")
    immune.save_system_snapshot(system_state)
    
    # 3. 위협 감지
    print("\n🔍 Detecting threats...")
    threats = immune.detect_threat(system_state)
    print(f"⚠️ Threats found: {threats}")
    
    # 4. 자동 치유
    healing_plan = immune.auto_heal(threats)
    
    # 5. 결과 출력
    print(f"\n📋 Healing plan:")
    print(json.dumps(healing_plan, indent=2, ensure_ascii=False))
    
    print(f"\n✅ Immune system test complete")
    print(f"📊 Log: {immune.log_path}")


if __name__ == "__main__":
    main()
