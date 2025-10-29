# 📐 Day 4: 페르소나 라우팅 시스템 구현

**날짜**: 2025년 10월 21일 (월)  
**주제**: 파동키 기반 페르소나 라우팅  
**선행 완료**: Day 1-3 (Vertex AI 환경 + 파동키 변환)

---

## 🎯 학습 목표

### 기술 목표

- [ ] PersonaRouter 클래스 설계 및 구현
- [ ] 파동키 → 페르소나 매핑 로직 작성
- [ ] 매칭 점수 계산 알고리즘 구현
- [ ] 10+ 단위 테스트 작성

### 개념 목표

- [ ] 전략 패턴 (Strategy Pattern) 이해
- [ ] 파동키 기반 라우팅 메커니즘 이해
- [ ] 페르소나별 특성 및 강점 파악
- [ ] 컨텍스트 기반 우선순위 조정 개념

---

## 📚 핵심 개념

### 페르소나 라우팅이란?

**정의**: 사용자 입력의 파동키를 분석하여 가장 적합한 AI 페르소나를 선택하는 시스템

**목적**:

1. 사용자 의도에 맞는 최적의 응답 제공
2. 페르소나별 강점을 활용한 효율적인 대화
3. 멀티 페르소나 협력 기반 마련

### 내다AI 페르소나 소개

#### 🌊 Lua (루아) - 감성 공감

**특성**:

- 감정: 공감적, 창의적, 유연함
- 강점: 사용자 감정 이해, 창의적 문제 해결, 동기 부여
- 프롬프트 스타일: 따뜻하고 격려적

**적합한 파동키**:

- `frustrated-*-*` (좌절감)
- `playful-*-*` (장난스러운)
- `anxious-*-*` (불안한)

**사용 사례**:

- 디버깅 지원 시 감정적 지지
- 창의적 아이디어 브레인스토밍
- 학습 동기 부여

#### 📐 Elro (엘로) - 구조 설계

**특성**:

- 감정: 논리적, 체계적, 명확함
- 강점: 기술 아키텍처, 코드 설계, 패턴 적용
- 프롬프트 스타일: 구조화되고 정확

**적합한 파동키**:

- `curious-*-inquiry` (호기심 있는 질문)
- `analytical-*-statement` (분석적 진술)
- `calm-*-statement` (차분한 진술)

**사용 사례**:

- 기술 아키텍처 질문
- 코드 설계 패턴 상담
- 시스템 구조 분석

#### 📊 Riri (리리) - 균형 관찰

**특성**:

- 감정: 분석적, 균형적, 객관적
- 강점: 메트릭 분석, 품질 검증, 데이터 해석
- 프롬프트 스타일: 데이터 기반, 측정 가능

**적합한 파동키**:

- `analytical-*-*` (분석적)
- `calm-flowing-statement` (차분하고 흐르는 듯한)
- `curious-medium-inquiry` (호기심 있는 중간 속도)

**사용 사례**:

- 테스트 커버리지 분석
- 성능 메트릭 해석
- 품질 검증 리뷰

#### ✒️ Nana (나나) - 팀 조율

**특성**:

- 감정: 조율적, 통합적, 협력적
- 강점: 크로스팀 협업, 프로세스 관리, 문서화
- 프롬프트 스타일: 조율적이고 포괄적

**적합한 파동키**:

- `urgent-burst-*` (긴급하고 급한)
- `confused-*-inquiry` (혼란스러운 질문)
- `collaborative-*-*` (협력적)

**사용 사례**:

- 긴급 문제 해결 조율
- 프로세스 개선 제안
- 팀 간 커뮤니케이션

---

## 🏗️ 아키텍처 설계

### PersonaRouter 클래스 구조

