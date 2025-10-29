# Phase 4 - API v2 Integration Design
## AI 권장사항 엔진 + 다중 턴 대화 시스템 통합

**문서**: Phase 3 API v2 확장 설계
**작성일**: 2025-10-18
**상태**: DESIGN PHASE

---

## 1. 개요

Phase 4에서 개발한 두 가지 주요 기능을 Phase 3 API v2에 통합합니다.

### 통합 기능
1. **AI 권장사항 엔진** (Week 19-21 완료)
   - 하이브리드 앙상블 추천
   - 협업 필터링 + 콘텐츠 기반

2. **다중 턴 대화 시스템** (Week 22-24 완료)
   - 세션 관리
   - 컨텍스트 유지

### 목표
- ✅ 기존 API v2 호환성 유지
- ✅ 신규 기능을 자연스럽게 추가
- ✅ A/B 테스트 가능하도록 설계
- ✅ 프로덕션 배포 준비

---

## 2. API 엔드포인트 설계

### 2.1 권장사항 엔진 엔드포인트

#### POST /api/v2/recommend/personalized
AI 기반 개인화 추천 생성

```json
Request:
{
  "user_id": "user_123",
  "query": "I want to learn Python",
  "context": {
    "tone": "calm",
    "pace": "flowing",
    "intent": "learning"
  },
  "options": {
    "top_k": 3,
    "use_ml_model": true,
    "include_explanation": true
  }
}

Response:
{
  "recommendation": {
    "primary_persona": "Lua",
    "confidence": 0.82,
    "all_scores": {
      "Lua": 0.82,
      "Elro": 0.45,
      "Riri": 0.38,
      "Nana": 0.35
    },
    "ranked_recommendations": [
      {
        "persona": "Lua",
        "score": 0.82,
        "reason": "Based on your learning preference..."
      },
      {
        "persona": "Elro",
        "score": 0.45,
        "reason": "..."
      },
      {
        "persona": "Riri",
        "score": 0.38,
        "reason": "..."
      }
    ]
  },
  "metadata": {
    "model_version": "ensemble_v1",
    "processing_time_ms": 95,
    "algorithm": "cf_40_cb_40_pa_20"
  }
}
```

#### POST /api/v2/recommend/compare
기존 라우터 vs 새 ML 모델 비교 (A/B 테스트용)

```json
Request:
{
  "user_id": "user_123",
  "query": "I need help with debugging",
  "include_legacy": true
}

Response:
{
  "new_recommendation": {
    "persona": "Elro",
    "confidence": 0.78,
    "method": "ensemble"
  },
  "legacy_recommendation": {
    "persona": "Elro",
    "confidence": 0.65,
    "method": "resonance_router"
  },
  "comparison": {
    "consensus": true,
    "confidence_improvement": 0.13,
    "recommendation_changed": false
  }
}
```

---

### 2.2 다중 턴 대화 엔드포인트

#### POST /api/v2/conversations/start
새 대화 세션 시작

```json
Request:
{
  "user_id": "user_123",
  "persona_id": "Lua",
  "options": {
    "session_ttl_hours": 24,
    "use_context_memory": true
  }
}

Response:
{
  "session_id": "session_abc123",
  "user_id": "user_123",
  "persona_id": "Lua",
  "created_at": "2025-10-18T19:30:00Z",
  "expires_at": "2025-10-19T19:30:00Z",
  "status": "active"
}
```

#### POST /api/v2/conversations/{session_id}/turn
대화 턴 처리

```json
Request:
{
  "user_message": "Tell me more about that",
  "metadata": {
    "context": {
      "tone": "calm",
      "pace": "flowing"
    }
  }
}

Response:
{
  "turn_number": 2,
  "session_id": "session_abc123",
  "response_text": "Based on our previous discussion...",
  "context_used": "Topics: [learning, Python]. Entities: [Python, loops]. User preferences: [calm, flowing]",
  "next_suggestion": "Would you like to explore functions or classes?",
  "metadata": {
    "processing_time_ms": 145,
    "tokens_used": 256,
    "confidence": 0.85,
    "persona_used": "Lua"
  }
}
```

