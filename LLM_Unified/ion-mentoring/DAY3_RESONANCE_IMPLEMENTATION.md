# 🎵 Ion Day 3: 파동키 변환 시스템 구현

**날짜**: 2025년 10월 20일 (월요일)  
**시간**: 09:00-17:00 (7시간)  
**목표**: Vertex AI를 활용한 파동키 변환 시스템 첫 구현  
**방식**: 페어 프로그래밍 (비노체 ↔ 이온)

---

## 📋 학습 목표

### 기술 목표

- [ ] 파동키 변환 시스템 개념 이해
- [ ] `ResonanceConverter` 클래스 설계 및 구현
- [ ] Vertex AI를 활용한 감정 톤 분석
- [ ] 리듬 패턴 추출 알고리즘 구현
- [ ] 단위 테스트 작성 (pytest)

### 소프트 스킬 목표

- [ ] 페어 프로그래밍 프랙티스 체험
- [ ] 드라이버/내비게이터 역할 전환 연습
- [ ] 실시간 코드 리뷰 프로세스
- [ ] TDD (테스트 주도 개발) 기초

---

## 🧩 파동키 변환 시스템이란?

### 핵심 개념

내다AI의 **파동키(Resonance Key)** 시스템은 사용자 입력의 **리듬**, **감정 톤**, **맥락**을 분석하여 적절한 AI 페르소나를 선택하는 핵심 메커니즘입니다.

```text
사용자 입력
    ↓
[리듬 분석] → 문장 구조, 속도, 패턴
    ↓
[감정 톤 감지] → calm, urgent, curious, playful 등
    ↓
[파동키 생성] → "calm-flowing-inquiry"
    ↓
[페르소나 라우팅] → 루아(감성) or 엘로(구조) or ...
```

### 예시

| 사용자 입력                                 | 리듬 패턴     | 감정 톤    | 파동키             | 선택 페르소나 |
| ------------------------------------------- | ------------- | ---------- | ------------------ | ------------- |
| "이 코드가 왜 안 돌아가는 거야?!"           | short-burst   | frustrated | urgent-technical   | 엘로 (구조)   |
| "혹시... 이 부분을 개선할 방법이 있을까요?" | long-flowing  | curious    | calm-inquiry       | 루아 (감성)   |
| "데이터 분석 결과 좀 확인해줄래?"           | medium-direct | neutral    | neutral-analytical | 리리 (균형)   |

---

## 🏗️ ResonanceConverter 아키텍처

### 클래스 설계

```python
# ion-mentoring/resonance_converter.py

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class RhythmPattern:
    """리듬 패턴 분석 결과"""
    avg_sentence_length: float
    punctuation_density: float  # 문장부호 밀도
    question_ratio: float       # 질문 비율
    exclamation_ratio: float    # 느낌표 비율
    pace: str                   # 'slow', 'medium', 'fast'


@dataclass
class EmotionTone:
    """감정 톤 분석 결과"""
    primary: str      # 'calm', 'urgent', 'curious', 'frustrated', 'playful'
    confidence: float # 0.0 ~ 1.0
    secondary: Optional[str] = None


class ResonanceConverter:
    """사용자 입력 → 파동키 변환 시스템"""

    def __init__(self, vertex_client=None):
        """
        Args:
            vertex_client: PromptClient 인스턴스 (Vertex AI 연결용)
                          None이면 오프라인 모드 (로컬 분석만)
        """
        self.vertex_client = vertex_client

    def analyze_rhythm(self, text: str) -> RhythmPattern:
        """
        텍스트에서 리듬 패턴 추출

        로컬 분석 항목:
        - 평균 문장 길이
        - 문장부호 밀도
        - 질문/느낌표 비율
        - 전체 속도감 (pace)

        Args:
            text: 분석할 사용자 입력

        Returns:
            RhythmPattern 객체
        """
        pass

    def detect_emotion_tone(self, text: str) -> EmotionTone:
        """
        감정 톤 감지 (Vertex AI 활용)

        Vertex AI Gemini를 사용하여:
        - 주요 감정 분류 (calm, urgent, curious 등)
        - 신뢰도 점수
        - 부차 감정 (있을 경우)

        Args:
            text: 분석할 사용자 입력

        Returns:
            EmotionTone 객체
        """
        pass

    def generate_resonance_key(self, rhythm: RhythmPattern, tone: EmotionTone) -> str:
        """
        파동키 생성

        리듬 패턴과 감정 톤을 조합하여 파동키 문자열 생성
        형식: "{tone}-{pace}-{intent}"
        예: "calm-flowing-inquiry", "urgent-burst-technical"

        Args:
            rhythm: 리듬 패턴 분석 결과
            tone: 감정 톤 분석 결과

        Returns:
            파동키 문자열
        """
        pass

    def convert(self, text: str) -> Dict[str, any]:
        """
        전체 변환 프로세스 실행

        Args:
            text: 사용자 입력

        Returns:
            {
                'rhythm': RhythmPattern,
                'emotion': EmotionTone,
                'resonance_key': str
            }
        """
        rhythm = self.analyze_rhythm(text)
        emotion = self.detect_emotion_tone(text)
        key = self.generate_resonance_key(rhythm, emotion)

        return {
            'rhythm': rhythm,
            'emotion': emotion,
            'resonance_key': key
        }
```

