"""
API v2 요청/응답 스키마

Week 11: API v2 개발
향상된 구조, 더 나은 에러 처리, 확장 가능한 설계
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class APIVersion(str, Enum):
    """API 버전"""

    V1 = "v1"
    V2 = "v2"


# ==================== Request Schemas ====================


@dataclass
class ResonanceKeyRequest:
    """파동키 요청 (v2)"""

    tone: str  # calm, frustrated, analytical, etc.
    pace: str  # burst, flowing, contemplative, medium
    intent: str  # seek_advice, problem_solving, learning, etc.

    def to_string(self) -> str:
        """파동키 문자열로 변환"""
        return f"{self.tone}-{self.pace}-{self.intent}"


@dataclass
class ChatMessageRequest:
    """채팅 메시지 요청 (v2)"""

    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


@dataclass
class ContextRequest:
    """컨텍스트 요청 (v2)"""

    user_id: Optional[str] = None
    session_id: Optional[str] = None
    message_history: Optional[List[ChatMessageRequest]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_chat_context(self):
        """ChatContext로 변환"""
        from persona_system.models import ChatContext

        history = []
        if self.message_history:
            for msg in self.message_history:
                history.append(
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    }
                )

        return ChatContext(
            user_id=self.user_id, session_id=self.session_id, message_history=history
        )


@dataclass
class PersonaProcessRequest:
    """페르소나 처리 요청 (v2)"""

    user_input: str
    resonance_key: ResonanceKeyRequest
    context: Optional[ContextRequest] = None
    include_metadata: bool = True
    use_cache: bool = True
    # 경량 요약 프롬프트 등 모드 지정 (예: "summary_light")
    prompt_mode: Optional[str] = None


@dataclass
class MultiPersonaProcessRequest:
    """멀티 페르소나 처리 요청 (v2)

    기본적으로 입력 복잡도를 분석하여 Single/Multi를 자동 선택하며,
    force_multi=true인 경우 강제 멀티 실행을 수행합니다.
    """

    user_input: str
    force_multi: bool = False


@dataclass
class PersonaRecommendRequest:
    """페르소나 추천 요청 (v2)"""

    scenario: str
    context: Optional[ContextRequest] = None


@dataclass
class BulkProcessRequest:
    """일괄 처리 요청 (v2)"""

    requests: List[PersonaProcessRequest]
    parallel: bool = False


# ==================== Response Schemas ====================


@dataclass
class RoutingScores:
    """라우팅 점수 (v2)"""

    lua: float
    elro: float
    riri: float
    nana: float

    @classmethod
    def from_dict(cls, scores_dict: Dict[str, float]):
        """딕셔너리에서 생성"""
        return cls(
            lua=scores_dict.get("Lua", 0.0),
            elro=scores_dict.get("Elro", 0.0),
            riri=scores_dict.get("Riri", 0.0),
            nana=scores_dict.get("Nana", 0.0),
        )


@dataclass
class RoutingInfo:
    """라우팅 정보 (v2)"""

    primary_persona: str
    secondary_persona: str
    confidence: float
    scores: RoutingScores
    reasoning: Optional[str] = None


@dataclass
class PersonaCapabilities:
    """페르소나 능력 정보 (v2)"""

    name: str
    traits: List[str]
    strengths: List[str]
    best_for_tones: List[str]
    best_for_paces: List[str]
    best_for_intents: List[str]


@dataclass
class PerformanceMetrics:
    """성능 메트릭 (v2)"""

    execution_time_ms: float
    cache_hit: bool
    cache_key: Optional[str] = None


@dataclass
class PersonaProcessResponse:
    """페르소나 처리 응답 (v2)"""

    # 필수
    success: bool
    content: str
    persona_used: str
    resonance_key: str

    # 선택
    routing: Optional[RoutingInfo] = None
    confidence: Optional[float] = None
    performance: Optional[PerformanceMetrics] = None
    metadata: Optional[Dict[str, Any]] = None

    # 응답 정보
    timestamp: Optional[datetime] = None
    request_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PersonaRecommendResponse:
    """페르소나 추천 응답 (v2)"""

    recommended_persona: str
    scores: Dict[str, float]
    capabilities: PersonaCapabilities
    reasoning: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class BulkProcessResponse:
    """일괄 처리 응답 (v2)"""

    success: bool
    total: int
    successful: int
    failed: int
    results: List[PersonaProcessResponse]
    errors: Optional[List[str]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


# ==================== Error Schemas ====================


@dataclass
class ErrorDetail:
    """에러 상세 (v2)"""

    code: str
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class ErrorResponse:
    """에러 응답 (v2)"""

    success: bool = False
    error: Optional[ErrorDetail] = None
    errors: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if not self.success:
            self.success = False


# ==================== Health & Status ====================


@dataclass
class ServiceStatus:
    """서비스 상태 (v2)"""

    status: str  # "operational", "degraded", "down"
    version: str
    timestamp: Optional[datetime] = None
    uptime_ms: Optional[float] = None
    cached_requests: Optional[int] = None
    error_rate: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class HealthResponse:
    """헬스 체크 응답 (v2)"""

    healthy: bool
    service_status: ServiceStatus
    dependencies: Dict[str, bool]  # redis, database, etc.
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


# ==================== Schema Conversion ====================


def convert_persona_response_to_v2(persona_response) -> PersonaProcessResponse:
    """v1 PersonaResponse를 v2 PersonaProcessResponse로 변환"""
    from persona_system.models import PersonaResponse

    if not isinstance(persona_response, PersonaResponse):
        raise ValueError("Invalid input type")

    # 라우팅 정보 추출
    routing_info = None
    if persona_response.metadata and "routing_result" in persona_response.metadata:
        routing_data = persona_response.metadata["routing_result"]
        scores = RoutingScores.from_dict(routing_data.get("all_scores", {}))
        routing_info = RoutingInfo(
            primary_persona=persona_response.persona_used,
            secondary_persona=routing_data.get("secondary_persona", "N/A"),
            confidence=persona_response.confidence,
            scores=scores,
            reasoning=routing_data.get("reasoning"),
        )

    # 성능 메트릭
    performance = PerformanceMetrics(
        execution_time_ms=persona_response.execution_time_ms,
        cache_hit=(
            persona_response.metadata.get("cached", False) if persona_response.metadata else False
        ),
        cache_key=persona_response.metadata.get("cache_key") if persona_response.metadata else None,
    )

    return PersonaProcessResponse(
        success=True,
        content=persona_response.content,
        persona_used=persona_response.persona_used,
        resonance_key=persona_response.resonance_key,
        routing=routing_info,
        confidence=persona_response.confidence,
        performance=performance,
        metadata=persona_response.metadata,
    )


def to_dict_for_json(obj: Any) -> Any:
    """JSON 직렬화를 위해 객체를 딕셔너리로 변환"""
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for field in obj.__dataclass_fields__:
            value = getattr(obj, field)
            if value is None:
                result[field] = None
            elif isinstance(value, (str, int, float, bool)):
                result[field] = value
            elif isinstance(value, datetime):
                result[field] = value.isoformat()
            elif isinstance(value, dict):
                result[field] = {k: to_dict_for_json(v) for k, v in value.items()}
            elif isinstance(value, list):
                result[field] = [to_dict_for_json(item) for item in value]
            elif hasattr(value, "__dataclass_fields__"):
                result[field] = to_dict_for_json(value)
            else:
                result[field] = str(value)
        return result
    elif isinstance(obj, dict):
        return {k: to_dict_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_dict_for_json(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj
