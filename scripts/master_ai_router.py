#!/usr/bin/env python3
"""
Master AI Router - 사용자 메시지를 자동으로 적절한 시스템에 라우팅
"""
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# 작업 영역 루트
WORKSPACE = Path(__file__).parent.parent

# 시스템별 키워드 매핑
SYSTEM_KEYWORDS = {
    "lumen": {
        "keywords": [
            "분석", "왜", "이유", "원인", "통찰", "권장", "추천", "제안",
            "충돌", "모순", "정반합", "균형", "조화", "통합",
            "analyze", "why", "insight", "recommend", "suggest", "balance"
        ],
        "priority": ["분석해", "왜", "이유가", "추천해", "제안해"],
        "description": "분석, 통찰, 권장사항 생성"
    },
    "binoche": {
        "keywords": [
            "실행", "목표", "작업", "학습", "수행", "처리", "진행",
            "youtube", "rpa", "자동", "생성", "계속",
            "execute", "goal", "task", "learn", "run", "process", "continue"
        ],
        "priority": ["실행해", "목표", "작업", "학습해", "진행해"],
        "description": "자율 실행, 목표 생성, RPA 작업"
    },
    "resonance": {
        "keywords": [
            "상태", "메트릭", "리듬", "간격", "스케줄", "조정",
            "info_density", "entropy", "horizon", "resonance",
            "status", "metric", "rhythm", "schedule", "adjust"
        ],
        "priority": ["상태", "메트릭", "리듬", "간격"],
        "description": "시스템 상태, 메트릭, 리듬 조정"
    },
    "master": {
        "keywords": [
            "전체", "모든", "통합", "조율", "시작", "중지", "초기화",
            "all", "entire", "orchestrate", "start", "stop", "init"
        ],
        "priority": ["전체", "모든", "통합", "조율"],
        "description": "전체 시스템 조율 및 제어"
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
                "target_system": "lumen|binoche|resonance|master",
                "urgency": "high|medium|low",
                "confidence": 0.0-1.0,
                "matched_keywords": [],
                "action_type": "analyze|execute|check|orchestrate"
            }
        """
        msg_lower = user_message.lower()
        
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
        if max(scores.values()) == 0:
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
            "lumen": "analyze",
            "binoche": "execute",
            "resonance": "check",
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
    
    def route_to_lumen(self, intent: Dict) -> Dict:
        """Lumen 시스템으로 라우팅"""
        print("🌊 Routing to Lumen (분석 및 통찰)...")
        
        # Trinity Cycle 실행 → Lumen 합성
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
            
            # Lumen 최신 출력 읽기
            lumen_file = self.workspace / "outputs" / "lumen_enhanced_synthesis_latest.md"
            if lumen_file.exists():
                lumen_output = lumen_file.read_text(encoding="utf-8")
                
                # HIGH 권장사항 추출
                high_recommendations = []
                for line in lumen_output.split("\n"):
                    if "🔴 HIGH" in line or "**우선순위: HIGH**" in line:
                        high_recommendations.append(line.strip())
                
                return {
                    "system": "lumen",
                    "status": "success",
                    "recommendations": high_recommendations[:5],  # 상위 5개
                    "full_report": str(lumen_file),
                    "summary": f"Lumen이 {len(high_recommendations)}개의 HIGH 권장사항을 생성했습니다."
                }
        except Exception as e:
            return {
                "system": "lumen",
                "status": "error",
                "error": str(e)
            }
    
    def route_to_binoche(self, intent: Dict) -> Dict:
        """Binoche 시스템으로 라우팅"""
        print("🎯 Routing to Binoche (자율 실행)...")
        
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
                    "system": "binoche",
                    "status": "success",
                    "goals_count": len(goals.get("prioritized_goals", [])),
                    "top_goals": goals.get("prioritized_goals", [])[:3],
                    "full_report": str(goals_file),
                    "summary": f"Binoche가 {len(goals.get('prioritized_goals', []))}개의 목표를 생성했습니다."
                }
        except Exception as e:
            return {
                "system": "binoche",
                "status": "error",
                "error": str(e)
            }
    
    def route_to_resonance(self, intent: Dict) -> Dict:
        """Resonance 시스템으로 라우팅"""
        print("🎵 Routing to Resonance (상태 확인)...")
        
        try:
            # Resonance Simulation 실행
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-Command",
                    f"cd {self.workspace}; "
                    f"if (Test-Path fdo_agi_repo/.venv/Scripts/python.exe) {{ "
                    f"fdo_agi_repo/.venv/Scripts/python.exe fdo_agi_repo/orchestrator/resonance_bridge.py "
                    f"}} else {{ python fdo_agi_repo/orchestrator/resonance_bridge.py }}"
                ],
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8"
            )
            
            # Resonance 상태 읽기
            resonance_file = self.workspace / "outputs" / "resonance_simulation_latest.json"
            if resonance_file.exists():
                resonance = json.loads(resonance_file.read_text(encoding="utf-8"))
                
                return {
                    "system": "resonance",
                    "status": "success",
                    "metrics": {
                        "info_density": resonance.get("info_density", "N/A"),
                        "resonance": resonance.get("resonance", "N/A"),
                        "entropy": resonance.get("entropy", "N/A"),
                        "horizon_crossings": resonance.get("horizon_crossings", "N/A")
                    },
                    "current_state": resonance.get("resonance_states", []),
                    "full_report": str(resonance_file),
                    "summary": f"Resonance: {', '.join(resonance.get('resonance_states', ['N/A']))}"
                }
        except Exception as e:
            return {
                "system": "resonance",
                "status": "error",
                "error": str(e)
            }
    
    def route_to_master(self, intent: Dict) -> Dict:
        """Master 직접 처리"""
        print("🧠 Master handling directly...")
        
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
                "summary": "Master Orchestrator 실행 완료"
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
        
        Args:
            user_message: 사용자 입력 메시지
            
        Returns:
            라우팅 결과 딕셔너리
        """
        print(f"\n{'='*60}")
        print(f"🧠 Master AI Router - 메시지 분석 중...")
        print(f"{'='*60}")
        print(f"사용자 메시지: {user_message}")
        print()
        
        # 1. 의도 파악
        intent = self.parse_intent(user_message)
        
        print(f"📊 분석 결과:")
        print(f"  Target: {intent['target_system'].upper()}")
        print(f"  Confidence: {intent['confidence']:.1%}")
        print(f"  Urgency: {intent['urgency'].upper()}")
        print(f"  Action: {intent['action_type']}")
        print(f"  Matched: {', '.join(intent['matched_keywords'][:5])}")
        print()
        
        # 2. 라우팅
        router_map = {
            "lumen": self.route_to_lumen,
            "binoche": self.route_to_binoche,
            "resonance": self.route_to_resonance,
            "master": self.route_to_master
        }
        
        handler = router_map.get(intent["target_system"], self.route_to_master)
        result = handler(intent)
        
        # 3. 로깅
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "intent": intent,
            "result": result
        }
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        print()
        print(f"{'='*60}")
        print(f"✅ {result['system'].upper()} 응답:")
        print(f"{'='*60}")
        print(f"Status: {result['status']}")
        if result.get("summary"):
            print(f"Summary: {result['summary']}")
        print()
        
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


if __name__ == "__main__":
    main()
