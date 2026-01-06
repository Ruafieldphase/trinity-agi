# Phase 4 기술 아키텍처 설계
**작성일**: 2025-10-18
**프로젝트**: ION Mentoring Phase 4
**기간**: Week 21-36 (12-16주)
**예산**: $234,000

---

## 1. 프로젝트 개요

### 1.1 목표
Phase 3의 안정적 운영 기반 위에 **고급 AI 기능** 5가지 추가 구현

| 기능 | 목표 | 예상 효과 |
|------|------|---------|
| AI 권장사항 엔진 | 사용자 행동 기반 스마트 페르소나 추천 | 정확도 85%+ |
| 다중 턴 대화 | 컨텍스트 유지 멀티턴 상호작용 | 대화 만족도 40% ↑ |
| 선호도 학습 | 사용자 피드백 기반 개인화 | 재방문율 60% ↑ |
| 분석 대시보드 | 사용 패턴 시각화 및 인사이트 | 의사결정 시간 50% ↓ |
| 모바일 앱 | iOS/Android 네이티브 앱 | 모바일 사용량 45% ↑ |

### 1.2 현황
- **Phase 3**: 완료 (99.95% SLA, $1,990/월 운영)
- **코드베이스**: 5,140 → 7,200+ 라인 (Phase 4)
- **테스트**: 164 → 280+ 테스트 케이스
- **배포**: 3지역 (US, EU, Asia) 준비 완료

---

## 2. 기능별 아키텍처 설계

### 2.1 AI 기반 권장사항 엔진

#### 2.1.1 개요
사용자의 과거 상호작용, 행동 패턴, 피드백을 분석하여 가장 적합한 페르소나를 추천

#### 2.1.2 데이터 구조

```python
# user_preferences.py
class UserProfile:
    user_id: str
    interaction_history: List[InteractionRecord]  # 최근 100개
    persona_ratings: Dict[str, float]  # Lua/Elro/Riri/Nana 선호도
    tone_affinity: Dict[str, float]    # 9개 톤 친화도
    pace_affinity: Dict[str, float]    # 4개 페이스 친화도
    intent_distribution: Dict[str, float]  # 6개 인텐트 분포
    created_at: datetime
    updated_at: datetime

class InteractionRecord:
    interaction_id: str
    timestamp: datetime
    persona_used: str
    resonance_key: str
    user_feedback: Optional[float]  # -1.0 ~ 1.0
    satisfaction_score: float  # 0 ~ 100
    session_duration: int  # 초
    completion: bool
    follow_up_count: int

class RecommendationModel:
    """협업 필터링 + 내용 기반 추천 하이브리드"""
    user_embeddings: np.ndarray  # (n_users, 64) - 사용자 특성 벡터
    persona_embeddings: np.ndarray  # (4, 64) - 페르소나 특성 벡터
    interaction_matrix: sparse_matrix  # (n_users, n_interactions)
    confidence_scores: Dict[str, float]  # 모델 신뢰도
```

#### 2.1.3 추천 엔진 로직

