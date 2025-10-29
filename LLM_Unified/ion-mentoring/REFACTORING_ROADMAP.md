# PersonaOrchestrator 리팩토링 로드맵

ION Mentoring의 핵심 코드 개선 프로젝트

**현재 상태**: 967줄 단일 클래스
**목표 상태**: 8개 전문화된 컴포넌트 (각 60-150줄)
**기간**: 10주
**복잡도 감소**: 40% → 5% (순환 복잡도)

---

## 📊 프로젝트 개요

### 문제점
- **단일 책임 원칙 위반**: 5개 이상의 관심사 혼재
- **테스트 불가**: 전체 구성 필요, 967줄 단일 테스트 진입점
- **유지보수 어려움**: 26개 인스턴스 변수, 20개 메서드
- **확장 어려움**: 새 기능 추가 시 복잡도 증가

### 해결책
**핵심 로직을 8개 전문화된 컴포넌트로 분리**
```
PersonaOrchestrator (Facade, 80줄)
├── OrchestrationEngine (150줄)
├── ValidationCoordinator (100줄)
├── ToolManager (120줄)
├── MemoryCoordinator (60줄)
├── MetricsCollector (150줄)
├── PromptBuilder (60줄)
├── SessionLogger (80줄)
└── ConfigurationManager (70줄)
```

### 기대 효과
- ✅ 테스트 커버리지: 0% → 80%+
- ✅ 순환 복잡도: 40 → 5 (평균)
- ✅ 개발 속도: 30% 향상
- ✅ 버그 수정 시간: 50% 단축

---

## 🗓️ 10주 로드맵

### Week 1-2: 테스트 기반 구축
**목표**: 현재 동작 테스트 커버리지 확보

#### Phase 1.1: 테스트 인프라 (3일)
```python
# tests/orchestration/conftest.py 생성
@pytest.fixture
def persona_registry():
    """Persona 등록 모킹"""
    return PersonaRegistry({
        "thesis": Persona("thesis", "논제", ["logical"]),
        "antithesis": Persona("antithesis", "반테", ["critical"]),
        "synthesis": Persona("synthesis", "종합", ["balanced"]),
    })

@pytest.fixture
def mock_backend_factory():
    """백엔드 팩토리 모킹"""
    factory = MagicMock()
    factory.create_backend.return_value = EchoBackend()
    return factory

@pytest.fixture
def mock_memory_store():
    """메모리 스토어 모킹"""
    store = MagicMock(spec=MemoryStore)
    store.store_response.return_value = "mem-123"
    return store

@pytest.fixture
def orchestrator(persona_registry, mock_backend_factory, mock_memory_store):
    """완전히 모킹된 오케스트레이터"""
    return PersonaOrchestrator(
        registry=persona_registry,
        backend_factory=mock_backend_factory,
        memory_store=mock_memory_store,
        config={"validators": {}, "symmetry": {}},
    )
```

#### Phase 1.2: 통합 테스트 (5일)
```python
# tests/orchestration/test_persona_orchestrator_integration.py

def test_orchestrator_full_cycle_with_echo_backend(orchestrator):
    """단일 순환 테스트 (깊이 1)"""
    result = orchestrator.run("초기 메시지", depth=1)

    assert "final_output" in result
    assert len(result["history"]) >= 1
    assert result["session_summary"]["total_cycles"] >= 1

def test_orchestrator_recursive_depth_2(orchestrator):
    """재귀 깊이 2 테스트"""
    result = orchestrator.run("메시지", depth=2)

    assert result["session_summary"]["max_depth"] == 2
    assert len(result["history"]) >= 3  # 적어도 thesis, antithesis, synthesis

def test_orchestrator_with_validation_retry(orchestrator):
    """검증 재시도 플로우 테스트"""
    orchestrator.config["validators"]["thesis"] = {
        "min_quality": 0.8,
        "required_sources": 2,
    }

    result = orchestrator.run("메시지", depth=1)
    # 재시도가 발생했는지 확인
    assert any("retry" in str(entry).lower() for entry in result["log_entries"])
```

