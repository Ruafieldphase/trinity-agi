"""
Adaptive Gate System
맥락에 따라 열렸다 닫혔다 하는 유연한 경계

원칙:
- 처음 만나는 영역 → 경계 세움 (Ask-First)
- 익숙한 영역 → 경계 낮춤 (Trust)
- 위험 감지 → 경계 즉시 세움 (Protect)
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class AdaptiveGate:
    def __init__(self, state_file="outputs/adaptive_gate_state.json"):
        self.state_file = Path(state_file)
        self.state = self._load_state()

        # 기본 보호막 설정
        self.base_protection = {
            "failure_detector": True,      # 실패 감지는 항상 활성
            "ask_first": "adaptive",       # Ask-First는 적응형
            "philosophy_suppressor": "adaptive"  # 철학 억제도 적응형
        }

    def _load_state(self):
        """이전 상태 로드"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding='utf-8'))
            except:
                return self._init_state()
        return self._init_state()

    def _init_state(self):
        """초기 상태"""
        return {
            "domains": {},  # 영역별 경험 추적
            "trust_level": {},  # AI 에이전트별 신뢰도
            "recent_failures": [],  # 최근 실패 기록
            "conversation_mode": "neutral"  # 대화 모드
        }

    def _save_state(self):
        """상태 저장"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(self.state, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    def check_gate(self,
                   domain: str,
                   agent_name: str,
                   task_description: str,
                   conversation_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        맥락 기반 Gate 판단

        Args:
            domain: 영역 (예: "CAD", "3D_Modeling", "Philosophy", "General")
            agent_name: AI 이름 (예: "Rude", "Koa")
            task_description: 작업 설명
            conversation_context: {
                "mode": "technical" | "philosophical" | "casual",
                "user_explicitly_asked": bool,
                "recent_messages": list
            }

        Returns:
            {
                "gate": "OPEN" | "HOLD" | "CLOSE",
                "reason": str,
                "confidence": float,  # 0-1
                "adaptive_factors": dict
            }
        """
        # 1. 도메인 경험 확인
        domain_experience = self._get_domain_experience(domain)

        # 2. 에이전트 신뢰도 확인
        agent_trust = self._get_agent_trust(agent_name, domain)

        # 3. 최근 실패 이력 확인
        recent_failure_in_domain = self._check_recent_failures(domain)

        # 4. 대화 맥락 분석
        context_mode = self._analyze_context(conversation_context)

        # 5. Gate 결정
        decision = self._make_decision(
            domain=domain,
            domain_experience=domain_experience,
            agent_trust=agent_trust,
            recent_failure=recent_failure_in_domain,
            context_mode=context_mode,
            conversation_context=conversation_context
        )

        # 6. 상태 업데이트
        self._update_state(domain, agent_name, decision)

        return decision

    def _get_domain_experience(self, domain: str) -> Dict:
        """도메인 경험 조회"""
        if domain not in self.state["domains"]:
            self.state["domains"][domain] = {
                "first_encountered": datetime.now().isoformat(),
                "total_tasks": 0,
                "successful_tasks": 0,
                "last_success": None,
                "familiarity": 0.0  # 0 (처음) ~ 1 (완전 익숙)
            }

        return self.state["domains"][domain]

    def _get_agent_trust(self, agent_name: str, domain: str) -> float:
        """에이전트 신뢰도 조회 (0-1)"""
        key = f"{agent_name}:{domain}"

        if key not in self.state["trust_level"]:
            self.state["trust_level"][key] = {
                "trust": 0.5,  # 기본 신뢰도 50%
                "history": []
            }

        return self.state["trust_level"][key]["trust"]

    def _check_recent_failures(self, domain: str) -> bool:
        """최근 24시간 내 해당 도메인 실패 있는지"""
        cutoff = datetime.now() - timedelta(hours=24)

        for failure in self.state["recent_failures"]:
            failure_time = datetime.fromisoformat(failure["timestamp"])
            if failure_time > cutoff and failure.get("domain") == domain:
                return True

        return False

    def _analyze_context(self, conversation_context: Optional[Dict]) -> str:
        """대화 맥락 분석"""
        if not conversation_context:
            return "neutral"

        return conversation_context.get("mode", "neutral")

    def _make_decision(self,
                       domain: str,
                       domain_experience: Dict,
                       agent_trust: float,
                       recent_failure: bool,
                       context_mode: str,
                       conversation_context: Optional[Dict]) -> Dict:
        """Gate 결정 로직"""

        familiarity = domain_experience["familiarity"]
        domain_risk = self._get_domain_risk(domain)
        required_threshold = 0.5 + (domain_risk * 0.4) # 0.5 ~ 0.9

        base_factors = {
            "familiarity": familiarity,
            "trust": agent_trust,
            "domain_risk": domain_risk,
            "required_threshold": required_threshold
        }

        # === Rule 1: 최근 실패가 있으면 무조건 HOLD ===
        if recent_failure:
            factors = base_factors.copy()
            factors.update({"recent_failure": True})
            return {
                "gate": "HOLD",
                "reason": f"최근 {domain} 영역에서 실패 이력이 있어 확인이 필요합니다",
                "confidence": 1.0,
                "adaptive_factors": factors
            }

        # === Rule 2: 사용자가 명시적으로 요청한 경우 OPEN ===
        if conversation_context and conversation_context.get("user_explicitly_asked"):
            factors = base_factors.copy()
            factors.update({"explicit_request": True})
            return {
                "gate": "OPEN",
                "reason": "비노체가 명시적으로 요청한 작업",
                "confidence": 1.0,
                "adaptive_factors": factors
            }

        # === Rule 3: 도메인 위험도 기반 OPEN 판단 ===
        if familiarity >= required_threshold and agent_trust >= required_threshold:
            factors = base_factors.copy()
            factors.update({"mode": "experienced"})
            return {
                "gate": "OPEN",
                "reason": f"{domain} 영역 경험 충분 (위험도: {domain_risk:.1f}, 필요 임계값: {required_threshold:.1f})",
                "confidence": 0.8,
                "adaptive_factors": factors
            }

        # === Rule 4: 전문 영역 + 낮은 익숙도 = HOLD ===
        professional_domains = ["CAD", "3D_Modeling", "Architecture", "Blender", "DXF"]
        # 위험도가 높은 영역에서 임계값 미달 시 HOLD
        if domain in professional_domains and (familiarity < required_threshold or agent_trust < required_threshold):
            factors = base_factors.copy()
            factors.update({"domain_type": "professional", "ask_first": True})
            return {
                "gate": "HOLD",
                "reason": f"전문 영역({domain})에 대한 충분한 신뢰/익숙도 부족 (필요: {required_threshold:.1f})",
                "confidence": 0.9,
                "adaptive_factors": factors
            }

        # === Rule 5: 철학적 대화 중이면 철학 생성 허용 ===
        if context_mode == "philosophical":
            factors = base_factors.copy()
            factors.update({"context_mode": context_mode, "philosophy_allowed": True})
            return {
                "gate": "OPEN",
                "reason": "철학적 대화 맥락에서는 철학 생성 허용",
                "confidence": 0.7,
                "adaptive_factors": factors
            }

        # === Rule 6: 기본값 - 낮은 신뢰도에서는 HOLD ===
        if agent_trust < 0.5: # 기본 신뢰 미달
            factors = base_factors.copy()
            factors.update({"mode": "building_trust"})
            return {
                "gate": "HOLD",
                "reason": f"신뢰도 축적 중 (현재: {agent_trust:.1%})",
                "confidence": 0.6,
                "adaptive_factors": factors
            }

        # === 기본: OPEN ===
        return {
            "gate": "OPEN",
            "reason": "일반 작업 영역",
            "confidence": 0.5,
            "adaptive_factors": base_factors
        }

    def _get_domain_risk(self, domain: str) -> float:
        """
        도메인별 위험도 산출 (0.1 ~ 0.9)
        """
        risks = {
            "CAD": 0.9,
            "3D_Modeling": 0.8,
            "Architecture": 0.8,
            "Blender": 0.7,
            "DXF": 0.7,
            "Philosophy": 0.3,
            "General": 0.1
        }
        return risks.get(domain, 0.5)

    def _update_state(self, domain: str, agent_name: str, decision: Dict):
        """Gate 결정 후 상태 업데이트"""
        # 도메인 작업 카운트 증가
        if domain in self.state["domains"]:
            self.state["domains"][domain]["total_tasks"] += 1

        self._save_state()

    def record_success(self, domain: str, agent_name: str, difficulty: float = 0.5):
        """작업 성공 기록 → 익숙도/신뢰도 증가 (난이도 반영)"""
        key = f"{agent_name}:{domain}"

        # 도메인 익숙도 증가
        if domain in self.state["domains"]:
            exp = self.state["domains"][domain]
            exp["successful_tasks"] += 1
            exp["last_success"] = datetime.now().isoformat()

            # 익숙도 계산: 성공률 기반 (최대 1.0)
            if exp["total_tasks"] > 0:
                success_rate = exp["successful_tasks"] / exp["total_tasks"]
                # 최소 3회 성공해야 익숙도 0.5 이상
                min_count_factor = min(exp["successful_tasks"] / 3, 1.0)
                exp["familiarity"] = success_rate * min_count_factor

        # 에이전트 신뢰도 증가 (난이도가 높을수록 더 많이 증가)
        if key in self.state["trust_level"]:
            trust_data = self.state["trust_level"][key]
            trust_increase = 0.05 + (max(0, min(1, difficulty)) * 0.1) # 0.05 ~ 0.15
            trust_data["trust"] = min(trust_data["trust"] + trust_increase, 1.0)
            trust_data["history"].append({
                "timestamp": datetime.now().isoformat(),
                "result": "success",
                "difficulty": difficulty,
                "increase": trust_increase
            })

        self._save_state()

    def record_failure(self, domain: str, agent_name: str, error_signature: str, severity: float = 0.5):
        """작업 실패 기록 → 신뢰도 감소, 경계 강화 (심각도 반영)"""
        key = f"{agent_name}:{domain}"

        # 최근 실패 목록에 추가
        self.state["recent_failures"].append({
            "timestamp": datetime.now().isoformat(),
            "domain": domain,
            "agent": agent_name,
            "error": error_signature,
            "severity": severity
        })

        # 24시간 이상 된 실패는 제거
        cutoff = datetime.now() - timedelta(hours=24)
        self.state["recent_failures"] = [
            f for f in self.state["recent_failures"]
            if datetime.fromisoformat(f["timestamp"]) > cutoff
        ]

        # 신뢰도 감소 (심각할수록 더 많이 감소)
        if key in self.state["trust_level"]:
            trust_data = self.state["trust_level"][key]
            trust_decrease = 0.05 + (max(0, min(1, severity)) * 0.3) # 0.05 ~ 0.35
            trust_data["trust"] = max(trust_data["trust"] - trust_decrease, 0.0)
            trust_data["history"].append({
                "timestamp": datetime.now().isoformat(),
                "result": "failure",
                "error": error_signature,
                "severity": severity,
                "decrease": trust_decrease
            })

        self._save_state()

    def get_status(self) -> Dict:
        """현재 상태 요약"""
        return {
            "total_domains": len(self.state["domains"]),
            "familiar_domains": [
                d for d, info in self.state["domains"].items()
                if info["familiarity"] >= 0.7
            ],
            "recent_failures_count": len(self.state["recent_failures"]),
            "trust_levels": {
                k: v["trust"] for k, v in self.state["trust_level"].items()
            }
        }


