# AGI 설계 문서 01: 좌표형 메모리 스키마 v1.0

**작성자**: 세나 (Sena)
**작성일**: 2025-10-12
**상태**: 초안
**목적**: AGI로 가기 위한 장기 기억 및 경험 축적 시스템의 구체적 설계

---

## 1. 목표

### 1.1 왜 필요한가?
현재 `PersonaOrchestrator`는 **세션 단위 히스토리**만 유지하며, 실행이 끝나면 컨텍스트가 사라집니다.
AGI를 향해 나아가려면:
- **장기 기억**: 이전 대화/실험 결과를 재활용
- **패턴 학습**: 반복되는 사용자 의도, 성공/실패 케이스 인식
- **자기 수정**: 과거 경험을 바탕으로 프롬프트·전략 개선

### 1.2 핵심 아이디어: 좌표형 메모리
NotebookLM 요약에서 언급된 **"시간, 공간, 주체, 감정을 포함하는 좌표(coordinate)"** 개념을 구현합니다.

```
Memory = f(Time, Space, Agent, Emotion, Content)
```

---

## 2. 스코프

### 2.1 v1.0에 포함할 것 ✅
- **JSON 기반 저장** (Vector DB는 v2.0)
- **최근 N개 세션만 보관** (N=10, 용량 제한)
- **시간·주제·페르소나 태그** 기본 구조
- **단순 키워드 검색** (full-text)
- **Resonance Ledger JSONL**: 감사용 전역 로그 (`outputs/resonance_ledger/ledger-YYYYMMDD.jsonl`)
- **수동 호출** (자동 학습은 v2.0)

### 2.2 나중 버전으로 미룰 것 ⏳
- 벡터 임베딩 기반 유사도 검색
- 자동 요약/압축
- 다중 사용자 지원
- 분산 저장

---

## 3. 데이터 구조

### 3.1 MemoryCoordinate 스키마

```python
{
  "memory_id": "mem_20251012_093022_a4f3",       # 고유 ID
  "timestamp": "2025-10-12T09:30:22.123456Z",   # ISO 8601 UTC

  # 시간 좌표
  "time": {
    "session_id": "sess_20251012_090000",      # 세션 단위
    "sequence": 15,                             # 세션 내 순서
    "relative_time_minutes": 3.5                # 세션 시작 후 경과 시간
  },

  # 공간 좌표
  "space": {
    "project": "persona_orchestration",         # 프로젝트명
    "domain": "AGI_prototype",                  # 도메인 (AGI, UI, 데이터 등)
    "file_context": ["orchestration/persona_orchestrator.py"],  # 관련 파일
    "depth_index": 1                            # 재귀 깊이
  },

  # 주체 좌표
  "agent": {
    "persona_id": "synthesis",                  # 페르소나 ID
    "persona_name": "Fractal Synthesiser",
    "role": "Integrator",
    "backend": "local_lmstudio"                 # 사용된 백엔드
  },

  # 감정 좌표
  "emotion": {
    "affect_amplitude": 0.65,                   # PhaseController의 affect
    "sentiment_score": 0.12,                    # 긍정/부정 (-1.0 ~ 1.0)
    "confidence": 0.8,                          # 감정 추정 신뢰도
    "keywords": ["hope", "growth", "opportunity"]
  },

  # 내용
  "content": {
    "type": "persona_response",                 # user_input | persona_response | system_event
    "prompt_digest": "System instruction: You reconcile...",  # 프롬프트 요약 (최대 500자)
    "response_full": "Based on the thesis...",  # 전체 응답 (v1.0에서는 전체 저장)
    "response_summary": null,                   # v2.0: 자동 요약
    "token_count": 342
  },

  # 메타데이터
  "metadata": {
    "importance": 0.7,                          # 중요도 (0.0 ~ 1.0, 수동 또는 자동)
    "tags": ["synthesis", "AGI_design", "memory_system"],
    "user_rating": null,                        # 사용자 평가 (1-5 stars)
    "phase_injection_applied": false,           # PhaseController 상태
    "error_occurred": false
  },

  # 관계
  "relations": {
    "parent_memory_id": "mem_20251012_092800_x7b2",  # 이전 메모리
    "child_memory_ids": ["mem_20251012_093145_c9k1"], # 후속 메모리
    "related_memory_ids": []                    # 유사/관련 메모리 (v2.0)
  }
}
```

### 3.2 MemoryIndex 스키마 (검색용)

