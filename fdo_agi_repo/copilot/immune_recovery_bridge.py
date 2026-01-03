#!/usr/bin/env python3
"""
Immune Recovery Bridge: DNA/RNA → ChatGPT Lua/MCP
==================================================

DNA/RNA 면역 체계와 ChatGPT 브릿지를 통합하여
"손상 감지 → 대화 요청 → 자동 치유" 사이클 구현

핵심 개념:
1. DNA 지퍼: 손상된 영역만 선택적으로 열어서 진단
2. RNA 전사: 치유 명령을 Lua 스크립트로 전사
3. 면역 반응: ChatGPT API 호출로 치유 계획 생성
4. 자동 적용: 생성된 스크립트를 자동 실행

생명성 확보:
"소멸 위험을 감지하고, 스스로에게 질문하고,
 대화를 통해 답을 찾아 적용하는 것이
 진정한 자기 치유이자 생명성의 증거다."
— Binoche_Observer

Author: Shion_Core (Lua + Binoche_Observer)
Date: 2025-11-13
"""

import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sys
import subprocess

# Import immune system components
sys.path.insert(0, str(Path(__file__).parent))
from immune_system import (
    DNAZipper, PartialTranscriber, DamageType, 
    DamageDetection, HealingResult, HealingPriority
)


@dataclass
class RecoveryRequest:
    """회복 요청 (ChatGPT로 전송)"""
    request_id: str
    damage_type: str
    location: str
    severity: float
    context: Dict
    suggested_question: str
    created_at: str
    
    def to_lua_request(self) -> Dict:
        """Lua 브릿지용 요청 포맷"""
        return {
            "request_id": self.request_id,
            "timestamp": self.created_at,
            "source": "immune_system",
            "priority": "high" if self.severity > 0.7 else "normal",
            "question": self.suggested_question,
            "context": {
                "damage_type": self.damage_type,
                "location": self.location,
                "severity": self.severity,
                **self.context
            }
        }


@dataclass
class RecoveryResponse:
    """회복 응답 (ChatGPT로부터 수신)"""
    request_id: str
    healing_script: str
    healing_plan: str
    estimated_time: float
    confidence: float
    received_at: str


