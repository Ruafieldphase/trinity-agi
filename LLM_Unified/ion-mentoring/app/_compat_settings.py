"""Compatibility wrapper for settings base classes.

At runtime, prefer pydantic-settings (v2). If it's not available (e.g., in tooling
or editor environment), fall back to pydantic.BaseModel to satisfy static analysis.
"""

from __future__ import annotations

try:
    # Preferred runtime dependency
    from pydantic_settings import BaseSettings as BaseSettings  # type: ignore
    from pydantic_settings import SettingsConfigDict as SettingsConfigDict
except Exception:  # pragma: no cover - tooling-only path
    try:
        from pydantic import BaseModel as _BaseModel  # type: ignore
    except Exception:  # extremely minimal fallback

        class _BaseModel:  # type: ignore
            pass

    # Provide shims
    class BaseSettings(_BaseModel):  # type: ignore
        pass

    class SettingsConfigDict(dict):  # type: ignore
        pass
