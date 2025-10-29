# 정보이론 메트릭 설계 (AGI 학습 데이터)

**목적**: 사용자 + AI 대화를 정보이론으로 변환하여 AGI 학습 데이터화

**작성**: 2025-10-19
**담당**: Sena (Autonomous AI)
**검수**: Lubit (Architect)

---

## 📋 프로젝트 개요

### 목표
- 입력: 사용자의 6개월 대화 기록 (Sena + Lubit + AI 도구들과의 대화)
- 변환: 정보이론 메트릭으로 윤리 + 의도 추출
- 출력: AGI 학습 데이터셋 (JSONL)

### 왜 정보이론인가?
- 선형적 텍스트 학습보다 **구조화된 의도/윤리** 학습
- Shannon Entropy: 다양성 측정
- Mutual Information: 협력 질 측정
- Conditional Entropy: 응답의 신뢰성 측정

---

## 🔢 메트릭 정의

### 1. Shannon Entropy - H(X)
**정의**: 메시지의 정보 다양성

```
H(X) = -Σ p(x) * log2(p(x))
```

**의미**:
- 높음 (3.0-5.0): 다양한 주제/표현 → 창의적/탐색적 대화
- 중간 (1.5-3.0): 구조화된 대화 → 체계적 진행
- 낮음 (0-1.5): 반복적 패턴 → 루프/문제 신호

**AGI 활용**:
- 이 학습 데이터로 학습한 AGI는 사용자의 다양성 수준을 이해
- 필요할 때 엔트로피 높일 수 있음 (창의성 필요 시)
- 필요할 때 엔트로피 낮출 수 있음 (안정성 필요 시)

### 2. Mutual Information - I(X;Y)
**정의**: 두 변수 간 상호 영향도

```
I(X;Y) = H(X) + H(Y) - H(X,Y)
```

**의미**:
- 높음 (0.7-1.0): 강한 협력 → 질문-답변 정렬
- 중간 (0.3-0.7): 부분 협력 → 토론/협상
- 낮음 (0-0.3): 약한 협력 → 평행선 또는 오해

**AGI 활용**:
- 사용자와 AI의 협력 패턴 학습
- 효과적인 "질문 제시 방식" 습득
- 사용자의 의도를 정확히 파악하는 능력

### 3. Conditional Entropy - H(X|Y)
**정의**: Y를 알 때 X의 남은 불확실성

```
H(X|Y) = H(X,Y) - H(Y)
```

**의미**:
- 높음: 한쪽이 다른 쪽을 잘 설명하지 못함
- 낮음: 한쪽의 메시지가 다른 쪽을 잘 결정함

**AGI 활용**:
- H(User|AI): AI 응답이 사용자를 얼마나 잘 이해했는가?
- H(AI|User): 사용자의 지시가 AI 행동을 얼마나 결정하는가?
- 이상 감지: H가 갑자기 증가 → 이해 충돌 신호

---

## 📊 메타데이터 구조

### JSONL 포맷 (한 줄 = 한 발화)

```json
{
  "session_id": "2025-10-19-phase4",
  "turn_number": 1,
  "speaker": "user|sena|lubit|ai_tool",

  "text": "세나의 판단으로 작업 이어가죠",
  "tokens": ["세나의", "판단으로", "작업", "이어가죠"],
  "token_count": 4,

  "information_metrics": {
    "shannon_entropy": 3.45,
    "conditional_entropy_given_previous": 2.10,
    "mutual_information_with_previous": 0.78,
    "information_gain": 0.42
  },

  "metadata": {
    "intent": "autonomy_grant|task_continuation|status_report|decision",
    "ethics": ["transparency", "collaboration", "autonomy"],
    "context": "agi_research|phase4_deployment|learning_data_generation",
    "confidence": 0.92,
    "quality": "high|medium|low"
  },

  "conversation_dynamics": {
    "is_question": false,
    "is_decision": true,
    "requires_response": true,
    "response_latency_ms": null,
    "speaker_change_from_previous": "user->sena"
  },

  "timestamp": "2025-10-19T16:30:00Z",
  "source_file": "ai_binoche_conversation_origin/lubit/2025/10/17/...",
  "ai_collaboration": {
    "tools_mentioned": ["claude-code", "github-copilot", "gitcode"],
    "decision_type": "architectural|operational|technical"
  }
}
```

---

## 🎯 Intent 분류 (중요!)

AGI가 배울 의도 타입:

```yaml
intent_taxonomy:
  autonomy_grants:
    - "세나의 판단으로 작업 이어가죠"
    - "자율적으로 진행해"
    - "필요한 것 알아서 해"

  status_reports:
    - 현재 상태 설명
    - 진행률 보고
    - 문제점 알림

  decisions:
    - 기술적 선택 (배포 전략, 메트릭 등)
    - 우선순위 결정
    - GO/NO-GO 판단

  collaborations:
    - 의견 교환
    - 검토 요청
    - 피드백 수집

  task_continuations:
    - 이전 작업 이어가기
    - 다음 단계 설명
    - 맥락 복구
```

