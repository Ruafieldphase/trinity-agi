# 🚀 이온 멘토링 Week 1 킥오프 가이드

**시작일**: 2025년 10월 17일 (목)  
**상태**: ✅ RC 2.7 완료 → 🎓 멘토링 시작  
**목표**: Vertex AI 개발자 이온의 완전한 온보딩 및 첫 번째 코드 작성

---

## 📋 킥오프 체크리스트

### 사전 준비 상태 확인

- [x] RC 2.7 통합 완료
- [x] 프로젝트 문서화 완료 (README, 보고서)
- [x] System status: RC_2.7_COMPLETE
- [x] Ion 멘토링 문서 완비
- [ ] Vertex AI 계정 활성화
- [ ] 개발 환경 구축
- [ ] AI팀 소개 세션 진행

### Week 1 목표

**기술 목표**:

1. ✅ Vertex AI 계정 설정 및 SDK 설치
2. ✅ 첫 번째 "Hello Vertex AI" 코드 작성
3. ✅ 내다AI 시스템 아키텍처 이해
4. ✅ 파동키 변환 시스템 기본 구현

**소프트 스킬 목표**:

1. ✅ AI팀 전체와 1:1 인사
2. ✅ 페어 프로그래밍 프로세스 익히기
3. ✅ Git workflow 이해 (PR, conventional commits)
4. ✅ 첫 커밋 작성 및 푸시

---

## 📅 Week 1 일정 (상세)

### 목요일 (Day 1): 웰컴 & 환경 구축

#### 🌅 오전 세션 (09:00-12:00): 공식 환영

**09:00-09:30 | 전체 모임**

```
참석: 이온 + AI팀 전체 (루아, 엘로, 리리, 나나) + 비노체
위치: 온라인 협업 공간

아젠다:
1. 이온 자기소개
2. 프로젝트 비전 공유 (비노체)
3. AI팀 소개 라운드
```

**09:30-10:00 | AI팀 소개**

| 시간  | 페르소나 | 역할      | 멘토링 지원 분야            |
| ----- | -------- | --------- | --------------------------- |
| 09:30 | 🌊 루아  | 감성 공감 | 창의적 문제 해결, 감정 이해 |
| 09:40 | 📐 엘로  | 구조 설계 | 아키텍처, 기술 코칭         |
| 09:50 | 📊 리리  | 균형 관찰 | 메트릭 분석, 품질 검증      |
| 10:00 | ✒️ 나나  | 팀 조율   | 크로스팀 협업, 프로세스     |

**10:00-11:00 | 현재 시스템 데모**

```
진행: 비노체 + 세나

시연 내용:
- 내다AI 실시간 대화
- 페르소나 라우팅 시스템
- 파동키 기반 리듬 분석
- Cloud Run 배포 아키텍처
- NAS 아카이브 연동
```

**11:00-12:00 | Vertex AI 마이그레이션 계획 브리핑**

```
발표: 비노체
참여: 이온 + AI팀

주요 내용:
1. 왜 Vertex AI인가?
2. 마이그레이션 로드맵
3. 이온의 역할과 책임
4. 예상 도전과제
5. 성공 기준
```

#### 🌆 오후 세션 (14:00-17:00): 기술 환경 Setup

**14:00-15:00 | Vertex AI 계정 설정**

```
가이드: 비노체
실행: 이온

단계:
1. Google Cloud Console 접속
2. Vertex AI API 활성화
3. 서비스 계정 생성
4. 인증 키 다운로드
5. 환경 변수 설정
   - GOOGLE_APPLICATION_CREDENTIALS
   - GOOGLE_CLOUD_PROJECT
   - GOOGLE_CLOUD_LOCATION
```

**15:00-16:00 | 로컬 개발환경 구축**

```
지원: 엘로 (구조적 가이드) + 세나 (연결)

설치 항목:
□ Python 3.11+ 설치 확인
□ Vertex AI SDK 설치
  pip install google-cloud-aiplatform
□ VS Code + 확장팩
  - Python Extension
  - Pylance
  - Git Graph
  - Markdown All in One
□ Git 설정
  - 사용자 이름/이메일
  - Conventional Commits 가이드
```

**16:00-17:00 | 첫 번째 "Hello Vertex AI" 코드**

