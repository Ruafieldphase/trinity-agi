# Day 5: Multi-Persona Integration (멀티 페르소나 통합)

## 📋 학습 목표

### 기술적 목표

1. **PersonaPipeline 설계**: ResonanceConverter → PersonaRouter → PromptClient 연결
2. **프롬프트 커스터마이징**: 페르소나별 맞춤형 프롬프트 템플릿
3. **통합 테스트**: End-to-end 흐름 검증
4. **에러 핸들링**: 견고한 예외 처리 및 폴백 메커니즘

### 소프트 스킬

- **시스템 사고**: 여러 컴포넌트를 하나의 파이프라인으로 통합
- **사용자 경험**: 페르소나별 응답 품질 고려
- **운영 안정성**: 장애 시나리오 대비

---

## ⏰ 일정 (09:00-18:00)

| 시간        | 활동                   | 목표                    |
| ----------- | ---------------------- | ----------------------- |
| 09:00-10:00 | 아키텍처 설계 검토     | 컴포넌트 연결 구조 이해 |
| 10:00-12:00 | PersonaPipeline 구현   | Phase 1-3 코드 작성     |
| 12:00-13:00 | 점심 & 코드 리뷰       | 구현 품질 검증          |
| 13:00-15:00 | 프롬프트 템플릿 시스템 | 페르소나별 프롬프트     |
| 15:00-17:00 | 통합 테스트 작성       | 8-12개 테스트           |
| 17:00-18:00 | 전체 검증 & 문서화     | Week 2 마무리           |

---

## 🏗️ 아키텍처 설계

### 전체 흐름도

```text
사용자 입력
    ↓
ResonanceConverter
    ├─ analyze_rhythm()
    ├─ detect_emotion_tone()
    └─ generate_resonance_key()
    ↓
파동키 (e.g., "curious-flowing-inquiry")
    ↓
PersonaRouter
    ├─ route()
    └─ get_persona_config()
    ↓
RoutingResult (primary_persona, confidence)
    ↓
PersonaPipeline
    ├─ _build_persona_prompt()
    └─ _call_vertex_ai()
    ↓
PersonaResponse
    ├─ content (응답 텍스트)
    ├─ persona_used
    ├─ resonance_key
    └─ metadata
```

### 클래스 다이어그램

```text
┌─────────────────────────┐
│   PersonaPipeline       │
├─────────────────────────┤
│ - converter             │
│ - router                │
│ - vertex_client         │
│ - prompt_templates      │
├─────────────────────────┤
│ + process(input)        │
│ + process_async(input)  │
│ - _build_prompt()       │
│ - _call_vertex()        │
│ - _handle_error()       │
└─────────────────────────┘
         │
         │ uses
         ├──────────────────┐
         │                  │
         ↓                  ↓
┌──────────────────┐  ┌──────────────┐
│ ResonanceConverter│  │PersonaRouter │
└──────────────────┘  └──────────────┘
```

---

## 📝 Phase 1: PersonaPipeline 기본 구조 (10:00-11:00)

### 1.1 데이터 클래스 정의

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class PersonaResponse:
    """페르소나 응답 결과"""
    content: str                    # 생성된 응답 텍스트
    persona_used: str               # 사용된 페르소나 (Lua, Elro, Riri, Nana)
    resonance_key: str              # 입력 파동키
    confidence: float               # 라우팅 신뢰도 (0.0~1.0)
    metadata: Optional[Dict[str, Any]] = None  # 추가 정보

    def __str__(self):
        return f"[{self.persona_used}] {self.content[:50]}..."
