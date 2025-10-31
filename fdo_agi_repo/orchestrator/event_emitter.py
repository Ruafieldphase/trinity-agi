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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from threading import Lock

# Thread-safe write lock
_write_lock = Lock()

# Repo root detection
_REPO_ROOT = Path(__file__).parent.parent
_LEDGER_PATH = _REPO_ROOT / "memory" / "resonance_ledger.jsonl"

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


def emit_event(
    event_type: str,
    payload: Dict[str, Any],
    *,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    persona_id: Optional[str] = None,
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
        sync: True면 즉시 쓰기, False면 버퍼링 (기본 True)
    
    Returns:
        성공 여부
    
    Example:
        emit_event('task_started', {
            'goal': 'RAG 시스템 개선',
            'priority': 'high'
        }, task_id='task-001', persona_id='gitko')
    """
    try:
        # Build event record
        record = {
            'ts': datetime.now(timezone.utc).isoformat(),
            'timestamp': time.time(),  # Unix timestamp for filtering
            'event': event_type,
        }
        
        # Add optional IDs
        if session_id:
            record['session_id'] = session_id
        if task_id:
            record['task_id'] = task_id
        if persona_id:
            record['persona_id'] = persona_id
        
        # Merge payload
        record.update(payload)
        
        # Write to ledger (thread-safe)
        if sync:
            _write_sync(record)
        else:
            _write_async(record)
        
        return True
        
    except Exception as e:
        # Silent failure to not disrupt main workflow
        # Log to stderr if available
        import sys
        print(f"[EventEmitter] Failed to emit {event_type}: {e}", file=sys.stderr)
        return False


def _write_sync(record: Dict[str, Any]) -> None:
    """Synchronous write with lock"""
    with _write_lock:
        _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_LEDGER_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')


def _write_async(record: Dict[str, Any]) -> None:
    """Async write via queue (future enhancement)"""
    # For now, just call sync version
    # TODO: Implement queue-based buffering for high-throughput scenarios
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
        component: 관련 컴포넌트 (예: 'health_gate', 'proxy', 'lumen_gateway')
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
    event_type = record.get('event', 'unknown')
    task_id = record.get('task_id')
    session_id = record.get('session_id')
    persona_id = record.get('persona_id')
    
    # Remove metadata from payload
    payload = {k: v for k, v in record.items() 
               if k not in ('event', 'task_id', 'session_id', 'persona_id', 'ts', 'timestamp')}
    
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