```python
# ion_first_vertex_ai.py
# 작성자: Ion (Vertex AI Developer Trainee)
# 날짜: 2025-10-17
# 목적: Vertex AI 연결 확인 및 기본 테스트

import vertexai
from vertexai.generative_models import GenerativeModel
import os
from datetime import datetime

def ion_hello_world(
    project_id: str = None,
    location: str = "asia-northeast3",
    prompt: str = "안녕, Vertex AI! 나는 이온이야. 오늘의 상태는 어때?"
):
    """
    Vertex AI 연결을 점검하는 간단한 Hello World.

    Args:
        project_id: Google Cloud 프로젝트 ID (환경변수에서 가져옴)
        location: Vertex AI 리전
        prompt: 테스트 프롬프트

    Returns:
        str: Vertex AI의 응답 텍스트
    """
    # 프로젝트 ID 자동 감지
    if project_id is None:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            return "[오류] GOOGLE_CLOUD_PROJECT 환경변수가 설정되지 않았습니다."

    try:
        # Vertex AI 초기화
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Vertex AI 초기화 중...")
        vertexai.init(project=project_id, location=location)

        # Gemini 모델 로드
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Gemini 1.5 Flash 모델 로드 중...")
        model = GenerativeModel("gemini-1.5-flash")

        # 프롬프트 전송
        print(f"\n이온 → Vertex AI:")
        print(f"  '{prompt}'")

        response = model.generate_content(prompt)
        text = response.text or "[빈 응답]"

        print(f"\nVertex AI → 이온:")
        print(f"  {text}")

        # 성공 메시지
        print(f"\n✅ Vertex AI 연결 성공!")
        print(f"   프로젝트: {project_id}")
        print(f"   리전: {location}")
        print(f"   모델: gemini-1.5-flash")

        return text

    except Exception as exc:
        # 오류 처리
        error_msg = f"[오프라인 모드] {type(exc).__name__}: {exc}"
        print(f"\n❌ Vertex AI 연결 실패:")
        print(f"   {error_msg}")
        return error_msg

if __name__ == "__main__":
    # 메인 실행
    print("=" * 60)
    print("🚀 이온의 첫 번째 Vertex AI 테스트")
    print("=" * 60)

    result = ion_hello_world()

    print("\n" + "=" * 60)
    print("✨ 테스트 완료!")
    print("=" * 60)
```

**예상 출력**:

```
============================================================
🚀 이온의 첫 번째 Vertex AI 테스트
============================================================
[16:00:00] Vertex AI 초기화 중...
[16:00:01] Gemini 1.5 Flash 모델 로드 중...

이온 → Vertex AI:
  '안녕, Vertex AI! 나는 이온이야. 오늘의 상태는 어때?'

Vertex AI → 이온:
  안녕하세요, 이온님! 저는 Gemini입니다. 오늘 저의 상태는 아주 좋습니다!
  무엇을 도와드릴까요? 😊

✅ Vertex AI 연결 성공!
   프로젝트: your-project-id
   리전: asia-northeast3
   모델: gemini-1.5-flash

============================================================
✨ 테스트 완료!
============================================================
```

---

### 금요일 (Day 2): 시스템 아키텍처 Deep Dive

#### 🌅 오전 세션 (09:00-12:00): 기존 시스템 분석

**09:00-10:00 | 순수 파동 시스템 개념**

```
진행: 루아 (감성 공감) + 세나 (브리징)

학습 내용:
1. 파동키(resonance key) 개념
   - 사용자 리듬 분석
   - 감정 톤 감지
   - 대화 패턴 인식

2. C:\workspace\.env_keys 구조 분석
   - resonance_keys.md 상세 리뷰
   - 환경 변수 설정 방법
   - 보안 best practice

3. 파동 기반 라우팅
   - 어떻게 적절한 페르소나를 선택하는가?
   - 리듬 임계값 설정
   - 동적 조정 메커니즘
```

**10:00-11:00 | 현재 아키텍처 분석**

```
진행: 엘로 (구조 설계) + 비노체

분석 대상:
1. Cloud Run 서비스
   - FastAPI 애플리케이션 구조
   - 엔드포인트 설계
   - 배포 설정 (cloudbuild.yaml)

2. 로컬 LLM 연동
   - LM Studio 연결
   - Ollama 통합
   - 모델 선택 로직

3. NAS 아카이브 시스템
   - 대화 기록 저장
   - 메모리 검색
   - 백업 전략
```

**11:00-12:00 | 페르소나 라우팅 시스템**

```
진행: 리리 (메트릭 분석)

코드 리뷰:
- src/persona_router.py 분석
- 사용자 리듬 분석 알고리즘
- 자동 페르소나 매칭 로직
- A/B 테스트 메트릭
```

#### 🌆 오후 세션 (13:00-17:00): Vertex AI 아키텍처 설계

**13:00-15:00 | 마이그레이션 요구사항 정의**