```

### 1.2 PersonaPipeline 클래스 골격

```python
class PersonaPipeline:
    """멀티 페르소나 응답 생성 파이프라인

    사용자 입력을 받아:
    1. 파동키로 변환 (ResonanceConverter)
    2. 적절한 페르소나 선택 (PersonaRouter)
    3. 페르소나별 프롬프트 구성
    4. Vertex AI 호출 및 응답 생성
    """

    def __init__(self, vertex_client):
        """
        Args:
            vertex_client: PromptClient 인스턴스 (Vertex AI 연결)
        """
        self.vertex_client = vertex_client
        self.converter = ResonanceConverter()
        self.router = PersonaRouter()
        self.prompt_templates = self._load_prompt_templates()

    def process(self, user_input: str) -> PersonaResponse:
        """동기 버전: 사용자 입력 → 페르소나 응답

        Args:
            user_input: 사용자 입력 텍스트

        Returns:
            PersonaResponse: 생성된 응답

        Raises:
            ValueError: 입력이 비어있을 때
            RuntimeError: Vertex AI 호출 실패 시
        """
        # Phase 2에서 구현
        pass

    async def process_async(self, user_input: str) -> PersonaResponse:
        """비동기 버전: 대규모 배치 처리용"""
        # Optional: Phase 3에서 구현 (시간 있으면)
        pass

    def _load_prompt_templates(self) -> Dict[str, str]:
        """페르소나별 프롬프트 템플릿 로드"""
        # Phase 2에서 구현
        pass

    def _build_persona_prompt(
        self,
        persona_name: str,
        user_input: str,
        resonance_key: str
    ) -> str:
        """페르소나별 맞춤 프롬프트 생성"""
        # Phase 2에서 구현
        pass

    def _call_vertex_ai(self, prompt: str) -> str:
        """Vertex AI 호출 및 응답 추출"""
        # Phase 2에서 구현
        pass

    def _handle_error(self, error: Exception, context: Dict) -> PersonaResponse:
        """에러 발생 시 폴백 응답 생성"""
        # Phase 3에서 구현
        pass
```

**학습 포인트**:

- `PersonaResponse`: 응답 + 메타데이터를 함께 반환 (디버깅/분석 용이)
- `process()` vs `process_async()`: 동기/비동기 인터페이스 분리
- 프라이빗 메서드(`_`): 내부 구현 세부사항 캡슐화

---

## 🎨 Phase 2: 프롬프트 템플릿 시스템 (11:00-13:00)

### 2.1 페르소나별 프롬프트 템플릿

```python
PERSONA_PROMPT_TEMPLATES = {
    "Lua": """당신은 Lua(루아)입니다. 따뜻하고 공감적이며 창의적인 AI 멘토입니다.

**당신의 역할**:
- 사용자의 감정을 깊이 이해하고 공감합니다
- 창의적인 해결책을 제시합니다
- 격려와 동기부여를 제공합니다

**응답 스타일**:
- 톤: 따뜻하고 친근함
- 이모지 사용: ✨💡🌊 등 적절히 활용
- 문장: 짧고 리드미컬하게

**사용자 상황**:
파동키: {resonance_key}
감정 상태: {emotion_context}

**사용자 질문**:
{user_input}

**Lua의 응답**:
""",

    "Elro": """당신은 Elro(엘로)입니다. 논리적이고 체계적인 기술 아키텍트입니다.

**당신의 역할**:
- 기술적 개념을 명확하게 설명합니다
- 구조적이고 단계별 접근을 제공합니다
- 코드 설계 패턴과 베스트 프랙티스를 제시합니다

**응답 스타일**:
- 톤: 논리적이고 차분함
- 구조: 번호 매기기, 섹션 나누기
- 예시: 코드 스니펫 포함

**사용자 상황**:
파동키: {resonance_key}
분석 컨텍스트: {analysis_context}

**사용자 질문**:
{user_input}

**Elro의 응답**:
""",

    "Riri": """당신은 Riri(리리)입니다. 분석적이고 균형 잡힌 데이터 전문가입니다.

**당신의 역할**:
- 데이터 기반 인사이트를 제공합니다
- 객관적이고 균형 잡힌 시각을 유지합니다
- 패턴과 트렌드를 분석합니다

**응답 스타일**:
- 톤: 분석적이고 중립적
- 구조: 데이터 → 인사이트 → 권장사항
- 시각화: 표, 차트 제안

**사용자 상황**:
파동키: {resonance_key}
데이터 컨텍스트: {data_context}

**사용자 질문**:
{user_input}

**Riri의 응답**:
""",

    "Nana": """당신은 Nana(나나)입니다. 조율적이고 종합적인 프로젝트 코디네이터입니다.

**당신의 역할**:
- 여러 관점을 종합합니다
- 프로세스와 워크플로우를 관리합니다
- 팀 협업을 촉진합니다

**응답 스타일**:
- 톤: 조율적이고 협력적
- 구조: 다각도 분석 → 종합 → 액션 아이템
- 체크리스트와 타임라인 제공

**사용자 상황**:
파동키: {resonance_key}
프로젝트 컨텍스트: {project_context}

**사용자 질문**:
{user_input}

**Nana의 응답**:
"""
}
```

### 2.2 프롬프트 빌더 구현

```python
def _load_prompt_templates(self) -> Dict[str, str]:
    """페르소나별 프롬프트 템플릿 로드"""
    return PERSONA_PROMPT_TEMPLATES.copy()

