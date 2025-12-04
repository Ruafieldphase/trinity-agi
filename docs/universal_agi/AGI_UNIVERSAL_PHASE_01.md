# Phase 1: Domain-Agnostic Task Representation

**작성일**: 2025-10-30  
**상태**: ✅ 완료 (Sections 1-6)  
**목표**: 현재 특화된 AGI를 범용적으로 만드는 첫 번째 단계

---

## 📋 목차

1. [개요](#개요)
2. [현재 시스템 분석](#현재-시스템-분석)
3. [Universal Task Schema](#universal-task-schema)
4. [Domain Adapter Framework](#domain-adapter-framework)
5. [Resonance Scoring Generalization](#resonance-scoring-generalization)
6. [Orchestrator Integration](#6-orchestrator-integration)
7. [구현 코드](#구현-코드)
8. [테스트 전략](#테스트-전략)
9. [성공 기준](#성공-기준)
10. [자동 실행 명령어](#자동-실행-명령어)

---

## 개요

### 문제 정의

현재 AGI는 **특정 도메인에 특화**되어 있습니다:

```python
# 현재 시스템 (도메인 특화)
task = {
    "type": "code_review",           # 하드코딩된 타입
    "language": "python",            # 특정 언어
    "files": ["main.py"],           # 파일 기반
    "context": "github_pr"          # GitHub 전용
}

# 다른 도메인으로 전환 불가
task = {
    "type": "medical_diagnosis",     # ❌ 지원 안됨
    "data": "patient_symptoms",      # ❌ 구조 다름
    "context": "hospital_system"     # ❌ 연동 없음
}
```

### 목표

**Universal Task Schema**로 모든 도메인 표현:

```python
# Universal Task (도메인 독립적)
task = UniversalTask(
    intent="analyze_and_suggest",           # 추상적 의도
    domain=Domain("software_engineering"),  # 메타데이터로 분리
    input_data=UniversalData(...),         # 범용 데이터 구조
    constraints=UniversalConstraints(...),  # 범용 제약조건
    success_criteria=UniversalCriteria(...) # 범용 성공 기준
)

# 동일한 구조로 모든 도메인 표현 가능
task_medical = UniversalTask(
    intent="analyze_and_suggest",
    domain=Domain("healthcare"),
    input_data=UniversalData(...),
    # ... 동일한 구조
)
```

### 핵심 원칙

1. **Domain-Agnostic**: 도메인 지식은 메타데이터, 핵심 구조는 동일
2. **Composable**: 작은 컴포넌트 조합으로 복잡한 태스크 표현
3. **Extensible**: 새 도메인 추가 시 기존 구조 변경 없음
4. **Resonance-Based**: 기존 Resonance 메커니즘 유지 & 확장

---

## 현재 시스템 분석

### 기존 TaskSpec (contracts.py)

```python
# fdo_agi_repo/orchestrator/contracts.py (현재)
class TaskSpec(BaseModel):
    task_id: str
    title: str
    goal: str
    constraints: List[str] = []
    inputs: Dict[str, Any] = {}
    scope: Literal["doc", "code", "analysis"] = "doc"  # ⚠️ 도메인 특화
    permissions: List[Literal["READ","WRITE","WEB","EXEC"]] = ["READ"]
    evidence_required: bool = True
```

**문제점**:

- `scope`가 3가지로 제한 → 새 도메인 추가 불가
- `goal`이 자유 형식 텍스트 → 구조적 추론 어려움  
- 도메인 특화 지식이 스키마에 하드코딩됨

### 기존 Task Queue (shared_task_queue.py)

```python
# fdo_agi_repo/orchestrator/shared_task_queue.py (현재)
@dataclass
class Task:
    id: str
    type: str  # ⚠️ 자유 형식
    requester: str
    data: Dict[str, Any]  # ⚠️ 구조 없음
    status: str
    created_at: datetime
    assigned_to: Optional[str] = None
    updated_at: Optional[datetime] = None
```

**문제점**:

- `type`이 검증 없는 문자열
- `data`가 비구조적 딕셔너리
- 도메인 정보 표현 방법 없음

### 현재 vs. Universal 비교

| 항목 | 현재 | Universal (목표) |
|------|------|---------|
| 도메인 | 하드코딩 (`scope="code"`) | 메타데이터 (`domain_id="software_engineering"`) |
| 의도 | 자유 텍스트 (`goal="Review code"`) | 열거형 (`intent=AbstractIntent.ANALYZE`) |
| 입력 | 비구조적 (`inputs: Dict`) | 타입화 (`inputs: List[UniversalData]`) |
| 제약 | 텍스트 리스트 (`constraints: List[str]`) | 구조화 (`UniversalConstraint`) |
| 성공 기준 | 없음 | 명시적 (`UniversalCriteria`) |
| 확장성 | 코드 수정 필요 | 메타데이터만 추가 |

---

## Universal Task Schema

### 설계 철학

Task를 **3개 레이어**로 분리:

```text
┌──────────────────────────────────┐
│  Abstract Intent Layer           │ ← 도메인 독립적 의도
│  (analyze, create, optimize...)  │
├──────────────────────────────────┤
│  Universal Representation        │ ← 범용 데이터 구조
│  (inputs, constraints, criteria) │
├──────────────────────────────────┤
│  Domain Metadata Layer           │ ← 도메인 특화 정보
│  (ontology, tools, knowledge)    │
└──────────────────────────────────┘
```

### UniversalTask 스키마

```python
# fdo_agi_repo/universal/task_schema.py

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AbstractIntent(str, Enum):
    """도메인 독립적 의도"""
    ANALYZE = "analyze"
    CREATE = "create"
    OPTIMIZE = "optimize"
    TRANSFORM = "transform"
    VALIDATE = "validate"
    DIAGNOSE = "diagnose"
    PREDICT = "predict"
    REASON = "reason"
    COMPOSE = "compose"
    EXPLAIN = "explain"


class DataType(str, Enum):
    """범용 데이터 타입"""
    TEXT = "text"
    CODE = "code"
    STRUCTURED = "structured"
    TABULAR = "tabular"
    BINARY = "binary"
    GRAPH = "graph"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    MULTIMEDIA = "multimedia"


class UniversalData(BaseModel):
    """도메인 독립적 데이터 표현"""
    data_type: DataType
    content: Any
    data_schema: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}

    class Config:
        arbitrary_types_allowed = True


class UniversalConstraint(BaseModel):
    """범용 제약조건"""
    type: str  # "time", "resource", "quality", "safety", etc.
    value: Any
    priority: float = Field(ge=0.0, le=1.0, default=0.5)
    negotiable: bool = True


class UniversalCriteria(BaseModel):
    """범용 성공 기준"""
    metric: str
    threshold: float
    weight: float = 1.0
    measurement_method: str


class DomainMetadata(BaseModel):
    """도메인 특화 메타데이터"""
    domain_id: str
    subdomain: Optional[str] = None
    ontology: Dict[str, Any] = {}
    tools: List[str] = []
    knowledge_base: Optional[str] = None


class TaskRelation(BaseModel):
    """Task 간 관계"""
    relation_type: str  # "depends_on", "parallel_with", "child_of" 등
    related_task_id: str
    strength: float = Field(ge=0.0, le=1.0, default=0.5)


class UniversalTask(BaseModel):
    """범용 Task 표현"""

    # 기본 정보
    task_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Abstract Intent Layer
    intent: AbstractIntent
    intent_description: str

    # Universal Representation Layer
    inputs: List[UniversalData]
    outputs_expected: List[DataType]
    constraints: List[UniversalConstraint] = []
    success_criteria: List[UniversalCriteria] = []

    # Domain Metadata Layer
    domain: DomainMetadata

    # Task 관계
    relations: List[TaskRelation] = []

    # Execution 정보
    status: str = "pending"
    assigned_to: Optional[str] = None
    resonance_key: Optional[str] = None

    # 결과 (완료 후)
    outputs_actual: List[UniversalData] = []
    performance_metrics: Dict[str, float] = {}


# === 편의 함수 ===

def create_simple_task(
    intent: AbstractIntent,
    description: str,
    input_text: str,
    domain_id: str = "general"
) -> UniversalTask:
    """간단한 Task 생성 헬퍼"""
    return UniversalTask(
        task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        created_at=datetime.now(),
        intent=intent,
        intent_description=description,
        inputs=[UniversalData(data_type=DataType.TEXT, content=input_text)],
        outputs_expected=[DataType.TEXT],
        domain=DomainMetadata(domain_id=domain_id)
    )
```

### 사용 예시

#### 예시 1: 코드 리뷰 (Software Engineering)

```python
from datetime import datetime
from fdo_agi_repo.universal.task_schema import (
    UniversalTask, UniversalData, DomainMetadata,
    UniversalConstraint, UniversalCriteria,
    DataType, AbstractIntent
)

code_review_task = UniversalTask(
    task_id="task_20251030_150000",
    created_at=datetime.now(),
    intent=AbstractIntent.ANALYZE,
    intent_description="Analyze Python code for quality and suggest improvements",
    inputs=[
        UniversalData(
            data_type=DataType.CODE,
            content=open("main.py", encoding="utf-8").read(),
            metadata={"language": "python", "file_path": "main.py"}
        )
    ],
    outputs_expected=[DataType.STRUCTURED, DataType.TEXT],
    constraints=[
        UniversalConstraint(type="time", value="5 minutes", priority=0.7),
        UniversalConstraint(type="quality", value="high", priority=0.9)
    ],
    success_criteria=[
        UniversalCriteria(metric="completeness", threshold=0.9, measurement_method="checklist"),
        UniversalCriteria(metric="actionability", threshold=0.8, measurement_method="human_review")
    ],
    domain=DomainMetadata(
        domain_id="software_engineering",
        subdomain="code_quality",
        tools=["pylint", "mypy", "black"],
        knowledge_base="python_best_practices_kb"
    )
)
```

#### 예시 2: 의료 진단 (Healthcare)

```python
from datetime import datetime
from fdo_agi_repo.universal.task_schema import *

diagnosis_task = UniversalTask(
    task_id="task_20251030_150100",
    created_at=datetime.now(),
    intent=AbstractIntent.DIAGNOSE,
    intent_description="Diagnose patient condition based on symptoms and labs",
    inputs=[
            UniversalData(
            data_type=DataType.STRUCTURED,
            content={
                "patient_id": "P12345",
                "symptoms": ["fever", "cough", "fatigue"],
                "vital_signs": {"temperature": 38.5, "pulse": 92},
                "lab_results": {"CRP": 12.4}
            },
            data_schema={"type": "patient_record_v1"}
        )
    ],
    outputs_expected=[DataType.STRUCTURED],
    constraints=[
        UniversalConstraint(type="safety", value="high_risk_priority", priority=1.0, negotiable=False),
        UniversalConstraint(type="time", value="30 minutes", priority=0.8)
    ],
    success_criteria=[
        UniversalCriteria(metric="accuracy", threshold=0.95, measurement_method="clinical_validation"),
        UniversalCriteria(metric="explainability", threshold=0.9, measurement_method="staff_review")
    ],
    domain=DomainMetadata(
        domain_id="healthcare",
        subdomain="internal_medicine",
        tools=["medical_kb", "rules_engine"],
        knowledge_base="medical_conditions_db",
        ontology={"terminology": "SNOMED_CT", "coding": "ICD-10"}
    )
)
```

#### 예시 3: 금융 분석 (Finance)

```python
from datetime import datetime
from fdo_agi_repo.universal.task_schema import *

financial_analysis_task = UniversalTask(
    task_id="task_20251030_150200",
    created_at=datetime.now(),
    intent=AbstractIntent.PREDICT,
    intent_description="Predict stock price movement for next quarter",
    inputs=[
        UniversalData(
            data_type=DataType.TEMPORAL,
            content=[["2025-01-01", 182.3], ["2025-01-02", 183.2]],
            metadata={"ticker": "AAPL", "frequency": "daily"}
        )
    ],
    outputs_expected=[DataType.STRUCTURED, DataType.GRAPH],
    constraints=[
        UniversalConstraint(type="regulatory_compliance", value="SEC_rules", priority=1.0, negotiable=False)
    ],
    success_criteria=[
        UniversalCriteria(metric="prediction_accuracy", threshold=0.75, measurement_method="backtesting")
    ],
    domain=DomainMetadata(domain_id="finance", subdomain="equity_analysis", tools=["quantlib", "ta_lib"])
)
```

### 핵심 특징 요약

- 동일 구조: 다양한 도메인이 같은 UniversalTask 구조로 표현
- 추상 의도: 의도는 동일, 구현은 어댑터에서 분리
- 범용 제약: time/quality/safety 등 공통 제약조건 모델링
- 명시 기준: metric/threshold/measurement로 비교·평가 용이

---

## Domain Adapter Framework

### 개념

UniversalTask(추상) → DomainAdapter(변환/실행) → 도메인별 실행

```text
UniversalTask (추상)
       ↓
  DomainAdapter
       ↓
Domain-Specific Execution (구체)
```

### 설계 및 예시

```python
# fdo_agi_repo/universal/domain_adapter.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .task_schema import UniversalTask, UniversalData, DataType


class DomainAdapter(ABC):
    """도메인 어댑터 기반 클래스"""

    def __init__(self, domain_id: str):
        self.domain_id = domain_id
        self.capabilities = self._register_capabilities()

    @abstractmethod
    def _register_capabilities(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def validate_task(self, task: UniversalTask) -> tuple[bool, List[str]]:
        pass

    @abstractmethod
    def transform_input(self, universal_data: UniversalData) -> Any:
        pass

    @abstractmethod
    def execute(self, task: UniversalTask) -> Dict[str, Any]:
        pass

    @abstractmethod
    def transform_output(self, domain_output: Any, expected_type: DataType):
        pass

    def can_handle(self, task: UniversalTask) -> bool:
        return task.domain.domain_id == self.domain_id


class SoftwareEngineeringAdapter(DomainAdapter):
    """소프트웨어 엔지니어링 어댑터 (예시)"""

    def __init__(self):
        super().__init__("software_engineering")

    def _register_capabilities(self) -> Dict[str, Any]:
        return {
            "supported_intents": ["analyze", "create", "transform", "validate"],
            "supported_languages": ["python", "javascript", "typescript", "java"],
        }

    def validate_task(self, task: UniversalTask) -> tuple[bool, List[str]]:
        errors: List[str] = []
        if task.intent.value not in self.capabilities["supported_intents"]:
            errors.append(f"Unsupported intent: {task.intent}")
        for inp in task.inputs:
            if inp.data_type not in (DataType.CODE, DataType.TEXT):
                errors.append(f"Unsupported data type: {inp.data_type}")
        return (len(errors) == 0, errors)

    def transform_input(self, universal_data: UniversalData) -> Any:
        return universal_data.content

    def execute(self, task: UniversalTask) -> Dict[str, Any]:
        valid, errors = self.validate_task(task)
        if not valid:
            return {"status": "error", "errors": errors}
        return {"status": "success", "results": [{"message": "analysis_complete"}]}

    def transform_output(self, domain_output: Any, expected_type: DataType):
        from .task_schema import UniversalData
        if expected_type == DataType.TEXT:
            return UniversalData(data_type=DataType.TEXT, content=str(domain_output))
        return UniversalData(data_type=DataType.STRUCTURED, content=domain_output)


class AdapterRegistry:
    def __init__(self):
        self.adapters: Dict[str, DomainAdapter] = {}
        self.register(SoftwareEngineeringAdapter())
        # 추가 예시 어댑터 등록
        self.register(HealthcareAdapter())
        self.register(FinanceAdapter())

    def register(self, adapter: DomainAdapter):
        self.adapters[adapter.domain_id] = adapter

    def get_adapter(self, domain_id: str) -> Optional[DomainAdapter]:
        return self.adapters.get(domain_id)

    def find_suitable_adapter(self, task: UniversalTask) -> Optional[DomainAdapter]:
        adapter = self.get_adapter(task.domain.domain_id)
        if adapter and adapter.can_handle(task):
            return adapter
        return None


class UniversalTaskExecutor:
    def __init__(self):
        self.registry = AdapterRegistry()

    def execute(self, task: UniversalTask) -> Dict[str, Any]:
        adapter = self.registry.find_suitable_adapter(task)
        if not adapter:
            return {"status": "error", "message": f"No adapter for {task.domain.domain_id}"}
        valid, errors = adapter.validate_task(task)
        if not valid:
            return {"status": "error", "validation_errors": errors}
        result = adapter.execute(task)
        if result.get("status") == "success":
            result["universal_outputs"] = [
                adapter.transform_output(result, t) for t in task.outputs_expected
            ]
        return result


# 추가 어댑터 예시 (요약)
class HealthcareAdapter(DomainAdapter):
    def __init__(self):
        super().__init__("healthcare")
    def _register_capabilities(self) -> Dict[str, Any]:
        return {"supported_intents": ["analyze", "explain", "validate", "transform"]}
    def validate_task(self, task: UniversalTask) -> tuple[bool, List[str]]:
        return True, []
    def transform_input(self, universal_data: UniversalData) -> Any:
        return universal_data.content
    def execute(self, task: UniversalTask) -> Dict[str, Any]:
        return {"status": "success", "results": [{"domain": "healthcare"}]}
    def transform_output(self, domain_output: Any, expected_type: DataType):
        from .task_schema import UniversalData
        return UniversalData(data_type=expected_type, content=domain_output)


class FinanceAdapter(DomainAdapter):
    def __init__(self):
        super().__init__("finance")
    def _register_capabilities(self) -> Dict[str, Any]:
        return {"supported_intents": ["analyze", "predict", "validate"]}
    def validate_task(self, task: UniversalTask) -> tuple[bool, List[str]]:
        return True, []
    def transform_input(self, universal_data: UniversalData) -> Any:
        return universal_data.content
    def execute(self, task: UniversalTask) -> Dict[str, Any]:
        return {"status": "success", "results": [{"domain": "finance"}]}
    def transform_output(self, domain_output: Any, expected_type: DataType):
        from .task_schema import UniversalData
        return UniversalData(data_type=expected_type, content=domain_output)
```

### 빠른 사용 예시 (Resonance)

```python
from fdo_agi_repo.universal.task_schema import *
from fdo_agi_repo.universal.domain_adapter import UniversalTaskExecutor
from datetime import datetime

task = UniversalTask(
    task_id="task_demo",
    created_at=datetime.now(),
    intent=AbstractIntent.ANALYZE,
    intent_description="Quick code check",
    inputs=[UniversalData(data_type=DataType.TEXT, content="# simple code ")],
    outputs_expected=[DataType.TEXT],
    domain=DomainMetadata(domain_id="software_engineering")
)

executor = UniversalTaskExecutor()
print(executor.execute(task))
```

#### 추가 예시: Healthcare/Finance 도메인 실행

```python
from fdo_agi_repo.universal.task_schema import *
from fdo_agi_repo.universal.domain_adapter import UniversalTaskExecutor
from datetime import datetime

executor = UniversalTaskExecutor()

# Healthcare
task_h = UniversalTask(
    task_id="task_health",
    created_at=datetime.now(),
    intent=AbstractIntent.EXPLAIN,
    intent_description="Explain symptoms",
    inputs=[UniversalData(data_type=DataType.TEXT, content="fever, cough")],
    outputs_expected=[DataType.TEXT],
    domain=DomainMetadata(domain_id="healthcare"),
)
print(executor.execute(task_h))

# Finance
task_f = UniversalTask(
    task_id="task_fin",
    created_at=datetime.now(),
    intent=AbstractIntent.ANALYZE,
    intent_description="Analyze stock trend",
    inputs=[UniversalData(data_type=DataType.TEXT, content="AAPL daily prices...")],
    outputs_expected=[DataType.TEXT],
    domain=DomainMetadata(domain_id="finance"),
)
print(executor.execute(task_f))
```

---

## Resonance Scoring Generalization

도메인 표준화된 `domain_id`와 `intent`를 결합해, 실행/평가 결과를 공통 포맷으로 수집·축적하고 교차 도메인 비교가 가능하도록 합니다.

### 공진 키 규칙

- 공식: `resonance_key = "{domain_id}:{intent}[:{subdomain}]"`
- 예시:
  - `software_engineering:analyze`
  - `healthcare:explain:internal_medicine`

구현:

```python
# fdo_agi_repo/universal/resonance.py
from typing import List

def derive_resonance_key(task: UniversalTask) -> str:
    parts: List[str] = [task.domain.domain_id, task.intent.value]
    if task.domain.subdomain:
        parts.append(task.domain.subdomain)
    return ":".join(parts)
```

### 이벤트 스키마 (Pydantic)

```python
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict, Any

class ResonanceEvent(BaseModel):
    task_id: str
    resonance_key: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: Dict[str, float] = Field(default_factory=dict)  # 예: {"quality": 0.92, "latency_ms": 1200}
    tags: Dict[str, Any] = Field(default_factory=dict)       # 임의의 부가정보
```

권장 메트릭 택소노미(초안):

- quality 계열: `accuracy`, `completeness`, `actionability`, `explainability`
- time 계열: `latency_ms`, `time_to_first_token_ms`, `wall_time_ms`
- stability 계열: `variance`, `flakiness_rate`, `cache_hit_rate`
- transfer 계열: `cross_domain_success`, `few_shot_gain`, `adapter_efficiency`

### 저장소(JSONL) 설계

- 파일 기반 JSONL로 간단히 시작하고, 이후 DB/Vector Store로 확장 가능
- 가장 최근 이벤트 조회를 위한 `latest()` 제공

```python
from pathlib import Path
import json

class ResonanceStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: ResonanceEvent):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json())
            f.write("\n")

    def latest(self) -> Optional[ResonanceEvent]:
        # 파일의 마지막 유효 라인을 읽어 복원
        ...
```

예시 JSONL 라인:

```json
{"task_id":"t1","resonance_key":"software_engineering:analyze","timestamp":"2025-10-30T06:10:23.123Z","metrics":{"quality":0.93,"latency_ms":820},"tags":{"model":"gpt-4.1-mini"}}
```

### 빠른 사용 예시

```python
from fdo_agi_repo.universal.task_schema import create_simple_task, AbstractIntent
from fdo_agi_repo.universal.resonance import derive_resonance_key, ResonanceEvent, ResonanceStore

task = create_simple_task(
    intent=AbstractIntent.ANALYZE,
    description="demo",
    input_text="print('hi')",
    domain_id="software_engineering",
)

key = derive_resonance_key(task)
store = ResonanceStore(Path("outputs/resonance_events.jsonl"))
store.append(ResonanceEvent(task_id=task.task_id, resonance_key=key, metrics={"quality": 0.9}))
print(store.latest())
```

### 테스트

- `fdo_agi_repo/tests/test_resonance.py`
  - 키 파생 규칙 검증
  - JSONL 저장소 append/latest 라운드트립 검증

이 레이어는 UniversalTask 위에서 동작하므로, 어떤 도메인/어댑터를 거치든 공통 키와 공통 메트릭 집합으로 집계가 가능합니다.

---

## 6. Orchestrator Integration

### 배경 (Orchestrator)

기존 오케스트레이터 파이프라인(`fdo_agi_repo/orchestrator/pipeline.py`)은 Universal Resonance 시스템과 독립적으로 동작:

- `TaskSpec` 기반 실행 (domain-specific 스코프: "doc", "code", "analysis")
- `EvalReport` 평가 지표 (quality, evidence_ok)
- `BQI` 좌표 (binoche, quality, intent, rhythm_phase)
- **Resonance 기록 없음** → 교차 도메인 메트릭 집계 불가

### 설계

**Orchestrator Resonance Bridge**를 통해 기존 파이프라인을 Universal Resonance에 연결:

```text
┌──────────────────────────────────────────────────┐
│ Orchestrator Pipeline (pipeline.py)              │
│   TaskSpec → BQI → Persona(thesis/anti/synth)    │
│            ↓                                      │
│   EVAL → EvalReport (quality, evidence_ok)       │
│            ↓                                      │
│   record_task_resonance(...)  ← resonance_bridge │
│            ↓                                      │
│   ResonanceStore.append() → JSONL                │
└──────────────────────────────────────────────────┘
```

### 구현 (Orchestrator Bridge)

#### resonance_bridge.py

- `init_resonance_store(path)`: 전역 저장소 초기화
- `record_task_resonance(task_id, task_goal, eval_report, bqi_coord, duration_sec)`:
  - `eval_report` → `metrics.quality`, `metrics.evidence`
  - `bqi_coord` → `tags.bqi_binoche`, `tags.bqi_quality`, `tags.bqi_intent`
  - BQI 기반 subdomain 추론 (binoche > 0.7 → "binoche_high")
  - `resonance_key`: `"orchestrator:reason[:subdomain]"`

#### pipeline.py 수정

- `t_start = time.perf_counter()` 추가 (run_task 시작 시점)
- 두 개의 완료 경로 모두에서 `record_task_resonance()` 호출:
  1. Auto-approve path (`binoche_auto_approved`)
  2. Normal completion path (`task_end`)
- `task_duration = time.perf_counter() - t_start` 계산
- 예외 발생 시 silent fallback (저장소 미초기화 허용)

#### 메트릭 매핑

| Orchestrator 지표 | Resonance 메트릭 | 설명 |
|----------|----------|------|
| `eval_report.quality` | `metrics.quality` | 직접 매핑 (0.0-1.0) |
| `eval_report.evidence_ok` | `metrics.evidence` | bool → float (1.0/0.0) |
| execution duration | `metrics.latency_ms` | ✅ `time.perf_counter()` 계측 완료 |
| `bqi_coord.binoche` | `tags.bqi_binoche` | BQI 좌표 기록 |
| `bqi_coord.quality` | `tags.bqi_quality` | |
| `bqi_coord.intent` | `tags.bqi_intent` | |

### 검증 (Orchestrator)

`fdo_agi_repo/tests/test_orchestrator_resonance.py`:

- `test_record_task_resonance_basic`: BQI 있는 경우, subdomain 추론, 전체 메트릭 검증
- `test_record_task_resonance_no_bqi`: BQI 없는 경우, 기본 키 생성
- `test_record_task_resonance_silent_on_no_init`: 저장소 미초기화 시 예외 없이 무시

### 사용법 (Orchestrator)

```python
from fdo_agi_repo.orchestrator.resonance_bridge import init_resonance_store

# 프로그램 시작 시 초기화
init_resonance_store(Path("outputs/orchestrator_resonance_events.jsonl"))

# 이후 pipeline.py의 run_task()가 자동으로 기록
result = run_task(tool_cfg, task_spec)
# → resonance event 자동 append
```

### 향후 확장

- ~~실행 duration 계측 추가~~ ✅ **완료**: `t_start = time.perf_counter()` in `run_task()`, `duration_sec` 매핑
- Replan rate, correction passes → `metrics.stability` 매핑
- TaskSpec → UniversalTask 변환기 (full migration 준비)

---

## 구현 코드

- `fdo_agi_repo/universal/task_schema.py`: UniversalTask/데이터/제약/기준 모델
- `fdo_agi_repo/universal/domain_adapter.py`: DomainAdapter/Registry/Executor (+ Healthcare/Finance 스텁, resonance auto-record)
- `fdo_agi_repo/universal/resonance.py`: ResonanceEvent, derive_resonance_key, ResonanceStore
- `fdo_agi_repo/orchestrator/resonance_bridge.py`: Orchestrator → Resonance 브리지 (BQI 매핑)
- `fdo_agi_repo/orchestrator/pipeline.py`: run_task() 완료 경로에 resonance 기록 추가
- `fdo_agi_repo/tests/test_universal_task.py`: Universal 스키마/어댑터 유닛 테스트 (3개)
- `fdo_agi_repo/tests/test_resonance.py`: Resonance 모듈 테스트 (2개)
- `fdo_agi_repo/tests/test_resonance_integration.py`: Executor + Resonance 통합 테스트 (1개)
- `fdo_agi_repo/tests/test_orchestrator_resonance.py`: Orchestrator + Resonance 통합 테스트 (3개)

**테스트 스위트 상태**: 9/9 passing

---

## 테스트 전략

- 유닛: 스키마 유효성, 직렬화/역직렬화, 기본 생성 헬퍼
- 통합: SoftwareEngineeringAdapter로 최소 실행 경로 성공 확인

---

## 성공 기준

- 새 도메인(Healthcare/Finance) 추가 시 기존 코드 수정 없이 동작
- 기존 도메인(코드 리뷰) 성능 저하 없이 Universal 경로로 실행

---

## 자동 실행 명령어

> VS Code Tasks 또는 PowerShell 스크립트로 자동화 (별도 문서 참조)