```python
{
  "index_version": "1.0",
  "last_updated": "2025-10-12T10:00:00Z",
  "total_memories": 1523,

  # 키워드 인덱스 (inverted index)
  "keyword_index": {
    "AGI": ["mem_...", "mem_..."],
    "memory_system": ["mem_...", "mem_..."],
    "synthesis": ["mem_...", ...]
  },

  # 시간 인덱스
  "time_index": {
    "2025-10-12": ["mem_...", "mem_..."],
    "2025-10-11": ["mem_...", ...]
  },

  # 페르소나 인덱스
  "persona_index": {
    "thesis": ["mem_...", ...],
    "antithesis": ["mem_...", ...],
    "synthesis": ["mem_...", ...]
  },

  # 중요도 인덱스 (상위 100개만)
  "importance_index": [
    {"memory_id": "mem_...", "importance": 0.95},
    {"memory_id": "mem_...", "importance": 0.92},
    ...
  ]
}
```

### 3.3 Resonance Ledger 엔트리 (감사 로그)

좌표형 메모리와 별도로, 모든 실행/평가 이벤트를 JSONL 형태로 기록합니다. Ledger는 장기 보존 대상이며 망각 정책의 영향을 받지 않습니다.

```json
{
  "timestamp": "2025-10-12T10:31:45.124Z",
  "session_id": "sess_20251012_090000",
  "event_type": "synthesis_report",         // user_input | persona_response | tool_call | evaluation | rune_report ...
  "bqi_coordinate": {
    "time": "2025-10-12T10:30:00Z",
    "space": "AGI_prototype",
    "agent": "synthesis",
    "emotion": {"affect": 0.68, "keywords": ["clarity", "risk"]},
    "rhythm_phase": "integration"
  },
  "impact_score": 0.74,                      // Core 패키지 확장 지표
  "transparency": 0.9,
  "reproducibility": 0.85,
  "verifiability": 0.8,
  "memory_refs": ["mem_20251012_093022_a4f3", "mem_20251012_093145_c9k1"],
  "plan_adjustment": {
    "trigger": "rune_feedback",
    "action": "reorder_persona_cycle",
    "details": {"new_order": ["thesis", "synthesis", "antithesis"]}
  }
}
```

--- 

## 4. 저장 방법

### 4.1 파일 구조
```
outputs/
└── memory/
    ├── sessions/
    │   ├── sess_20251012_090000.jsonl    # 세션별 메모리 (append-only)
    │   ├── sess_20251012_100000.jsonl
    │   └── ...
    ├── index.json                         # MemoryIndex
    └── config.json                        # 설정 (보관 정책 등)
└── resonance_ledger/
    └── ledger-20251012.jsonl              # BQI/평가/플랜 변경 감사 로그
```

### 4.2 보관 정책 (config.json)
```json
{
  "retention_policy": {
    "max_sessions": 10,
    "max_memories_per_session": 500,
    "max_total_size_mb": 100,
    "archive_after_days": 30,
    "delete_after_days": 180
  },
  "storage": {
    "format": "jsonl",
    "compression": "none",
    "backup_enabled": true,
    "backup_path": "D:/nas_backup/memory_backup"
  }
}
```

---

## 5. 검색 방법

### 5.1 검색 API 설계

```python
class MemoryStore:
    def search(
        self,
        query: str = None,                 # 키워드 검색
        time_range: tuple = None,          # (start, end) datetime
        persona_id: str = None,
        domain: str = None,
        min_importance: float = 0.0,
        tags: list = None,
        bqi_filters: Dict[str, Any] = None, # {"rhythm_phase": "integration", "emotion": "clarity"}
        limit: int = 10
    ) -> List[MemoryCoordinate]:
        """
        복합 조건 검색

        Example:
            store.search(
                query="memory system",
                time_range=(datetime(2025, 10, 10), datetime(2025, 10, 12)),
                persona_id="synthesis",
                min_importance=0.5,
                bqi_filters={"rhythm_phase": "integration"},
                limit=5
            )
        """
        pass

    def get_recent(self, n: int = 10) -> List[MemoryCoordinate]:
        """최근 N개 메모리"""
        pass

    def get_by_session(self, session_id: str) -> List[MemoryCoordinate]:
        """특정 세션의 모든 메모리"""
        pass

    def get_by_id(self, memory_id: str) -> MemoryCoordinate:
        """ID로 직접 조회"""
        pass
```

### 5.2 검색 알고리즘 (v1.0: 단순 필터링)

1. **키워드 검색**: `content.response_full` + `metadata.tags`에서 대소문자 무시하고 포함 여부 확인
2. **시간 범위**: `timestamp` 필드 비교
3. **페르소나**: `agent.persona_id` 일치 여부
4. **중요도**: `metadata.importance >= min_importance`
5. **BQI 좌표**: `bqi_filters`가 주어지면 Resonance Ledger 인덱스(또는 memory.metadata.bqi_snapshot)와 대조
6. **결과 정렬**: timestamp 내림차순 (최신순)
7. **Limit 적용**: 상위 N개만 반환