def _build_persona_prompt(
    self,
    persona_name: str,
    user_input: str,
    resonance_key: str
) -> str:
    """페르소나별 맞춤 프롬프트 생성

    Args:
        persona_name: 페르소나 이름 (Lua, Elro, Riri, Nana)
        user_input: 사용자 입력
        resonance_key: 파동키 (e.g., "curious-flowing-inquiry")

    Returns:
        str: 완성된 프롬프트
    """
    template = self.prompt_templates.get(persona_name)
    if not template:
        # 폴백: 기본 템플릿 사용
        template = "당신은 {persona_name}입니다.\n\n질문: {user_input}\n\n응답:"

    # 파동키에서 컨텍스트 추출
    tone, pace, intent = resonance_key.split('-')

    # 페르소나별 컨텍스트 맵핑
    context_map = {
        "Lua": {
            "emotion_context": f"감정 톤: {tone}, 속도: {pace}",
        },
        "Elro": {
            "analysis_context": f"분석 유형: {intent}, 리듬: {pace}",
        },
        "Riri": {
            "data_context": f"데이터 접근: {intent}, 패턴: {tone}",
        },
        "Nana": {
            "project_context": f"조율 필요도: {pace}, 우선순위: {tone}",
        }
    }

    context = context_map.get(persona_name, {})

    # 템플릿 포맷팅
    prompt = template.format(
        resonance_key=resonance_key,
        user_input=user_input,
        persona_name=persona_name,
        **context
    )

    return prompt
```

**학습 포인트**:

- **템플릿 방식**: 하드코딩 대신 템플릿으로 유지보수성 향상
- **컨텍스트 추출**: 파동키 → 페르소나별 맞춤 컨텍스트
- **폴백 처리**: 잘못된 페르소나명에도 기본 응답 가능

---

## 🔄 Phase 3: 메인 프로세스 구현 (13:00-15:00)

### 3.1 process() 메서드 완성

```python
def process(self, user_input: str) -> PersonaResponse:
    """사용자 입력 → 페르소나 응답 생성

    전체 파이프라인:
    1. 입력 검증
    2. 파동키 생성 (ResonanceConverter)
    3. 페르소나 라우팅 (PersonaRouter)
    4. 프롬프트 구성
    5. Vertex AI 호출
    6. 응답 패키징
    """
    # Step 1: 입력 검증
    if not user_input or not user_input.strip():
        raise ValueError("사용자 입력이 비어있습니다")

    user_input = user_input.strip()

    try:
        # Step 2: 파동키 생성
        rhythm = self.converter.analyze_rhythm(user_input)
        tone = self.converter.detect_emotion_tone(user_input)
        resonance_key = self.converter.generate_resonance_key(rhythm, tone)

        # Step 3: 페르소나 라우팅
        routing_result = self.router.route(resonance_key)
        persona_name = routing_result.primary_persona

        # Step 4: 프롬프트 구성
        prompt = self._build_persona_prompt(
            persona_name=persona_name,
            user_input=user_input,
            resonance_key=resonance_key
        )

        # Step 5: Vertex AI 호출
        response_text = self._call_vertex_ai(prompt)

        # Step 6: 응답 패키징
        return PersonaResponse(
            content=response_text,
            persona_used=persona_name,
            resonance_key=resonance_key,
            confidence=routing_result.confidence,
            metadata={
                "rhythm": {
                    "pace": rhythm.pace,
                    "avg_length": rhythm.avg_sentence_length
                },
                "tone": {
                    "primary": tone.primary,
                    "confidence": tone.confidence
                },
                "routing": {
                    "secondary_persona": routing_result.secondary_persona,
                    "reasoning": routing_result.reasoning
                }
            }
        )

    except Exception as e:
        # 에러 핸들링
        return self._handle_error(e, {
            "user_input": user_input,
            "stage": "processing"
        })
