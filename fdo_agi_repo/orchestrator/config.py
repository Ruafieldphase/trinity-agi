from __future__ import annotations
import os
from functools import lru_cache
from typing import Any, Dict

import yaml

# Load environment variables from .env file
try:
    from pathlib import Path
    from dotenv import load_dotenv

    # Load .env from repo root (absolute path)
    # This ensures .env is found regardless of working directory
    repo_root = Path(__file__).parent.parent
    env_file = repo_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()  # Fallback to default behavior
except ImportError:
    pass  # dotenv not installed, environment variables must be set manually

# Initialize Vertex AI using environment when available (non-fatal)
try:
    import vertexai
    _vx_project = os.getenv("VERTEX_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
    _vx_location = os.getenv("VERTEX_LOCATION") or os.getenv("GCP_LOCATION") or os.getenv("GOOGLE_CLOUD_REGION")
    if _vx_project and _vx_location:
        # 일부 버전의 vertexai.init은 api_key 매개변수를 지원하지 않으므로 보수적으로 기본 시그니처만 사용
        vertexai.init(project=_vx_project, location=_vx_location)
    # else: skip init; downstream code can handle defaults or ADC
except Exception:
    # Library not installed or init failure; allow downstream fallbacks
    pass

_APP_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "app.yaml")
_APP_CONFIG_CACHE = None  # simple in-process cache
_APP_CONFIG_MTIME = None  # last known mtime


# @lru_cache(maxsize=1)

def get_app_config() -> Dict[str, Any]:
    """Load app config with mtime-based freshness and safe defaults."""
    global _APP_CONFIG_CACHE, _APP_CONFIG_MTIME
    path = _APP_CONFIG_PATH
    try:
        if (_APP_CONFIG_CACHE is not None) and os.path.exists(path):
            cur = os.path.getmtime(path)
            if (_APP_CONFIG_MTIME is not None) and (cur == _APP_CONFIG_MTIME):
                return _APP_CONFIG_CACHE  # type: ignore[return-value]
    except Exception:
        pass

    if not os.path.exists(path):
        data: Dict[str, Any] = {
            "llm": {"enabled": False, "persona_overrides": {}},
            "corrections": {"enabled": True, "max_passes": 2},
        }
        _APP_CONFIG_CACHE = data
        _APP_CONFIG_MTIME = None
        return data

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # Defaults - LLM
    llm = data.get("llm", {})
    if "enabled" not in llm:
        llm["enabled"] = False
    if "provider" not in llm:
        llm["provider"] = "local_proxy"
    if "endpoint" not in llm:
        llm["endpoint"] = "http://localhost:8080/v1/chat/completions"
    if "persona_overrides" not in llm:
        llm["persona_overrides"] = {}
    data["llm"] = llm

    # Defaults - corrections
    corrections = data.get("corrections", {})
    if "enabled" not in corrections:
        corrections["enabled"] = True
    if "max_passes" not in corrections:
        corrections["max_passes"] = 2
    data["corrections"] = corrections

    try:
        _APP_CONFIG_MTIME = os.path.getmtime(path)
    except Exception:
        _APP_CONFIG_MTIME = None
    _APP_CONFIG_CACHE = data
    return data

def is_llm_enabled() -> bool:
    cfg = get_app_config()
    return bool(cfg.get("llm", {}).get("enabled", False))

def llm_runtime_defaults() -> Dict[str, Any]:
    cfg = get_app_config()
    llm = cfg.get("llm", {})
    return {
        "provider": llm.get("provider", "local_proxy"),
        "model": llm.get("model", "yanolja_-_eeve-korean-instruct-10.8b-v1.0"),
        "endpoint": llm.get("endpoint", "http://localhost:8080/v1/chat/completions"),
        "persona_overrides": llm.get("persona_overrides", {})
    }


def _env_to_bool(val: str) -> bool:
    return val.strip().lower() in ("1", "true", "yes", "y", "on")


