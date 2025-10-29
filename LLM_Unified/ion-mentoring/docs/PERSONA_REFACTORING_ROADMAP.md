# PersonaOrchestrator 리팩토링 로드맵 (10주 계획)

## 📋 현재 상태 분석

### 코드 구조

```
현재 구조:
├── persona_pipeline.py       (PersonaPipeline 클래스)
│   ├── 프롬프트 템플릿 (4개 페르소나)
│   ├── process() 메서드 (161-241줄)
│   ├── 프롬프트 생성
│   ├── Vertex AI 호출
│   └── 에러 핸들링
│
├── persona_router.py         (PersonaRouter 클래스)
│   ├── 페르소나 설정 (53-98줄)
│   ├── route() 메서드 (100-155줄)
│   ├── 매칭 점수 계산 (175-231줄)
│   └── 파동키 파싱 (233-259줄)
│
└── resonance_converter.py    (외부 모듈, 파동키 생성)
```

### 주요 문제점

**1. 모놀리식 클래스 설계**
- PersonaPipeline이 너무 많은 책임을 가짐
- 프롬프트 관리, API 호출, 에러 처리 등 섞여 있음
- 단일 책임 원칙(SRP) 위반

**2. 프롬프트 관리 비효율**
- 프롬프트가 코드에 하드코딩됨 (42-129줄)
- 페르소나별 프롬프트 수정 시 코드 변경 필요
- 버전 관리, 테스트 어려움

**3. 라우팅 로직 정체**
- 점수 계산이 하드코딩 (214-229줄)
- 새로운 라우팅 알고리즘 추가 어려움
- 컨텍스트 활용 미흡

**4. 테스트 가능성 부족**
- 의존성 주입 불충분
- Mock 객체 생성 복잡
- 통합 테스트만 가능

**5. 확장성 제약**
- 새로운 페르소나 추가 어려움
- 파이프라인 단계 추가 복잡
- 미들웨어 적용 불가능

---

## 🎯 리팩토링 목표

### 설계 원칙

✅ **Single Responsibility Principle (SRP)**
- 각 클래스는 하나의 책임만
- 클래스 크기 200줄 이내 유지

✅ **Dependency Injection**
- 의존성을 생성자로 주입
- Mock 객체 작성 용이

✅ **Open/Closed Principle**
- 확장에는 열려있고 수정에는 닫혀있음
- 새로운 페르소나 추가 시 기존 코드 수정 안 함

✅ **Strategy Pattern**
- 라우팅 알고리즘 플러그인화
- 프롬프트 생성 전략 분리

---

## 📐 리팩토링 아키텍처

### 목표 구조

```
persona_system/
├── __init__.py
├── models.py                 # 데이터 모델
│   ├── PersonaConfig
│   ├── PersonaResponse
│   ├── RoutingResult
│   └── RhythmAnalysis
│
├── router/                   # 라우팅 시스템
│   ├── __init__.py
│   ├── base.py              # AbstractRouter
│   ├── resonance_router.py  # ResonanceBasedRouter (기본)
│   └── ml_router.py         # MLRouter (향후)
│
├── personas/                # 페르소나 정의
│   ├── __init__.py
│   ├── base.py              # AbstractPersona
│   ├── lua.py               # LuaPersona
│   ├── elro.py              # ElroPersona
│   ├── riri.py              # RiriPersona
│   └── nana.py              # NanaPersona
│
├── prompts/                 # 프롬프트 관리
│   ├── __init__.py
│   ├── base.py              # AbstractPromptBuilder
│   ├── template_loader.py   # PromptTemplateLoader
│   └── builders/
│       ├── lua_builder.py
│       ├── elro_builder.py
│       ├── riri_builder.py
│       └── nana_builder.py
│
├── pipeline.py              # 메인 파이프라인 (리팩토링)
├── config.py                # 설정 관리
└── middleware.py            # 미들웨어 (로깅, 캐싱 등)
```

---

## 📅 10주 리팩토링 계획

### Week 1-2: 데이터 모델 분리 (2주)

**목표**: 데이터 모델을 독립적인 모듈로 분리