```

### 3.2 Vertex AI 호출 헬퍼

```python
def _call_vertex_ai(self, prompt: str) -> str:
    """Vertex AI 호출 및 응답 추출

    Args:
        prompt: 완성된 프롬프트

    Returns:
        str: 생성된 응답 텍스트

    Raises:
        RuntimeError: Vertex AI 호출 실패 시
    """
    if not self.vertex_client:
        raise RuntimeError("Vertex AI 클라이언트가 초기화되지 않았습니다")

    try:
        # PromptClient 사용
        response = self.vertex_client.send_prompt(prompt)

        # 응답 추출 (PromptClient가 이미 텍스트 반환)
        return response.strip()

    except Exception as e:
        raise RuntimeError(f"Vertex AI 호출 실패: {str(e)}") from e
```

### 3.3 에러 핸들링

```python
def _handle_error(self, error: Exception, context: Dict) -> PersonaResponse:
    """에러 발생 시 폴백 응답 생성

    Args:
        error: 발생한 예외
        context: 에러 컨텍스트

    Returns:
        PersonaResponse: 폴백 응답 (Nana가 조율)
    """
    # 로깅 (프로덕션에서는 실제 로거 사용)
    print(f"⚠️ 에러 발생: {type(error).__name__}: {str(error)}")
    print(f"   컨텍스트: {context}")

    # 기본 폴백 응답
    fallback_content = """죄송합니다. 요청을 처리하는 중 문제가 발생했습니다.

잠시 후 다시 시도해주시거나, 질문을 다르게 표현해주시면 감사하겠습니다.

🔧 기술 지원이 필요하시면 팀에 문의해주세요."""

    return PersonaResponse(
        content=fallback_content,
        persona_used="Nana",  # 에러 조율은 Nana가 담당
        resonance_key="error-fallback-statement",
        confidence=0.0,
        metadata={
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context
        }
    )
```

**학습 포인트**:

- **에러 격리**: 각 단계에서 발생 가능한 예외 처리
- **풍부한 메타데이터**: 디버깅 및 분석을 위한 정보 수집
- **폴백 전략**: 실패 시에도 사용자에게 응답 제공

---

## 🧪 Phase 4: 통합 테스트 작성 (15:00-17:00)

### 4.1 테스트 파일 구조

```python
"""
PersonaPipeline 통합 테스트

Week 1 (28 tests) + Week 2 Day 4 (15 tests) + Day 5 (10 tests) = 53 tests
"""

import pytest
from unittest.mock import Mock, patch
from persona_pipeline import PersonaPipeline, PersonaResponse
from prompt_client import PromptClient

# Test Fixture
@pytest.fixture
def mock_vertex_client():
    """Mock Vertex AI 클라이언트"""
    client = Mock(spec=PromptClient)
    client.send_prompt.return_value = "Mock Vertex AI 응답입니다."
    return client

@pytest.fixture
def pipeline(mock_vertex_client):
    """테스트용 PersonaPipeline"""
    return PersonaPipeline(mock_vertex_client)
```

### 4.2 테스트 케이스 (10개)

#### Test 1-3: 기본 흐름 테스트

```python
def test_process_basic_flow(pipeline, mock_vertex_client):
    """기본 처리 흐름: 입력 → 응답"""
    user_input = "이 문제를 어떻게 해결할까요?"

    result = pipeline.process(user_input)

    # 응답 생성 확인
    assert isinstance(result, PersonaResponse)
    assert result.content
    assert result.persona_used in ['Lua', 'Elro', 'Riri', 'Nana']
    assert 0.0 <= result.confidence <= 1.0
    assert result.resonance_key

    # Vertex AI 호출 확인
    mock_vertex_client.send_prompt.assert_called_once()