```python
# recommendation_engine.py (420 라인)
class AIRecommendationEngine:

    def __init__(self):
        self.cf_model = CollaborativeFiltering()  # 협업 필터링
        self.cb_model = ContentBasedModel()        # 콘텐츠 기반
        self.ensemble_weight = {
            'cf': 0.4,      # 협업 필터링 40%
            'cb': 0.4,      # 콘텐츠 기반 40%
            'persona_affinity': 0.2  # 페르소나 친화도 20%
        }

    async def get_recommendation(self, user_id: str, context: Dict) -> RecommendationResult:
        """
        사용자에 대한 페르소나 추천 생성

        Args:
            user_id: 사용자 ID
            context: 현재 세션 컨텍스트 (tone, pace, intent)

        Returns:
            RecommendationResult: 점수 매겨진 추천 목록
        """
        # 1. 사용자 프로필 로드
        user_profile = await self.load_user_profile(user_id)

        # 2. 3가지 추천 방식 계산
        cf_scores = self._collaborative_filtering_score(user_id, context)
        cb_scores = self._content_based_score(user_profile, context)
        pa_scores = self._persona_affinity_score(user_profile)

        # 3. 앙상블 종합 (가중 평균)
        final_scores = {}
        for persona in ['Lua', 'Elro', 'Riri', 'Nana']:
            final_scores[persona] = (
                self.ensemble_weight['cf'] * cf_scores.get(persona, 0.5) +
                self.ensemble_weight['cb'] * cb_scores.get(persona, 0.5) +
                self.ensemble_weight['persona_affinity'] * pa_scores.get(persona, 0.5)
            )

        # 4. 신뢰도 계산 (표준편차 기반)
        confidence = self._calculate_confidence(user_profile, final_scores)

        # 5. 결과 반환
        recommendations = sorted(
            [(persona, score) for persona, score in final_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )

        return RecommendationResult(
            primary_recommendation=recommendations[0][0],
            confidence_score=confidence,
            all_scores=final_scores,
            explanation=self._generate_explanation(recommendations, user_profile)
        )

    def _collaborative_filtering_score(self, user_id: str, context: Dict) -> Dict[str, float]:
        """협업 필터링 기반 추천 점수 계산"""
        # 유사한 사용자 찾기
        similar_users = self.cf_model.find_similar_users(user_id, k=5)

        # 유사 사용자의 선호도 집계
        scores = {}
        for persona in ['Lua', 'Elro', 'Riri', 'Nana']:
            persona_ratings = []
            for sim_user, similarity_score in similar_users:
                if sim_user in self.cf_model.user_ratings:
                    rating = self.cf_model.user_ratings[sim_user].get(persona, 0.5)
                    persona_ratings.append(rating * similarity_score)

            scores[persona] = sum(persona_ratings) / len(persona_ratings) if persona_ratings else 0.5

        return scores

    def _content_based_score(self, user_profile: UserProfile, context: Dict) -> Dict[str, float]:
        """콘텐츠 기반 추천 점수 계산"""
        scores = {}
        for persona in ['Lua', 'Elro', 'Riri', 'Nana']:
            # 페르소나의 특성과 사용자 프로필 유사도
            persona_characteristics = self._get_persona_characteristics(persona)
            similarity = cosine_similarity(
                user_profile.embedding,
                persona_characteristics
            )

            # 컨텍스트 적응성 점수
            context_fit = self._calculate_context_fit(persona, context)

            # 결합 점수
            scores[persona] = 0.6 * similarity + 0.4 * context_fit

        return scores

    def _persona_affinity_score(self, user_profile: UserProfile) -> Dict[str, float]:
        """사용자의 페르소나 선호도 직접 점수"""
        return user_profile.persona_ratings

    def _calculate_confidence(self, user_profile: UserProfile, scores: Dict[str, float]) -> float:
        """추천 신뢰도 계산 (데이터 기반)"""
        # 상호작용 히스토리 크기 (100 기준)
        history_factor = min(len(user_profile.interaction_history) / 100, 1.0)

        # 점수 분포 (높을수록 확신도 낮음)
        score_std = np.std(list(scores.values()))
        distribution_factor = 1 - (score_std / 0.5)  # 0.5 정규화

        # 최근 피드백 일관성
        recent_feedback = user_profile.interaction_history[-10:] if user_profile.interaction_history else []
        consistency_factor = 1.0 if len(recent_feedback) < 3 else 0.8

        # 최종 신뢰도 (0 ~ 1)
        confidence = (history_factor * 0.4 +
                     max(0, distribution_factor) * 0.4 +
                     consistency_factor * 0.2)

        return max(0.3, min(1.0, confidence))  # 0.3 ~ 1.0 범위

class RecommendationResult:
    primary_recommendation: str
    confidence_score: float  # 0 ~ 1
    all_scores: Dict[str, float]
    explanation: str
```

#### 2.1.4 성능 목표
- **추천 정확도**: 85%+ (사용자 선택 일치율)
- **응답시간**: <100ms (캐시 포함)
- **모델 재학습**: 일 1회 (밤 10시)
- **온라인 학습**: 실시간 피드백 반영 (1시간 마다)

#### 2.1.5 구현 계획
- **Week 21-23**: 협업 필터링 + 콘텐츠 기반 모델 개발
- **Week 24-25**: 하이브리드 앙상블 및 신뢰도 계산
- **Week 26**: 테스트 및 프로덕션 배포

---

### 2.2 다중 턴 대화 시스템

#### 2.2.1 개요
사용자와의 연속적인 대화에서 이전 맥락을 유지하여 더욱 응집력 있는 상호작용 제공

#### 2.2.2 데이터 구조

