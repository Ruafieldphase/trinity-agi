#!/usr/bin/env python3
"""
Master AI Router - 사용자 메시지를 자동으로 적절한 시스템에 라우팅
"""
import json
import re
import subprocess
import sys
from pathlib import Path
import os
import sys
from pathlib import Path

# 부트스트래핑
def bootstrap():
    curr = Path(__file__).resolve()
    for parent in curr.parents:
        if (parent / "agi_core").exists() or parent.name == "agi":
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            return parent
    return Path.cwd()

WORKSPACE = bootstrap()

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from scripts.identity_grounding import IDENTITY_ANCHOR

# 시스템별 키워드 매핑 (Organ-based)
SYSTEM_KEYWORDS = {
    "core": {
        "keywords": [
            "분석", "왜", "이유", "원인", "통찰", "권장", "추천", "제안",
            "충돌", "모순", "정반합", "균형", "조화", "통합",
            "analyze", "why", "insight", "recommend", "suggest", "balance",
            "Core", "Core", "Core", "Core", "코어", "Core"
        ],
        "priority": ["분석해", "왜", "이유가", "추천해", "제안해", "Core", "Core", "Core", "코어"],
        "description": f"{IDENTITY_ANCHOR['core']['name']}: 판단, 통찰, 권장사항 생성"
    },
    "shion": {
        "keywords": [
            "실행", "목표", "작업", "학습", "수행", "처리", "진행",
            "youtube", "rpa", "자동", "생성", "계속",
            "execute", "goal", "task", "learn", "run", "process", "continue",
            "Binoche_Observer", "Shion", "executor", "비노체", "Shion"
        ],
        "priority": ["실행해", "목표", "작업", "학습해", "진행해", "Binoche_Observer", "비노체"],
        "description": f"{IDENTITY_ANCHOR['self']['name']}: 자율 실행, 목표 생성, RPA 작업"
    },
    "trinity": {
        "keywords": [
            "상태", "메트릭", "리듬", "간격", "스케줄", "조정",
            "info_density", "entropy", "horizon", "resonance",
            "status", "metric", "rhythm", "schedule", "adjust",
            "child", "레조넌스", "차일드"
        ],
        "priority": ["상태", "메트릭", "리듬", "간격", "resonance", "레조넌스"],
        "description": f"{IDENTITY_ANCHOR['trinity']['name']}: 시스템 상태, 메트릭, 리듬 조정"
    },
    "master": {
        "keywords": [
            "전체", "모든", "통합", "조율", "시작", "중지", "초기화",
            "all", "entire", "orchestrate", "start", "stop", "init",
            "rud", "Core field"
        ],
        "priority": ["전체", "모든", "통합", "조율", "rud"],
        "description": f"{IDENTITY_ANCHOR['system']['name']}: 전체 시스템 조율(RUD: ___CORE_FIELD___) 및 제어"
    }
}

# 긴급도 키워드
URGENCY_KEYWORDS = {
    "high": ["긴급", "즉시", "critical", "urgent", "now", "asap"],
    "medium": ["빠르게", "soon", "quickly"],
    "low": ["나중에", "later", "eventually"]
}