---

## 🔧 Phase 1: 리듬 분석 구현 (09:00-11:00)

### 1.1 analyze_rhythm() 메서드

**페어 구성**: 비노체 (드라이버) + 이온 (내비게이터)

#### 구현 계획

```python
def analyze_rhythm(self, text: str) -> RhythmPattern:
    """텍스트 리듬 패턴 분석"""

    # 1. 문장 분리
    sentences = self._split_sentences(text)

    # 2. 평균 문장 길이 계산
    avg_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

    # 3. 문장부호 밀도 계산
    punctuation_count = sum(1 for c in text if c in '.,!?;:')
    punctuation_density = punctuation_count / max(len(text), 1)

    # 4. 질문/느낌표 비율
    question_ratio = text.count('?') / max(len(sentences), 1)
    exclamation_ratio = text.count('!') / max(len(sentences), 1)

    # 5. 속도감 분류
    pace = self._classify_pace(avg_length, punctuation_density)

    return RhythmPattern(
        avg_sentence_length=avg_length,
        punctuation_density=punctuation_density,
        question_ratio=question_ratio,
        exclamation_ratio=exclamation_ratio,
        pace=pace
    )

def _split_sentences(self, text: str) -> list[str]:
    """문장 분리 헬퍼"""
    import re
    # 간단한 문장 분리 (., !, ? 기준)
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]

def _classify_pace(self, avg_length: float, density: float) -> str:
    """속도감 분류"""
    if avg_length < 5 and density > 0.05:
        return 'fast'
    elif avg_length > 15 and density < 0.03:
        return 'slow'
    else:
        return 'medium'
```

### 1.2 테스트 작성

**역할 전환**: 이온 (드라이버) + 비노체 (내비게이터)

```python
# ion-mentoring/tests/test_resonance_converter.py

import pytest
from resonance_converter import ResonanceConverter, RhythmPattern


def test_analyze_rhythm_fast_pace():
    """빠른 리듬 감지 테스트"""
    converter = ResonanceConverter()
    text = "뭐야! 안 돼! 왜?!"

    rhythm = converter.analyze_rhythm(text)

    assert rhythm.pace == 'fast'
    assert rhythm.exclamation_ratio > 0
    assert rhythm.avg_sentence_length < 5


def test_analyze_rhythm_slow_pace():
    """느린 리듬 감지 테스트"""
    converter = ResonanceConverter()
    text = "이 시스템의 아키텍처를 천천히 살펴보면, 여러 흥미로운 패턴들을 발견할 수 있습니다."

    rhythm = converter.analyze_rhythm(text)

    assert rhythm.pace == 'slow'
    assert rhythm.avg_sentence_length > 10


def test_analyze_rhythm_question_pattern():
    """질문 패턴 감지 테스트"""
    converter = ResonanceConverter()
    text = "이게 맞나요? 혹시 다른 방법은 없을까요?"

    rhythm = converter.analyze_rhythm(text)

    assert rhythm.question_ratio > 0
```

---

## 🧠 Phase 2: 감정 톤 분석 구현 (11:00-13:00)

### 2.1 detect_emotion_tone() 메서드

**페어 구성**: 이온 (드라이버) + 비노체 (내비게이터)

#### Vertex AI 프롬프트 설계