```python
# conversation_manager.py
class ConversationContext:
    session_id: str
    user_id: str
    persona_id: str
    turn_count: int
    messages: List[ConversationTurn]
    global_context: Dict[str, Any]  # 세션 전역 상태
    local_context: Dict[str, Any]   # 페르소나별 로컬 상태
    created_at: datetime
    last_activity: datetime
    token_usage: int  # 모니터링용

class ConversationTurn:
    turn_id: int
    user_message: str
    user_intent: str
    user_tone: str
    user_pace: str
    ai_response: str
    response_tokens: int
    timestamp: datetime
    feedback: Optional[float]  # -1 ~ 1

class ContextMemory:
    """컨텍스트 메모리 관리"""
    short_term: Deque[str]  # 최근 5 턴 (현재 메모리)
    long_term: List[str]    # 중요 정보 저장
    entity_memory: Dict[str, Any]  # 엔티티 추출 결과
    topic_memory: List[str]  # 논의된 주제 목록
    user_preferences: Dict[str, Any]  # 세션 중 습득한 사용자 선호도

    def summarize(self) -> str:
        """장기 메모리를 요약문으로 변환"""
        return self._create_context_summary()
```

#### 2.2.3 다중 턴 엔진

```python
# multiturn_engine.py (520 라인)
class MultiTurnConversationEngine:

    def __init__(self):
        self.context_manager = ConversationContextManager()
        self.memory_manager = ContextMemoryManager()
        self.intent_tracker = IntentTracker()
        self.entity_extractor = EntityExtractor()
        self.summarizer = ContextSummarizer()

    async def process_turn(self,
                          session_id: str,
                          user_message: str,
                          metadata: Dict) -> ConversationResponse:
        """
        사용자 메시지 처리 및 응답 생성

        Returns:
            ConversationResponse: 페르소나 응답 + 컨텍스트 유지
        """
        # 1. 세션 컨텍스트 로드
        context = await self.context_manager.load_context(session_id)
        if not context:
            context = self._initialize_conversation_context(session_id)

        # 2. 턴 증가
        context.turn_count += 1

        # 3. 사용자 메시지 분석
        intent = self.intent_tracker.extract_intent(user_message)
        entities = self.entity_extractor.extract(user_message)
        tone, pace = self._infer_tone_pace(user_message, context)

        # 4. 컨텍스트 메모리 업데이트
        memory = context.local_context.get('memory', ContextMemory())
        memory.short_term.append(user_message)
        memory.entity_memory.update(entities)
        if intent not in memory.topic_memory:
            memory.topic_memory.append(intent)

        # 5. 프롬프트 구성 (컨텍스트 포함)
        persona = context.persona_id
        prompt = self._build_contextual_prompt(
            user_message=user_message,
            context=context,
            memory=memory,
            intent=intent,
            persona=persona
        )

        # 6. 페르소나 응답 생성
        response = await self._generate_response(persona, prompt)

        # 7. 턴 기록 저장
        turn = ConversationTurn(
            turn_id=context.turn_count,
            user_message=user_message,
            user_intent=intent,
            user_tone=tone,
            user_pace=pace,
            ai_response=response.text,
            response_tokens=response.token_count,
            timestamp=datetime.now()
        )
        context.messages.append(turn)

        # 8. 세션 타임아웃 연장
        context.last_activity = datetime.now()

        # 9. 컨텍스트 저장 (Redis 캐시 + DB)
        await self.context_manager.save_context(context)

        # 10. 응답 반환
        return ConversationResponse(
            response_text=response.text,
            session_id=session_id,
            turn_number=context.turn_count,
            context_used=self._format_context_used(memory),
            suggestion_for_next_turn=self._suggest_next_topic(context, memory)
        )

    def _build_contextual_prompt(self,
                                 user_message: str,
                                 context: ConversationContext,
                                 memory: ContextMemory,
                                 intent: str,
                                 persona: str) -> str:
        """
        컨텍스트를 포함한 프롬프트 구성

        구조:
        1. 페르소나 역할 정의
        2. 대화 히스토리 (최근 5 턴 요약)
        3. 세션 메타데이터 (사용자 선호도, 진행 상황)
        4. 현재 메시지
        5. 지시사항 (톤, 페이스, 인텐트 유지)
        """
        # 히스토리 요약 (토큰 절약)
        if context.turn_count > 5:
            history_summary = self.summarizer.summarize_history(
                context.messages[-5:],
                max_tokens=150
            )
        else:
            history_summary = "\n".join([
                f"User: {turn.user_message}\nAssistant: {turn.ai_response}"
                for turn in context.messages[-5:]
            ])

        # 엔티티 맥락
        entity_context = self._format_entity_context(memory.entity_memory)

        # 최종 프롬프트
        prompt = f"""
# 역할: {persona} 페르소나로서 대화 진행

## 대화 히스토리
{history_summary}

## 주요 엔티티 및 맥락
{entity_context}

## 지시사항
- 톤: {memory.user_preferences.get('tone', intent)}
- 페이스: {memory.user_preferences.get('pace', 'balanced')}
- 인텐트: {intent}
- 대화 턴: {context.turn_count} / 최대 10턴
- 토큰 예산: {3000 - sum(turn.response_tokens for turn in context.messages[-5:])}

## 현재 사용자 메시지
User: {user_message}

## 응답 작성 시 고려사항
1. 이전 맥락 유지
2. 사용자 이름/선호도 참고 (가능한 경우)
3. 자연스러운 연속성
4. 페르소나 성격 일관성
5. 대화 진행도 고려 (너무 길지 않게)
"""

        return prompt

    def _suggest_next_topic(self, context: ConversationContext, memory: ContextMemory) -> str:
        """다음 턴을 위한 주제 제안"""
        # 논의된 주제 기반으로 자연스러운 다음 주제 제안
        return self._generate_topic_suggestion(memory.topic_memory, context.turn_count)

    async def _generate_response(self, persona: str, prompt: str) -> Response:
        """LLM을 통한 응답 생성"""
        # 실제 구현에서는 OpenAI API 호출
        pass

class ConversationResponse:
    response_text: str
    session_id: str
    turn_number: int
    context_used: str
    suggestion_for_next_turn: str
```

