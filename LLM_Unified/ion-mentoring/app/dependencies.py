"""
Phase 4 - Dependency Injection Configuration
싱글톤 패턴으로 AI 권장사항 엔진, 세션 관리자, 다중 턴 엔진을 관리합니다.
"""

import logging
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# Phase 4 엔진 임포트
try:
    from phase4_development.conversation_system.multiturn_engine import MultiTurnConversationEngine
    from phase4_development.conversation_system.session_manager import (
        ConversationSessionManager,
        InMemorySessionStorage,
    )
    from phase4_development.recommendation_engine.ensemble import EnsembleRecommendationEngine

    phase4_engines_available = True
    logger.info("✅ Phase 4 engines imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Phase 4 engines not available: {str(e)}")
    phase4_engines_available = False
    EnsembleRecommendationEngine = None
    ConversationSessionManager = None
    InMemorySessionStorage = None
    MultiTurnConversationEngine = None


# === 싱글톤 엔진 인스턴스 ===

_recommendation_engine: Optional[object] = None
_session_manager: Optional[object] = None
_multiturn_engine: Optional[object] = None


@lru_cache(maxsize=1)
def get_recommendation_engine():
    """
    AI 권장사항 엔진 싱글톤 획득

    반복 호출 시에도 동일한 인스턴스를 반환합니다.

    Returns:
        EnsembleRecommendationEngine: 권장사항 엔진 인스턴스

    Raises:
        RuntimeError: Phase 4 엔진을 사용할 수 없을 때
    """
    global _recommendation_engine

    if not phase4_engines_available:
        raise RuntimeError("Phase 4 recommendation engine is not available")

    if _recommendation_engine is None:
        try:
            logger.info("Initializing EnsembleRecommendationEngine...")
            _recommendation_engine = EnsembleRecommendationEngine(
                n_factors=10,  # SVD 차원수
                cf_weight=0.4,  # 협업 필터링 가중치
                cb_weight=0.4,  # 콘텐츠 기반 가중치
                pa_weight=0.2,  # 페르소나 친화도 가중치
            )
            logger.info("✅ EnsembleRecommendationEngine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize recommendation engine: {str(e)}")
            raise RuntimeError(f"Recommendation engine initialization failed: {str(e)}")

    return _recommendation_engine


@lru_cache(maxsize=1)
def get_session_manager():
    """
    대화 세션 관리자 싱글톤 획득

    세션 저장소로 메모리 기반 저장소를 사용합니다.
    프로덕션 환경에서는 Redis 또는 데이터베이스 기반 저장소로 교체할 수 있습니다.

    Returns:
        ConversationSessionManager: 세션 관리자 인스턴스

    Raises:
        RuntimeError: Phase 4 엔진을 사용할 수 없을 때
    """
    global _session_manager

    if not phase4_engines_available:
        raise RuntimeError("Phase 4 session manager is not available")

    if _session_manager is None:
        try:
            logger.info("Initializing ConversationSessionManager...")
            storage = InMemorySessionStorage()
            _session_manager = ConversationSessionManager(storage=storage)
            logger.info("✅ ConversationSessionManager initialized with InMemorySessionStorage")
        except Exception as e:
            logger.error(f"Failed to initialize session manager: {str(e)}")
            raise RuntimeError(f"Session manager initialization failed: {str(e)}")

    return _session_manager


@lru_cache(maxsize=1)
def get_multiturn_engine():
    """
    다중 턴 대화 엔진 싱글톤 획득

    세션 관리자와 권장사항 엔진이 초기화된 후 생성됩니다.

    Returns:
        MultiTurnConversationEngine: 다중 턴 엔진 인스턴스

    Raises:
        RuntimeError: Phase 4 엔진을 사용할 수 없을 때
    """
    global _multiturn_engine

    if not phase4_engines_available:
        raise RuntimeError("Phase 4 multiturn engine is not available")

    if _multiturn_engine is None:
        try:
            logger.info("Initializing MultiTurnConversationEngine...")
            session_manager = get_session_manager()
            _multiturn_engine = MultiTurnConversationEngine(
                session_manager=session_manager,
                context_window_size=5,  # 최근 5 턴을 컨텍스트에 포함
            )
            logger.info("✅ MultiTurnConversationEngine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize multiturn engine: {str(e)}")
            raise RuntimeError(f"Multiturn engine initialization failed: {str(e)}")

    return _multiturn_engine


# === 엔진 상태 확인 ===


def get_phase4_status():
    """
    Phase 4 엔진 상태 확인

    Returns:
        dict: 각 엔진의 가용성과 초기화 상태
    """
    return {
        "phase4_available": phase4_engines_available,
        "recommendation_engine_initialized": _recommendation_engine is not None,
        "session_manager_initialized": _session_manager is not None,
        "multiturn_engine_initialized": _multiturn_engine is not None,
    }


def initialize_all_engines():
    """
    모든 Phase 4 엔진 초기화

    앱 시작 시 이 함수를 호출하여 엔진을 미리 초기화할 수 있습니다.

    Returns:
        dict: 초기화 결과
    """
    if not phase4_engines_available:
        logger.warning("Phase 4 engines are not available - skipping initialization")
        return {"success": False, "message": "Phase 4 engines not available"}

    try:
        logger.info("🚀 Initializing all Phase 4 engines...")

        # 순서대로 초기화 (의존성 순서)
        get_session_manager()  # 세션 관리자 먼저
        get_recommendation_engine()  # 권장사항 엔진
        get_multiturn_engine()  # 다중 턴 엔진 (세션 관리자에 의존)

        status = get_phase4_status()
        logger.info(f"✅ All Phase 4 engines initialized: {status}")

        return {
            "success": True,
            "message": "All Phase 4 engines initialized successfully",
            "status": status,
        }
    except Exception as e:
        logger.error(f"Failed to initialize Phase 4 engines: {str(e)}")
        return {"success": False, "message": f"Initialization failed: {str(e)}"}


# === FastAPI 의존성 함수 ===
# 라우터에서 Depends()로 사용할 수 있습니다.


def get_recommendation_engine_dependency():
    """FastAPI 의존성: 권장사항 엔진"""
    return get_recommendation_engine()


def get_session_manager_dependency():
    """FastAPI 의존성: 세션 관리자"""
    return get_session_manager()


def get_multiturn_engine_dependency():
    """FastAPI 의존성: 다중 턴 엔진"""
    return get_multiturn_engine()
