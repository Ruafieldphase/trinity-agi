#!/usr/bin/env python3
"""
Real-time Event Emitter for AGI System
실시간 이벤트 발생 및 Resonance Ledger 기록

Usage:
    from orchestrator.event_emitter import emit_event
    
    emit_event('task_started', {
        'task_id': 'demo-001',
        'goal': 'AGI 자기교정 루프 설명',
        'persona': 'gitko'
    })
"""

from __future__ import annotations

import json
import os
import time
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from threading import Lock, Thread, Event
from queue import Queue, Full as QueueFull
from contextlib import contextmanager

# Structured logger for event emitter internals
_logger = logging.getLogger(__name__)

# Thread-safe write lock
_write_lock = Lock()

# Async write queue (lazy initialized)
_async_queue: Optional[Queue] = None
_async_worker: Optional[Thread] = None
_worker_stop_event = Event()
_async_queue_max_size = 1000  # Prevent unbounded memory growth

# Repo root detection
_REPO_ROOT = Path(__file__).parent.parent
_LEDGER_PATH = _REPO_ROOT / "memory" / "resonance_ledger.jsonl"

# Field name aliases for normalization (Core 권장: 필드명 통합)
FIELD_ALIASES = {
    'agi_quality': 'quality',
    'quality_score': 'quality',  # Resonance quality_score → quality
    'core_latency_ms': 'latency_ms',
    'duration_sec': 'latency_ms',  # 변환 필요
}

# Start/End event pair mapping for latency auto-enrichment
# Key: end/completion event -> start event counterpart
_END_START_PAIRS = {
    'task_completed': 'task_started',
    'task_failed': 'task_started',  # still measure duration till failure
    'thesis_end': 'thesis_start',
    'synthesis_end': 'synthesis_start',
}

# In-memory registry for start timestamps to compute latency automatically.
# Key strategy: (start_event_type, task_id or session_id or persona_id or explicit correlation_id)
# We retain minimal data (start_ts) and prune after end event.
_start_time_registry: Dict[str, float] = {}
_start_time_lock = Lock()

def _make_registry_key(event_type: str, task_id: Optional[str], session_id: Optional[str], persona_id: Optional[str], correlation_id: Optional[str]) -> str:
    """Build a stable key for start/end correlation."""
    base = [event_type]
    if correlation_id:
        base.append(f"cid={correlation_id}")
    if task_id:
        base.append(f"task={task_id}")
    if session_id:
        base.append(f"session={session_id}")
    if persona_id:
        base.append(f"persona={persona_id}")
    return '|'.join(base)

def _record_start(event_type: str, task_id: Optional[str], session_id: Optional[str], persona_id: Optional[str], correlation_id: Optional[str]) -> None:
    key = _make_registry_key(event_type, task_id, session_id, persona_id, correlation_id)
    with _start_time_lock:
        _start_time_registry[key] = time.time()

def _consume_latency(end_event_type: str, task_id: Optional[str], session_id: Optional[str], persona_id: Optional[str], correlation_id: Optional[str]) -> Optional[float]:
    """Return latency_ms if matching start event exists; remove it from registry."""
    # Derive start event type
    if end_event_type in _END_START_PAIRS:
        start_type = _END_START_PAIRS[end_event_type]
    elif end_event_type.endswith('_end'):
        start_type = end_event_type[:-4] + '_start'
    elif end_event_type.endswith('_completed'):
        start_type = end_event_type[:-10] + '_started'
    else:
        start_type = None
    if not start_type:
        return None
    key = _make_registry_key(start_type, task_id, session_id, persona_id, correlation_id)
    with _start_time_lock:
        start_ts = _start_time_registry.pop(key, None)
    if start_ts is None:
        return None
    return (time.time() - start_ts) * 1000.0