#### GET /api/v2/conversations/{session_id}
세션 조회

```json
Response:
{
  "session_id": "session_abc123",
  "user_id": "user_123",
  "persona_id": "Lua",
  "turn_count": 3,
  "messages": [
    {
      "turn_id": 1,
      "user_message": "I want to learn Python",
      "ai_response": "Great! Python is a powerful language...",
      "timestamp": "2025-10-18T19:30:05Z"
    },
    {
      "turn_id": 2,
      "user_message": "Tell me about loops",
      "ai_response": "Loops allow you to...",
      "timestamp": "2025-10-18T19:31:12Z"
    },
    {
      "turn_id": 3,
      "user_message": "More on this",
      "ai_response": "Building on that...",
      "timestamp": "2025-10-18T19:32:20Z"
    }
  ],
  "context_memory": {
    "topics": ["learning", "Python", "loops"],
    "entities": {
      "language": ["Python"],
      "concept": ["loops", "functions"]
    },
    "user_preferences": {
      "tone": "calm",
      "pace": "flowing"
    }
  },
  "state": "active",
  "expires_at": "2025-10-19T19:30:00Z"
}
```

#### POST /api/v2/conversations/{session_id}/close
세션 종료

```json
Request:
{
  "save_conversation": true
}

Response:
{
  "session_id": "session_abc123",
  "closed_at": "2025-10-18T19:35:00Z",
  "summary": {
    "total_turns": 3,
    "total_duration_minutes": 5,
    "main_topics": ["learning", "Python"],
    "user_satisfaction": null
  }
}
```

#### GET /api/v2/conversations
사용자의 모든 세션 조회

```json
Response:
{
  "user_id": "user_123",
  "sessions": [
    {
      "session_id": "session_abc123",
      "persona_id": "Lua",
      "turn_count": 3,
      "created_at": "2025-10-18T19:30:00Z",
      "last_activity": "2025-10-18T19:35:00Z",
      "state": "completed"
    },
    {
      "session_id": "session_def456",
      "persona_id": "Elro",
      "turn_count": 5,
      "created_at": "2025-10-18T15:00:00Z",
      "last_activity": "2025-10-18T15:45:00Z",
      "state": "active"
    }
  ],
  "total_count": 2,
  "active_count": 1
}
```

---

## 3. API 구현 구조

### 3.1 라우터 추가

```python
# app/api/v2_routes.py에 추가

from recommendation_engine import EnsembleRecommendationEngine
from conversation_system import MultiTurnConversationEngine, ConversationSessionManager

# 권장사항 엔진 라우터
@router.post("/api/v2/recommend/personalized")
async def recommend_personalized(request: PersonalizedRecommendationRequest):
    """AI 기반 개인화 추천"""
    engine = get_recommendation_engine()
    recommendation = engine.get_recommendation(
        user_id=request.user_id,
        context=request.context,
        top_k=request.options.top_k
    )
    return RecommendationResponse(recommendation=recommendation)

@router.post("/api/v2/recommend/compare")
async def compare_recommendations(request: ComparisonRequest):
    """기존 vs 새 모델 비교"""
    # 기존 ResonanceBasedRouter
    legacy = legacy_router.route(request.query)

    # 새 ML 모델
    new_engine = get_recommendation_engine()
    new = new_engine.get_recommendation(request.user_id, context=extract_context(request.query))

    return ComparisonResponse(
        new_recommendation=new,
        legacy_recommendation=legacy,
        comparison=compare_results(new, legacy)
    )

# 대화 세션 라우터
@router.post("/api/v2/conversations/start")
async def start_conversation(request: StartConversationRequest):
    """새 대화 세션 시작"""
    session_manager = get_session_manager()
    context = session_manager.create_session(
        user_id=request.user_id,
        persona_id=request.persona_id
    )
    return ConversationStartResponse(session=context)

@router.post("/api/v2/conversations/{session_id}/turn")
async def process_turn(session_id: str, request: TurnRequest):
    """대화 턴 처리"""
    engine = get_multiturn_engine()
    response = await engine.process_turn(
        session_id=session_id,
        user_message=request.user_message,
        metadata=request.metadata
    )
    return TurnResponse(response=response)

@router.get("/api/v2/conversations/{session_id}")
async def get_conversation(session_id: str):
    """세션 조회"""
    session_manager = get_session_manager()
    context = session_manager.get_session(session_id)
    if not context:
        raise HTTPException(status_code=404, detail="Session not found")
    return ConversationContextResponse(context=context)

@router.post("/api/v2/conversations/{session_id}/close")
async def close_conversation(session_id: str, request: CloseConversationRequest):
    """세션 종료"""
    session_manager = get_session_manager()
    success = session_manager.close_session(session_id)
    return CloseConversationResponse(closed=success)

@router.get("/api/v2/conversations")
async def list_conversations(user_id: str):
    """사용자 세션 목록"""
    session_manager = get_session_manager()
    sessions = session_manager.get_user_sessions(user_id)
    return ListConversationsResponse(sessions=sessions)
```