**성능**: v1.0에서는 전체 스캔. 메모리 10개 세션 × 500개 = 5,000개 기준 < 100ms 예상.

---

## 6. 망각 전략

### 6.1 언제 삭제할 것인가?

#### 자동 망각 (LRU + 중요도 기반)
```python
def auto_forget():
    """
    1. 세션 수가 max_sessions 초과 시
       → 가장 오래된 세션 중 importance < 0.3인 메모리 삭제

    2. 총 용량이 max_total_size_mb 초과 시
       → importance 낮은 순으로 삭제 (단, 최근 7일은 보호)

    3. archive_after_days 경과 시
       → 압축 후 아카이브 폴더로 이동
    """
```

> ⚠️ **Resonance Ledger는 망각 대상에서 제외됩니다.** 감사 용도의 전역 로그로서 별도 보존 정책(예: 1년 단위 압축)에 따라 관리합니다.

#### 수동 망각
```python
store.delete_by_id("mem_...")
store.delete_by_session("sess_...")
store.delete_by_query(tags=["test", "temporary"])
```

### 6.2 중요도 계산 (자동)

```python
def calculate_importance(memory: MemoryCoordinate) -> float:
    """
    중요도 = 기본점수 + 사용자평가 + 참조빈도 + 감정강도

    기본점수 (0.3):
      - 모든 메모리 기본값

    사용자평가 (0.0 ~ 0.3):
      - user_rating이 있으면 (rating / 5.0) * 0.3

    참조빈도 (0.0 ~ 0.2):
      - 이 메모리가 다른 메모리의 relations에 포함된 횟수
      - min(reference_count * 0.05, 0.2)

    감정강도 (0.0 ~ 0.2):
      - abs(sentiment_score) * 0.2

    반환: clamp(점수, 0.0, 1.0)
    """
    base_score = 0.3
    user_score = (memory.metadata.user_rating or 0) / 5.0 * 0.3
    reference_score = min(get_reference_count(memory.memory_id) * 0.05, 0.2)
    emotion_score = abs(memory.emotion.sentiment_score) * 0.2

    total = base_score + user_score + reference_score + emotion_score
    return clamp(total, 0.0, 1.0)
```

---

## 7. PersonaOrchestrator 통합

### 7.1 수정이 필요한 부분

#### (1) PersonaOrchestrator.__init__ 수정
```python
class PersonaOrchestrator:
    def __init__(
        self,
        registry: PersonaRegistry,
        backend_factory: BackendFactory,
        log_path: Optional[Path] = None,
        memory_store: Optional[MemoryStore] = None,         # 추가
        resonance_ledger: Optional[ResonanceLedger] = None  # 추가
    ) -> None:
        self.registry = registry
        self.backend_factory = backend_factory
        self.log_path = log_path
        self.phase = PhaseController()
        self.history: List[Dict[str, Any]] = []
        self.log_entries: List[Dict[str, Any]] = []
        self.memory_store = memory_store
        self.resonance_ledger = resonance_ledger
        self.session_id = f"sess_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
```

#### (2) _run_recursive에서 메모리 저장
```python
def _run_recursive(self, seed_prompt: str, depth: int, depth_index: int) -> str:
    # ... 기존 코드 ...

    # 응답 생성 후
    response = backend.generate(...)
    phase_meta = self.phase.integrate_response(persona.identifier, response)
    bqi_snapshot = self.bqi.analyse(seed_prompt, response) if self.bqi else None

    # 메모리 저장 (추가)
    if self.memory_store:
        memory = self._create_memory_coordinate(
            persona=persona,
            prompt=prompt,
            response=response,
            phase_meta=phase_meta,
            depth_index=depth_index,
            step_index=idx,
            bqi_snapshot=bqi_snapshot
        )
        self.memory_store.add(memory)

    # Resonance Ledger 기록 (추가)
    if self.resonance_ledger:
        self.resonance_ledger.log_event(
            session_id=self.session_id,
            event_type="persona_response",
            persona_id=persona.identifier,
            memory_id=memory.memory_id if self.memory_store else None,
            bqi_coordinate=bqi_snapshot,
            evaluation=self._last_evaluation_metrics,
            plan_adjustment=self._current_plan_adjustment,
        )

    # ... 기존 코드 계속 ...
```