#### Phase 1.3: 유닛 테스트 (4일)
```python
# tests/orchestration/test_persona_orchestrator_unit.py

def test_normalize_citations():
    """인용 정규화 테스트"""
    from orchestration.persona_orchestrator import normalize_citations

    text = "[1] 출처1; [2] 출처2"
    result = normalize_citations("thesis", text)

    assert result.startswith("[T1]")
    assert "[A" not in result

def test_combine_decisions():
    """결정 병합 테스트"""
    from orchestration.persona_orchestrator import combine_decisions

    decisions = {
        "thesis": {"valid": True, "score": 0.9},
        "antithesis": {"valid": False, "score": 0.4},
    }
    result = combine_decisions(decisions)

    assert result["primary"] == "thesis"
    assert result["confidence"] > 0.7

def test_update_fact_metrics():
    """팩트 메트릭 업데이트 테스트"""
    collector = orchestrator.metrics

    collector.update_fact_metrics("검증된 사실1. 검증된 사실2.")

    assert collector.facts_total >= 2
```

**예상 커버리지**: 50%

---

### Week 3-4: 저위험 컴포넌트 추출
**목표**: 3개 컴포넌트 추출 및 배포

#### Phase 3.1: ConfigurationManager 추출 (3일)

```python
# orchestration/config_manager.py
class ConfigurationManager:
    """설정 파싱 및 검증"""

    @staticmethod
    def parse_validators(raw_config: Dict) -> Dict[str, Dict[str, Any]]:
        """검증기 설정 파싱"""
        validators = {}
        for persona_id, config in raw_config.get("validators", {}).items():
            validators[persona_id] = {
                "quality_threshold": config.get("quality_threshold", 0.7),
                "min_sources": config.get("min_sources", 1),
                "review_enabled": config.get("review_enabled", True),
            }
        return validators

    @staticmethod
    def parse_symmetry_thresholds(raw_config: Dict) -> Dict[int, Tuple[float, float]]:
        """대칭성 임계값 파싱"""
        thresholds = {}
        for depth_str, values in raw_config.get("symmetry_thresholds", {}).items():
            depth = int(depth_str)
            thresholds[depth] = (values[0], values[1])
        return thresholds

    @staticmethod
    def parse_retry_limits(raw_config: Dict) -> Dict[str, int]:
        """재시도 제한 파싱"""
        return raw_config.get("retry_limits", {
            "validation_retry": 2,
            "tool_retry": 1,
            "backend_retry": 3,
        })
```

**변경 사항**:
```python
# PersonaOrchestrator.__init__() 수정
config_mgr = ConfigurationManager()
self.validator_config = config_mgr.parse_validators(config or {})
self.symmetry_thresholds = config_mgr.parse_symmetry_thresholds(config or {})
self.retry_limits = config_mgr.parse_retry_limits(config or {})
```

#### Phase 3.2: PromptBuilder 추출 (3일)

```python
# orchestration/prompt_builder.py
class PromptBuilder:
    """프롬프트 조성 전문가"""

    def compose_prompt(
        self,
        persona: Persona,
        seed_prompt: str,
        history: List[Dict[str, Any]],
        depth: int,
        step_index: int,
    ) -> str:
        """완전한 프롬프트 조성"""
        parts = [
            f"# {persona.name} 페르소나",
            f"특징: {', '.join(persona.traits)}",
            f"\n## 입력",
            f"{seed_prompt}",
        ]

        if history:
            parts.append(f"\n## 이전 응답들 ({len(history)}개)")
            for entry in history[-3:]:  # 최근 3개만
                parts.append(f"- {entry['persona']}: {entry['summary']}")

        parts.append(f"\n## 지시사항")
        parts.append(f"깊이: {depth}, 단계: {step_index}")
        parts.append(f"논리적이고 일관성 있는 응답을 제공하세요.")

        return "\n".join(parts)

    def augment_with_feedback(self, base_prompt: str, feedback: List[str]) -> str:
        """피드백으로 프롬프트 증강"""
        if not feedback:
            return base_prompt

        feedback_section = "## 이전 피드백\n"
        for fb in feedback:
            feedback_section += f"- {fb}\n"

        return base_prompt + "\n" + feedback_section
```

#### Phase 3.3: SessionLogger 추출 (2일)

```python
# orchestration/session_logger.py
class SessionLogger:
    """세션 로깅 및 추적"""

    def __init__(self, log_path: Optional[Path] = None):
        self.log_entries = []
        self.log_path = log_path

    def log_turn(
        self,
        depth_index: int,
        step_index: int,
        persona_id: str,
        prompt_digest: str,
        response: str,
        evaluation: Dict[str, Any],
    ) -> None:
        """턴 로깅"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "depth": depth_index,
            "step": step_index,
            "persona": persona_id,
            "prompt_hash": prompt_digest[:10],
            "response_length": len(response),
            "evaluation": evaluation,
        }
        self.log_entries.append(entry)

    def write_session(self, session_id: str) -> None:
        """세션 파일에 저장"""
        if not self.log_path:
            return

        file_path = self.log_path / f"session_{session_id}.json"
        with open(file_path, 'w') as f:
            json.dump(self.log_entries, f, indent=2, ensure_ascii=False)
```