### 3.2 의존성 주입

```python
# app/dependencies.py에 추가

from recommendation_engine import EnsembleRecommendationEngine
from conversation_system import ConversationSessionManager, MultiTurnConversationEngine

# 싱글톤 인스턴스
_recommendation_engine: Optional[EnsembleRecommendationEngine] = None
_session_manager: Optional[ConversationSessionManager] = None
_multiturn_engine: Optional[MultiTurnConversationEngine] = None

def get_recommendation_engine() -> EnsembleRecommendationEngine:
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = EnsembleRecommendationEngine()
        _recommendation_engine.train_models()
    return _recommendation_engine

def get_session_manager() -> ConversationSessionManager:
    global _session_manager
    if _session_manager is None:
        storage = InMemorySessionStorage()  # 또는 Redis, DB 저장소
        _session_manager = ConversationSessionManager(storage=storage)
    return _session_manager

def get_multiturn_engine() -> MultiTurnConversationEngine:
    global _multiturn_engine
    if _multiturn_engine is None:
        session_manager = get_session_manager()
        _multiturn_engine = MultiTurnConversationEngine(session_manager)
    return _multiturn_engine
```

---

## 4. A/B 테스트 프레임워크

### 4.1 테스트 설계

```python
class ABTestFramework:
    """A/B 테스트 프레임워크"""

    def __init__(self, control_ratio: float = 0.5):
        self.control_ratio = control_ratio  # 50% 기존, 50% 신규

    def assign_group(self, user_id: str) -> str:
        """사용자를 A/B 그룹에 할당"""
        # 사용자 ID 해시 기반 일관성 있는 할당
        hash_val = hash(user_id) % 100
        if hash_val < self.control_ratio * 100:
            return "control"  # 기존 ResonanceBasedRouter
        else:
            return "treatment"  # 새 ML 모델

    def log_result(self, user_id: str, group: str, result: Dict):
        """테스트 결과 로깅"""
        # BigQuery 또는 로컬 저장소에 저장
        record = {
            "timestamp": datetime.now(),
            "user_id": user_id,
            "group": group,
            "recommendation": result["persona"],
            "confidence": result["confidence"],
            "user_feedback": result.get("feedback")
        }
        # 저장 로직
```

### 4.2 메트릭 수집

```python
class MetricsCollector:
    """메트릭 수집"""

    @staticmethod
    def calculate_metrics(control_results: List, treatment_results: List) -> Dict:
        """A/B 테스트 메트릭 계산"""
        return {
            "control": {
                "avg_confidence": np.mean([r["confidence"] for r in control_results]),
                "user_satisfaction": np.mean([r.get("feedback", 0.5) for r in control_results]),
                "sample_size": len(control_results)
            },
            "treatment": {
                "avg_confidence": np.mean([r["confidence"] for r in treatment_results]),
                "user_satisfaction": np.mean([r.get("feedback", 0.5) for r in treatment_results]),
                "sample_size": len(treatment_results)
            },
            "improvement": {
                "confidence_delta": (treatment["avg_confidence"] - control["avg_confidence"]),
                "satisfaction_delta": (treatment["user_satisfaction"] - control["user_satisfaction"]),
                "statistical_significance": calculate_pvalue(control_results, treatment_results)
            }
        }
```