@contextmanager
def timed_event(base_event: str, *, task_id: Optional[str] = None, session_id: Optional[str] = None,
                persona_id: Optional[str] = None, correlation_id: Optional[str] = None, payload: Optional[Dict[str, Any]] = None):
    """Context manager for measuring latency of a code block.

    Usage:
        with timed_event('thesis', task_id='task-123', payload={'goal': 'Improve RAG'}):
            run_thesis_phase()

    Emits <base_event>_start and <base_event>_end events with auto latency_ms.
    """
    payload = payload or {}
    emit_event(f'{base_event}_start', payload, task_id=task_id, session_id=session_id, persona_id=persona_id)
    start_perf = time.perf_counter()
    try:
        yield
        success = True
    except Exception:
        success = False
        raise
    finally:
        latency_ms = (time.perf_counter() - start_perf) * 1000.0
        end_payload = dict(payload)
        end_payload['latency_ms'] = latency_ms
        end_payload['success'] = success
        emit_event(f'{base_event}_end', end_payload, task_id=task_id, session_id=session_id, persona_id=persona_id)

# Event categories for filtering/routing
EVENT_CATEGORIES = {
    # Core AGI lifecycle
    'task_started', 'task_completed', 'task_failed',
    'thesis_start', 'thesis_end',
    'synthesis_start', 'synthesis_end',
    'eval', 'rune', 'replan',
    
    # Evidence & RAG
    'evidence_search', 'evidence_added', 'evidence_rejected',
    'rag_retrieval', 'citation_added',
    
    # Self-correction
    'second_pass', 'quality_check', 'confidence_check',
    
    # System operations
    'system_startup', 'system_shutdown',
    'health_check', 'performance_metric',
    
    # Infrastructure
    'migration', 'deployment', 'rollback',
    'configuration_change', 'scale_event',
    
    # BQI Learning
    'bqi_pattern_learned', 'bqi_rule_applied',
    'binoche_decision', 'ensemble_update',
    
    # Monitoring & Alerts
    'alert_triggered', 'alert_resolved',
    'threshold_exceeded', 'anomaly_detected',
    
    # Session management
    'session_start', 'session_end',
    'persona_activated', 'persona_switched',
}


