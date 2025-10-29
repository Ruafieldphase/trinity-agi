# Day 5 Preview: Multi-Persona Integration

## 🎯 학습 목표

Day 5에서는 PersonaRouter를 실제 Vertex AI 프롬프트 시스템과 통합하여
완전한 멀티 페르소나 응답 파이프라인을 구축합니다.

## 📋 주요 작업

### 1. PersonaPipeline 클래스 설계 (10:00-12:00)

**목적**: ResonanceConverter + PersonaRouter + PromptClient를 연결

```python
class PersonaPipeline:
    """멀티 페르소나 응답 생성 파이프라인"""

    def __init__(self, vertex_client):
        self.vertex_client = vertex_client
        self.converter = ResonanceConverter()
        self.router = PersonaRouter()

    async def process(self, user_input: str) -> PersonaResponse:
        """
        사용자 입력 → 파동키 → 페르소나 → Vertex AI 프롬프트 → 응답
        """
        # 1. 파동키 생성
        # 2. 페르소나 라우팅
        # 3. 페르소나별 프롬프트 구성
        # 4. Vertex AI 호출
        # 5. 응답 후처리
```

### 2. 프롬프트 템플릿 시스템 (13:00-15:00)

**페르소나별 프롬프트 커스터마이징**:

```python
PERSONA_PROMPTS = {
    "Lua": """
당신은 Lua입니다. 따뜻하고 공감적인 톤으로 응답하세요.
사용자 감정: {emotion_context}
질문: {user_input}
""",
    "Elro": """
당신은 Elro입니다. 논리적이고 체계적인 설명을 제공하세요.
분석 컨텍스트: {analysis_context}
질문: {user_input}
"""
}
```

### 3. 통합 테스트 작성 (15:00-17:00)

**테스트 시나리오**:

1. **End-to-End 흐름 테스트**:

   - 사용자 입력 → 최종 응답까지 전체 파이프라인
   - Mock Vertex AI 응답 사용

2. **멀티 페르소나 협업 테스트**:

   - Primary + Secondary 페르소나 조합
   - 응답 품질 검증

3. **에러 핸들링 테스트**:
   - 잘못된 파동키 처리
   - Vertex AI 장애 시 폴백

**목표**: 8-12개 통합 테스트 작성

## 📊 예상 결과

- `persona_pipeline.py`: ~250-300 lines
- `test_integration.py`: 8-12 tests
- 총 테스트 수: 51-55개 (Week 1: 28 + Week 2: 23-27)

## 🔗 연결 고리

- **Week 1**: PromptClient 기반 구축 ✅
- **Week 2 Day 4**: PersonaRouter 완성 ✅
- **Week 2 Day 5**: 전체 시스템 통합 ⏳

## 🚀 다음 단계

Day 5 완료 후:

- Week 2 Summary 작성
- 실제 대화 데모 구현
- Cloud Run 배포 준비 (Week 3 예고)

---

**작성**: 깃코 (Git AI)  
**날짜**: 2025-10-17  
**상태**: 📝 Preview