---

## 5. 마이그레이션 전략

### Phase: Gradual Rollout

#### Phase 1: 내부 테스트 (Day 1-3)
- 개발팀만 사용
- 신규 엔드포인트 검증
- 버그 수정

#### Phase 2: 카나리 배포 (Day 4-7)
- 5% 사용자에게 신규 기능 배포
- 메트릭 모니터링
- 이슈 대응

#### Phase 3: 50/50 A/B 테스트 (Day 8-21)
- 50% 사용자: 신규 기능
- 50% 사용자: 기존 기능
- 메트릭 비교 분석

#### Phase 4: 완전 배포 (Day 22+)
- 100% 사용자에게 신규 기능 배포
- 모니터링 지속
- 성능 최적화

---

## 6. 모니터링 및 롤백

### 6.1 핵심 메트릭

```python
CRITICAL_METRICS = {
    "availability": {
        "threshold": 0.995,  # 99.5% SLA
        "action": "rollback"
    },
    "error_rate": {
        "threshold": 0.005,  # 0.5% 이상
        "action": "investigate"
    },
    "response_time_p95": {
        "threshold": 100,  # ms
        "action": "optimize"
    },
    "recommendation_accuracy": {
        "threshold": 0.80,  # 80% 이상
        "action": "retrain"
    },
    "user_satisfaction": {
        "threshold": 4.2,  # 5점 기준
        "action": "investigate"
    }
}
```

### 6.2 롤백 절차

```python
async def health_check() -> bool:
    """헬스 체크"""
    metrics = await collect_metrics()

    for metric_name, config in CRITICAL_METRICS.items():
        if metrics[metric_name] < config["threshold"]:
            if config["action"] == "rollback":
                await trigger_rollback()
                return False

    return True
```

---

## 7. 구현 일정

| 항목 | 기간 | 담당 |
|------|------|------|
| API 설계 완료 | Day 1 | 아키텍처 팀 |
| 라우터 구현 | Day 2-3 | 백엔드 팀 |
| 의존성 주입 설정 | Day 2-3 | 백엔드 팀 |
| 테스트 작성 | Day 3-4 | QA 팀 |
| 통합 테스트 | Day 4 | 전체 팀 |
| 내부 배포 | Day 5 | DevOps |
| 카나리 배포 (5%) | Day 6-7 | DevOps |
| A/B 테스트 (50%) | Day 8-21 | 분석 팀 |
| 완전 배포 | Day 22+ | DevOps |

---

## 8. 성공 기준

### 기술적 성공 기준
- ✅ API 응답 시간 <100ms (P95)
- ✅ 에러율 <0.5%
- ✅ 가용성 99.95%

### 사용자 경험 성공 기준
- ✅ 추천 정확도 >80%
- ✅ 사용자 만족도 >4.2/5.0
- ✅ 다중 턴 대화 사용률 >40%

### 비즈니스 성공 기준
- ✅ DAU 증가 (2,000 → 3,000+)
- ✅ 세션 길이 증가 (8분 → 12분+)
- ✅ 재방문율 증가 (60% → 70%+)

---

## 결론

Phase 4 AI 권장사항 엔진과 다중 턴 대화 시스템을 Phase 3 API v2에 통합함으로써:

1. ✅ 기존 기능 보존 (하위 호환성)
2. ✅ 신규 기능 추가 (개선된 사용자 경험)
3. ✅ A/B 테스트 가능 (데이터 기반 의사결정)
4. ✅ 안전한 배포 (카나리, 점진적 롤아웃)

프로덕션 환경에서 신규 기능의 실제 효과를 검증할 수 있습니다.

**다음 단계**: API 라우터 구현 및 테스트 작성 (Day 1-4)
