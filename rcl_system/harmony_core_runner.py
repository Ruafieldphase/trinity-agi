"""
Harmony Core Runner
-------------------

Implements the runtime half of the RCL (Rhythm-Coherence Loop) design:

- 30Hz tick loop that keeps track of resonance/phase metrics
- `/status` endpoint for dashboards and bridges
- `/adjust` endpoint with clamp + guardrails
- `/metrics` lightweight view for automation

This runner intentionally keeps the numerical model lightweight so it can run
inside the developer workstation without extra dependencies. The goal is to
provide a living structure that matches the design docs so future agents can
extend the physics/drift models without having to bootstrap the service again.
"""

from __future__ import annotations

import asyncio
import math
import os
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional

from fastapi import FastAPI, HTTPException

from rcl_system.models import AdjustPayload


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class HarmonyCoreState:
    """Maintains tick loop state and exposes safe snapshots."""

    def __init__(self, tick_hz: float = 30.0, status_window_seconds: int = 60) -> None:
        self.tick_hz = tick_hz
        self.tick_interval = 1.0 / tick_hz
        self.status_window_seconds = status_window_seconds
        self._stop_event = asyncio.Event()
        self._lock = asyncio.Lock()

        # Dynamic parameters (adjustable)
        self.sync_rate = 1.0
        self.autotune_gain = 1.0
        self.cooling_mode = "normal"
        self.feedback_enabled = True

        # Metrics
        self.phase = 0.0
        self.e_eq = 0.0
        self.drift_ppm = 0.0
        self.forecast_rmse = 0.0
        self.tick_jitter_ms = 0.0
        self.total_ticks = 0
        self.last_adjusted_at: Optional[datetime] = None
        self.last_adjust_note: Optional[str] = None

        self._status_history: Deque[Dict[str, Any]] = deque(maxlen=status_window_seconds)
        self._last_tick_started = time.perf_counter()

    async def run(self) -> None:
        """Background loop."""
        while not self._stop_event.is_set():
            start = time.perf_counter()
            async with self._lock:
                self._tick()
            elapsed = time.perf_counter() - start
            await asyncio.sleep(max(0.0, self.tick_interval - elapsed))

    async def stop(self) -> None:
        self._stop_event.set()
        await asyncio.sleep(0)

    async def adjust(self, payload: AdjustPayload) -> Dict[str, Any]:
        """Apply an adjustment request."""
        async with self._lock:
            if payload.sync_rate is not None:
                self.sync_rate = payload.sync_rate
            if payload.autotune_gain is not None:
                self.autotune_gain = payload.autotune_gain
            if payload.cooling_mode is not None:
                self.cooling_mode = payload.cooling_mode
            if payload.feedback_enabled is not None:
                self.feedback_enabled = payload.feedback_enabled
            if payload.note:
                self.last_adjust_note = payload.note
            self.last_adjusted_at = _utc_now()

            snapshot = self._snapshot()
            snapshot["message"] = "adjustment_applied"
            return snapshot

    async def get_status(self) -> Dict[str, Any]:
        async with self._lock:
            return self._snapshot()

    def _tick(self) -> None:
        """Single tick update."""
        now_perf = time.perf_counter()
        cycle_ms = (now_perf - self._last_tick_started) * 1_000
        self._last_tick_started = now_perf
        self.tick_jitter_ms = max(0.0, abs(cycle_ms - (self.tick_interval * 1_000)))

        # Basic oscillator
        self.phase = (self.phase + self.sync_rate * self.tick_interval * 2 * math.pi) % (
            2 * math.pi
        )
        phase_error = math.sin(self.phase)
        self.e_eq = 1.0 - abs(phase_error)

        # Convert sync_rate drift into ppm
        self.drift_ppm = (self.sync_rate - 1.0) * 1_000_000

        # Toy RMSE (coupled to autotune gain and jitter)
        jitter_component = min(5.0, self.tick_jitter_ms / 4.0)
        gain_component = abs(self.autotune_gain - 1.0) * 0.5
        self.forecast_rmse = round((jitter_component + gain_component) * 0.5, 4)

        self.total_ticks += 1
        snapshot = self._snapshot()
        self._status_history.append(snapshot)

    def _snapshot(self) -> Dict[str, Any]:
        fsm_state = self._resolve_fsm_state()
        return {
            "timestamp": _utc_now().isoformat(),
            "tick_hz": self.tick_hz,
            "sync_rate": round(self.sync_rate, 4),
            "autotune_gain": round(self.autotune_gain, 4),
            "cooling_mode": self.cooling_mode,
            "feedback_enabled": self.feedback_enabled,
            "phase": round(self.phase, 6),
            "equilibrium": round(self.e_eq, 6),
            "drift_ppm": round(self.drift_ppm, 2),
            "forecast_rmse": self.forecast_rmse,
            "tick_jitter_ms": round(self.tick_jitter_ms, 4),
            "fsm_state": fsm_state,
            "total_ticks": self.total_ticks,
            "history_window": self.status_window_seconds,
            "last_adjusted_at": self.last_adjusted_at.isoformat()
            if self.last_adjusted_at
            else None,
            "last_adjust_note": self.last_adjust_note,
        }

    def _resolve_fsm_state(self) -> str:
        """Simple FSM mapping (Active/Drift/Recover/Resting)."""
        if not self.feedback_enabled:
            return "RESTING"
        if abs(self.drift_ppm) > 150_000:
            return "DRIFT"
        if self.forecast_rmse > 1.5:
            return "RECOVER"
        return "ACTIVE"