```python
def detect_emotion_tone(self, text: str) -> EmotionTone:
    """Vertex AI로 감정 톤 분석"""

    if not self.vertex_client or not self.vertex_client.ready():
        # 오프라인 모드: 간단한 키워드 기반 분류
        return self._offline_emotion_detection(text)

    # Vertex AI 프롬프트 구성
    prompt = f"""다음 텍스트의 감정 톤을 분석해주세요.

텍스트: "{text}"

가능한 감정 톤:
- calm: 차분하고 안정적
- urgent: 급하고 긴박한
- curious: 호기심 많고 탐구적
- frustrated: 답답하고 좌절적
- playful: 장난스럽고 가벼운
- analytical: 분석적이고 객관적

응답 형식 (JSON):
{{
    "primary": "감정톤",
    "confidence": 0.0-1.0,
    "secondary": "부차감정 (optional)"
}}
"""

    try:
        response = self.vertex_client.send(prompt)
        # JSON 파싱
        import json
        result = json.loads(response)

        return EmotionTone(
            primary=result.get('primary', 'neutral'),
            confidence=result.get('confidence', 0.5),
            secondary=result.get('secondary')
        )
    except Exception as e:
        print(f"⚠️ Vertex AI 감정 분석 실패: {e}")
        return self._offline_emotion_detection(text)

def _offline_emotion_detection(self, text: str) -> EmotionTone:
    """오프라인 감정 분류 (키워드 기반)"""
    text_lower = text.lower()

    # 간단한 키워드 매칭
    if any(word in text_lower for word in ['급해', '빨리', '!!!', '안 돼']):
        return EmotionTone(primary='urgent', confidence=0.7)
    elif any(word in text_lower for word in ['궁금', '?', '혹시', '어떻게']):
        return EmotionTone(primary='curious', confidence=0.7)
    elif any(word in text_lower for word in ['답답', '왜', '이상', '문제']):
        return EmotionTone(primary='frustrated', confidence=0.6)
    else:
        return EmotionTone(primary='calm', confidence=0.5)
```

### 2.2 테스트 작성

```python
def test_detect_emotion_urgent():
    """긴급 감정 감지 테스트"""
    converter = ResonanceConverter()  # 오프라인 모드
    text = "빨리 해결해야 해요! 급합니다!"

    emotion = converter.detect_emotion_tone(text)

    assert emotion.primary == 'urgent'
    assert emotion.confidence > 0.5


def test_detect_emotion_curious():
    """호기심 감정 감지 테스트"""
    converter = ResonanceConverter()
    text = "이 기능은 어떻게 동작하나요? 궁금합니다."

    emotion = converter.detect_emotion_tone(text)

    assert emotion.primary == 'curious'


def test_detect_emotion_with_vertex_ai(monkeypatch):
    """Vertex AI 통합 감정 분석 테스트"""
    from prompt_client import PromptClient

    class MockVertexClient:
        def ready(self):
            return True

        def send(self, prompt):
            return '{"primary": "analytical", "confidence": 0.85}'

    converter = ResonanceConverter(vertex_client=MockVertexClient())
    text = "데이터 분석 결과를 확인해주세요."

    emotion = converter.detect_emotion_tone(text)

    assert emotion.primary == 'analytical'
    assert emotion.confidence == 0.85
```

---

## 🎯 Phase 3: 파동키 생성 통합 (14:00-16:00)

### 3.1 generate_resonance_key() 메서드

```python
def generate_resonance_key(self, rhythm: RhythmPattern, tone: EmotionTone) -> str:
    """리듬 + 감정 → 파동키"""

    # Pace 맵핑
    pace_map = {
        'fast': 'burst',
        'medium': 'flowing',
        'slow': 'contemplative'
    }
    pace_word = pace_map.get(rhythm.pace, 'neutral')

    # Intent 추론 (질문/느낌표 비율 기반)
    if rhythm.question_ratio > 0.3:
        intent = 'inquiry'
    elif rhythm.exclamation_ratio > 0.3:
        intent = 'expressive'
    else:
        intent = 'statement'

    # 파동키 조합
    key = f"{tone.primary}-{pace_word}-{intent}"
    return key
```

### 3.2 전체 convert() 통합 테스트

```python
def test_convert_full_pipeline():
    """전체 변환 파이프라인 테스트"""
    converter = ResonanceConverter()
    text = "이 코드가 왜 안 돌아가는 거야?! 답답해!"

    result = converter.convert(text)

    assert 'rhythm' in result
    assert 'emotion' in result
    assert 'resonance_key' in result

    # 예상: "frustrated-burst-inquiry" 또는 유사
    key = result['resonance_key']
    assert 'frustrated' in key or 'urgent' in key
    assert 'burst' in key or 'fast' in key


def test_convert_calm_inquiry():
    """차분한 질문 변환 테스트"""
    converter = ResonanceConverter()
    text = "혹시 이 부분을 개선할 수 있는 방법이 있을까요?"

    result = converter.convert(text)
    key = result['resonance_key']

    assert 'curious' in key or 'calm' in key
    assert 'inquiry' in key
```