#### 2.2.4 성능 목표
- **세션 메모리**: Redis 5GB (3개 지역)
- **컨텍스트 유지**: 최대 10턴 (약 30분)
- **응답 시간**: <150ms (컨텍스트 포함)
- **토큰 효율**: 평균 2,500 토큰/세션

#### 2.2.5 구현 계획
- **Week 27-28**: 컨텍스트 관리 시스템 구현
- **Week 29-30**: 다중 턴 엔진 및 메모리 관리
- **Week 31**: 테스트 및 프로덕션 배포

---

### 2.3 선호도 학습 시스템

#### 2.3.1 개요
사용자의 명시적 피드백(평점, 좋아요)과 암묵적 신호(세션 시간, 완료율)를 기반으로 개인화 모델 학습

#### 2.3.2 데이터 구조

```python
# preference_learner.py
class UserPreferences:
    user_id: str
    explicit_feedback: Dict[str, float]  # {resonance_key: rating}
    implicit_signals: Dict[str, Any]  # 행동 신호
    feature_importance: Dict[str, float]  # 각 톤/페이스/인텐트의 중요도
    learning_rate: float = 0.01
    updated_at: datetime

class PreferenceLearner:
    """온라인 학습 기반 선호도 최적화"""

    def update_preferences(self, user_id: str, interaction: InteractionRecord):
        """상호작용 기반 선호도 업데이트"""
        # 1. 명시적 피드백 수집
        explicit = self._extract_explicit_feedback(interaction)

        # 2. 암묵적 신호 추출
        implicit = self._extract_implicit_signals(interaction)

        # 3. 선호도 가중치 업데이트 (온라인 학습)
        self._update_weights(user_id, explicit, implicit)

        # 4. 모델 재학습 트리거
        if should_trigger_retraining(user_id):
            self._async_retrain_model(user_id)
```

#### 2.3.3 성능 목표
- **학습 응답성**: 새로운 피드백 반영 시간 < 1시간
- **개인화 정확도**: 93%+ (A/B 테스트 기준)
- **재방문율**: 60% 개선 (Phase 3: 35% → Phase 4: 56%)

#### 2.3.4 구현 계획
- **Week 32-33**: 피드백 수집 및 신호 추출
- **Week 34**: 온라인 학습 엔진 구현
- **Week 35**: 테스트 및 프로덕션 배포

---

### 2.4 분석 대시보드

#### 2.4.1 개요
관리자와 분석가를 위한 사용 패턴, 성능, 비즈니스 메트릭 시각화 대시보드

#### 2.4.2 기능 목록