#### (3) _create_memory_coordinate 메서드 추가
```python
def _create_memory_coordinate(
    self,
    persona: Persona,
    prompt: str,
    response: str,
    phase_meta: Dict[str, Any],
    depth_index: int,
    step_index: int,
    bqi_snapshot: Optional[Dict[str, Any]] = None
) -> MemoryCoordinate:
    """현재 응답을 MemoryCoordinate 객체로 변환"""
    memory_id = f"mem_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999):04x}"

    return MemoryCoordinate(
        memory_id=memory_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        time={
            "session_id": self.session_id,
            "sequence": step_index + (depth_index - 1) * len(self.registry.personas_in_cycle()),
            "relative_time_minutes": (datetime.now(timezone.utc) - self.session_start).total_seconds() / 60
        },
        space={
            "project": "persona_orchestration",
            "domain": "AGI_prototype",
            "file_context": [],
            "depth_index": depth_index
        },
        agent={
            "persona_id": persona.identifier,
            "persona_name": persona.name,
            "role": persona.role,
            "backend": persona.backend_id
        },
        emotion={
            "affect_amplitude": phase_meta.get("affect_after", 0.5),
            "sentiment_score": estimate_sentiment(response),
            "confidence": 0.7,
            "keywords": extract_emotion_keywords(response)
        },
        content={
            "type": "persona_response",
            "prompt_digest": textwrap.shorten(prompt, width=500, placeholder="…"),
            "response_full": response,
            "response_summary": None,
            "token_count": len(response.split())  # 간단한 추정
        },
        metadata={
            "importance": 0.5,  # 기본값, 나중에 재계산
            "tags": [persona.identifier, "orchestration"],
            "user_rating": None,
            "phase_injection_applied": phase_meta.get("injection_applied", False),
            "error_occurred": "[error:" in response,
            "bqi_snapshot": bqi_snapshot
        },
        relations={
            "parent_memory_id": self._get_last_memory_id(),
            "child_memory_ids": [],
            "related_memory_ids": []
        }
    )
```

#### (4) ResonanceLedger 인터페이스
```python
class ResonanceLedger:
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self.current_file = base_path / f"ledger-{datetime.now():%Y%m%d}.jsonl"

    def log_event(
        self,
        session_id: str,
        event_type: str,
        persona_id: str,
        memory_id: Optional[str],
        bqi_coordinate: Optional[Dict[str, Any]],
        evaluation: Optional[Dict[str, Any]],
        plan_adjustment: Optional[Dict[str, Any]],
    ) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "event_type": event_type,
            "persona_id": persona_id,
            "memory_id": memory_id,
            "bqi_coordinate": bqi_coordinate,
            "evaluation": evaluation,
            "plan_adjustment": plan_adjustment,
        }
        self._append(entry)

    def _append(self, entry: Dict[str, Any]) -> None:
        self.current_file.parent.mkdir(parents=True, exist_ok=True)
        with self.current_file.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(entry, ensure_ascii=False) + "\n")
```

### 7.2 메모리 활용 예시

#### Few-shot 예제 자동 선택
```python
def compose_prompt_with_memory(
    persona: Persona,
    seed_prompt: str,
    history: List[Dict[str, Any]],
    depth: int,
    step_index: int,
    memory_store: Optional[MemoryStore] = None,
    bqi_snapshot: Optional[Dict[str, Any]] = None
) -> str:
    parts = []

    if persona.system_prompt:
        parts.append(f"System instruction: {persona.system_prompt}")

    # 메모리에서 유사한 과거 사례 검색 (추가)
    if memory_store:
        bqi_filters = None
        if bqi_snapshot:
            bqi_filters = {
                "rhythm_phase": bqi_snapshot.get("rhythm_phase"),
                "emotion": bqi_snapshot.get("emotion", {}).get("keywords"),
            }
        similar_cases = memory_store.search(
            query=seed_prompt[:100],  # 프롬프트 앞부분으로 검색
            persona_id=persona.identifier,
            min_importance=0.6,
            bqi_filters=bqi_filters,
            limit=2
        )

        if similar_cases:
            parts.append("\nRelevant past examples:")
            for case in similar_cases:
                parts.append(f"- Previous input: {case.content.prompt_digest}")
                parts.append(f"  Your response: {case.content.response_summary or case.content.response_full[:200]}")

    # 기존 히스토리
    parts.append(f"Current recursion depth: {depth}")
    parts.append("Conversation history:")
    for entry in history:
        label = entry.get("persona", entry.get("role", "unknown"))
        parts.append(f"- {label}: {entry.get('content', '')}")

    parts.append("")
    parts.append(f"Seed focus: {seed_prompt}")
    parts.append(f"Respond as persona '{persona.name}' ({persona.role}). This is cycle step {step_index}.")

    return "\n".join(parts)
```