---

## 🧪 Phase 4: 실전 테스트 및 개선 (16:00-17:00)

### 4.1 실제 사용 예시

```python
# ion-mentoring/examples/resonance_demo.py

from prompt_client import create_default_vertex_prompt_client
from resonance_converter import ResonanceConverter


def main():
    """파동키 변환 데모"""

    # Vertex AI 클라이언트 준비
    vertex_client = create_default_vertex_prompt_client()
    vertex_client.initialize().load()

    # ResonanceConverter 생성
    converter = ResonanceConverter(vertex_client=vertex_client)

    # 테스트 입력들
    test_inputs = [
        "이 코드가 왜 안 돌아가는 거야?!",
        "혹시 이 부분을 개선할 방법이 있을까요?",
        "데이터 분석 결과를 확인해주세요.",
        "와! 이거 정말 멋진데요! 어떻게 만든 거예요?"
    ]

    print("=" * 60)
    print("🎵 파동키 변환 시스템 데모")
    print("=" * 60)

    for i, text in enumerate(test_inputs, 1):
        print(f"\n[{i}] 입력: \"{text}\"")

        result = converter.convert(text)

        print(f"   리듬: {result['rhythm'].pace} (평균 문장 길이: {result['rhythm'].avg_sentence_length:.1f})")
        print(f"   감정: {result['emotion'].primary} (신뢰도: {result['emotion'].confidence:.2f})")
        print(f"   🎯 파동키: {result['resonance_key']}")


if __name__ == "__main__":
    main()
```

### 4.2 개선 아이디어 토론

**비노체 + 이온 세션**:

1. **정확도 향상**

   - 더 많은 감정 톤 카테고리 추가?
   - 문맥 기반 분석 강화?
   - 사용자 히스토리 반영?

2. **성능 최적화**

   - 감정 분석 결과 캐싱
   - 배치 처리 지원
   - 비동기 처리?

3. **확장성**
   - 다국어 지원
   - 커스텀 감정 톤 정의
   - 플러그인 아키텍처?

---

## ✅ Day 3 완료 체크리스트

### 코드 구현

- [ ] `ResonanceConverter` 클래스 완성
- [ ] `analyze_rhythm()` 메서드 구현
- [ ] `detect_emotion_tone()` 메서드 구현
- [ ] `generate_resonance_key()` 메서드 구현
- [ ] `convert()` 통합 메서드 구현

### 테스트

- [ ] 리듬 분석 테스트 (3개 이상)
- [ ] 감정 톤 테스트 (3개 이상)
- [ ] 파동키 생성 테스트 (2개 이상)
- [ ] 전체 파이프라인 테스트 (2개 이상)
- [ ] 모든 테스트 통과 (pytest -v)

### 문서

- [ ] 코드 주석 (docstring) 작성
- [ ] `examples/resonance_demo.py` 작성
- [ ] Day 3 완료 보고서 초안

### 페어 프로그래밍

- [ ] 드라이버/내비게이터 최소 2회 교대
- [ ] 실시간 코드 리뷰 진행
- [ ] 페어 세션 회고 (15분)

---

## 📚 참고 자료

### 관련 문서

- [DAY1_ENVIRONMENT_SETUP.md](./DAY1_ENVIRONMENT_SETUP.md) - Vertex AI 기초
- [DAY2_ARCHITECTURE_AND_DESIGN.md](./DAY2_ARCHITECTURE_AND_DESIGN.md) - 시스템 설계
- [WEEK1_KICKOFF.md](./WEEK1_KICKOFF.md) - 전체 일정

### 외부 참고

- [Vertex AI Generative Models](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Dataclasses](https://docs.python.org/3/library/dataclasses.html)

---

## 🎯 다음 단계 (Day 4 예고)

Day 4에서는 구현한 `ResonanceConverter`를 실제 페르소나 라우팅 시스템과 통합합니다:

- 파동키 → 페르소나 매핑 테이블
- 동적 페르소나 선택 로직
- 실시간 대화 테스트
- Cloud Run 배포 준비

**➡️ [Day 4: 페르소나 라우팅 구현 가이드](./DAY4_PERSONA_ROUTING.md)**

---

**문서 작성**: 깃코 (Git AI)  
**검토**: 비노체 (Architect)  
**버전**: 1.0  
**날짜**: 2025-10-17  
**상태**: ✅ 실행 준비 완료