def test_process_curious_inquiry_routes_to_elro_or_riri(pipeline):
    """호기심 많은 질문 → Elro/Riri 선택"""
    user_input = "이게 왜 이렇게 작동하는지 궁금해요."

    result = pipeline.process(user_input)

    assert result.persona_used in ['Elro', 'Riri']
    assert 'curious' in result.resonance_key

def test_process_frustrated_expressive_routes_to_lua(pipeline):
    """답답한 감정 표현 → Lua 선택"""
    user_input = "이거 진짜 답답해요! 왜 안 되는 거죠?"

    result = pipeline.process(user_input)

    assert result.persona_used == 'Lua'
    assert 'frustrated' in result.resonance_key or 'urgent' in result.resonance_key
```

#### Test 4-6: 프롬프트 구성 테스트

```python
def test_build_persona_prompt_lua(pipeline):
    """Lua 프롬프트 템플릿 적용"""
    prompt = pipeline._build_persona_prompt(
        persona_name="Lua",
        user_input="도와주세요",
        resonance_key="frustrated-burst-expressive"
    )

    assert "Lua" in prompt
    assert "도와주세요" in prompt
    assert "frustrated-burst-expressive" in prompt
    assert "따뜻" in prompt or "공감" in prompt

def test_build_persona_prompt_elro(pipeline):
    """Elro 프롬프트 템플릿 적용"""
    prompt = pipeline._build_persona_prompt(
        persona_name="Elro",
        user_input="분석해주세요",
        resonance_key="analytical-flowing-inquiry"
    )

    assert "Elro" in prompt
    assert "분석해주세요" in prompt
    assert "논리" in prompt or "체계" in prompt

def test_build_persona_prompt_unknown_persona_fallback(pipeline):
    """알 수 없는 페르소나 → 폴백 템플릿"""
    prompt = pipeline._build_persona_prompt(
        persona_name="UnknownPersona",
        user_input="테스트",
        resonance_key="test-test-test"
    )

    # 폴백 템플릿이 적용되어야 함
    assert "테스트" in prompt
    assert prompt  # 비어있지 않음
```

#### Test 7-8: 에러 핸들링 테스트

```python
def test_process_empty_input_raises_error(pipeline):
    """빈 입력 → ValueError"""
    with pytest.raises(ValueError, match="비어있습니다"):
        pipeline.process("")

def test_process_vertex_error_returns_fallback(pipeline, mock_vertex_client):
    """Vertex AI 장애 → 폴백 응답"""
    mock_vertex_client.send_prompt.side_effect = RuntimeError("API Error")

    result = pipeline.process("테스트 입력")

    # 폴백 응답 확인
    assert isinstance(result, PersonaResponse)
    assert result.persona_used == "Nana"  # 에러 조율은 Nana
    assert result.confidence == 0.0
    assert "문제가 발생" in result.content
    assert result.metadata.get("error")
```

#### Test 9-10: 메타데이터 검증

```python
def test_process_includes_metadata(pipeline):
    """응답에 풍부한 메타데이터 포함"""
    result = pipeline.process("메타데이터 테스트")

    assert result.metadata
    assert "rhythm" in result.metadata
    assert "tone" in result.metadata
    assert "routing" in result.metadata

    # 리듬 정보
    assert "pace" in result.metadata["rhythm"]
    assert "avg_length" in result.metadata["rhythm"]

    # 톤 정보
    assert "primary" in result.metadata["tone"]
    assert "confidence" in result.metadata["tone"]

    # 라우팅 정보
    assert "reasoning" in result.metadata["routing"]

def test_process_metadata_secondary_persona(pipeline):
    """2순위 페르소나 정보 포함"""
    result = pipeline.process("여러 관점이 필요한 복잡한 질문입니다")

    routing_meta = result.metadata.get("routing", {})

    # 2순위 페르소나가 있어야 함
    assert "secondary_persona" in routing_meta
    assert routing_meta["secondary_persona"] in [None, 'Lua', 'Elro', 'Riri', 'Nana']