```python
# persona_system/models.py

from dataclasses import dataclass
from typing import Dict, Optional, Any, List

@dataclass
class PersonaConfig:
    """페르소나 설정 (불변)"""
    name: str
    traits: List[str]
    strengths: List[str]
    prompt_style: str
    preferred_tones: List[str]
    description: str
    examples: List[Dict[str, str]]

@dataclass
class PersonaResponse:
    """페르소나 응답"""
    content: str
    persona_used: str
    resonance_key: str
    confidence: float
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class RoutingResult:
    """라우팅 결과"""
    primary_persona: str
    confidence: float
    secondary_persona: Optional[str] = None
    reasoning: str = ""
    all_scores: Dict[str, float] = None  # 모든 점수 기록 (디버깅용)

@dataclass
class RhythmAnalysis:
    """리듬 분석 결과"""
    pace: str  # 'burst', 'flowing', 'medium'
    avg_sentence_length: float
    punctuation_density: float

@dataclass
class ToneAnalysis:
    """톤 분석 결과"""
    primary: str
    confidence: float
    secondary: Optional[str] = None
```

**관련 커밋**:
- `refactor: extract data models to separate module`

---

### Week 2-3: 추상 기본 클래스 설계 (1.5주)

**목표**: 확장 가능한 추상 기본 클래스 설계

```python
# persona_system/router/base.py

from abc import ABC, abstractmethod
from typing import Dict, Optional
from ..models import RoutingResult, RhythmAnalysis, ToneAnalysis

class AbstractRouter(ABC):
    """라우팅 알고리즘의 추상 기본 클래스"""

    @abstractmethod
    def route(
        self,
        resonance_key: str,
        context: Optional[Dict] = None
    ) -> RoutingResult:
        """라우팅 실행"""
        pass

    @abstractmethod
    def get_available_personas(self) -> List[str]:
        """사용 가능한 페르소나 목록"""
        pass

# persona_system/personas/base.py

class AbstractPersona(ABC):
    """페르소나의 추상 기본 클래스"""

    @property
    @abstractmethod
    def config(self) -> PersonaConfig:
        """페르소나 설정"""
        pass

    @abstractmethod
    def generate_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        pass

    @abstractmethod
    def build_user_prompt(
        self,
        user_input: str,
        resonance_key: str
    ) -> str:
        """사용자 프롬프트 구성"""
        pass
```

**관련 커밋**:
- `refactor: introduce abstract base classes for extensibility`

---

### Week 3-4: 페르소나 클래스 개별화 (2주)

**목표**: 각 페르소나를 독립적인 클래스로 분리

```python
# persona_system/personas/lua.py

from .base import AbstractPersona
from ..models import PersonaConfig

class LuaPersona(AbstractPersona):
    """루아 (감성 공감)"""

    @property
    def config(self) -> PersonaConfig:
        return PersonaConfig(
            name="Lua",
            traits=["empathetic", "creative", "flexible"],
            strengths=["emotion_understanding", "creative_problem_solving"],
            prompt_style="warm_and_encouraging",
            preferred_tones=["frustrated", "playful", "anxious"],
            description="따뜻하고 공감적인 감성형 멘토",
            examples=[...]
        )

    def generate_system_prompt(self) -> str:
        """루아의 시스템 프롬프트"""
        return """당신은 Lua입니다...
        """

    def build_user_prompt(
        self,
        user_input: str,
        resonance_key: str
    ) -> str:
        """사용자 프롬프트 구성"""
        tone, pace, intent = self._parse_resonance_key(resonance_key)
        return f"""..."""

# persona_system/personas/elro.py
class ElroPersona(AbstractPersona):
    """엘로 (구조 설계)"""
    ...

# persona_system/personas/riri.py
class RiriPersona(AbstractPersona):
    """리리 (균형 관찰)"""
    ...

# persona_system/personas/nana.py
class NanaPersona(AbstractPersona):
    """나나 (팀 조율)"""
    ...
```

**관련 커밋**:
- `refactor: extract individual persona classes`
- `refactor: implement Lua persona class`
- `refactor: implement Elro persona class`
- `refactor: implement Riri persona class`
- `refactor: implement Nana persona class`

---

### Week 4-5: 프롬프트 빌더 패턴 (1.5주)

**목표**: 프롬프트 생성을 전략 패턴으로 구현

```python
# persona_system/prompts/base.py

from abc import ABC, abstractmethod
from typing import Dict, Optional

class AbstractPromptBuilder(ABC):
    """프롬프트 빌더 추상 기본 클래스"""

    @abstractmethod
    def build(
        self,
        user_input: str,
        resonance_key: str,
        context: Optional[Dict] = None
    ) -> str:
        """프롬프트 구성"""
        pass

# persona_system/prompts/template_loader.py

class PromptTemplateLoader:
    """프롬프트 템플릿 로더 (파일 기반)"""

    def __init__(self, template_dir: str = "prompts/templates"):
        self.template_dir = template_dir

    def load_template(self, persona: str, version: str = "v1") -> str:
        """파일에서 프롬프트 템플릿 로드

        파일 위치:
        prompts/templates/lua_v1.txt
        prompts/templates/elro_v1.txt
        ...
        """
        path = f"{self.template_dir}/{persona.lower()}_{version}.txt"
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
```