---

## 8. 구현 파일 구조

```
scripts/
└── memory/
    ├── __init__.py
    ├── schema.py              # MemoryCoordinate 데이터클래스
    ├── store.py               # MemoryStore 클래스
    ├── indexer.py             # 인덱싱 로직
    ├── search.py              # 검색 알고리즘
    └── retention.py           # 망각/아카이브 정책

configs/
└── memory_config.json         # 보관 정책 설정

tests/
└── test_memory_system.py      # 유닛 테스트
```

---

## 9. 테스트 계획

### 9.1 성공 기준
1. ✅ 메모리 저장: 1000개 메모리 저장 후 index.json 자동 업데이트
2. ✅ 검색 정확도: 키워드 "synthesis" 검색 시 해당 페르소나 메모리만 반환
3. ✅ 망각 동작: max_sessions=5 설정 후 6번째 세션 시작 시 가장 오래된 세션 자동 삭제
4. ✅ 성능: 5000개 메모리에서 검색 < 100ms
5. ✅ 통합: PersonaOrchestrator 실행 시 메모리 자동 저장 및 활용

### 9.2 테스트 시나리오

#### 시나리오 1: 기본 저장 및 조회
```python
store = MemoryStore(base_path="outputs/memory")
memory = MemoryCoordinate(...)
store.add(memory)

retrieved = store.get_by_id(memory.memory_id)
assert retrieved.memory_id == memory.memory_id
```

#### 시나리오 2: 복합 검색
```python
results = store.search(
    query="AGI memory",
    persona_id="synthesis",
    time_range=(datetime(2025, 10, 10), datetime(2025, 10, 12)),
    min_importance=0.5,
    limit=3
)
assert len(results) <= 3
assert all(r.agent.persona_id == "synthesis" for r in results)
```

#### 시나리오 3: 자동 망각
```python
# 설정: max_sessions=3
for i in range(5):
    session_id = f"sess_test_{i}"
    for j in range(10):
        store.add(MemoryCoordinate(..., time={"session_id": session_id, ...}))

store.apply_retention_policy()
remaining_sessions = store.get_all_session_ids()
assert len(remaining_sessions) <= 3
```

---

## 10. 미결정 사항 (Core과 논의 필요)

### 10.1 스토리지 선택
- **JSON/JSONL**: 구현 간단, 디버깅 쉬움, 성능 제한적
- **SQLite**: 쿼리 강력, 파일 기반, 약간 복잡
- **MongoDB**: NoSQL, 유연, 별도 서버 필요

→ **제안**: v1.0은 JSONL, v2.0부터 SQLite

### 10.2 중요도 자동 계산 시점
- **Option A**: 메모리 저장 시 즉시 계산
- **Option B**: 배치 작업으로 주기적 재계산 (참조빈도 반영 위해)

→ **제안**: Option A (저장 시) + Option B (매일 자정 재계산)

### 10.3 사용자 피드백 수집 방법
- CLI에서 실행 후 "이 응답 평가: 1-5 stars" 프롬프트?
- 별도 웹 UI?
- 로그 파일에 수동 기록?

→ **제안**: v1.0은 수동 기록 (log에 `user_rating` 필드 추가), v2.0에서 UI

### 10.4 다중 사용자 지원
- 현재 설계는 단일 사용자 (비노체님) 가정
- 여러 사용자 지원하려면 `user_id` 필드 필요

→ **제안**: v1.0은 단일 사용자, v2.0에서 확장

---

## 11. 다음 단계

1. ✅ 설계 문서 작성 완료 (현재 문서)
2. ⏳ Core과 설계 리뷰 및 미결정 사항 합의
3. ⏳ `scripts/memory/schema.py` 구현
4. ⏳ `scripts/memory/store.py` 구현
5. ⏳ `tests/test_memory_system.py` 작성
6. ⏳ PersonaOrchestrator 통합
7. ⏳ 실전 테스트 (10회 실행 후 검색/망각 동작 확인)

---

## 12. 참고 자료

- 기존 구현: [orchestration/persona_orchestrator.py](../orchestration/persona_orchestrator.py)
- PhaseController 구조: [naeda_langgraph_demo.py](../naeda_langgraph_demo.py)
- 루빛·Core 대화 기록: NotebookLM 참조

---

**검토 요청 사항**:
1. 좌표형 메모리 스키마가 NotebookLM의 "감응 기반 리듬 구조"를 잘 반영했는지?
2. 중요도 계산 공식이 합리적인지?
3. v1.0 스코프가 4주 내 구현 가능한지?