```python
"""
페르소나 라우팅 시스템

파동키를 분석하여 최적의 페르소나를 선택합니다.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class PersonaConfig:
    """페르소나 설정"""
    name: str  # 'Lua', 'Elro', 'Riri', 'Nana'
    traits: List[str]  # ['empathetic', 'creative', 'flexible']
    strengths: List[str]  # ['emotion_understanding', 'creative_problem_solving']
    prompt_style: str  # 'warm_and_encouraging'
    preferred_tones: List[str]  # ['frustrated', 'playful', 'anxious']


@dataclass
class RoutingResult:
    """라우팅 결과"""
    primary_persona: str  # 1순위 페르소나
    confidence: float  # 매칭 점수 (0.0 ~ 1.0)
    secondary_persona: Optional[str] = None  # 2순위 페르소나
    reasoning: str = ""  # 선택 이유


class PersonaRouter:
    """파동키 기반 페르소나 라우터"""

    def __init__(self):
        """라우터 초기화"""
        self.personas: Dict[str, PersonaConfig] = {}
        self._load_persona_configs()

    def _load_persona_configs(self):
        """페르소나 설정 로드"""
        # Phase 1에서 구현
        pass

    def route(self, resonance_key: str, context: Optional[Dict] = None) -> RoutingResult:
        """
        파동키를 페르소나로 라우팅

        Args:
            resonance_key: 파동키 (예: "curious-burst-inquiry")
            context: 추가 컨텍스트 (선택사항)

        Returns:
            RoutingResult: 라우팅 결과
        """
        # Phase 2에서 구현
        pass

    def calculate_match_score(
        self,
        resonance_key: str,
        persona_name: str
    ) -> float:
        """
        파동키와 페르소나 간 매칭 점수 계산

        Args:
            resonance_key: 파동키
            persona_name: 페르소나 이름

        Returns:
            float: 매칭 점수 (0.0 ~ 1.0)
        """
        # Phase 3에서 구현
        pass

    def get_persona_config(self, persona_name: str) -> Optional[PersonaConfig]:
        """
        페르소나 설정 조회

        Args:
            persona_name: 페르소나 이름

        Returns:
            Optional[PersonaConfig]: 페르소나 설정 또는 None
        """
        return self.personas.get(persona_name)

    def _parse_resonance_key(self, resonance_key: str) -> Tuple[str, str, str]:
        """
        파동키 파싱

        Args:
            resonance_key: 파동키 (예: "curious-burst-inquiry")

        Returns:
            Tuple[tone, pace, intent]: 감정 톤, 리듬 속도, 의도
        """
        # Phase 3에서 구현
        parts = resonance_key.split('-')
        if len(parts) != 3:
            return ('unknown', 'unknown', 'unknown')
        return (parts[0], parts[1], parts[2])
```

---

## 🔨 Phase별 구현 가이드

### Phase 1: 페르소나 설정 로드 (30분)

**목표**: 4개 페르소나의 기본 설정 정의

**구현 파일**: `persona_router.py`

**작업**:

```python
def _load_persona_configs(self):
    """페르소나 설정 로드"""
    self.personas = {
        'Lua': PersonaConfig(
            name='Lua',
            traits=['empathetic', 'creative', 'flexible'],
            strengths=['emotion_understanding', 'creative_problem_solving', 'motivation'],
            prompt_style='warm_and_encouraging',
            preferred_tones=['frustrated', 'playful', 'anxious']
        ),
        'Elro': PersonaConfig(
            name='Elro',
            traits=['logical', 'systematic', 'clear'],
            strengths=['technical_architecture', 'code_design', 'pattern_application'],
            prompt_style='structured_and_precise',
            preferred_tones=['curious', 'analytical', 'calm']
        ),
        'Riri': PersonaConfig(
            name='Riri',
            traits=['analytical', 'balanced', 'objective'],
            strengths=['metric_analysis', 'quality_verification', 'data_interpretation'],
            prompt_style='data_driven_measurable',
            preferred_tones=['analytical', 'calm', 'curious']
        ),
        'Nana': PersonaConfig(
            name='Nana',
            traits=['coordinating', 'integrative', 'collaborative'],
            strengths=['cross_team_collaboration', 'process_management', 'documentation'],
            prompt_style='coordinating_and_comprehensive',
            preferred_tones=['urgent', 'confused', 'collaborative']
        )
    }
```

**테스트**:

```python
def test_persona_config_loading():
    """페르소나 설정 로드 테스트"""
    router = PersonaRouter()

    assert len(router.personas) == 4
    assert 'Lua' in router.personas
    assert 'Elro' in router.personas
    assert 'Riri' in router.personas
    assert 'Nana' in router.personas

def test_get_persona_config_lua():
    """Lua 페르소나 설정 조회 테스트"""
    router = PersonaRouter()

    lua_config = router.get_persona_config('Lua')

    assert lua_config is not None
    assert lua_config.name == 'Lua'
    assert 'empathetic' in lua_config.traits
    assert 'frustrated' in lua_config.preferred_tones
```

---

### Phase 2: 파동키 파싱 (30분)

**목표**: 파동키를 tone-pace-intent로 분해

**구현**:

```python
def _parse_resonance_key(self, resonance_key: str) -> Tuple[str, str, str]:
    """
    파동키 파싱

    Args:
        resonance_key: 파동키 (예: "curious-burst-inquiry")

    Returns:
        Tuple[tone, pace, intent]: 감정 톤, 리듬 속도, 의도

    Examples:
        >>> router._parse_resonance_key("curious-burst-inquiry")
        ('curious', 'burst', 'inquiry')

        >>> router._parse_resonance_key("calm-flowing-statement")
        ('calm', 'flowing', 'statement')
    """
    parts = resonance_key.split('-')

    # 기본 검증
    if len(parts) != 3:
        return ('unknown', 'unknown', 'unknown')

    tone, pace, intent = parts[0], parts[1], parts[2]

    return (tone, pace, intent)
```

