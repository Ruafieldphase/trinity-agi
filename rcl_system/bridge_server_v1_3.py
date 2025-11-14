"""
Secure Bridge Server v1.3
-------------------------

Bridges browser/UI requests to the Harmony Core Runner by enforcing:

- HMAC-SHA256 signatures (header: `X-RCL-Signature`)
- Burst rate-limiting (default: 3 requests / 5 seconds per IP)
- Audit logging (`outputs/rcl/adjust_audit.log`)
- Metrics endpoint for monitoring tasks

Run locally:

```bash
set ADJUST_SECRET=rcl_bridge_secret
set RUNNER_URL=http://127.0.0.1:8090
uvicorn rcl_system.bridge_server_v1_3:app --host 127.0.0.1 --port 8091
```
"""

from __future__ import annotations

import hmac
import json
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Deque, Dict, Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from rcl_system.models import BridgeAdjustRequest


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RUNNER_URL = os.getenv("RUNNER_URL", "http://127.0.0.1:8090")
ADJUST_SECRET = os.getenv("ADJUST_SECRET")
RATE_LIMIT = int(os.getenv("BRIDGE_RATE_LIMIT", "3"))
RATE_WINDOW = float(os.getenv("BRIDGE_RATE_WINDOW_SECONDS", "5"))
AUDIT_PATH = Path(os.getenv("BRIDGE_AUDIT_PATH", "outputs/rcl/adjust_audit.log"))
AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class BridgeMetrics:
    total_adjust_requests: int = 0
    rejected_rate_limited: int = 0
    rejected_signature: int = 0
    last_adjust_status: Optional[str] = None
    last_adjust_timestamp: Optional[str] = None


class RateLimiter:
    """Simple sliding-window rate limiter."""

    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._buckets: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        bucket = self._buckets[key]
        now = time.monotonic()
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.limit:
            raise HTTPException(
                status_code=429,
                detail=f"rate limit exceeded ({self.limit}/{self.window_seconds}s)",
            )
        bucket.append(now)


rate_limiter = RateLimiter(RATE_LIMIT, RATE_WINDOW)
metrics = BridgeMetrics()


def compute_signature(timestamp: str, payload: Dict) -> str:
    if not ADJUST_SECRET:
        raise HTTPException(status_code=500, detail="Bridge not configured with ADJUST_SECRET")
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    canonical = f"{timestamp}\n{canonical_payload}".encode("utf-8")
    secret = ADJUST_SECRET.encode("utf-8")
    digest = hmac.new(secret, canonical, sha256).hexdigest()
    return digest


def verify_signature(expected_hex: str, provided_hex: str) -> None:
    if not hmac.compare_digest(expected_hex, provided_hex):
        raise HTTPException(status_code=401, detail="invalid signature")


async def forward_adjust(payload: BridgeAdjustRequest) -> Dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(f"{RUNNER_URL}/adjust", json=payload.payload.dict())
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


def log_adjust(entry: Dict) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_PATH.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(entry, ensure_ascii=False) + "\n")


app = FastAPI(
    title="RCL Bridge v1.3",
    version="1.3.0",
    description="Secure adjust proxy between UI (Lua) and Harmony Core Runner.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def rate_limit_dependency(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    try:
        rate_limiter.check(client_ip)
    except HTTPException:
        metrics.rejected_rate_limited += 1
        raise


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "runner": RUNNER_URL}


@app.get("/metrics")
async def bridge_metrics() -> Dict:
    return {
        "total_adjust_requests": metrics.total_adjust_requests,
        "rejected_rate_limited": metrics.rejected_rate_limited,
        "rejected_signature": metrics.rejected_signature,
        "last_adjust_status": metrics.last_adjust_status,
        "last_adjust_timestamp": metrics.last_adjust_timestamp,
        "rate_limit": RATE_LIMIT,
        "rate_window_seconds": RATE_WINDOW,
        "runner_url": RUNNER_URL,
    }


@app.post("/adjust", dependencies=[Depends(rate_limit_dependency)])
async def adjust_handler(
    payload: BridgeAdjustRequest,
    signature: str = Header(..., alias="X-RCL-Signature"),
) -> Dict:
    metrics.total_adjust_requests += 1

    # Signature verification
    try:
        expected = compute_signature(payload.timestamp, payload.payload.dict())
        verify_signature(expected, signature)
    except HTTPException:
        metrics.rejected_signature += 1
        raise

    # Forward to runner
    runner_response = await forward_adjust(payload)
    metrics.last_adjust_status = runner_response.get("fsm_state")
    metrics.last_adjust_timestamp = runner_response.get("timestamp")

    log_adjust(
        {
            "timestamp": payload.timestamp,
            "payload": payload.payload.dict(),
            "runner_response": runner_response,
        }
    )
    return runner_response


def main() -> None:
    """CLI entrypoint."""
    import uvicorn

    host = os.getenv("RCL_BRIDGE_HOST", "127.0.0.1")
    port = int(os.getenv("RCL_BRIDGE_PORT", "8091"))
    uvicorn.run("rcl_system.bridge_server_v1_3:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