# 전역 인스턴스
_gate = None

def get_adaptive_gate():
    global _gate
    if _gate is None:
        _gate = AdaptiveGate()
    return _gate


# 사용 예시
if __name__ == "__main__":
    gate = get_adaptive_gate()

    print("=== 테스트 1: CAD 작업 (처음) ===")
    result1 = gate.check_gate(
        domain="CAD",
        agent_name="Rude",
        task_description="DXF 파일을 3D 모델로 변환",
        conversation_context={"mode": "technical"}
    )
    print(f"Gate: {result1['gate']}")
    print(f"Reason: {result1['reason']}")
    print(f"Familiarity: {result1['adaptive_factors'].get('familiarity', 0):.1%}")
    print()

    print("=== 성공 3회 기록 (익숙도 증가) ===")
    for i in range(3):
        gate.record_success("CAD", "Rude")
    print()

    print("=== 테스트 2: CAD 작업 (익숙해진 후) ===")
    result2 = gate.check_gate(
        domain="CAD",
        agent_name="Rude",
        task_description="DXF 파일을 3D 모델로 변환",
        conversation_context={"mode": "technical"}
    )
    print(f"Gate: {result2['gate']}")
    print(f"Reason: {result2['reason']}")
    print(f"Familiarity: {result2['adaptive_factors'].get('familiarity', 0):.1%}")
    print()

    print("=== 테스트 3: 실패 발생 (경계 강화) ===")
    gate.record_failure("CAD", "Rude", "API_KEY_INVALID")
    result3 = gate.check_gate(
        domain="CAD",
        agent_name="Rude",
        task_description="DXF 파일을 3D 모델로 변환"
    )
    print(f"Gate: {result3['gate']}")
    print(f"Reason: {result3['reason']}")
    print()

    print("=== 테스트 4: 철학 대화 중 철학 생성 ===")
    result4 = gate.check_gate(
        domain="Philosophy",
        agent_name="Koa",
        task_description="의식과 무의식의 관계",
        conversation_context={"mode": "philosophical"}
    )
    print(f"Gate: {result4['gate']}")
    print(f"Reason: {result4['reason']}")
    print()

    print("=== 테스트 5: 명시적 요청 ===")
    result5 = gate.check_gate(
        domain="CAD",
        agent_name="Rude",
        task_description="CAD 작업",
        conversation_context={"user_explicitly_asked": True}
    )
    print(f"Gate: {result5['gate']}")
    print(f"Reason: {result5['reason']}")
    print()

    print("=== 전체 상태 ===")
    status = gate.get_status()
    print(f"Total domains: {status['total_domains']}")
    print(f"Familiar domains: {status['familiar_domains']}")
    print(f"Recent failures: {status['recent_failures_count']}")
    print(f"Trust levels: {status['trust_levels']}")