| 대시보드 | 메트릭 | 갱신 주기 | 사용자 |
|---------|--------|---------|--------|
| **운영 대시보드** | 실시간 트래픽, 에러율, 응답시간 | 1분 | 운영팀 |
| **비즈니스 대시보드** | DAU, MAU, 재방문율, 전환율 | 시간별 | 비즈니스팀 |
| **분석 대시보드** | 페르소나 선호도, 톤/페이스/인텐트 분포 | 일별 | 분석팀 |
| **성능 대시보드** | P95, P99, 캐시 히트율, DB 성능 | 5분 | 개발팀 |
| **AI 모델 대시보드** | 추천 정확도, 학습 진행률, 이상 탐지 | 시간별 | ML팀 |

#### 2.4.3 구현 계획
- **Week 36-37**: 대시보드 프로토타입 개발
- **Week 38**: 프로덕션 배포 및 최적화

---

### 2.5 모바일 앱 (iOS/Android)

#### 2.5.1 개요
네이티브 iOS/Android 앱으로 모바일 접근성 및 사용 경험 향상

#### 2.5.2 기술 스택

```
iOS:
├─ Swift 5.9
├─ SwiftUI (UI Framework)
├─ URLSession (네트워킹)
├─ CoreData (로컬 스토리지)
└─ Push Notifications

Android:
├─ Kotlin
├─ Jetpack Compose (UI)
├─ Retrofit (네트워킹)
├─ Room (로컬 DB)
└─ Firebase Cloud Messaging (알림)

공통:
├─ BDD (Behavior-Driven Development)
├─ 오프라인 우선 동기화
├─ 256-bit 로컬 캐싱
└─ OAuth 2.0 인증
```

#### 2.5.3 구현 계획
- **Week 39-40**: iOS 앱 개발
- **Week 41-42**: Android 앱 개발
- **Week 43-44**: 테스트 및 스토어 출시 준비
- **Week 45-48**: App Store / Google Play 출시 및 최적화

---

## 3. 팀 구성 및 역할

### 3.1 조직 구조

```
Phase 4 프로젝트 PM
├─ Backend Lead (1명)
│  ├─ ML 엔지니어 (2명) - 추천 엔진, 선호도 학습
│  ├─ Backend 엔지니어 (2명) - 다중 턴, API 확장
│  └─ DevOps 엔지니어 (1명) - 배포, 모니터링
├─ Frontend Lead (1명)
│  ├─ Dashboard 개발자 (2명)
│  └─ Web 엔지니어 (1명)
├─ Mobile Lead (1명)
│  ├─ iOS 개발자 (2명)
│  └─ Android 개발자 (2명)
├─ QA Lead (1명)
│  ├─ 자동화 테스트 (2명)
│  └─ 수동 테스트 (2명)
└─ Product Manager (1명)

총 18명 (현재 팀 5명 포함)
```

### 3.2 역할 정의

| 역할 | 책임 | 필요 경험 |
|------|------|---------|
| **ML 엔지니어** | 추천 엔진, 협업 필터링 | ML, Python, TensorFlow |
| **Backend 엔지니어** | API, 다중 턴 엔진 | Python, FastAPI, Redis |
| **DevOps 엔지니어** | GCP, Docker, Kubernetes | 클라우드, CI/CD |
| **iOS 개발자** | Swift, SwiftUI | iOS, Swift |
| **Android 개발자** | Kotlin, Jetpack | Android, Kotlin |
| **Dashboard 개발자** | React/Vue, D3.js | Frontend, 시각화 |
| **QA 엔지니어** | 자동화 테스트, 성능 테스트 | Pytest, 성능 분석 |

---

## 4. 프로젝트 일정 및 마일스톤

### 4.1 타임라인 (Week 21-48, 28주)

```
Week 19-20: 팀 모집 및 온보딩 (현재 진행 중)

Week 21-26: Phase 1 - AI 권장사항 엔진
├─ Week 21-23: 협업 필터링 개발
├─ Week 24-25: 앙상블 모델 및 신뢰도
└─ Week 26: 테스트 및 배포

Week 27-31: Phase 2 - 다중 턴 대화
├─ Week 27-28: 컨텍스트 관리
├─ Week 29-30: 메모리 엔진
└─ Week 31: 테스트 및 배포

Week 32-35: Phase 3 - 선호도 학습
├─ Week 32-33: 피드백 수집
├─ Week 34: 온라인 학습
└─ Week 35: 테스트 및 배포

Week 36-38: Phase 4 - 분석 대시보드
├─ Week 36-37: 대시보드 개발
└─ Week 38: 배포 및 최적화

Week 39-48: Phase 5 - 모바일 앱
├─ Week 39-40: iOS 앱
├─ Week 41-42: Android 앱
├─ Week 43-44: 테스트 및 준비
└─ Week 45-48: App Store 출시 및 최적화

Week 49: 프로젝트 완료 및 문서화
```