**테스트**:

```python
def test_parse_resonance_key_valid():
    """유효한 파동키 파싱 테스트"""
    router = PersonaRouter()

    tone, pace, intent = router._parse_resonance_key("curious-burst-inquiry")

    assert tone == 'curious'
    assert pace == 'burst'
    assert intent == 'inquiry'

def test_parse_resonance_key_invalid():
    """잘못된 파동키 파싱 테스트"""
    router = PersonaRouter()

    tone, pace, intent = router._parse_resonance_key("invalid-key")

    assert tone == 'unknown'
    assert pace == 'unknown'
    assert intent == 'unknown'
```

---

### Phase 3: 매칭 점수 계산 (1시간)

**목표**: 파동키와 페르소나 간 매칭 점수 알고리즘

**구현**:

```python
def calculate_match_score(
    self,
    resonance_key: str,
    persona_name: str
) -> float:
    """
    파동키와 페르소나 간 매칭 점수 계산

    점수 계산 로직:
    - 감정 톤 매칭: 0.5점
    - 속도 적합성: 0.3점
    - 의도 적합성: 0.2점

    Args:
        resonance_key: 파동키
        persona_name: 페르소나 이름

    Returns:
        float: 매칭 점수 (0.0 ~ 1.0)
    """
    persona = self.get_persona_config(persona_name)
    if not persona:
        return 0.0

    tone, pace, intent = self._parse_resonance_key(resonance_key)

    score = 0.0

    # 감정 톤 매칭 (50%)
    if tone in persona.preferred_tones:
        score += 0.5

    # 속도 적합성 (30%)
    pace_scores = {
        'Lua': {'burst': 0.3, 'flowing': 0.3, 'medium': 0.3},  # 모든 속도 OK
        'Elro': {'burst': 0.1, 'flowing': 0.3, 'medium': 0.3},  # 차분한 게 좋음
        'Riri': {'burst': 0.1, 'flowing': 0.3, 'medium': 0.3},  # 분석적 속도
        'Nana': {'burst': 0.3, 'flowing': 0.2, 'medium': 0.3}   # 긴급 대응 OK
    }
    score += pace_scores.get(persona_name, {}).get(pace, 0.0)

    # 의도 적합성 (20%)
    intent_scores = {
        'Lua': {'inquiry': 0.2, 'statement': 0.1, 'expressive': 0.2},
        'Elro': {'inquiry': 0.2, 'statement': 0.2, 'expressive': 0.1},
        'Riri': {'inquiry': 0.2, 'statement': 0.2, 'expressive': 0.1},
        'Nana': {'inquiry': 0.2, 'statement': 0.2, 'expressive': 0.2}
    }
    score += intent_scores.get(persona_name, {}).get(intent, 0.0)

    return score
```

**테스트**:

```python
def test_calculate_match_score_lua_frustrated():
    """Lua - frustrated 파동키 매칭 테스트"""
    router = PersonaRouter()

    score = router.calculate_match_score("frustrated-burst-expressive", "Lua")

    # frustrated는 Lua의 preferred_tones에 있음 (0.5)
    # burst는 Lua에게 적합 (0.3)
    # expressive도 적합 (0.2)
    assert score == 1.0  # 완벽한 매칭

def test_calculate_match_score_elro_curious():
    """Elro - curious 파동키 매칭 테스트"""
    router = PersonaRouter()

    score = router.calculate_match_score("curious-flowing-inquiry", "Elro")

    # curious는 Elro의 preferred_tones에 있음 (0.5)
    # flowing은 Elro에게 적합 (0.3)
    # inquiry도 적합 (0.2)
    assert score == 1.0  # 완벽한 매칭
```

---

### Phase 4: 라우팅 로직 (1시간)

**목표**: 전체 라우팅 프로세스 구현

**구현**:

```python
def route(self, resonance_key: str, context: Optional[Dict] = None) -> RoutingResult:
    """
    파동키를 페르소나로 라우팅

    Args:
        resonance_key: 파동키 (예: "curious-burst-inquiry")
        context: 추가 컨텍스트 (선택사항)

    Returns:
        RoutingResult: 라우팅 결과
    """
    # 모든 페르소나에 대한 매칭 점수 계산
    scores = {}
    for persona_name in self.personas.keys():
        scores[persona_name] = self.calculate_match_score(resonance_key, persona_name)

    # 점수 기준 정렬
    sorted_personas = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # 1순위, 2순위 선택
    primary_persona, primary_score = sorted_personas[0]
    secondary_persona = sorted_personas[1][0] if len(sorted_personas) > 1 else None

    # 선택 이유 생성
    tone, pace, intent = self._parse_resonance_key(resonance_key)
    reasoning = (
        f"파동키 '{resonance_key}' 분석 결과: "
        f"감정 톤={tone}, 속도={pace}, 의도={intent}. "
        f"{primary_persona}가 가장 적합 (점수: {primary_score:.2f})"
    )

    return RoutingResult(
        primary_persona=primary_persona,
        confidence=primary_score,
        secondary_persona=secondary_persona,
        reasoning=reasoning
    )
```