**관련 파일 생성**:
- `prompts/templates/lua_v1.txt` (프롬프트 템플릿)
- `prompts/templates/elro_v1.txt`
- `prompts/templates/riri_v1.txt`
- `prompts/templates/nana_v1.txt`

**관련 커밋**:
- `refactor: extract prompt builders`
- `refactor: implement template-based prompts`
- `feat: add prompt template versioning`

---

### Week 5-6: 라우팅 알고리즘 개선 (1.5주)

**목표**: 라우팅 알고리즘을 더 나은 설계로 개선

```python
# persona_system/router/resonance_router.py

class ResonanceBasedRouter(AbstractRouter):
    """파동키 기반 라우터 (기본)"""

    def __init__(self, personas_config: Dict[str, PersonaConfig]):
        self.personas = personas_config
        self.scoring_weights = {
            'tone': 0.5,
            'pace': 0.3,
            'intent': 0.2
        }

    def route(
        self,
        resonance_key: str,
        context: Optional[Dict] = None
    ) -> RoutingResult:
        """향상된 라우팅"""
        # 1. 파동키 파싱
        tone, pace, intent = self._parse_resonance_key(resonance_key)

        # 2. 모든 페르소나에 대한 점수 계산
        scores = {}
        for persona_name, config in self.personas.items():
            scores[persona_name] = self._calculate_score(
                tone, pace, intent, config, context
            )

        # 3. 상위 2개 선택
        sorted_personas = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return RoutingResult(
            primary_persona=sorted_personas[0][0],
            confidence=sorted_personas[0][1],
            secondary_persona=sorted_personas[1][0] if len(sorted_personas) > 1 else None,
            all_scores=scores  # 디버깅용
        )

    def _calculate_score(
        self,
        tone: str,
        pace: str,
        intent: str,
        persona_config: PersonaConfig,
        context: Optional[Dict] = None
    ) -> float:
        """점수 계산 (개선된 로직)"""
        score = 0.0

        # 톤 매칭 (50%)
        tone_score = 1.0 if tone in persona_config.preferred_tones else 0.5
        score += tone_score * self.scoring_weights['tone']

        # 속도 적합성 (30%)
        pace_scores = self._get_pace_scores(persona_config.name)
        pace_score = pace_scores.get(pace, 0.5)
        score += pace_score * self.scoring_weights['pace']

        # 의도 적합성 (20%)
        intent_scores = self._get_intent_scores(persona_config.name)
        intent_score = intent_scores.get(intent, 0.5)
        score += intent_score * self.scoring_weights['intent']

        return score

# 향후: MLRouter (머신러닝 기반)
class MLRouter(AbstractRouter):
    """머신러닝 기반 라우터"""
    ...
```

**관련 커밋**:
- `refactor: improve routing algorithm with weights`
- `feat: add all_scores to routing result for debugging`
- `refactor: make router strategy-pluggable`

---

### Week 6-7: 파이프라인 리팩토링 (1.5주)

**목표**: PersonaPipeline을 간결하고 명확하게 재구성

```python
# persona_system/pipeline.py

class PersonaPipeline:
    """간결한 파이프라인"""

    def __init__(
        self,
        vertex_client,
        router: AbstractRouter,
        personas: Dict[str, AbstractPersona],
        middleware: Optional[List] = None
    ):
        self.vertex_client = vertex_client
        self.router = router
        self.personas = personas
        self.middleware = middleware or []

    async def process(self, user_input: str) -> PersonaResponse:
        """간결한 파이프라인"""
        # 1. 입력 검증
        if not self._validate_input(user_input):
            return self._get_error_response()

        # 2. 미들웨어 전처리
        for mw in self.middleware:
            user_input = await mw.preprocess(user_input)

        # 3. 라우팅
        routing_result = await self.router.route(resonance_key)
        persona_name = routing_result.primary_persona
        persona = self.personas[persona_name]

        # 4. 프롬프트 생성
        prompt = persona.build_user_prompt(user_input, resonance_key)

        # 5. LLM 호출
        response_text = await self._call_llm(prompt)

        # 6. 미들웨어 후처리
        for mw in reversed(self.middleware):
            response_text = await mw.postprocess(response_text)

        # 7. 응답 패킹
        return PersonaResponse(
            content=response_text,
            persona_used=persona_name,
            resonance_key=resonance_key,
            confidence=routing_result.confidence,
            metadata={...}
        )
```

**관련 커밋**:
- `refactor: simplify PersonaPipeline`
- `feat: add middleware support to pipeline`
- `refactor: make pipeline async-compatible`