def build_state_from_env() -> HarmonyCoreState:
    tick_hz = float(os.getenv("HARMONY_TICK_HZ", "30.0"))
    window_seconds = int(os.getenv("HARMONY_STATUS_WINDOW_SECONDS", "90"))
    return HarmonyCoreState(tick_hz=tick_hz, status_window_seconds=window_seconds)


state = build_state_from_env()
app = FastAPI(
    title="Harmony Core Runner",
    version="0.1.0",
    description="Reference implementation for the RCL Harmony Core Runner.",
)


@app.on_event("startup")
async def _startup_loop() -> None:
    app.state.runner_task = asyncio.create_task(state.run())


@app.on_event("shutdown")
async def _shutdown_loop() -> None:
    await state.stop()
    task: asyncio.Task = getattr(app.state, "runner_task", None)
    if task:
        task.cancel()


@app.get("/health")
async def health() -> Dict[str, Any]:
    snapshot = await state.get_status()
    return {"status": "ok", "fsm_state": snapshot["fsm_state"], "ticks": snapshot["total_ticks"]}


@app.get("/status")
async def status() -> Dict[str, Any]:
    return await state.get_status()


@app.get("/metrics")
async def metrics() -> Dict[str, Any]:
    snapshot = await state.get_status()
    return {
        "drift_ppm": snapshot["drift_ppm"],
        "forecast_rmse": snapshot["forecast_rmse"],
        "tick_jitter_ms": snapshot["tick_jitter_ms"],
        "fsm_state": snapshot["fsm_state"],
        "feedback_enabled": snapshot["feedback_enabled"],
        "cooling_mode": snapshot["cooling_mode"],
    }


@app.post("/adjust")
async def adjust(payload: AdjustPayload) -> Dict[str, Any]:
    snapshot = await state.adjust(payload)
    if snapshot["fsm_state"] == "DRIFT" and payload.sync_rate and payload.sync_rate > 2.5:
        raise HTTPException(status_code=202, detail="Adjustment accepted but drift remains high.")
    return snapshot


def main() -> None:
    """CLI entrypoint."""
    import uvicorn

    host = os.getenv("HARMONY_RUNNER_HOST", "127.0.0.1")
    port = int(os.getenv("HARMONY_RUNNER_PORT", "8090"))
    uvicorn.run("rcl_system.harmony_core_runner:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