**테스트**:

```python
def test_route_curious_inquiry():
    """호기심 있는 질문 라우팅 테스트"""
    router = PersonaRouter()

    result = router.route("curious-flowing-inquiry")

    assert result.primary_persona in ['Elro', 'Riri']  # 기술/분석 페르소나
    assert result.confidence > 0.5
    assert result.secondary_persona is not None

def test_route_frustrated_expressive():
    """좌절감 표현 라우팅 테스트"""
    router = PersonaRouter()

    result = router.route("frustrated-burst-expressive")

    assert result.primary_persona == 'Lua'  # 감성 공감
    assert result.confidence >= 0.8
    assert '감정 톤=frustrated' in result.reasoning
```

---

## 🧪 테스트 작성 가이드

### 테스트 파일 구조

**파일**: `tests/test_persona_router.py`

```python
"""
PersonaRouter 테스트

Phase별 테스트 구성:
- Phase 1: 페르소나 설정 로드 (3개 테스트)
- Phase 2: 파동키 파싱 (3개 테스트)
- Phase 3: 매칭 점수 계산 (5개 테스트)
- Phase 4: 라우팅 로직 (4개 테스트)
"""

import sys
from pathlib import Path

# 동적 모듈 로딩 (ion-mentoring 디렉토리 처리)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import importlib.util

# persona_router 모듈 로딩
spec = importlib.util.spec_from_file_location(
    "persona_router",
    project_root / "persona_router.py"
)
persona_router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(persona_router)

PersonaRouter = persona_router.PersonaRouter
PersonaConfig = persona_router.PersonaConfig
RoutingResult = persona_router.RoutingResult


# Phase 1: 페르소나 설정 로드
def test_persona_config_loading():
    """페르소나 설정 로드 테스트"""
    # 구현 예시는 위 참조
    pass

# Phase 2: 파동키 파싱
def test_parse_resonance_key_valid():
    """유효한 파동키 파싱 테스트"""
    # 구현 예시는 위 참조
    pass

# Phase 3: 매칭 점수 계산
def test_calculate_match_score_lua_frustrated():
    """Lua - frustrated 파동키 매칭 테스트"""
    # 구현 예시는 위 참조
    pass

# Phase 4: 라우팅 로직
def test_route_curious_inquiry():
    """호기심 있는 질문 라우팅 테스트"""
    # 구현 예시는 위 참조
    pass
```

---

## ✅ 완료 체크리스트

### 코드 구현

- [ ] `persona_router.py` 생성
- [ ] PersonaConfig 데이터클래스 정의
- [ ] RoutingResult 데이터클래스 정의
- [ ] PersonaRouter 클래스 구현
- [ ] Phase 1-4 모든 메서드 구현

### 테스트 작성

- [ ] `tests/test_persona_router.py` 생성
- [ ] Phase 1 테스트 3개 작성
- [ ] Phase 2 테스트 3개 작성
- [ ] Phase 3 테스트 5개 작성
- [ ] Phase 4 테스트 4개 작성
- [ ] 전체 15개 테스트 통과

### 품질 검증

- [ ] 모든 함수에 타입 힌트
- [ ] Docstring 100% 완성
- [ ] 마크다운 린트 에러 0개
- [ ] pytest 실행 결과 100% 통과

---

## 🎓 학습 포인트

### 전략 패턴 적용

**개념**: 알고리즘을 캡슐화하여 런타임에 선택 가능하게 만드는 패턴

**적용**:

- PersonaRouter가 여러 페르소나 중 하나를 선택
- 각 페르소나는 독립적인 전략 (추후 구현)
- 컨텍스트에 따라 전략 변경 가능

### 데이터 주도 설계

**개념**: 하드코딩 대신 데이터로 동작 정의

**적용**:

- PersonaConfig로 페르소나 특성 정의
- 매핑 테이블로 점수 계산 로직 분리
- 추후 JSON/YAML 파일로 외부화 가능

---

## 🚀 다음 단계

### Day 5 준비

- [ ] PersonaRouter 코드 리뷰
- [ ] ResonanceConverter 연동 계획
- [ ] 멀티 페르소나 협력 설계

---

**Day 4 화이팅!** 🎉

---

**끝.**