**테스트**:
```python
# tests/orchestration/test_config_manager.py
def test_parse_validators():
    config = {
        "validators": {
            "thesis": {"quality_threshold": 0.8}
        }
    }
    result = ConfigurationManager.parse_validators(config)
    assert result["thesis"]["quality_threshold"] == 0.8

# tests/orchestration/test_prompt_builder.py
def test_compose_prompt_includes_history():
    builder = PromptBuilder()
    persona = Persona("thesis", "논제", [])
    history = [{"persona": "seed", "summary": "요약"}]

    prompt = builder.compose_prompt(persona, "초기", history, depth=1, step=1)
    assert "이전 응답" in prompt
    assert "요약" in prompt

# tests/orchestration/test_session_logger.py
def test_log_turn_records_entry():
    logger = SessionLogger()
    logger.log_turn(1, 1, "thesis", "abc123", "응답", {"score": 0.9})

    assert len(logger.log_entries) == 1
    assert logger.log_entries[0]["persona"] == "thesis"
```

**배포**:
```bash
# Dev 환경에서 테스트
git checkout -b feature/extract-config-prompt-logger
# 코드 변경
pytest tests/orchestration/ -v
# 통과 시 PR 생성
```

**예상 커버리지**: 60%

---

### Week 5-6: 중간위험 컴포넌트 추출
**목표**: 2개 컴포넌트 추출 및 스테이징 배포

#### Phase 5.1: ToolManager 추출 (4일)

```python
# orchestration/tool_manager.py
class ToolManager:
    """도구 실행 관리 (RAG, 외부 API)"""

    def __init__(self, rag_engine: Optional[Any] = None):
        self.rag_engine = rag_engine
        self.allowed_doc_ids = {}

    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        persona_id: str,
    ) -> Dict[str, Any]:
        """도구 실행 라우팅"""
        if tool_name == "rag_search":
            return self.handle_rag_search(
                parameters.get("query", ""),
                persona_id,
                parameters.get("top_k", 3),
            )
        elif tool_name == "verify_fact":
            return self.verify_fact(parameters.get("fact", ""))
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def handle_rag_search(
        self,
        query: str,
        persona_id: str,
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """RAG 검색 실행"""
        if not self.rag_engine:
            return {"error": "RAG engine not available", "results": []}

        results = self.rag_engine.search(query, top_k=top_k)

        # 인용 정규화
        normalized = []
        for i, result in enumerate(results, 1):
            normalized.append({
                "rank": i,
                "text": result["text"][:500],
                "source": f"[{persona_id[0].upper()}{i}]",
                "score": result.get("score", 0.0),
            })

        return {"results": normalized, "query": query}

    def normalize_citations(
        self,
        persona_id: str,
        text: str,
    ) -> str:
        """인용 정규화 ([1] → [T1])"""
        persona_prefix = persona_id[0].upper()

        def replace_citation(match):
            num = match.group(1)
            return f"[{persona_prefix}{num}]"

        return re.sub(r"\[(\d+)\]", replace_citation, text)
```

#### Phase 5.2: MemoryCoordinator 추출 (3일)

```python
# orchestration/memory_coordinator.py
class MemoryCoordinator:
    """메모리 저장소 및 좌표계 관리"""

    def __init__(
        self,
        memory_store: Optional[Any] = None,
        resonance_ledger: Optional[Any] = None,
    ):
        self.memory_store = memory_store
        self.resonance_ledger = resonance_ledger
        self._last_memory_id = None

    def store_response(
        self,
        persona_id: str,
        prompt: str,
        response: str,
        evaluation: Dict[str, Any],
        session_id: str,
    ) -> Optional[str]:
        """응답 저장"""
        if not self.memory_store:
            return None

        memory_id = self.memory_store.store({
            "persona": persona_id,
            "prompt_hash": hashlib.md5(prompt.encode()).hexdigest(),
            "response": response,
            "evaluation": evaluation,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
        })

        self._last_memory_id = memory_id
        return memory_id

    def log_resonance_event(
        self,
        session_id: str,
        event_type: str,
        persona_id: str,
        memory_id: Optional[str],
        evaluation: Dict[str, Any],
    ) -> None:
        """공명 원장에 이벤트 기록"""
        if not self.resonance_ledger:
            return

        self.resonance_ledger.record({
            "session_id": session_id,
            "event_type": event_type,
            "persona": persona_id,
            "memory_id": memory_id,
            "timestamp": datetime.now().isoformat(),
            "evaluation": evaluation,
        })
```