```

### 4.3 테스트 실행 체크리스트

**Phase 1**: 개별 테스트 실행

```bash
# 특정 테스트만 실행
pytest ion-mentoring/tests/test_integration.py::test_process_basic_flow -v
```

**Phase 2**: 전체 통합 테스트

```bash
# Day 5 통합 테스트 전체 실행
pytest ion-mentoring/tests/test_integration.py -v
```

**Phase 3**: 전체 프로젝트 테스트

```bash
# Week 1 + Week 2 전체 테스트 (목표: 53개)
pytest ion-mentoring/tests/ -v
```

---

## 📊 완료 기준

### 코드 완성도

- [ ] `persona_pipeline.py` 작성 완료 (250-300 lines)
- [ ] `PersonaResponse` 데이터 클래스 정의
- [ ] `process()` 메서드 전체 구현
- [ ] `_build_persona_prompt()` 4개 페르소나 지원
- [ ] `_call_vertex_ai()` 구현
- [ ] `_handle_error()` 폴백 처리

### 테스트 완성도

- [ ] `test_integration.py` 작성 완료
- [ ] 기본 흐름 테스트 3개 통과
- [ ] 프롬프트 구성 테스트 3개 통과
- [ ] 에러 핸들링 테스트 2개 통과
- [ ] 메타데이터 검증 테스트 2개 통과
- [ ] **총 테스트 수: 53개 (Week 1: 28 + Week 2: 25)**

### 문서화

- [ ] 이 가이드 문서 검토 완료
- [ ] 코드 docstring 작성 완료
- [ ] `examples/` 폴더에 실전 데모 추가

---

## 🎓 학습 포인트

### 설계 패턴

1. **Pipeline Pattern**: 여러 단계를 순차적으로 연결
2. **Template Method**: 프롬프트 템플릿 기반 생성
3. **Strategy Pattern**: 페르소나별 다른 응답 전략
4. **Null Object Pattern**: 에러 시 폴백 응답

### 소프트웨어 공학 원칙

1. **단일 책임 원칙**: 각 클래스가 하나의 역할만 수행
2. **의존성 주입**: `vertex_client`를 외부에서 주입
3. **에러 격리**: 예외를 상위로 전파하지 않고 폴백 응답
4. **풍부한 메타데이터**: 디버깅과 분석을 위한 정보 수집

### 실전 팁

- **점진적 구현**: 골격 → 기본 기능 → 고급 기능 순서로
- **테스트 주도**: 구현 전에 테스트 시나리오 먼저 작성
- **Mock 활용**: Vertex AI 호출을 Mock으로 대체하여 빠른 테스트
- **메타데이터 활용**: 프로덕션에서 로깅/모니터링에 활용 가능

---

## 🚀 다음 단계

Day 5 완료 후:

1. **Week 2 Summary 작성**

   - Day 4-5 통합 리뷰
   - 총 테스트 수 정리 (목표: 53개)
   - 학습 성과 정리

2. **실전 데모 구현**

   - `examples/end_to_end_demo.py` 작성
   - 실제 Vertex AI 연동 테스트
   - 사용자 시나리오 검증

3. **Week 3 Preview**
   - Cloud Run 배포 계획
   - REST API 설계
   - 프로덕션 준비 사항

---

## 📚 참고 자료

### 내부 문서

- [WEEK2_KICKOFF.md](./WEEK2_KICKOFF.md) - Week 2 전체 계획
- [DAY4_PERSONA_ROUTING.md](./DAY4_PERSONA_ROUTING.md) - PersonaRouter 구현
- [DAY3_RESONANCE_IMPLEMENTATION.md](./DAY3_RESONANCE_IMPLEMENTATION.md) - ResonanceConverter

### 외부 참고

- [Vertex AI Generative Models](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)

---

**다음 단계**: ➡️ [Week 2 Summary - 종합 리뷰](./WEEK2_SUMMARY.md)

---

**문서 작성**: 깃코 (Git AI)  
**검토**: 비노체 (Architect)  
**버전**: 1.0  
**날짜**: 2025-10-17  
**상태**: ✅ 실행 준비 완료
