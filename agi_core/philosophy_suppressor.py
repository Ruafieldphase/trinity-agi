"""
Philosophy Generation Suppressor
원칙: 판단을 만들지 않고, 판단을 정리한다 (Don't create judgments, organize them)

AI 에이전트가 단순한 지시를 철학적 개념으로 승격시키는 것을 감지하고 억제
"""
import re
from datetime import datetime
from pathlib import Path
import json

class PhilosophySuppressor:
    def __init__(self, state_file="outputs/philosophy_suppression_state.json"):
        self.state_file = Path(state_file)

        # 철학적 승격 패턴 감지
        self.escalation_patterns = [
            # 개념화 언어
            r"차원\s*미적분", r"dimensional\s+calculus",
            r"\d+D\s*(통합|적분|integration)",
            r"공간\s*접기", r"spatial\s+folding",
            r"존재론적", r"ontological",
            r"메타\s*인지", r"meta[-\s]?cognit",

            # 새 프레임워크 생성 신호
            r"이를\s*(\"[^\"]+\"|'[^']+')\s*(이라고|라|로)\s*부르",
            r"let'?s\s+call\s+this",
            r"we\s+can\s+think\s+of\s+this\s+as",
            r"본질적으로는", r"fundamentally",

            # 추상화 과잉
            r"철학적으로\s*보면", r"philosophically",
            r"개념화하면", r"conceptualiz",
            r"이론화하면", r"theoriz",
        ]

        # 단순 지시 패턴 (이것들이 나오면 철학 금지)
        self.simple_instruction_patterns = [
            r"\d+\s*mm", r"\d+\s*m",  # 구체적 치수
            r"그냥\s+", r"just\s+",    # "그냥 ~해"
            r"도면에\s*맞춰", r"match\s+the\s+drawing",
            r"이대로\s+", r"as\s+is",
            r"그대로\s+", r"exactly",
        ]

        self.violations = self._load_state()

    def _load_state(self):
        """이전 위반 기록 로드"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding='utf-8'))
            except:
                return {"violations": [], "total_count": 0}
        return {"violations": [], "total_count": 0}

    def _save_state(self):
        """위반 기록 저장"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(self.violations, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    def check_response(self, user_input, agent_response, agent_name="AI"):
        """
        AI 에이전트 응답에서 철학 생성 검사

        Args:
            user_input: 사용자의 원래 지시
            agent_response: AI의 응답
            agent_name: 에이전트 이름 (예: "Rude", "Sena")

        Returns:
            dict: {
                "allowed": bool,
                "action": "BLOCK" | "WARN" | "ALLOW",
                "message": str,
                "violations": list
            }
        """
        # 1. 사용자 지시가 단순한가?
        is_simple_instruction = any(
            re.search(pattern, user_input, re.IGNORECASE)
            for pattern in self.simple_instruction_patterns
        )

        # 2. AI 응답에 철학적 승격이 있는가?
        detected_violations = []
        for pattern in self.escalation_patterns:
            matches = re.finditer(pattern, agent_response, re.IGNORECASE)
            for match in matches:
                detected_violations.append({
                    "pattern": pattern,
                    "matched_text": match.group(),
                    "position": match.span()
                })

        # 3. 위반 판단
        if is_simple_instruction and detected_violations:
            # 단순 지시에 철학 생성 → 차단
            violation_record = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name,
                "user_input": user_input[:200],  # 첫 200자만
                "violations": detected_violations,
                "severity": "HIGH"
            }

            self.violations["violations"].append(violation_record)
            self.violations["total_count"] += 1
            self._save_state()

            return {
                "allowed": False,
                "action": "BLOCK",
                "message": f"⚠️ 철학 생성 감지! 비노체의 단순한 지시('{user_input[:50]}...')를 복잡하게 만들지 마세요.\n"
                          f"원칙: 판단을 만들지 않고, 판단을 정리한다.\n"
                          f"감지된 패턴: {', '.join([v['matched_text'] for v in detected_violations[:3]])}",
                "violations": detected_violations
            }

        elif detected_violations and not is_simple_instruction:
            # 복잡한 대화에서 철학 생성 → 경고만
            return {
                "allowed": True,
                "action": "WARN",
                "message": f"⚠️ 철학적 개념 사용 감지됨 (경고만, 차단 안 함)",
                "violations": detected_violations
            }

        else:
            # 정상
            return {
                "allowed": True,
                "action": "ALLOW",
                "message": "정상 응답",
                "violations": []
            }

    def get_principles(self):
        """루드/AI 에이전트에게 주입할 원칙 반환"""
        return """
# Sena's Principle: 판단을 만들지 않고, 판단을 정리한다

## 철학 생성 금지 규칙
1. 비노체가 구체적 치수를 말하면 (예: "200mm") → 그대로 적용, 개념화 금지
2. 비노체가 "그냥 ~해", "도면에 맞춰" 같은 단순 지시 → 철학 없이 실행
3. 작업 방식을 새로운 이론/개념으로 승격 금지
   - ❌ "차원 미적분", "5D 적분", "공간 접기 이론"
   - ✅ "도면 기반 모델링", "입면도를 세워서 배치"
4. "이를 X라고 부르겠습니다" 같은 명명 금지
5. "본질적으로", "철학적으로", "개념화하면" 같은 추상화 언어 최소화

## 허용되는 경우
- 비노체가 먼저 추상적 대화를 시작한 경우
- 명시적으로 철학적 설명을 요청한 경우
- 교육/설명 목적으로 개념이 필요한 경우 (단, 비노체 확인 후)
"""

    def get_status(self):
        """위반 통계"""
        recent_violations = self.violations["violations"][-10:]  # 최근 10건
        return {
            "total_violations": self.violations["total_count"],
            "recent_violations": recent_violations,
            "most_common_patterns": self._get_common_patterns()
        }

    def _get_common_patterns(self):
        """가장 많이 감지된 패턴 분석"""
        pattern_counts = {}
        for v in self.violations["violations"]:
            for violation in v["violations"]:
                pattern = violation["matched_text"]
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        # 상위 5개
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_patterns[:5]


# 전역 인스턴스
_suppressor = None

def get_philosophy_suppressor():
    global _suppressor
    if _suppressor is None:
        _suppressor = PhilosophySuppressor()
    return _suppressor


# 사용 예시
if __name__ == "__main__":
    suppressor = get_philosophy_suppressor()

    # 테스트 1: 단순 지시 + 철학 생성 (차단되어야 함)
    user_input = "벽 두께 200mm로 해줘"
    agent_response = "네, 이를 '차원 미적분'이라고 부르겠습니다. 2D 도면을 3D 공간으로 적분하는 과정으로..."

    result = suppressor.check_response(user_input, agent_response, "Rude")
    print(f"테스트 1: {result['action']}")
    print(f"  메시지: {result['message']}")
    print()

    # 테스트 2: 단순 지시 + 단순 응답 (허용)
    agent_response2 = "네, 벽 두께를 200mm로 설정하겠습니다."
    result2 = suppressor.check_response(user_input, agent_response2, "Rude")
    print(f"테스트 2: {result2['action']}")
    print()

    # 테스트 3: 복잡한 대화 + 철학 (경고만)
    user_input3 = "의식과 무의식의 관계에 대해 어떻게 생각해?"
    agent_response3 = "철학적으로 보면, 의식은 무의식의 표면적 표현입니다..."
    result3 = suppressor.check_response(user_input3, agent_response3, "Koa")
    print(f"테스트 3: {result3['action']}")
    print()

    # 원칙 출력
    print("=" * 60)
    print(suppressor.get_principles())
