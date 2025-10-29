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
    _vx_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if _vx_project and _vx_location:
        if _vx_api_key:
            vertexai.init(project=_vx_project, location=_vx_location, api_key=_vx_api_key)
        else:
            vertexai.init(project=_vx_project, location=_vx_location)
    # else: skip init; downstream code can handle defaults or ADC
except Exception:
    # Library not installed or init failure; allow downstream fallbacks
    pass

_APP_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "app.yaml")


@lru_cache(maxsize=1)
def get_app_config() -> Dict[str, Any]:
    path = _APP_CONFIG_PATH
    if not os.path.exists(path):
        # 기본값 반환 (파일 없을 때도 안전하게 동작)
        return {
            "llm": {"enabled": False, "persona_overrides": {}},
            "corrections": {"enabled": True, "max_passes": 2},
        }
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # 합리적 기본값 보강 - LLM
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

    # 합리적 기본값 보강 - 자기교정(corrections)
    corrections = data.get("corrections", {})
    if "enabled" not in corrections:
        corrections["enabled"] = True  # 현 동작과 호환: 기본 on
    if "max_passes" not in corrections:
        corrections["max_passes"] = 2  # 1차 + 추가 1회 재시도
    data["corrections"] = corrections

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
    # 환경변수 우선 적용, 없으면 설정 파일 사용
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
    # 환경변수로 max_passes 오버라이드 지원 (선택)
    env_mp = os.environ.get("CORRECTIONS_MAX_PASSES")
    if env_mp and env_mp.isdigit():
        out["max_passes"] = int(env_mp)
    return out

def get_evaluation_config() -> Dict[str, Any]:
    """평가 관련 설정: 최소 품질 임계값 등.
    우선순위: 환경변수(EVAL_MIN_QUALITY) > 설정파일(evaluation.min_quality) > 기본값(0.6)
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