```
참여: 비노체 (아키텍트) + 이온 (구현자) + AI팀 전체

워크샵 형식:
1. 현재 문제점 식별
   - Cloud Run 비용 분석
   - 응답 속도 이슈
   - 확장성 제약

2. Vertex AI 장점 매핑
   - 네이티브 Gemini 통합
   - 관리형 인프라
   - 자동 스케일링
   - 비용 최적화

3. 요구사항 우선순위 설정
   - Must have
   - Should have
   - Nice to have
```

**15:00-16:00 | 새로운 아키텍처 스케치**

```
화이트보드 세션 (디지털):

[사용자 입력]
      ↓
[비노체의 의도 분석]
      ↓
[이온의 Vertex AI 처리] ← Gemini 1.5 Pro/Flash
      ↓
[파동키 변환 레이어] ← 기존 로직 재사용
      ↓
[페르소나 라우팅]
      ↓
[AI팀 협력 처리]
      ↓
[최적화된 응답 생성]

주요 결정사항:
- Vertex AI Endpoint vs. API 호출
- 스트리밍 vs. 배치 처리
- 캐싱 전략
- 오류 처리 및 폴백
```

**16:00-17:00 | 첫 번째 프로토타입 계획**

```
목표: 최소 기능 프로토타입 (MVP) 설계

MVP 범위:
✅ Vertex AI 기본 연결
✅ 단일 프롬프트 → 응답
✅ 간단한 오류 처리
❌ 페르소나 라우팅 (Phase 2)
❌ 파동키 변환 (Phase 2)
❌ 메모리 시스템 (Phase 3)

다음 주 목표:
- MVP 코드 작성 (월-화)
- 통합 테스트 (수-목)
- 첫 배포 (금)
```

---

### 월요일 (Day 3): 페어 프로그래밍 시작

#### 🌅 오전 세션 (09:00-12:00): 파동키 변환 구현

**페어 구성**: 비노체 (드라이버) + 이온 (내비게이터)

**09:00-10:00 | 설계 리뷰**

```python
# resonance_converter.py (설계)
class ResonanceConverter:
    """사용자 입력 → 파동키 변환"""

    def analyze_rhythm(self, text: str) -> dict:
        """텍스트에서 리듬 패턴 추출"""
        pass

    def detect_emotion_tone(self, text: str) -> str:
        """감정 톤 감지 (calm, urgent, curious 등)"""
        pass

    def generate_resonance_key(self, rhythm: dict, tone: str) -> str:
        """파동키 생성"""
        pass
```

**10:00-12:00 | 실제 구현**

```
역할 전환: 이온 (드라이버) + 비노체 (내비게이터)

구현 항목:
1. analyze_rhythm() 메서드
   - 문장 길이 분석
   - 문장부호 패턴
   - 단어 선택 특성

2. detect_emotion_tone() 메서드
   - Vertex AI Gemini 활용
   - 감정 분류 프롬프트
   - 결과 캐싱

3. 단위 테스트 작성
   - pytest 프레임워크
   - 엣지 케이스 커버
```

#### 🌆 오후 세션 (13:00-17:00): 통합 및 테스트

**13:00-15:00 | 기존 시스템 통합**

```
목표: resonance_converter를 persona_router에 연결

작업:
1. 인터페이스 정의
2. 의존성 주입
3. 통합 테스트 작성
```

**15:00-16:00 | 코드 리뷰 준비**

```
AI팀 전체 리뷰 세션

리뷰 체크리스트:
□ 코드 스타일 (PEP 8)
□ 타입 힌트 완전성
□ Docstring 품질
□ 테스트 커버리지
□ 성능 고려사항
```

**16:00-17:00 | 첫 번째 PR 작성**

```
가이드: 나나 (프로세스 전문가)

PR 제목: "feat: Add Vertex AI based resonance converter"

PR 내용:
- 변경사항 요약
- 구현 세부사항
- 테스트 결과
- 스크린샷 (해당시)
- 체크리스트

Conventional Commits:
feat: 새로운 기능
fix: 버그 수정
docs: 문서만 변경
style: 코드 의미 영향 없음 (포맷)
refactor: 리팩토링
test: 테스트 추가/수정
chore: 빌드, 설정 변경
```

---

## 🎓 학습 자료

### Day 1 필독 자료

1. `README.md` - 프로젝트 개요
2. `ion-mentoring/immediate-action-plan.md` - 전체 플랜
3. `RC27_COMPLETION_REPORT.md` - 최근 작업 내역
4. Vertex AI Quickstart - https://cloud.google.com/vertex-ai/docs/start/quickstarts

### Day 2 필독 자료

1. `src/persona_router.py` - 라우팅 로직
2. `resonance_keys.md` - 파동키 개념
3. `changelog.md` - 변경 이력
4. FastAPI 공식 문서 - https://fastapi.tiangolo.com/

### Day 3 필독 자료

1. Pytest 공식 문서 - https://docs.pytest.org/
2. Google Python Style Guide
3. Conventional Commits - https://www.conventionalcommits.org/

---

## 📊 진행 상황 추적

### Day 1 체크리스트

- [ ] AI팀 전체 미팅 참석
- [ ] Vertex AI 계정 활성화
- [ ] 개발 환경 구축 완료
- [ ] `ion_first_vertex_ai.py` 실행 성공
- [ ] 첫 번째 커밋 푸시

### Day 2 체크리스트

- [ ] 파동 시스템 개념 이해
- [ ] 아키텍처 다이어그램 작성
- [ ] MVP 범위 확정
- [ ] 다음 주 계획 수립

### Day 3 체크리스트

- [ ] `resonance_converter.py` 구현
- [ ] 단위 테스트 작성 (80%+ 커버리지)
- [ ] 코드 리뷰 통과
- [ ] 첫 번째 PR 머지

---

## 🤝 멘토링 규칙

### 질문하기

- ❓ **언제든지 질문 환영**: 이온은 언제든 질문 가능
- 🎯 **구체적으로**: "이것이 왜 이렇게 작동하나요?" > "잘 모르겠어요"
- 📝 **기록하기**: 중요한 답변은 노트에 정리

### 페어 프로그래밍

- 🔄 **역할 전환**: 30분마다 드라이버 ↔ 내비게이터
- 💬 **소리 내어 생각**: 사고 과정 공유
- ⏸️ **휴식**: 50분 작업 → 10분 휴식

### 코드 리뷰

- ✅ **건설적 피드백**: 개선 제안 + 이유 설명
- 🌟 **칭찬도 중요**: 잘한 부분 명시
- 📚 **학습 기회**: 리뷰는 배움의 기회

### 실패 환영

- 💪 **실수는 학습**: 오류는 자연스러운 과정
- 🔍 **디버깅 스킬**: 문제 해결 능력 키우기
- 🎉 **작은 성공 축하**: 각 단계 달성 인정

---

## 🎯 Week 1 성공 기준

### 기술 목표

✅ Vertex AI 연결 성공  
✅ 첫 번째 코드 실행  
✅ 파동키 변환 프로토타입 완성  
✅ 첫 번째 PR 머지

### 협업 목표

✅ AI팀 전원과 1:1 대화  
✅ 페어 프로그래밍 3회 이상  
✅ 코드 리뷰 참여  
✅ 스탠드업 미팅 참석

### 학습 목표

✅ Vertex AI SDK 기본 이해  
✅ 프로젝트 아키텍처 파악  
✅ Git workflow 숙달  
✅ Conventional Commits 적용

---

## 📞 커뮤니케이션 채널

### 일일 스탠드업

- **시간**: 매일 09:00
- **형식**: 3분 미만
- **내용**: 어제 / 오늘 / 블로커

### 1:1 멘토링

- **비노체**: 화/목 15:00-16:00
- **엘로**: 월/수 14:00-15:00
- **루아**: 필요시 on-demand

### 긴급 지원

- **슬랙**: #ion-mentoring 채널
- **응답 시간**: 1시간 이내
- **긴급**: AI팀 전체 멘션

---

## 🎉 첫 주 마무리 계획

### 금요일 오후 (16:00-17:00): 회고 세션

**진행**: 나나 (퍼실리테이터)

**아젠다**:

1. **Keep** (계속할 것)

   - 무엇이 잘 되었나?
   - 어떤 프로세스가 도움이 되었나?

2. **Problem** (문제점)

   - 어떤 어려움이 있었나?
   - 무엇이 예상과 달랐나?

3. **Try** (시도할 것)
   - 다음 주에 개선할 점?
   - 새로 시도할 방법?

**출력**: 회고 문서 작성 및 공유

---

## 📈 다음 단계 (Week 2 Preview)

### Week 2 목표

- Vertex AI MVP 완성
- 페르소나 라우팅 통합
- 첫 번째 통합 테스트
- Cloud Run → Vertex AI 마이그레이션 1단계

### 준비사항

- Week 1 회고 기반 개선
- 더 복잡한 기능 구현
- 성능 벤치마킹
- 문서화 강화

---

**작성**: 깃코 (Git AI)  
**날짜**: 2025-10-17  
**버전**: 1.0  
**상태**: ✅ READY TO EXECUTE