def _normalize_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    필드명 정규화: 레거시 필드명을 표준 필드명으로 변환
    
    Core(合) 권장: 일관된 메트릭 필드명 사용으로 분석 효율 향상
    - agi_quality → quality
    - core_latency_ms → latency_ms
    - duration_sec → latency_ms (단위 변환)
    - quality_score → quality (이전 공명/평가 필드 통합)

    추가 기능 (2025-11-08): 자동 레이턴시(enrichment) 파이프라인과 결합.
    emit_event 호출 시:
      1. *_start / task_started / thesis_start / synthesis_start 이벤트는 내부 레지스트리에 시작 시각 기록
      2. 대응하는 *_end / *_completed 이벤트가 latency_ms 없이 도착하면 자동 계산 후 주입
         (registry 기반; 밀리초 단위 float, 소수 첫째 자리 반올림)
    개발자가 직접 측정하고 싶다면:
      - contextmanager timed_event 사용
      - start_timed_event / complete_timed_event 헬퍼 사용
    
    Args:
        payload: 이벤트 페이로드
    
    Returns:
        정규화된 페이로드
    """
    normalized = payload.copy()
    
    for old_name, new_name in FIELD_ALIASES.items():
        if old_name in normalized and new_name not in normalized:
            value = normalized[old_name]
            
            # duration_sec → latency_ms 변환 (초 → 밀리초)
            if old_name == 'duration_sec' and new_name == 'latency_ms':
                value = value * 1000
            
            normalized[new_name] = value
    
    return normalized


# Public alias for external use (e.g., backfill scripts)
normalize_metric_fields = _normalize_fields


def emit_event(
    event_type: str,
    payload: Dict[str, Any],
    *,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    persona_id: Optional[str] = None,
    quality: Optional[float] = None,
    latency_ms: Optional[float] = None,
    correlation_id: Optional[str] = None,
    sync: bool = True
) -> bool:
    """
    실시간 이벤트 발생 및 Ledger 기록
    
    Args:
        event_type: 이벤트 타입 (EVENT_CATEGORIES 참고)
        payload: 이벤트 상세 데이터
        session_id: 세션 ID (선택)
        task_id: 태스크 ID (선택)
        persona_id: 페르소나 ID (선택, gitko/sena/lubit 등)
        quality: 품질 메트릭 0.0-1.0 (선택, 자동 추가됨)
        latency_ms: 레이턴시 밀리초 (선택, 자동 추가됨)
        sync: True면 즉시 쓰기, False면 버퍼링 (기본 True)
    
    Returns:
        성공 여부
    
    Example:
        emit_event('task_started', {
            'goal': 'RAG 시스템 개선',
            'priority': 'high'
        }, task_id='task-001', persona_id='gitko', quality=0.85)
    """
    try:
        # Build event record
        record = {
            'ts': datetime.now(timezone.utc).isoformat(),
            'timestamp': time.time(),  # Unix timestamp for filtering
            'event_type': event_type,  # Core 권장: 일관된 필드명 사용
        }
        
        # Add optional IDs
        if session_id:
            record['session_id'] = session_id
        if task_id:
            record['task_id'] = task_id
        if persona_id:
            record['persona_id'] = persona_id
        if correlation_id:
            record['correlation_id'] = correlation_id
        
        # Core(合) 권장: 자동 메트릭 추가로 정보 밀도 향상
        if quality is not None:
            record['quality'] = round(quality, 3)
        if latency_ms is not None:
            record['latency_ms'] = round(latency_ms, 1)
        
        # Normalize field names before merging (Core 권장: 필드명 통합)
        normalized_payload = _normalize_fields(payload)
        
        # Merge payload (payload의 quality/latency가 우선순위)
        record.update(normalized_payload)

        # Auto-start registry recording for *_start events (only if not already recorded)
        if event_type.endswith('_start') or event_type in {'task_started', 'thesis_start', 'synthesis_start'}:
            _record_start(event_type, task_id, session_id, persona_id, record.get('correlation_id'))
        else:
            # Attempt latency auto-enrichment for end/completed events if latency_ms absent
            if 'latency_ms' not in record:
                auto_latency = _consume_latency(event_type, task_id, session_id, persona_id, record.get('correlation_id'))
                if auto_latency is not None:
                    record['latency_ms'] = round(auto_latency, 1)
        
        # Write to ledger (thread-safe)
        if sync:
            _write_sync(record)
        else:
            _write_async(record)
        
        return True
        
    except Exception as e:
        # Silent failure to not disrupt main workflow
        # Structured logging for debugging without blocking caller
        _logger.warning(f"Failed to emit {event_type}: {e}", exc_info=False, extra={
            'event_type': event_type,
            'task_id': task_id,
            'session_id': session_id,
        })
        return False


def _write_sync(record: Dict[str, Any]) -> None:
    """Synchronous write with lock and exception isolation"""
    try:
        with _write_lock:
            _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_LEDGER_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
    except Exception as e:
        _logger.error(f"Sync write failed for event {record.get('event_type', 'unknown')}: {e}", exc_info=False)
        # Silent failure - do not propagate to caller


def _async_queue_worker():
    """Background worker for async writes"""
    while not _worker_stop_event.is_set():
        try:
            # Block with timeout to allow graceful shutdown
            record = _async_queue.get(timeout=0.5)
            if record is None:  # Poison pill
                break
            _write_sync(record)
        except Exception as e:
            # Worker should never crash
            _logger.error(f"Async worker error: {e}", exc_info=False)
            continue


def _ensure_async_worker():
    """Lazy initialize async queue and worker thread"""
    global _async_queue, _async_worker
    if _async_queue is None:
        _async_queue = Queue(maxsize=_async_queue_max_size)
        _async_worker = Thread(target=_async_queue_worker, daemon=True, name='EventEmitterWorker')
        _async_worker.start()
        _logger.debug("Async queue worker started")


def _write_async(record: Dict[str, Any]) -> None:
    """Async write via queue with safe fallback"""
    try:
        _ensure_async_worker()
        _async_queue.put_nowait(record)
    except QueueFull:
        _logger.warning(f"Async queue full (size={_async_queue_max_size}), falling back to sync write")
        _write_sync(record)
    except Exception as e:
        _logger.error(f"Async write setup failed: {e}, falling back to sync", exc_info=False)
        _write_sync(record)


def emit_system_event(event_type: str, details: str, **kwargs) -> bool:
    """
    시스템 이벤트 발생 (간편 래퍼)
    
    Example:
        emit_system_event('migration', 'D drive to C drive', 
                         reason='SSD_performance', status='completed')
    """
    payload = {'details': details}
    payload.update(kwargs)
    return emit_event(event_type, payload)


def emit_task_lifecycle(
    lifecycle: str,
    task_id: str,
    **kwargs
) -> bool:
    """
    태스크 라이프사이클 이벤트 (간편 래퍼)
    
    Args:
        lifecycle: 'started' | 'completed' | 'failed'
        task_id: 태스크 ID
        **kwargs: 추가 데이터
    
    Example:
        emit_task_lifecycle('started', 'task-001', goal='AGI 설명', persona='gitko')
        emit_task_lifecycle('completed', 'task-001', quality=0.85, confidence=0.78)
    """
    event_type = f"task_{lifecycle}"
    return emit_event(event_type, kwargs, task_id=task_id)


def start_timed_event(base_event: str, *, task_id: Optional[str] = None, session_id: Optional[str] = None,
                      persona_id: Optional[str] = None, correlation_id: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Manual start of a timed event. Returns a token dict for later completion."""
    payload = payload or {}
    emit_event(f'{base_event}_start', payload, task_id=task_id, session_id=session_id, persona_id=persona_id, correlation_id=correlation_id)
    return {
        'base_event': base_event,
        'task_id': task_id,
        'session_id': session_id,
        'persona_id': persona_id,
        'correlation_id': correlation_id,
    }