### 4.2 주요 마일스톤

| 마일스톤 | 날짜 | 상태 |
|---------|------|------|
| 팀 완벽 구성 | Week 21 (11/11) | ⏳ 예정 |
| 권장사항 엔진 v1 | Week 26 (12/23) | ⏳ 예정 |
| 다중 턴 시스템 v1 | Week 31 (1/27) | ⏳ 예정 |
| 선호도 학습 v1 | Week 35 (2/24) | ⏳ 예정 |
| 분석 대시보드 출시 | Week 38 (3/18) | ⏳ 예정 |
| 모바일 앱 출시 | Week 48 (5/27) | ⏳ 예정 |

---

## 5. 예산 및 리소스

### 5.1 예산 구성 ($234,000)

```
인건비 (28주 × 18명 평균 $250/시간):
├─ 엔지니어링: $185,000
├─ 관리 및 PM: $28,000
└─ 오버헤드: $21,000

총예산: $234,000
주당 예산: $8,357
월 운영비: $2,160 (기존 $1,990 + 추가)
```

### 5.2 리소스 할당

| 리소스 | 용도 | 비용 |
|--------|------|------|
| **GCP 컴퓨팅** | ML 모델 학습, 추가 인스턴스 | $15,000 |
| **데이터 스토리지** | 사용자 데이터, 모델 체크포인트 | $8,000 |
| **외부 API** | 테스트, 분석 서비스 | $5,000 |
| **개발 도구** | IDE, 라이선스, CI/CD | $3,000 |
| **문서 및 교육** | 온보딩, 기술 문서 | $2,000 |

---

## 6. 리스크 관리

### 6.1 주요 리스크

| 리스크 | 영향도 | 가능성 | 완화 전략 |
|--------|--------|--------|---------|
| 팀 모집 지연 | 높음 | 중간 | 외부 컨설턴트 활용 |
| ML 모델 성능 미달 | 높음 | 중간 | A/B 테스트, 점진적 롤아웃 |
| 모바일 앱 출시 지연 | 중간 | 낮음 | 동시 개발, 외부팀 지원 |
| 데이터 보안 이슈 | 매우높음 | 낮음 | 보안 감시, 암호화 강화 |

### 6.2 완화 전략

1. **팀 모집**: 즉시 채용 프로세스 개시
2. **기술 리스크**: 주 1회 기술 리뷰 및 검증
3. **일정 리스크**: 2주 버퍼 마진 유지

---

## 7. 성공 지표 (KPI)

### 7.1 기술 KPI

| KPI | 목표 | 측정 방법 |
|-----|------|---------|
| 권장사항 정확도 | 85%+ | A/B 테스트 |
| 다중 턴 만족도 | 4.2/5.0 | 사용자 평점 |
| 선호도 학습 정확도 | 93%+ | 오프라인 테스트 |
| 대시보드 로드 시간 | <2초 | 성능 모니터링 |
| 모바일 앱 크래시율 | <0.1% | Crashlytics |

### 7.2 비즈니스 KPI

| KPI | 목표 | 측정 방법 |
|-----|------|---------|
| DAU | 50,000+ | 분석 대시보드 |
| 재방문율 | 60% | 세션 추적 |
| 전환율 | 25% | 퍼널 분석 |
| 평균 세션 시간 | 12분+ | 사용자 행동 |
| Net Promoter Score | 65+ | 설문조사 |

---

## 8. 다음 단계

### 즉시 조치 (이번 주)
1. Phase 4 팀 채용 공고 발행
2. 기술 아키텍처 검토 회의 개최
3. 개발 환경 준비 시작

### 1주 내
1. 핵심 팀원 면접 및 선발
2. 온보딩 프로세스 준비
3. 개발 일정 확정

### 2주 내
1. 팀 완벽 구성
2. Week 21 개발 시작
3. 주 1회 진행 상황 보고

---

**문서 작성**: Claude AI Agent
**승인 상태**: ✓ Phase 4 기술 계획 완료
**다음 리뷰**: 2025-10-25 (팀 모집 진행 상황)