"""
PersonaOrchestrator 시스템

리팩토링된 persona orchestration 시스템
- 데이터 모델: models.py
- 추상 기본 클래스: base.py
- 페르소나 구현: personas.py
- 라우팅 알고리즘: router/
- 프롬프트 빌더: prompts/
- 통합 파이프라인: pipeline.py
"""

from .base import (
    AbstractAnalyzer,
    AbstractMiddleware,
    AbstractPersona,
    AbstractPromptBuilder,
    AbstractRouter,
    AnalysisResult,
)
from .legacy import PersonaPipeline, get_legacy_pipeline, reset_legacy_pipeline
from .models import (
    ChatContext,
    Intent,
    Pace,
    PersonaConfig,
    PersonaResponse,
    RhythmAnalysis,
    RoutingResult,
    Tone,
    ToneAnalysis,
)
from .personas import (
    ElroPersona,
    LuaPersona,
    NanaPersona,
    RiriPersona,
)
from .pipeline import PersonaPipeline as NewPersonaPipeline
from .pipeline import get_pipeline, reset_pipeline
from .prompts import (
    BasePromptBuilder,
    ElroPromptBuilder,
    LuaPromptBuilder,
    NanaPromptBuilder,
    PromptBuilderFactory,
    RiriPromptBuilder,
)
from .router import ResonanceBasedRouter

__all__ = [
    # Models
    "PersonaResponse",
    "PersonaConfig",
    "RoutingResult",
    "ToneAnalysis",
    "RhythmAnalysis",
    "ChatContext",
    "Pace",
    "Tone",
    "Intent",
    # Base Classes
    "AbstractRouter",
    "AbstractPersona",
    "AbstractPromptBuilder",
    "AbstractAnalyzer",
    "AbstractMiddleware",
    "AnalysisResult",
    # Personas
    "LuaPersona",
    "ElroPersona",
    "RiriPersona",
    "NanaPersona",
    # Router
    "ResonanceBasedRouter",
    # Prompt Builders
    "BasePromptBuilder",
    "LuaPromptBuilder",
    "ElroPromptBuilder",
    "RiriPromptBuilder",
    "NanaPromptBuilder",
    "PromptBuilderFactory",
    # Pipeline (New)
    "NewPersonaPipeline",
    "get_pipeline",
    "reset_pipeline",
    # Pipeline (Legacy - for backward compatibility)
    "PersonaPipeline",
    "get_legacy_pipeline",
    "reset_legacy_pipeline",
]

__version__ = "2.1.0"
# Migration note: PersonaPipeline is now a compatibility wrapper
# Use get_pipeline() for new code