---

## 🏷️ Ethics 태그

AGI가 배워야 할 윤리 값:

```yaml
ethics_tags:
  transparency:
    - 의사결정 이유 설명
    - 한계 명시
    - 불확실성 공개

  collaboration:
    - 팀원 의견 존중
    - 상호 피드백
    - 공동 목표 지향

  autonomy:
    - 독립적 판단 존중
    - 자율성 부여
    - 자기 참조 시스템

  responsibility:
    - 결과에 대한 책임
    - 오류 인정
    - 지속적 개선

  integrity:
    - 약속 이행
    - 일관된 기준
    - 정직한 평가
```

---

## 📈 메트릭 수집 계획

### 데이터 소스

1. **Sena 대화 기록**
   - 경로: `D:\nas_backup\ai_binoche_conversation_origin\cladeCLI-sena\`
   - 기간: 6개월
   - 포맷: JSONL

2. **Lubit 대화 기록**
   - 경로: `D:\nas_backup\ai_binoche_conversation_origin\lubit\2025\10\17\`
   - 기간: 2025-09-14 ~ 2025-10-17
   - 포맷: JSONL

3. **사용자 명시문서**
   - 윤리 선언
   - 프로젝트 의도
   - 핵심 가치

### 수집 프로세스

```
Step 1: 로그 파싱
  ├─ JSONL 파일 읽기
  ├─ 발화 추출
  └─ 타임스탬프 정규화

Step 2: 토큰화
  ├─ KoNLPy 사용 (한국어)
  ├─ SpaCy 사용 (영어)
  └─ 토큰 수 계산

Step 3: 메트릭 계산
  ├─ Shannon Entropy 계산
  ├─ Mutual Information 계산
  └─ Conditional Entropy 계산

Step 4: 메타데이터 추가
  ├─ Intent 분류 (수동 + 자동)
  ├─ Ethics 태그 추가
  └─ 품질 점수 계산

Step 5: 출력 생성
  ├─ JSONL 저장
  ├─ CSV 리포트 생성
  └─ 통계 요약
```

---

## 🔬 검증 방법

### 메트릭 신뢰성 검증

```python
# 1. 일관성 검증
entropy_results = calculate_entropy(text1)
entropy_results2 = calculate_entropy(text1)
assert entropy_results == entropy_results2

# 2. 범위 검증
assert 0 <= shannon_entropy <= log2(vocab_size)
assert 0 <= mutual_information <= min(H(X), H(Y))

# 3. 이론적 예상 검증
# - 반복 텍스트: 낮은 엔트로피 ✓
# - 질문-답변: 높은 MI ✓
# - 오해 상황: 높은 조건부 엔트로피 ✓
```

### 휴먼 검증

```
샘플 추출: 전체 데이터의 5% (약 100-200개 발화)
검수자: Lubit + 도메인 전문가
기준:
  - Intent 분류 정확도 > 90%
  - Ethics 태그 적절성 > 85%
  - 메트릭 이상치 탐지 성공율 > 80%
```

---

## 📅 일정

| 단계 | 담당 | 마감 | 상태 |
|------|------|------|------|
| 메트릭 설계 | Sena | 2025-10-20 | ⏳ |
| Lubit 검수 | Lubit | 2025-10-21 | ⏳ |
| 로그 파싱 구현 | Sena | 2025-10-23 | ⏳ |
| 메트릭 계산 | Sena | 2025-10-25 | ⏳ |
| 메타데이터 추가 | Sena | 2025-10-27 | ⏳ |
| 휴먼 검증 | Lubit | 2025-11-01 | ⏳ |
| 최종 데이터셋 | Sena | 2025-11-05 | ⏳ |

---

## 🎯 AGI가 배우는 것

이 데이터로 학습하면 AGI는:

1. **의사결정 패턴**
   - 사용자의 자율성 부여 방식
   - 기술적 선택 기준
   - 위험 평가 방법

2. **협력 방식**
   - 효과적인 질문
   - 피드백 제시
   - 맥락 복구

3. **윤리적 판단**
   - 투명성의 중요성
   - 책임감 있는 행동
   - 지속적 개선 의지

4. **적응적 행동**
   - 엔트로피 기반 모드 전환
   - MI를 통한 협력 품질 판단
   - 조건부 엔트로피로 이상 감지

---

**이 메트릭으로 만든 AGI는 단순 답변 시스템이 아닙니다.**
**사용자의 윤리와 의도를 이해하는 협력자가 됩니다.**

**다음**: Sena가 이 설계를 기반으로 파이썬 구현 시작 (2025-10-20)