**테스트 및 배포**: Week 5-6 스테이징 환경에 배포

**예상 커버리지**: 70%

---

### Week 7-8: 고위험 컴포넌트 추출
**목표**: 2개 컴포넌트 추출, A/B 테스트

#### Phase 7.1: ValidationCoordinator 추출
#### Phase 7.2: MetricsCollector 추출

**A/B 테스트 설정**:
```python
# feature flag 추가
USE_NEW_VALIDATION = os.getenv("USE_NEW_VALIDATION", "false") == "true"

if USE_NEW_VALIDATION:
    from orchestration.validation_coordinator_v2 import ValidationCoordinator
else:
    from orchestration.validation_coordinator import ValidationCoordinator
```

**예상 커버리지**: 80%

---

### Week 9-10: 핵심 엔진 및 배포
**목표**: OrchestrationEngine 추출, 프로덕션 배포

#### Phase 9.1: OrchestrationEngine 추출 (4일)

```python
# orchestration/engine.py
class OrchestrationEngine:
    """핵심 오케스트레이션 엔진"""

    def run_recursive(
        self,
        seed_prompt: str,
        depth: int,
        depth_index: int,
        context: "OrchestrationContext",
    ) -> str:
        """재귀적 오케스트레이션 실행"""
        # 이 메서드는 _run_recursive의 최적화된 버전
        pass
```

#### Phase 9.2: Facade 업데이트 및 배포 (3일)

```python
# orchestration/persona_orchestrator.py (리팩토링 후)
class PersonaOrchestrator:
    """파사드 - 모든 컴포넌트를 조율"""

    def __init__(self, ...):
        self.engine = OrchestrationEngine(...)
        self.validator = ValidationCoordinator(...)
        self.tools = ToolManager(...)
        self.memory = MemoryCoordinator(...)
        self.metrics = MetricsCollector(...)
        self.prompts = PromptBuilder()
        self.logger = SessionLogger(...)

    def run(self, seed_prompt: str, depth: int = 1) -> Dict[str, Any]:
        """메인 엔트리포인트"""
        context = OrchestrationContext(
            validator=self.validator,
            tools=self.tools,
            memory=self.memory,
            metrics=self.metrics,
            prompts=self.prompts,
            logger=self.logger,
        )

        result = self.engine.run_recursive(
            seed_prompt, depth, 1, context
        )

        return {
            "final_output": result,
            "history": self.engine.history,
            "log_entries": self.logger.log_entries,
        }
```

**프로덕션 배포 전략**:
```yaml
Week 9:  10% 트래픽 → 모니터링
         선택 사항: Feature flag 사용

Week 10 (Day 1-3): 50% 트래픽 → 메트릭 검증
                    - 검증 정확도 확인
                    - 응답 시간 비교
                    - 에러율 모니터링

Week 10 (Day 4-7): 100% 트래픽 → 완전 이전
                    - 구 구현 아카이브
                    - 기능 플래그 제거
                    - 문서 업데이트
```

**최종 커버리지**: 85%+

---

## 📈 성공 지표

| 지표 | 현재 | 목표 | 개선도 |
|------|------|------|--------|
| 테스트 커버리지 | 0% | 85% | ∞ |
| 순환 복잡도 (평균) | 40 | 5 | 8배 |
| 최대 메서드 길이 | 275줄 | 60줄 | 4.6배 |
| 클래스 크기 (평균) | 967줄 | 100줄 | 9.7배 |
| 개발 시간 | - | -30% | 개선 |
| 버그 수정 시간 | - | -50% | 개선 |

---

## 🛡️ 롤백 계획

```python
# Feature flag 방식
if os.getenv("USE_REFACTORED", "false") == "true":
    from orchestration.persona_orchestrator_v2 import PersonaOrchestrator
else:
    from orchestration.persona_orchestrator import PersonaOrchestrator

# 환경 변수만 변경하면 즉시 롤백 가능
os.environ["USE_REFACTORED"] = "false"  # 롤백
```

---

## 📚 참고 문서

- **현재 구현**: `d:\nas_backup\orchestration\persona_orchestrator.py`
- **검증기**: `d:\nas_backup\orchestration\validators.py`
- **테스트 가이드**: 추가 예정 (`tests/orchestration/README.md`)

---

**리팩토링 준비 완료 - GO 승인** ✅
