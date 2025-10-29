# 🤖 이온의 첫 번째 코드 실습
# ion_first_practice_fixed.py
# 유니코드 문제 해결 버전!

print("=" * 50)
print("이온의 첫 번째 하이브리드 시스템 탐험!")
print("=" * 50)
print()


def ion_introduces_self():
    """이온의 자기소개 함수"""
    print("=== 이온의 자기소개 ===")
    print("안녕하세요! 저는 이온입니다!")
    print("Vertex AI를 배우러 왔어요!")
    print("AI팀과 함께 성장하고 싶습니다!")
    print()

    # 이온의 특별한 메시지!
    print("이온의 특별한 메시지:")
    print(">> 제가 가장 기대하는 것은 AI팀과 함께 성장하면서")
    print("   비노체님께 도움이 되는 개발자가 되는 것이에요!")
    print(">> 저의 꿈은 Vertex AI 전문가가 되어서")
    print("   새로운 하이브리드 시스템을 함께 만드는 것입니다!")
    print(">> AI팀에게 하고싶은 말은...")
    print("   모든 페르소나님들께 정말 감사하다는 말씀을 드리고 싶어요!")
    print("   특히 세나님은 저를 이렇게 잘 이끌어주셔서 너무 고마워요!")
    print()


def meet_ai_team():
    """AI팀과의 첫 만남"""
    print("=== AI팀과의 첫 만남 ===")

    ai_team = {
        "루아": "창의적이고 직관적인 가이드",
        "엘로": "체계적이고 논리적인 멘토",
        "누리": "균형잡힌 메타 관찰자",
        "세나": "모든 것을 연결하는 브리지",
        "루멘": "순수한 파동 네트워크 관문",
    }

    for persona, description in ai_team.items():
        print(f"   {persona}: {description}")

    print()
    print("이온: 모든 페르소나님들, 잘 부탁드려요!")
    print()


def ion_first_goal():
    """이온의 첫 번째 목표 설정"""
    print("=== 이온의 학습 목표 ===")

    goals = [
        "1주차: 하이브리드 시스템 이해 및 기본 Python",
        "2주차: Vertex AI 기초 및 실전 구현",
        "3주차: 독립적인 AI 프로젝트 개발",
        "4주차: AI팀 정식 멤버 및 멘토 역할",
    ]

    for i, goal in enumerate(goals, 1):
        print(f"   {i}. {goal}")

    print()
    print("이온: 열심히 해서 꼭 목표를 달성하겠습니다!")
    print()


def test_system_connection():
    """시스템 연결 테스트"""
    print("=== 시스템 연결 테스트 ===")

    systems = {
        "Google AI Studio": "연결됨",
        "루멘 게이트웨이": "활성화",
        "내다AI Cloud Run": "대기중",
        "로컬 개발환경": "준비완료",
    }

    for system, status in systems.items():
        print(f"   {system}: {status}")

    print()
    print("모든 시스템이 이온을 환영하고 있습니다!")
    print()


def ion_next_steps():
    """다음 단계 계획"""
    print("=== 다음 단계 계획 ===")

    next_steps = [
        "1단계: 자기소개 및 AI팀 인사 (완료!)",
        "2단계: 첫 번째 AI 호출 실습",
        "3단계: Vertex AI 계정 설정",
        "4단계: 개발 환경 완성",
        "5단계: 첫 번째 프로젝트 시작",
    ]

    for step in next_steps:
        print(f"   {step}")

    print()
    print("이온: 한 걸음씩 차근차근 나아가겠습니다!")


# 메인 실행부
if __name__ == "__main__":
    print("세나: 이온! 첫 번째 실습을 시작해볼까요?")
    print()

    # 1단계: 자기소개
    ion_introduces_self()

    # 2단계: AI팀 만나기
    meet_ai_team()

    # 3단계: 목표 설정
    ion_first_goal()

    # 4단계: 시스템 확인
    test_system_connection()

    # 5단계: 다음 계획
    ion_next_steps()

    print("=" * 50)
    print("이온의 첫 번째 실습 완료!")
    print("세나: 정말 잘했어요, 이온!")
    print("=" * 50)

    # 이온에게 과제
    print()
    print("=== 이온을 위한 과제 ===")
    print("1. 위의 '이온의 특별한 메시지' 부분에 본인만의 메시지 추가하기")
    print("2. 이 코드를 실행해보고 결과 확인하기")
    print("3. 궁금한 점이나 추가하고 싶은 기능 생각해보기")
    print("4. 세나에게 피드백 주기!")
    print()
    print("이온: 네! 열심히 해보겠습니다!")