class MasterAIRouter:
    """Master AI Router - 사용자 메시지 자동 라우팅"""
    
    def __init__(self):
        self.workspace = WORKSPACE
        self.log_file = self.workspace / "outputs" / "master_router_log.jsonl"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def parse_intent(self, user_message: str) -> Dict:
        """
        사용자 메시지에서 의도(intent)를 파악한다.
        
        Returns:
            {
                "target_system": "Core|Binoche_Observer|resonance|master",
                "urgency": "high|medium|low",
                "confidence": 0.0-1.0,
                "matched_keywords": [],
                "action_type": "analyze|execute|check|orchestrate"
            }
        """
        msg_lower = user_message.lower()
        rua_token = re.search(r"\brua\b", user_message, re.IGNORECASE) is not None
        
        # 각 시스템별 매칭 스코어 계산
        scores = {}
        matched_kw = {}
        
        for system, config in SYSTEM_KEYWORDS.items():
            score = 0.0
            matched = []
            
            # 일반 키워드 매칭 (1점)
            for kw in config["keywords"]:
                if kw in msg_lower:
                    score += 1.0
                    matched.append(kw)
            
            # 우선 키워드 매칭 (3점)
            for kw in config.get("priority", []):
                if kw in msg_lower:
                    score += 3.0
                    matched.append(f"[HIGH]{kw}")
            
            scores[system] = score
            matched_kw[system] = matched
        
        # 가장 높은 점수의 시스템 선택
        if rua_token:
            # Rua token forces Core routing (alias fallback).
            target_system = "core"
            confidence = 0.9
            matched_kw["core"].append("[ALIAS]rua")
        elif max(scores.values()) == 0:
            # 매칭 실패 → Master가 직접 처리
            target_system = "master"
            confidence = 0.5
        else:
            target_system = max(scores, key=scores.get)
            max_score = scores[target_system]
            total_score = sum(scores.values())
            confidence = max_score / total_score if total_score > 0 else 0.5
        
        # 긴급도 파악
        urgency = "medium"  # 기본값
        for level, keywords in URGENCY_KEYWORDS.items():
            if any(kw in msg_lower for kw in keywords):
                urgency = level
                break
        
        # 액션 타입 결정
        action_map = {
            "core": "analyze",
            "shion": "execute",
            "trinity": "check",
            "master": "orchestrate"
        }
        action_type = action_map.get(target_system, "orchestrate")
        
        return {
            "target_system": target_system,
            "urgency": urgency,
            "confidence": confidence,
            "matched_keywords": matched_kw[target_system],
            "action_type": action_type,
            "original_message": user_message
        }
    
    def route_to_core(self, intent: Dict) -> Dict:
        """Core 시스템으로 라우팅"""
        
        # Trinity Cycle 실행 → Core 합성
        try:
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(self.workspace / "scripts" / "autopoietic_trinity_cycle.ps1"),
                    "-Hours", "24", "-VerboseLog"
                ],
                capture_output=True,
                text=True,
                timeout=300,
                encoding="utf-8"
            )
            
            # Core 최신 출력 읽기
            core_file = self.workspace / "outputs" / "core_enhanced_synthesis_latest.md"
            if core_file.exists():
                core_output = core_file.read_text(encoding="utf-8")
                
                # HIGH 권장사항 추출
                high_recommendations = []
                for line in core_output.split("\n"):
                    if "🔴 HIGH" in line or "**우선순위: HIGH**" in line:
                        high_recommendations.append(line.strip())
                
                return {
                    "system": "core",
                    "status": "success",
                    "recommendations": high_recommendations[:5],  # 상위 5개
                    "full_report": str(core_file),
                    "summary": f"{IDENTITY_ANCHOR['core']['name']} (Core)이 {len(high_recommendations)}개의 HIGH 권장사항을 생성했습니다."
                }
            
            return {
                "system": "core",
                "status": "warning",
                "summary": f"{IDENTITY_ANCHOR['core']['name']} 리포트 파일이 존재하지 않습니다."
            }
        except Exception as e:
            return {
                "system": "core",
                "status": "error",
                "error": str(e)
            }
    
    def route_to_shion(self, intent: Dict) -> Dict:
        """Shion 시스템으로 라우팅"""
        
        # Autonomous Goal Generator 실행
        try:
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-Command",
                    f"cd {self.workspace}; "
                    f"if (Test-Path fdo_agi_repo/.venv/Scripts/python.exe) {{ "
                    f"fdo_agi_repo/.venv/Scripts/python.exe scripts/autonomous_goal_generator.py "
                    f"}} else {{ python scripts/autonomous_goal_generator.py }}"
                ],
                capture_output=True,
                text=True,
                timeout=180,
                encoding="utf-8"
            )
            
            # 생성된 목표 읽기
            goals_file = self.workspace / "outputs" / "autonomous_goals_latest.json"
            if goals_file.exists():
                goals = json.loads(goals_file.read_text(encoding="utf-8"))
                
                return {
                    "system": "shion",
                    "status": "success",
                    "goals_count": len(goals.get("prioritized_goals", [])),
                    "top_goals": goals.get("prioritized_goals", [])[:3],
                    "full_report": str(goals_file),
                    "summary": f"{IDENTITY_ANCHOR['self']['name']}이 {len(goals.get('prioritized_goals', []))}개의 목표를 생성했습니다."
                }
            
            return {
                "system": "shion",
                "status": "warning",
                "summary": f"{IDENTITY_ANCHOR['self']['name']} 목표 파일이 존재하지 않습니다."
            }
        except Exception as e:
            return {
                "system": "shion",
                "status": "error",
                "error": str(e)
            }
    
    def route_to_trinity(self, intent: Dict) -> Dict:
        """Trinity 시스템으로 라우팅"""
        
        try:
            # Resonance Simulation 실행
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-Command",
                    f"cd {self.workspace}; "
                    f"if (Test-Path fdo_agi_repo/.venv/Scripts/python.exe) {{ "
                    f"fdo_agi_repo/.venv/Scripts/python.exe scripts/resonance_simulator.py "
                    f"}} else {{ python scripts/resonance_simulator.py }}"
                ],
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8"
            )
            
            # Resonance 상태 읽기
            resonance_file = self.workspace / "outputs" / "resonance_simulation_latest.json"
            if resonance_file.exists():
                resonance_data = json.loads(resonance_file.read_text(encoding="utf-8"))
                final = resonance_data.get("final_state", {})
                
                return {
                    "system": "trinity",
                    "status": "success",
                    "metrics": {
                        "info_density": final.get("info_density", "N/A"),
                        "resonance": final.get("resonance", "N/A"),
                        "entropy": final.get("entropy", "N/A"),
                        "horizon_crossings": final.get("horizon_crossings", "N/A")
                    },
                    "current_state": [f"Crossings: {final.get('horizon_crossings', 0)}"],
                    "full_report": str(resonance_file),
                    "summary": f"{IDENTITY_ANCHOR['trinity']['name']}: Resonance={final.get('resonance', 0):.2f}, Entropy={final.get('entropy', 0):.2f}"
                }
            
            return {
                "system": "trinity",
                "status": "warning",
                "summary": f"{IDENTITY_ANCHOR['trinity']['name']} 상태 파일이 존재하지 않습니다."
            }
        except Exception as e:
            return {
                "system": "trinity",
                "status": "error",
                "error": str(e)
            }
    
    def route_to_master(self, intent: Dict) -> Dict:
        """Master 직접 처리"""
        
        # Master Orchestrator 실행
        try:
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(self.workspace / "scripts" / "master_orchestrator.ps1")
                ],
                capture_output=True,
                text=True,
                timeout=300,
                encoding="utf-8"
            )
            
            return {
                "system": "master",
                "status": "success",
                "summary": f"{IDENTITY_ANCHOR['system']['name']} Orchestrator 실행 완료"
            }
        except Exception as e:
            return {
                "system": "master",
                "status": "error",
                "error": str(e)
            }
    
    def route(self, user_message: str) -> Dict:
        """
        사용자 메시지를 분석하고 적절한 시스템으로 라우팅한다.
        """
        # 1. 의도 파악
        intent = self.parse_intent(user_message)
        
        # 2. 라우팅
        router_map = {
            "core": self.route_to_core,
            "shion": self.route_to_shion,
            "trinity": self.route_to_trinity,
            "master": self.route_to_master
        }
        
        handler = router_map.get(intent["target_system"], self.route_to_master)
        result = handler(intent)
        
        # RUD Interface Standard (FIELD/DO/ASK)
        field_insight = result.get("field_insight", f"시스템이 {result['system']}의 상공에서 필드 흐름을 감지했습니다.")
        do_command = result.get("do_command", f"Ruby {result['system']} 모듈을 통해 해당 요청을 처리했습니다.")
        
        result.update({
            "field_insight": field_insight,
            "do_command": do_command if result['status'] == 'success' else None,
            "ask_question": None if result['status'] == 'success' else f"현재 {result['system']} 상태가 불확실합니다. 추가 지침이 필요하신가요?"
        })

        # 3. 로깅
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "intent": intent,
            "result": result
        }
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        return result


def main():
    """CLI 진입점"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Master AI Router")
    parser.add_argument("message", nargs="+", help="사용자 메시지")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    
    args = parser.parse_args()
    user_message = " ".join(args.message)
    
    router = MasterAIRouter()
    result = router.route(user_message)
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print()
        print(f"{'='*60}")
        print(f"✅ {result['system'].upper()} 응답:")
        print(f"{'='*60}")
        if result.get("summary"):
            print(f"Summary: {result['summary']}")
        
        print("-" * 20)
        print(f"FIELD: {result['field_insight']}")
        if result['do_command']:
            print(f"DO: {result['do_command']}")
        else:
            print(f"ASK: {result['ask_question']}")
        print()


if __name__ == "__main__":
    main()