def complete_timed_event(token: Dict[str, Any], payload: Optional[Dict[str, Any]] = None, *, success: Optional[bool] = None) -> None:
    """Complete a previously started timed event; auto latency injected if possible."""
    payload = payload or {}
    if success is not None:
        payload['success'] = success
    emit_event(f"{token['base_event']}_end", payload,
               task_id=token.get('task_id'), session_id=token.get('session_id'),
               persona_id=token.get('persona_id'), correlation_id=token.get('correlation_id'))


def emit_alert(
    severity: str,
    message: str,
    component: str,
    **kwargs
) -> bool:
    """
    알림 이벤트 발생
    
    Args:
        severity: 'info' | 'warning' | 'error' | 'critical'
        message: 알림 메시지
        component: 관련 컴포넌트 (예: 'health_gate', 'proxy', 'core_gateway')
        **kwargs: 추가 데이터
    
    Example:
        emit_alert('warning', 'Proxy port 18091 not responding', 
                   component='proxy', port=18091)
    """
    payload = {
        'severity': severity,
        'message': message,
        'component': component
    }
    payload.update(kwargs)
    return emit_event('alert_triggered', payload)


def emit_monitoring_snapshot(metrics: Dict[str, float]) -> bool:
    """
    모니터링 스냅샷 기록
    
    Example:
        emit_monitoring_snapshot({
            'confidence': 0.786,
            'quality': 0.691,
            'second_pass_rate': 0.137,
            'cpu_percent': 50.9,
            'memory_percent': 33.2
        })
    """
    return emit_event('performance_metric', metrics)


# Backward compatibility: alias to existing memory_bus
def append_ledger(record: Dict[str, Any]) -> None:
    """
    Backward compatibility with memory_bus.append_ledger
    
    Automatically extracts event type and IDs from record
    """
    # Support both legacy 'event' and new 'event_type' keys
    event_type = record.get('event_type') or record.get('event', 'unknown')
    task_id = record.get('task_id')
    session_id = record.get('session_id')
    persona_id = record.get('persona_id')
    
    # Remove metadata from payload
    payload = {k: v for k, v in record.items() 
               if k not in ('event', 'event_type', 'task_id', 'session_id', 'persona_id', 'ts', 'timestamp')}
    
    emit_event(
        event_type,
        payload,
        session_id=session_id,
        task_id=task_id,
        persona_id=persona_id
    )


if __name__ == '__main__':
    # Self-test
    print(f"[EventEmitter] Ledger path: {_LEDGER_PATH}")
    print(f"[EventEmitter] Event categories: {len(EVENT_CATEGORIES)}")
    
    # Test emit
    success = emit_event('system_startup', {
        'component': 'event_emitter',
        'version': '1.0',
        'test_mode': True
    })
    
    print(f"[EventEmitter] Test emit: {'✅ OK' if success else '❌ FAILED'}")
