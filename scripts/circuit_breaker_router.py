#!/usr/bin/env python3
"""
Circuit Breaker Pattern for AGI LLM Routing

Provides intelligent fallback between Core Gateway and Local LLM
with failure tracking and automatic recovery.

Features:
- Automatic fallback on timeout/failure
- Exponential backoff retry logic
- Health tracking and circuit state management
- Configurable thresholds
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from workspace_root import get_workspace_root


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures detected, using fallback
    HALF_OPEN = "half_open"  # Testing if primary recovered


@dataclass
class CircuitConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 3  # Consecutive failures before opening
    timeout_ms: int = 2000      # Request timeout
    reset_timeout_sec: int = 60  # Time before trying half-open
    success_threshold: int = 2   # Successes needed to close from half-open


@dataclass
class BackendHealth:
    """Health tracking for a backend"""
    name: str
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_requests: int = 0
    total_failures: int = 0


class CircuitBreakerRouter:
    """
    Intelligent router with circuit breaker pattern
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config = CircuitConfig()

        # Backend configurations
        self.backends = {
            "Core": {
                "url": "https://Core-gateway-x4qvsargwa-uc.a.run.app/chat",
                "timeout": self.config.timeout_ms / 1000,
                "priority": 1  # Higher priority
            },
            "local": {
                "url": "http://localhost:8080/v1/completions",
                "timeout": 10.0,  # Local is slower but more reliable
                "priority": 2  # Lower priority (fallback)
            }
        }

        # Health tracking
        self.health = {
            "Core": BackendHealth(name="Core"),
            "local": BackendHealth(name="local")
        }

        # Circuit state
        self.circuit_state = CircuitState.CLOSED
        self.state_changed_at = time.time()

        # State file
        workspace = get_workspace_root()
        self.state_file = workspace / "outputs" / "circuit_breaker_state.json"
        self.log_file = workspace / "outputs" / "circuit_breaker_log.jsonl"

        # Load previous state if exists
        self._load_state()

    def _load_state(self):
        """Load previous circuit state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                self.circuit_state = CircuitState(state.get("circuit_state", "closed"))
                self.state_changed_at = state.get("state_changed_at", time.time())

                # Restore health stats
                for backend_name, health_data in state.get("health", {}).items():
                    if backend_name in self.health:
                        self.health[backend_name] = BackendHealth(**health_data)
            except Exception as e:
                print(f"Warning: Could not load circuit state: {e}")

    def _save_state(self):
        """Save circuit state"""
        state = {
            "circuit_state": self.circuit_state.value,
            "state_changed_at": self.state_changed_at,
            "health": {
                name: asdict(health)
                for name, health in self.health.items()
            },
            "updated_at": datetime.now().isoformat()
        }

        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def _log_event(self, event_type: str, backend: str, **kwargs):
        """Log circuit breaker events"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "backend": backend,
            "circuit_state": self.circuit_state.value,
            **kwargs
        }

        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def _call_backend(self, backend_name: str, message: str, **kwargs) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Call a specific backend

        Returns: (success, response, latency_ms)
        """
        backend = self.backends[backend_name]
        health = self.health[backend_name]

        health.total_requests += 1

        try:
            start = time.time()

            if backend_name == "Core":
                # Core Gateway format
                payload = {
                    "message": message,
                    "persona_key": kwargs.get("persona_key", "pen"),
                    "stream": False
                }
                response = requests.post(
                    backend["url"],
                    json=payload,
                    timeout=backend["timeout"]
                )
            else:
                # Local LLM format (OpenAI compatible)
                payload = {
                    "model": "local-model",
                    "prompt": message,
                    "max_tokens": kwargs.get("max_tokens", 256),
                    "temperature": kwargs.get("temperature", 0.7)
                }
                response = requests.post(
                    backend["url"],
                    json=payload,
                    timeout=backend["timeout"]
                )

            latency_ms = (time.time() - start) * 1000

            response.raise_for_status()

            # Parse response
            data = response.json()

            if backend_name == "Core":
                if data.get("success"):
                    result = data.get("response", "")
                else:
                    raise Exception(f"Core error: {data.get('error', 'Unknown')}")
            else:
                # OpenAI format
                choices = data.get("choices", [])
                if choices:
                    result = choices[0].get("text", "")
                else:
                    raise Exception("No response from local LLM")

            # Success
            health.consecutive_successes += 1
            health.consecutive_failures = 0
            health.last_success_time = time.time()

            self._log_event("success", backend_name, latency_ms=latency_ms)

            return True, result, latency_ms

        except Exception as e:
            # Failure
            health.consecutive_failures += 1
            health.consecutive_successes = 0
            health.last_failure_time = time.time()
            health.total_failures += 1

            self._log_event("failure", backend_name, error=str(e))

            return False, None, None

    def _update_circuit_state(self, backend_name: str, success: bool):
        """Update circuit state based on backend health"""
        if backend_name != "Core":
            return  # Only track primary backend

        health = self.health["Core"]

        if self.circuit_state == CircuitState.CLOSED:
            # Normal operation
            if health.consecutive_failures >= self.config.failure_threshold:
                # Open circuit - too many failures
                self.circuit_state = CircuitState.OPEN
                self.state_changed_at = time.time()
                self._log_event("circuit_opened", "Core",
                               reason=f"{health.consecutive_failures} consecutive failures")
                print(f"⚠️  Circuit OPENED: Core Gateway unreliable, using Local LLM")

        elif self.circuit_state == CircuitState.OPEN:
            # Using fallback
            time_since_open = time.time() - self.state_changed_at

            if time_since_open >= self.config.reset_timeout_sec:
                # Try half-open - test if primary recovered
                self.circuit_state = CircuitState.HALF_OPEN
                self.state_changed_at = time.time()
                self._log_event("circuit_half_open", "Core",
                               reason="Reset timeout elapsed")
                print(f"🔄 Circuit HALF-OPEN: Testing Core Gateway recovery")

        elif self.circuit_state == CircuitState.HALF_OPEN:
            # Testing recovery
            if success and health.consecutive_successes >= self.config.success_threshold:
                # Recovered - close circuit
                self.circuit_state = CircuitState.CLOSED
                self.state_changed_at = time.time()
                self._log_event("circuit_closed", "Core",
                               reason=f"{health.consecutive_successes} consecutive successes")
                print(f"✅ Circuit CLOSED: Core Gateway recovered")

            elif not success:
                # Still failing - reopen
                self.circuit_state = CircuitState.OPEN
                self.state_changed_at = time.time()
                self._log_event("circuit_reopened", "Core",
                               reason="Still failing during half-open test")
                print(f"❌ Circuit RE-OPENED: Core Gateway still failing")

        self._save_state()

    def route(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Route message with circuit breaker logic

        Returns: {
            "success": bool,
            "response": str,
            "backend_used": str,
            "latency_ms": float,
            "circuit_state": str,
            "fallback_used": bool
        }
        """
        fallback_used = False

        # Determine primary backend based on circuit state
        if self.circuit_state == CircuitState.CLOSED:
            primary = "Core"
        elif self.circuit_state == CircuitState.HALF_OPEN:
            primary = "Core"  # Test if recovered
        else:  # OPEN
            primary = "local"
            fallback_used = True

        # Try primary
        success, response, latency = self._call_backend(primary, message, **kwargs)

        if primary == "Core":
            self._update_circuit_state("Core", success)

        # If primary failed and it was Core, try fallback
        if not success and primary == "Core":
            print(f"⚠️  Core failed, falling back to Local LLM")
            fallback_used = True
            success, response, latency = self._call_backend("local", message, **kwargs)

        return {
            "success": success,
            "response": response or "Error: All backends failed",
            "backend_used": "local" if fallback_used else primary,
            "latency_ms": latency,
            "circuit_state": self.circuit_state.value,
            "fallback_used": fallback_used,
            "health": {
                name: {
                    "failure_rate": (h.total_failures / h.total_requests * 100) if h.total_requests > 0 else 0,
                    "consecutive_failures": h.consecutive_failures,
                    "total_requests": h.total_requests
                }
                for name, h in self.health.items()
            }
        }

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "circuit_state": self.circuit_state.value,
            "state_duration_sec": time.time() - self.state_changed_at,
            "health": {
                name: asdict(health)
                for name, health in self.health.items()
            }
        }


def main():
    """CLI interface for testing"""
    import sys

    router = CircuitBreakerRouter()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python circuit_breaker_router.py 'Your message here'")
        print("  python circuit_breaker_router.py --status")
        sys.exit(1)

    if sys.argv[1] == "--status":
        status = router.get_status()
        print(json.dumps(status, indent=2, default=str))
        sys.exit(0)

    message = ' '.join(sys.argv[1:])

    print(f"\n🔀 Circuit Breaker Router")
    print(f"Message: {message}\n")

    result = router.route(message)

    print(f"✅ Result:")
    print(f"  Backend: {result['backend_used']}")
    print(f"  Circuit State: {result['circuit_state']}")
    print(f"  Fallback Used: {result['fallback_used']}")
    print(f"  Latency: {result['latency_ms']:.0f}ms" if result['latency_ms'] else "  Latency: N/A")
    print(f"\n  Response: {result['response'][:200]}..." if len(result['response']) > 200 else f"\n  Response: {result['response']}")
    print(f"\n📊 Health:")
    for backend, health in result['health'].items():
        print(f"  {backend}: {health['failure_rate']:.1f}% failure rate ({health['total_requests']} requests)")


if __name__ == '__main__':
    main()
