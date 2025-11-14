"""Shared models for the RCL system components."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, validator


class AdjustPayload(BaseModel):
    """Guarded payload accepted by Harmony Core Runner."""

    sync_rate: Optional[float] = Field(
        None, ge=0.25, le=3.5, description="Relative sync multiplier vs base clock."
    )
    autotune_gain: Optional[float] = Field(
        None, ge=0.1, le=8.0, description="Feedback gain applied to drift compensation."
    )
    cooling_mode: Optional[str] = Field(
        None, description="Cooling profile (normal/cooldown/lock)."
    )
    feedback_enabled: Optional[bool] = Field(
        None, description="Override for forecast feedback worker."
    )
    note: Optional[str] = Field(
        None, max_length=120, description="Short free-form annotation."
    )

    @validator("cooling_mode")
    def validate_cooling_mode(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        allowed = {"normal", "cooldown", "lock"}
        if value not in allowed:
            raise ValueError(f"cooling_mode must be one of {sorted(allowed)}")
        return value


class BridgeAdjustRequest(BaseModel):
    """Payload accepted by the secure bridge server."""

    timestamp: str = Field(
        ..., description="ISO8601 timestamp from the caller (used for HMAC)."
    )
    payload: AdjustPayload = Field(..., description="Validated Harmony Core adjustment.")