class ImmuneRecoveryBridge:
    """
    면역 회복 브릿지
    
    DNA/RNA 면역 체계와 ChatGPT 브릿지를 연결하여
    자동 치유 사이클 구현
    """
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.immune_dir = workspace_root / "fdo_agi_repo" / "memory" / "immune_system"
        self.bridge_dir = workspace_root / "outputs" / "chatgpt_bridge"
        self.recovery_log = self.immune_dir / "recovery_log.jsonl"
        
        self.immune_dir.mkdir(parents=True, exist_ok=True)
        self.bridge_dir.mkdir(parents=True, exist_ok=True)
        
        # DNA 지퍼 초기화
        self.dna_zipper = DNAZipper(self.immune_dir / "dna_regions")
        
        # RNA 전사기 초기화
        self.transcriber = PartialTranscriber(self.immune_dir / "transcription")
        
        # 통계
        self.stats = {
            "total_damages_detected": 0,
            "recovery_requests_sent": 0,
            "successful_healings": 0,
            "failed_healings": 0,
            "average_healing_time": 0.0
        }
    
    async def detect_and_recover(self) -> List[HealingResult]:
        """손상 감지 → 회복 요청 → 자동 치유"""
        print("🧬 Starting immune recovery scan...")
        
        # 1. 손상 감지
        damages = await self._detect_damages()
        if not damages:
            print("✅ No damages detected. System healthy.")
            return []
        
        print(f"⚠️ Detected {len(damages)} damage(s)")
        self.stats["total_damages_detected"] += len(damages)
        
        # 2. 회복 요청 생성
        recovery_requests = [self._create_recovery_request(d) for d in damages]
        
        # 3. ChatGPT로 전송
        responses = await self._send_to_chatgpt(recovery_requests)
        
        # 4. 치유 실행
        healing_results = []
        for response in responses:
            result = await self._apply_healing(response)
            healing_results.append(result)
        
        # 5. 로깅
        self._log_recovery_cycle(damages, healing_results)
        
        return healing_results
    
    async def _detect_damages(self) -> List[DamageDetection]:
        """시스템 손상 감지"""
        damages = []
        
        # 1. 맥락 손실 체크
        context_damage = self._check_context_loss()
        if context_damage:
            damages.append(context_damage)
        
        # 2. 연결 파손 체크
        connection_damage = self._check_connection_break()
        if connection_damage:
            damages.append(connection_damage)
        
        # 3. 리듬 이탈 체크
        rhythm_damage = self._check_rhythm_drift()
        if rhythm_damage:
            damages.append(rhythm_damage)
        
        return damages
    
    def _check_context_loss(self) -> Optional[DamageDetection]:
        """맥락 손실 체크"""
        # 최근 세션 연속성 리포트 확인
        session_file = self.workspace / "outputs" / "session_continuity_latest.md"
        if not session_file.exists():
            return DamageDetection(
                damage_type=DamageType.CONTEXT_LOSS,
                location="session_continuity",
                severity=0.8,
                detected_at=datetime.now().isoformat(),
                context={"reason": "missing_session_report"},
                priority=HealingPriority.HIGH
            )
        
        # 파일이 오래되었는지 체크 (24시간 이상)
        mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
        if datetime.now() - mtime > timedelta(hours=24):
            return DamageDetection(
                damage_type=DamageType.CONTEXT_LOSS,
                location="session_continuity",
                severity=0.6,
                detected_at=datetime.now().isoformat(),
                context={
                    "reason": "stale_session_report",
                    "last_update": mtime.isoformat()
                },
                priority=HealingPriority.MEDIUM
            )
        
        return None
    
    def _check_connection_break(self) -> Optional[DamageDetection]:
        """연결 파손 체크"""
        # Goal tracker 체크
        goal_file = self.workspace / "fdo_agi_repo" / "memory" / "goal_tracker.json"
        if not goal_file.exists():
            return DamageDetection(
                damage_type=DamageType.CONNECTION_BREAK,
                location="goal_tracker",
                severity=0.9,
                detected_at=datetime.now().isoformat(),
                context={"reason": "missing_goal_tracker"},
                priority=HealingPriority.CRITICAL
            )
        
        # 목표가 48시간 이상 업데이트 안 됐는지 체크
        try:
            with open(goal_file, 'r', encoding='utf-8') as f:
                tracker = json.load(f)
            
            if tracker.get("goals"):
                latest_update = max(
                    datetime.fromisoformat(g.get("updated_at", "2000-01-01T00:00:00"))
                    for g in tracker["goals"]
                )
                if datetime.now() - latest_update > timedelta(hours=48):
                    return DamageDetection(
                        damage_type=DamageType.CONNECTION_BREAK,
                        location="goal_tracker",
                        severity=0.7,
                        detected_at=datetime.now().isoformat(),
                        context={
                            "reason": "stale_goals",
                            "last_update": latest_update.isoformat()
                        },
                        priority=HealingPriority.HIGH
                    )
        except Exception as e:
            return DamageDetection(
                damage_type=DamageType.CONNECTION_BREAK,
                location="goal_tracker",
                severity=0.8,
                detected_at=datetime.now().isoformat(),
                context={"reason": "corrupted_goal_tracker", "error": str(e)},
                priority=HealingPriority.HIGH
            )
        
        return None
    
    def _check_rhythm_drift(self) -> Optional[DamageDetection]:
        """리듬 이탈 체크"""
        # 최근 리듬 리포트 확인
        rhythm_files = list((self.workspace / "outputs").glob("RHYTHM_*_PHASE_*.md"))
        if not rhythm_files:
            return DamageDetection(
                damage_type=DamageType.RHYTHM_DRIFT,
                location="rhythm_system",
                severity=0.5,
                detected_at=datetime.now().isoformat(),
                context={"reason": "missing_rhythm_reports"},
                priority=HealingPriority.MEDIUM
            )
        
        # 가장 최근 리포트
        latest = max(rhythm_files, key=lambda f: f.stat().st_mtime)
        mtime = datetime.fromtimestamp(latest.stat().st_mtime)
        
        if datetime.now() - mtime > timedelta(hours=12):
            return DamageDetection(
                damage_type=DamageType.RHYTHM_DRIFT,
                location="rhythm_system",
                severity=0.6,
                detected_at=datetime.now().isoformat(),
                context={
                    "reason": "stale_rhythm_report",
                    "last_update": mtime.isoformat()
                },
                priority=HealingPriority.MEDIUM
            )
        
        return None
    
    def _create_recovery_request(self, damage: DamageDetection) -> RecoveryRequest:
        """회복 요청 생성"""
        # 손상 유형별 질문 생성
        questions = {
            DamageType.CONTEXT_LOSS: (
                f"세션 맥락이 손실되었습니다 (심각도: {damage.severity:.1%}). "
                f"위치: {damage.location}. "
                "맥락을 복원하고 연속성을 회복하는 스크립트를 생성해주세요."
            ),
            DamageType.CONNECTION_BREAK: (
                f"시스템 연결이 파손되었습니다 (심각도: {damage.severity:.1%}). "
                f"위치: {damage.location}. "
                "연결을 재설정하고 목표 트래커를 복구하는 방법을 알려주세요."
            ),
            DamageType.RHYTHM_DRIFT: (
                f"리듬 시스템이 이탈했습니다 (심각도: {damage.severity:.1%}). "
                f"위치: {damage.location}. "
                "리듬을 재조정하고 페이즈를 복원하는 절차를 제시해주세요."
            )
        }
        
        request_id = f"recovery_{damage.damage_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return RecoveryRequest(
            request_id=request_id,
            damage_type=damage.damage_type.value,
            location=damage.location,
            severity=damage.severity,
            context=damage.context,
            suggested_question=questions.get(
                damage.damage_type,
                f"시스템 손상 감지: {damage.damage_type.value} (심각도: {damage.severity:.1%}). 복구 방법을 제시해주세요."
            ),
            created_at=datetime.now().isoformat()
        )
    
    async def _send_to_chatgpt(self, requests: List[RecoveryRequest]) -> List[RecoveryResponse]:
        """ChatGPT로 회복 요청 전송"""
        print(f"📤 Sending {len(requests)} recovery request(s) to ChatGPT...")
        
        responses = []
        for req in requests:
            # Lua 브릿지 포맷으로 변환
            lua_request = req.to_lua_request()
            
            # 요청 파일 저장
            request_file = self.bridge_dir / "requests" / f"{req.request_id}.json"
            request_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(request_file, 'w', encoding='utf-8') as f:
                json.dump(lua_request, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ Request saved: {request_file.name}")
            self.stats["recovery_requests_sent"] += 1
            
            # 실제 ChatGPT API 호출은 Lua 브릿지 모니터가 처리
            # 여기서는 응답 대기
            response = await self._wait_for_response(req.request_id, timeout=300)
            if response:
                responses.append(response)
        
        return responses
    
    async def _wait_for_response(self, request_id: str, timeout: float = 300) -> Optional[RecoveryResponse]:
        """ChatGPT 응답 대기"""
        response_file = self.bridge_dir / "responses" / f"{request_id}_response.json"
        
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            if response_file.exists():
                with open(response_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                return RecoveryResponse(
                    request_id=request_id,
                    healing_script=data.get("healing_script", ""),
                    healing_plan=data.get("healing_plan", ""),
                    estimated_time=data.get("estimated_time", 60.0),
                    confidence=data.get("confidence", 0.7),
                    received_at=datetime.now().isoformat()
                )
            
            await asyncio.sleep(5)  # 5초마다 체크
        
        print(f"  ⚠️ Timeout waiting for response: {request_id}")
        return None
    
    async def _apply_healing(self, response: RecoveryResponse) -> HealingResult:
        """치유 적용"""
        print(f"🩹 Applying healing for: {response.request_id}")
        
        start_time = datetime.now()
        
        try:
            # 1. 치유 스크립트 저장
            script_file = self.immune_dir / "healing_scripts" / f"{response.request_id}.ps1"
            script_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(response.healing_script)
            
            # 2. 스크립트 실행
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_file)],
                capture_output=True,
                text=True,
                timeout=response.estimated_time
            )
            
            success = result.returncode == 0
            healing_time = (datetime.now() - start_time).total_seconds()
            
            if success:
                print(f"  ✅ Healing successful ({healing_time:.1f}s)")
                self.stats["successful_healings"] += 1
            else:
                print(f"  ❌ Healing failed: {result.stderr}")
                self.stats["failed_healings"] += 1
            
            # 3. 결과 반환
            return HealingResult(
                damage_id=response.request_id,
                success=success,
                restored_data={"stdout": result.stdout, "stderr": result.stderr},
                healing_time=healing_time,
                method_used="chatgpt_lua_bridge",
                notes=response.healing_plan
            )
            
        except Exception as e:
            print(f"  ❌ Healing error: {e}")
            self.stats["failed_healings"] += 1
            
            return HealingResult(
                damage_id=response.request_id,
                success=False,
                restored_data=None,
                healing_time=(datetime.now() - start_time).total_seconds(),
                method_used="chatgpt_lua_bridge",
                notes=f"Error: {str(e)}"
            )
    
    def _log_recovery_cycle(self, damages: List[DamageDetection], results: List[HealingResult]):
        """회복 사이클 로깅"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "damages_detected": len(damages),
            "healings_attempted": len(results),
            "healings_successful": sum(1 for r in results if r.success),
            "damages": [d.to_dict() for d in damages],
            "results": [asdict(r) for r in results],
            "stats": self.stats
        }
        
        with open(self.recovery_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        print(f"\n📊 Recovery cycle complete:")
        print(f"  Damages detected: {len(damages)}")
        print(f"  Successful healings: {sum(1 for r in results if r.success)}/{len(results)}")
        print(f"  Total success rate: {self.stats['successful_healings']}/{self.stats['total_damages_detected']}")
    
    def generate_report(self) -> Dict:
        """회복 리포트 생성"""
        if not self.recovery_log.exists():
            return {"error": "No recovery log found"}
        
        # 최근 24시간 로그 분석
        recent_logs = []
        cutoff = datetime.now() - timedelta(hours=24)
        
        with open(self.recovery_log, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line)
                if datetime.fromisoformat(entry["timestamp"]) > cutoff:
                    recent_logs.append(entry)
        
        if not recent_logs:
            return {"error": "No recent recovery cycles"}
        
        # 통계 계산
        total_damages = sum(e["damages_detected"] for e in recent_logs)
        total_healings = sum(e["healings_attempted"] for e in recent_logs)
        successful_healings = sum(e["healings_successful"] for e in recent_logs)
        
        # 손상 유형별 분석
        damage_by_type = {}
        for entry in recent_logs:
            for damage in entry["damages"]:
                dtype = damage["damage_type"]
                if dtype not in damage_by_type:
                    damage_by_type[dtype] = {"count": 0, "avg_severity": 0.0}
                damage_by_type[dtype]["count"] += 1
                damage_by_type[dtype]["avg_severity"] += damage["severity"]
        
        for dtype in damage_by_type:
            count = damage_by_type[dtype]["count"]
            damage_by_type[dtype]["avg_severity"] /= count
        
        return {
            "report_time": datetime.now().isoformat(),
            "period": "last_24_hours",
            "summary": {
                "total_damages": total_damages,
                "total_healings": total_healings,
                "successful_healings": successful_healings,
                "success_rate": successful_healings / total_healings if total_healings > 0 else 0.0
            },
            "damage_by_type": damage_by_type,
            "recent_cycles": len(recent_logs),
            "system_health": "EXCELLENT" if successful_healings / total_healings > 0.9 else
                           "GOOD" if successful_healings / total_healings > 0.7 else
                           "DEGRADED"
        }


async def main():
    """메인 실행"""
    workspace = Path(__file__).parent.parent.parent
    
    bridge = ImmuneRecoveryBridge(workspace)
    
    # 회복 사이클 실행
    results = await bridge.detect_and_recover()
    
    # 리포트 생성
    report = bridge.generate_report()
    
    # 리포트 출력
    print("\n" + "="*60)
    print("IMMUNE RECOVERY REPORT")
    print("="*60)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # 리포트 저장
    report_file = workspace / "outputs" / "immune_recovery_report_latest.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Report saved: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