def is_corrections_enabled() -> bool:
    # ?섍꼍蹂???곗꽑 ?곸슜, ?놁쑝硫??ㅼ젙 ?뚯씪 ?ъ슜
    env_val = os.environ.get("CORRECTIONS_ENABLED")
    if env_val is not None:
        try:
            return _env_to_bool(env_val)
        except Exception:
            pass
    cfg = get_app_config()
    return bool(cfg.get("corrections", {}).get("enabled", True))

def get_corrections_config() -> Dict[str, Any]:
    cfg = get_app_config().get("corrections", {})
    out = {
        "enabled": is_corrections_enabled(),
        "max_passes": int(cfg.get("max_passes", 2)),
    }
    # ?섍꼍蹂?섎줈 max_passes ?ㅻ쾭?쇱씠??吏??(?좏깮)
    env_mp = os.environ.get("CORRECTIONS_MAX_PASSES")
    if env_mp and env_mp.isdigit():
        out["max_passes"] = int(env_mp)
    return out

def get_evaluation_config() -> Dict[str, Any]:
    """?됯? 愿???ㅼ젙: 理쒖냼 ?덉쭏 ?꾧퀎媛???
    ?곗꽑?쒖쐞: ?섍꼍蹂??EVAL_MIN_QUALITY) > ?ㅼ젙?뚯씪(evaluation.min_quality) > 湲곕낯媛?0.6)
    """
    cfg = get_app_config().get("evaluation", {})
    default_min_q = 0.6
    try:
        env_min_q = os.environ.get("EVAL_MIN_QUALITY")
        if env_min_q is not None:
            return {"min_quality": float(env_min_q)}
    except Exception:
        pass
    return {"min_quality": float(cfg.get("min_quality", default_min_q))}


def is_async_thesis_enabled() -> bool:
    """Async Thesis ?ㅽ뻾 ?щ? ?뚮옒洹?
    ?곗꽑?쒖쐞: ?섍꼍蹂??ASYNC_THESIS_ENABLED) > ?ㅼ젙?뚯씪(orchestration.async_thesis.enabled) > 湲곕낯媛?False)
    """
    # 1) ?섍꼍蹂???곗꽑
    env_val = os.environ.get("ASYNC_THESIS_ENABLED")
    if env_val is not None:
        try:
            return _env_to_bool(env_val)
        except Exception:
            pass

    # 2) ?ㅼ젙 ?뚯씪
    try:
        cfg = get_app_config()
        orch = cfg.get("orchestration", {})
        async_cfg = orch.get("async_thesis", {})
        return bool(async_cfg.get("enabled", False))
    except Exception:
        return False


def is_response_cache_enabled() -> bool:
    """Response Cache (LLM ?묒떟 罹먯떛) ?щ? ?뚮옒洹?
    ?곗꽑?쒖쐞: ?섍꼍蹂??RESPONSE_CACHE_ENABLED) > ?ㅼ젙?뚯씪(orchestration.response_cache.enabled) > 湲곕낯媛?True)
    
    Default: True (?덈럩 ?ㅽ듃 ?덉뼱蹂대굹 罹먯떛 ?먰낵媛?梨됱?
    """
    # 1) ?섍꼍蹂???곗꽑
    env_val = os.environ.get("RESPONSE_CACHE_ENABLED")
    if env_val is not None:
        try:
            return _env_to_bool(env_val)
        except Exception:
            pass

    # 2) ?ㅼ젙 ?뚯씪
    try:
        cfg = get_app_config()
        orch = cfg.get("orchestration", {})
        cache_cfg = orch.get("response_cache", {})
        return bool(cache_cfg.get("enabled", True))  # Default: True
    except Exception:
        return True  # Fail-safe: enable by default


def get_response_cache_config() -> Dict[str, Any]:
    """Response Cache ?ㅼ젙 媛??몄삤湲?
    Returns:
        dict: {enabled: bool, ttl_seconds: int, max_entries: int}
    """
    cfg = get_app_config().get("orchestration", {}).get("response_cache", {})
    return {
        "enabled": is_response_cache_enabled(),
        "ttl_seconds": int(cfg.get("ttl_seconds", 3600)),  # Default: 1 hour
        "max_entries": int(cfg.get("max_entries", 500))
    }



