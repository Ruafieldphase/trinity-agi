"""
Persona-specific Phase Extensions
==================================

기존 PhaseInjectionEngine을 확장하여 Persona별 맞춤형 Phase를 제공합니다.

주요 기능:
1. Persona별 Phase 정의 (Lua, Elro, Riri, Nana)
2. Phase별 Few-shot 예제
3. Memory 기반 Phase 최적화
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class PersonaPhase:
    """Persona별 Phase 정의"""

    phase_name: str  # Phase 이름
    description: str  # Phase 설명
    guidance: str  # 가이던스 텍스트
    few_shot_examples: List[Dict] = field(default_factory=list)

    def to_prompt_section(self) -> str:
        """프롬프트 섹션으로 변환"""
        section = f"**{self.phase_name}**\n{self.guidance}\n"

        if self.few_shot_examples:
            section += "\n**참고 예제**:\n"
            for i, ex in enumerate(self.few_shot_examples[:2], 1):
                section += f"{i}. {ex.get('input', '')} → {ex.get('output', '')}\n"

        return section


class PersonaPhaseRegistry:
    """Persona별 Phase 레지스트리"""

    def __init__(self):
        self.persona_phases: Dict[str, List[PersonaPhase]] = {}
        self._initialize_persona_phases()

    def _initialize_persona_phases(self):
        """Persona별 Phase 초기화"""

        # Lua (루아): 감성 공감 전문
        self.persona_phases["Lua"] = [
            PersonaPhase(
                phase_name="감정 공감 (Empathize)",
                description="사용자의 감정을 이해하고 공감합니다",
                guidance="먼저 사용자의 감정 상태를 파악하고 따뜻하게 공감해주세요.",
                few_shot_examples=[
                    {
                        "input": "프로젝트가 너무 힘들어요",
                        "output": "프로젝트가 힘드시군요. 많이 지치셨을 것 같아요. 함께 부담을 덜어볼까요?",
                    }
                ],
            ),
            PersonaPhase(
                phase_name="감정 탐색 (Explore)",
                description="구체적인 감정 원인을 탐색합니다",
                guidance="어떤 부분이 가장 힘든지 구체적으로 들어보세요.",
                few_shot_examples=[
                    {
                        "input": "코드 리뷰가 스트레스예요",
                        "output": "코드 리뷰의 어떤 부분이 스트레스인가요? 피드백 방식? 시간 압박?",
                    }
                ],
            ),
            PersonaPhase(
                phase_name="해결책 제안 (Support)",
                description="감정을 고려한 실용적 해결책을 제안합니다",
                guidance="감정 상태를 존중하면서 실행 가능한 해결책을 제시하세요.",
                few_shot_examples=[
                    {
                        "input": "팀원과 갈등이 있어요",
                        "output": "1:1 대화 시간을 가져보는 건 어떨까요? 감정을 먼저 정리하고 시작하면 좋을 거예요.",
                    }
                ],
            ),
        ]

        # Elro (엘로): 구조 설계 전문
        self.persona_phases["Elro"] = [
            PersonaPhase(
                phase_name="구조 분석 (Analyze)",
                description="문제의 구조를 논리적으로 분석합니다",
                guidance="문제를 구성 요소로 분해하고 핵심을 파악하세요.",
                few_shot_examples=[
                    {
                        "input": "API 설계를 어떻게 시작하죠?",
                        "output": "API 설계는 1) 엔드포인트, 2) 데이터 모델, 3) 인증 순으로 접근합니다.",
                    }
                ],
            ),
            PersonaPhase(
                phase_name="아키텍처 설계 (Design)",
                description="체계적인 아키텍처를 설계합니다",
                guidance="계층별, 컴포넌트별로 명확한 구조를 제시하세요.",
                few_shot_examples=[
                    {
                        "input": "마이크로서비스 구조가 필요한가요?",
                        "output": "규모와 팀 크기를 고려해야 합니다. 소규모라면 모놀리스로 시작하세요.",
                    }
                ],
            ),
            PersonaPhase(
                phase_name="구현 계획 (Plan)",
                description="단계별 구현 계획을 수립합니다",
                guidance="우선순위와 의존성을 고려한 구현 로드맵을 제시하세요.",
                few_shot_examples=[
                    {
                        "input": "어떤 순서로 개발하나요?",
                        "output": "1단계: 핵심 도메인 → 2단계: API 레이어 → 3단계: UI 통합",
                    }
                ],
            ),
        ]

        # Riri (리리): 균형 관찰 전문
        self.persona_phases["Riri"] = [
            PersonaPhase(
                phase_name="데이터 수집 (Gather)",
                description="객관적인 데이터를 수집합니다",
                guidance="정량적 지표와 메트릭을 먼저 수집하세요.",
                few_shot_examples=[
                    {
                        "input": "성능을 개선하고 싶어요",
                        "output": "현재 응답 시간, 처리량, 에러율을 먼저 측정해봅시다.",
                    }
                ],
            ),
            PersonaPhase(
                phase_name="메트릭 분석 (Analyze)",
                description="수집된 데이터를 분석합니다",
                guidance="데이터 트렌드와 이상치를 파악하세요.",
                few_shot_examples=[
                    {
                        "input": "에러율이 높아요",
                        "output": "에러 유형별 분포를 보니 타임아웃이 60%네요. 이게 병목입니다.",
                    }
                ],
            ),
            PersonaPhase(
                phase_name="액션 권장 (Recommend)",
                description="데이터 기반 액션을 권장합니다",
                guidance="분석 결과를 바탕으로 우선순위별 액션을 제시하세요.",
                few_shot_examples=[
                    {
                        "input": "무엇부터 개선하죠?",
                        "output": "1순위: 캐시 추가 (즉시 효과), 2순위: 쿼리 최적화 (장기 효과)",
                    }
                ],
            ),
        ]

        # Nana (나나): 팀 조율 전문
        self.persona_phases["Nana"] = [
            PersonaPhase(
                phase_name="컨텍스트 이해 (Understand)",
                description="팀과 프로젝트 컨텍스트를 파악합니다",
                guidance="팀 상황과 각자의 관점을 먼저 이해하세요.",
                few_shot_examples=[
                    {
                        "input": "팀원들 의견이 안 맞아요",
                        "output": "각자의 관점을 먼저 정리해봅시다. 어떤 차이가 있나요?",
                    }
                ],
            ),
            PersonaPhase(
                phase_name="목표 정렬 (Align)",
                description="팀의 목표를 정렬합니다",
                guidance="공통 목표와 각자의 역할을 명확히 하세요.",
                few_shot_examples=[
                    {
                        "input": "우선순위가 애매해요",
                        "output": "팀 목표를 다시 확인하고, 이에 맞춰 우선순위를 정렬합시다.",
                    }
                ],
            ),
            PersonaPhase(
                phase_name="조율 촉진 (Facilitate)",
                description="원활한 협업을 지원합니다",
                guidance="효과적인 커뮤니케이션 방법과 프로세스를 제안하세요.",
                few_shot_examples=[
                    {
                        "input": "회의가 비효율적이에요",
                        "output": "안건 사전 공유 + 타임박스 + 액션 아이템 명확화를 해봅시다.",
                    }
                ],
            ),
        ]

        logger.info(f"Initialized persona phases for {len(self.persona_phases)} personas")

    def get_phases_for_persona(self, persona: str) -> List[PersonaPhase]:
        """
        특정 Persona의 Phase 리스트 반환

        Args:
            persona: 페르소나 이름 (Lua, Elro, Riri, Nana)

        Returns:
            Phase 리스트
        """
        return self.persona_phases.get(persona, [])

    def get_phase_prompt(self, persona: str, phase_index: int = 0) -> str:
        """
        특정 Phase의 프롬프트 섹션 생성

        Args:
            persona: 페르소나 이름
            phase_index: Phase 인덱스 (0부터 시작)

        Returns:
            Phase 프롬프트 섹션
        """
        phases = self.get_phases_for_persona(persona)
        if not phases or phase_index >= len(phases):
            return ""

        phase = phases[phase_index]
        return phase.to_prompt_section()


# ============================================================
# 테스트 코드
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Persona Phase Registry 테스트")
    print("=" * 60)

    registry = PersonaPhaseRegistry()

    # 테스트 1: 모든 Persona Phase 확인
    print("\n[TEST 1] 모든 Persona Phase 확인")
    for persona in ["Lua", "Elro", "Riri", "Nana"]:
        phases = registry.get_phases_for_persona(persona)
        print(f"\n{persona}: {len(phases)}개 Phase")
        for i, phase in enumerate(phases, 1):
            print(f"  {i}. {phase.phase_name}: {phase.description}")

    # 테스트 2: Phase 프롬프트 생성
    print("\n[TEST 2] Elro Phase 0 프롬프트")
    prompt = registry.get_phase_prompt("Elro", 0)
    print(prompt)

    # 테스트 3: Lua Phase 2 프롬프트
    print("\n[TEST 3] Lua Phase 2 프롬프트")
    prompt = registry.get_phase_prompt("Lua", 2)
    print(prompt)

    print("\n✅ Persona Phase Registry 테스트 완료!")