---

### Week 7-8: 테스트 작성 (2주)

**목표**: 각 컴포넌트의 단위 테스트 작성

```python
# tests/unit/test_personas.py

def test_lua_persona_config():
    """루아 페르소나 설정"""
    lua = LuaPersona()
    assert lua.config.name == "Lua"
    assert "empathetic" in lua.config.traits

# tests/unit/test_routers.py

def test_resonance_router_basic():
    """기본 라우팅"""
    router = ResonanceBasedRouter(PERSONAS_CONFIG)
    result = router.route("frustrated-burst-expressive")
    assert result.primary_persona == "Lua"
    assert result.confidence > 0.7

# tests/unit/test_pipeline.py

@pytest.mark.asyncio
async def test_pipeline_full_flow():
    """파이프라인 전체 흐름"""
    pipeline = PersonaPipeline(mock_client, router, personas)
    response = await pipeline.process("도와주세요!")
    assert response.persona_used in ["Lua", "Elro", "Riri", "Nana"]
    assert response.confidence > 0
```

**커버리지 목표**: 95% 이상

---

### Week 8-9: 마이그레이션 및 통합 (1.5주)

**목표**: 기존 코드에서 새로운 구조로 전환

```python
# 호환성 레이어
class LegacyPersonaPipelineAdapter:
    """기존 PersonaPipeline과 호환성 유지"""

    def __init__(self):
        # 새로운 구조 초기화
        self.new_pipeline = PersonaPipeline(...)

    # 기존 인터페이스 유지
    def process(self, user_input: str) -> PersonaResponse:
        """기존 process() 메서드 호환"""
        import asyncio
        return asyncio.run(self.new_pipeline.process(user_input))
```

**관련 커밋**:
- `refactor: complete pipeline refactoring`
- `feat: add backward compatibility layer`
- `migration: update app/main.py to use new pipeline`

---

### Week 9-10: 최적화 및 문서화 (2주)

**목표**: 성능 최적화 및 완벽한 문서화

**성능 최적화**:
- 페르소나 설정 캐싱
- 프롬프트 템플릿 캐싱
- 비동기 처리 최적화
- 메모리 프로파일링

**문서화**:
- 아키텍처 설명
- 새로운 페르소나 추가 가이드
- 라우팅 알고리즘 설명
- 예제 코드

**관련 커밋**:
- `perf: add caching to persona configurations`
- `docs: document persona system architecture`
- `docs: add guide for extending personas`

---

## 📊 리팩토링 효과

### 코드 품질

| 메트릭 | 이전 | 이후 | 개선 |
|--------|------|------|------|
| 클래스 크기 | 400+ 줄 | < 200 줄 | ✅ |
| 순환 복잡도 | 15 | < 5 | ✅ |
| 테스트 커버리지 | 60% | 95% | ✅ |
| 코드 중복도 | 높음 | 낮음 | ✅ |

### 운영 효율

| 항목 | 개선사항 |
|------|----------|
| **새 페르소나 추가** | 기존: 1일 → 이후: 2시간 |
| **프롬프트 수정** | 기존: 코드 수정 → 이후: 파일만 수정 |
| **버그 수정** | 기존: 고위험 → 이후: 격리된 영역만 |
| **테스트 작성** | 기존: 어려움 → 이후: 쉬움 |

---

## 🔄 롤백 계획

각 주 마다 릴리즈할 수 있도록 설계:

```
Week 1-2: ✅ models.py (비파괴적)
Week 2-3: ✅ base classes (비파괴적)
Week 3-5: ✅ 개별 페르소나 (하위호환)
Week 5-6: ✅ 라우터 (플러그인)
Week 6-7: ✅ 파이프라인 (호환성 레이어)
Week 8-9: ✅ 마이그레이션 (완전 전환)
Week 9-10: ✅ 최적화 (프로덕션)
```

---

## ✅ 체크리스트

- [ ] Week 1-2: 데이터 모델 분리
- [ ] Week 2-3: 추상 기본 클래스
- [ ] Week 3-4: 페르소나 개별화
- [ ] Week 4-5: 프롬프트 빌더
- [ ] Week 5-6: 라우팅 개선
- [ ] Week 6-7: 파이프라인 리팩토링
- [ ] Week 7-8: 단위 테스트 (95% 이상)
- [ ] Week 8-9: 마이그레이션
- [ ] Week 9-10: 최적화 및 문서화
- [ ] 모든 기존 테스트 통과
- [ ] 성능 회귀 없음

---

**10주 리팩토링으로 유지보수성, 확장성, 테스트 가능성을 극적으로 개선하겠습니다! 🚀**
