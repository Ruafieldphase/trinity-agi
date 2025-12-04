from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from datetime import datetime, timezone


class AbstractIntent(str, Enum):
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
    data_type: DataType
    content: Any
    data_schema: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Pydantic v2 style config
    model_config = ConfigDict(arbitrary_types_allowed=True)


class UniversalConstraint(BaseModel):
    type: str
    value: Any
    priority: float = Field(ge=0.0, le=1.0, default=0.5)
    negotiable: bool = True


class UniversalCriteria(BaseModel):
    metric: str
    threshold: float
    weight: float = 1.0
    measurement_method: str


class DomainMetadata(BaseModel):
    domain_id: str
    subdomain: Optional[str] = None
    ontology: Dict[str, Any] = Field(default_factory=dict)
    tools: List[str] = Field(default_factory=list)
    knowledge_base: Optional[str] = None


class TaskRelation(BaseModel):
    relation_type: str
    related_task_id: str
    strength: float = Field(ge=0.0, le=1.0, default=0.5)


class UniversalTask(BaseModel):
    task_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    intent: AbstractIntent
    intent_description: str

    inputs: List[UniversalData]
    outputs_expected: List[DataType]
    constraints: List[UniversalConstraint] = Field(default_factory=list)
    success_criteria: List[UniversalCriteria] = Field(default_factory=list)

    domain: DomainMetadata

    relations: List[TaskRelation] = Field(default_factory=list)

    status: str = "pending"
    assigned_to: Optional[str] = None
    resonance_key: Optional[str] = None

    outputs_actual: List[UniversalData] = Field(default_factory=list)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)


def create_simple_task(
    intent: AbstractIntent,
    description: str,
    input_text: str,
    domain_id: str = "general",
) -> UniversalTask:
    return UniversalTask(
        task_id=f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        created_at=datetime.now(timezone.utc),
        intent=intent,
        intent_description=description,
        inputs=[UniversalData(data_type=DataType.TEXT, content=input_text)],
        outputs_expected=[DataType.TEXT],
        domain=DomainMetadata(domain_id=domain_id),
    )
