#!/usr/bin/env python3
"""
AGI Metrics Collector
실시간으로 resonance_ledger.jsonl을 분석하여 핵심 메트릭 추출
+ Lumen gateway, Local proxy, System 리소스 통합 모니터링
"""

import json
import subprocess
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Sequence, Tuple, Callable
from collections import defaultdict
import statistics
import os
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    # Alignment with CLI summaries: reuse default regression filters if available
    from scripts.summarize_ledger import DEFAULT_EXCLUDE_PREFIXES  # type: ignore
except Exception:
    DEFAULT_EXCLUDE_PREFIXES: Tuple[str, ...] = ()


def ttl_cache(ttl_seconds: float = 60.0):
    """TTL (Time-To-Live) 캐싱 데코레이터

    Args:
        ttl_seconds: 캐시 유효 시간 (초)

    Usage:
        @ttl_cache(ttl_seconds=60.0)
        def expensive_function(arg1, arg2):
            ...
    """
    def decorator(func: Callable) -> Callable:
        cache: Dict[str, Tuple[Any, float]] = {}
        lock = threading.Lock()

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성 (self 제외)
            cache_key = str((args[1:], tuple(sorted(kwargs.items()))))
            current_time = time.time()

            with lock:
                if cache_key in cache:
                    cached_value, cached_time = cache[cache_key]
                    if current_time - cached_time < ttl_seconds:
                        return cached_value

                # 캐시 miss: 함수 실행
                result = func(*args, **kwargs)
                cache[cache_key] = (result, current_time)
                return result

        # 캐시 클리어 함수 추가
        def clear_cache():
            with lock:
                cache.clear()

        wrapper.clear_cache = clear_cache  # type: ignore
        return wrapper

    return decorator


class MetricsCollector:
    """AGI 시스템 메트릭 수집 및 분석"""

    def __init__(self, repo_root: Optional[Path] = None, exclude_prefixes: Optional[Sequence[str]] = None, include_default_excludes: bool = True):
        if repo_root is None:
            # 스크립트 위치 기준으로 repo root 찾기
            repo_root = Path(__file__).parent.parent

        self.repo_root = Path(repo_root)
        self.ledger_path = self.repo_root / "memory" / "resonance_ledger.jsonl"
        self.coordinate_path = self.repo_root / "memory" / "coordinate.jsonl"
        self.health_gate_state_path = self.repo_root / "outputs" / "health_gate_state.json"
        combined: List[str] = []
        if include_default_excludes and DEFAULT_EXCLUDE_PREFIXES:
            combined.extend(DEFAULT_EXCLUDE_PREFIXES)
        if exclude_prefixes:
            combined.extend(exclude_prefixes)
        self.exclude_prefixes: Tuple[str, ...] = tuple(dict.fromkeys(combined))
        self.default_excludes_applied: bool = bool(include_default_excludes and DEFAULT_EXCLUDE_PREFIXES)

    def _filters_snapshot(self) -> Dict[str, Any]:
        return {
            "exclude_prefixes": list(self.exclude_prefixes),
            "default_excludes_applied": self.default_excludes_applied,
        }

    @staticmethod
    def _to_epoch_ts(raw: Any) -> float:
        """Normalize various timestamp representations to epoch seconds (float).

        Accepts:
        - float/int: treated as epoch seconds
        - str: ISO 8601 string (with optional 'Z'), converted to epoch
        Returns 0.0 when parsing fails or value missing.
        """
        try:
            if isinstance(raw, (int, float)):
                return float(raw)
            if isinstance(raw, str) and raw:
                try:
                    # Support 'Z' suffix by mapping to +00:00
                    s = raw.replace('Z', '+00:00')
                    return datetime.fromisoformat(s).timestamp()
                except Exception:
                    return 0.0
        except Exception:
            return 0.0
        return 0.0

    @staticmethod
    def _extract_task_id(event: Dict[str, Any]) -> Optional[str]:
        task_id = event.get("task_id")
        if task_id:
            return str(task_id)
        task = event.get("task")
        if isinstance(task, dict):
            task_id = task.get("task_id")
            if task_id:
                return str(task_id)
        return None

    def _is_excluded(self, event: Dict[str, Any]) -> bool:
        if not self.exclude_prefixes:
            return False
        task_id = self._extract_task_id(event)
        if not task_id:
            return False
        return any(task_id.startswith(prefix) for prefix in self.exclude_prefixes)

    def read_events(self, hours: float = 24.0) -> List[Dict[str, Any]]:
        """최근 N시간 이벤트 읽기"""
        if not self.ledger_path.exists():
            return []

        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        events = []

<<<<<<< HEAD
        # Ledger는 다양한 소스가 append하는 JSONL이라 인코딩이 섞일 수 있다.
        # 모니터링이 전체를 멈추지 않도록 디코드 오류는 치환 후 파서에서 스킵한다.
        with open(self.ledger_path, 'r', encoding='utf-8', errors='replace') as f:
=======
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
>>>>>>> origin/main
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # ts 필드를 timestamp로 변환하여 비교
                ts_str = event.get('ts', '')
                if ts_str:
                    try:
                        event_ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00')).timestamp()
                        if event_ts < cutoff_time:
                            continue
                    except (ValueError, AttributeError):
                        # 파싱 실패 시 해당 이벤트 포함
                        pass
                if self._is_excluded(event):
                    continue
                events.append(event)

        return events

    def get_realtime_metrics(self, hours: float = 1.0) -> Dict[str, Any]:
        """실시간 메트릭 추출 (최근 N시간)"""
        events = self.read_events(hours)

        # 이벤트 카운트
        event_counts = defaultdict(int)
        for event in events:
            event_type = event.get('event', 'unknown')
            event_counts[event_type] += 1

        # 메트릭 계산
        confidence_values = []
        quality_values = []
        replan_count = 0
        second_pass_count = 0

        # Persona별 LLM 호출 성능
        persona_stats = defaultdict(lambda: {'success': 0, 'failure': 0, 'total_duration': 0.0})

        # Task별 분석
        task_ids = set()
        
        # Evidence correction 통계
        evidence_correction_attempts = 0
        evidence_correction_hits = []  # hits 값들
        evidence_correction_added = []  # added 값들
        evidence_correction_relevance = []  # avg_relevance 값들
        evidence_correction_fallbacks = 0  # fallback_used=True 카운트

        for event in events:
            event_type = event.get('event')

            # Meta-cognition confidence
            if event_type == 'meta_cognition':
                # confidence는 이벤트 자체에 바로 있음
                if 'confidence' in event:
                    confidence_values.append(event['confidence'])

            # Eval quality
            if event_type == 'eval':
                eval_data = event.get('eval', {})
                if 'quality' in eval_data and eval_data['quality'] is not None:
                    quality_values.append(eval_data['quality'])

            # RUNE replan
            if event_type == 'rune':
                rune_data = event.get('rune', {})
                if rune_data.get('replan'):
                    replan_count += 1

            # Second pass
            if event_type == 'second_pass':
                second_pass_count += 1
            
            # Evidence correction
            if event_type == 'evidence_correction':
                evidence_correction_attempts += 1
                if 'hits' in event:
                    evidence_correction_hits.append(event['hits'])
                if 'added' in event:
                    evidence_correction_added.append(event['added'])
                if 'avg_relevance' in event:
                    evidence_correction_relevance.append(event['avg_relevance'])
                if event.get('fallback_used'):
                    evidence_correction_fallbacks += 1

            # Persona LLM stats
            # 최신 로그 스키마는 persona_llm_run 을 사용하고, 과거 스키마는 persona_llm_end 를 사용합니다.
            # 두 타입 모두 동일하게 집계합니다.
            if event_type in ('persona_llm_end', 'persona_llm_run'):
                persona = event.get('persona', 'unknown')
                ok = event.get('ok', False)
                duration = event.get('duration_sec', 0.0)

                if ok:
                    persona_stats[persona]['success'] += 1
                else:
                    persona_stats[persona]['failure'] += 1
                persona_stats[persona]['total_duration'] += duration

            # Task tracking
            task_id = event.get('task_id')
            if task_id:
                task_ids.add(task_id)

        # 통계 계산
        avg_confidence = statistics.mean(confidence_values) if confidence_values else 0.0
        avg_quality = statistics.mean(quality_values) if quality_values else 0.0
        total_tasks = len(task_ids)
        
        # Evidence correction 통계 계산
        avg_evidence_hits = statistics.mean(evidence_correction_hits) if evidence_correction_hits else 0.0
        avg_evidence_added = statistics.mean(evidence_correction_added) if evidence_correction_added else 0.0
        avg_evidence_relevance = statistics.mean(evidence_correction_relevance) if evidence_correction_relevance else 0.0

        return {
            'timestamp': datetime.now().isoformat(),
            'window_hours': hours,
            'total_events': len(events),
            'event_counts': dict(event_counts),
            'metrics': {
                'avg_confidence': round(avg_confidence, 3),
                'avg_quality': round(avg_quality, 3),
                'total_tasks': total_tasks,
                'replan_count': replan_count,
                'second_pass_count': second_pass_count,
                'second_pass_rate': round(second_pass_count / max(total_tasks, 1), 3),
                'samples': {
                    'confidence': len(confidence_values),
                    'quality': len(quality_values),
                },
                'evidence_correction': {
                    'attempts': evidence_correction_attempts,
                    'avg_hits': round(avg_evidence_hits, 2),
                    'avg_added': round(avg_evidence_added, 2),
                    'avg_relevance': round(avg_evidence_relevance, 3),
                    'success_rate': round(
                        sum(1 for h in evidence_correction_hits if h > 0) / max(len(evidence_correction_hits), 1),
                        3
                    ) if evidence_correction_hits else 0.0,
                    'fallback_rate': round(
                        (evidence_correction_fallbacks / evidence_correction_attempts) if evidence_correction_attempts else 0.0,
                        3
                    ),
                }
            },
            'persona_performance': {
                persona: {
                    'success_rate': round(
                        stats['success'] / max(stats['success'] + stats['failure'], 1),
                        3
                    ),
                    'avg_duration': round(
                        stats['total_duration'] / max(stats['success'] + stats['failure'], 1),
                        2
                    ),
                    'total_calls': stats['success'] + stats['failure'],
                }
                for persona, stats in persona_stats.items()
            },
            'filters': self._filters_snapshot(),
        }

    def get_timeline_data(self, hours: float = 24.0, interval_minutes: int = 30) -> List[Dict[str, Any]]:
        """시간대별 메트릭 타임라인"""
        events = self.read_events(hours)

        # 시간대별 이벤트 분류
        timeline = []
        interval_seconds = interval_minutes * 60

        if not events:
            return timeline

        # 시작/끝 시간 계산 (ts가 문자열/숫자 혼재 가능 → 정규화 필요)
        ts_values = [self._to_epoch_ts(e.get('ts')) for e in events]
        ts_values = [t for t in ts_values if t > 0]
        if not ts_values:
            return timeline
        min_ts = min(ts_values)
        max_ts = max(ts_values)

        current_ts = min_ts
        while current_ts <= max_ts:
            next_ts = current_ts + interval_seconds

            # 해당 구간의 이벤트 필터링
            interval_events = []
            for e in events:
                ts = self._to_epoch_ts(e.get('ts'))
                if ts and current_ts <= ts < next_ts:
                    interval_events.append(e)

            # 구간별 메트릭 계산
            quality_values = []
            confidence_values = []
            eval_counter = 0
            second_pass_counter = 0

            for event in interval_events:
                event_type = event.get('event')
                if event_type == 'eval':
                    eval_counter += 1
                    q = event.get('eval', {}).get('quality')
                    if q is not None:
                        quality_values.append(q)

                if event_type == 'meta_cognition':
                    # confidence는 이벤트 자체에 바로 있음
                    c = event.get('confidence')
                    if c is not None:
                        confidence_values.append(c)
                if event_type == 'second_pass':
                    second_pass_counter += 1

            timeline.append({
                'timestamp': datetime.fromtimestamp(current_ts).isoformat(),
                'event_count': len(interval_events),
                'avg_quality': round(statistics.mean(quality_values), 3) if quality_values else None,
                'avg_confidence': round(statistics.mean(confidence_values), 3) if confidence_values else None,
                'second_pass_rate': round(second_pass_counter / eval_counter, 3) if eval_counter else 0.0,
            })

            current_ts = next_ts

        return timeline

    def get_persona_timeline_data(self, hours: float = 24.0, interval_minutes: int = 30) -> Dict[str, Any]:
        """페르소나별 시간대 성능 타임라인
        반환 형식:
        {
          "bins": [ISO8601...],
          "personas": {
            "thesis": {"success_rate": [...], "avg_duration": [...], "total_calls": [...]},
            ...
          }
        }
        """
        events = self.read_events(hours)

        result: Dict[str, Any] = {"bins": [], "personas": {}}
        if not events:
            return result

        interval_seconds = interval_minutes * 60
        ts_values = [self._to_epoch_ts(e.get('ts')) for e in events]
        ts_values = [t for t in ts_values if t > 0]
        if not ts_values:
            return result
        min_ts = min(ts_values)
        max_ts = max(ts_values)

        current_ts = min_ts
        bins: List[str] = []
        # First pass: gather persona names to ensure stable arrays
        persona_names = set()
        for e in events:
            et = e.get('event')
            if et in ('persona_llm_end', 'persona_llm_run'):
                persona_names.add(e.get('persona', 'unknown'))

        personas: Dict[str, Dict[str, List[Optional[float]]]] = {}
        for name in persona_names:
            personas[name] = {
                "success_rate": [],
                "avg_duration": [],
                "total_calls": [],
            }

        while current_ts <= max_ts:
            next_ts = current_ts + interval_seconds
            bins.append(datetime.fromtimestamp(current_ts).isoformat())

            # 집계 버킷
            bucket: Dict[str, Dict[str, float]] = defaultdict(lambda: {
                'success': 0.0,
                'failure': 0.0,
                'total_duration': 0.0,
            })

            for e in events:
                ts = self._to_epoch_ts(e.get('ts'))
                if not (ts and current_ts <= ts < next_ts):
                    continue
                et = e.get('event')
                if et in ('persona_llm_end', 'persona_llm_run'):
                    persona = e.get('persona', 'unknown')
                    ok = bool(e.get('ok', False))
                    dur = float(e.get('duration_sec', 0.0))
                    if ok:
                        bucket[persona]['success'] += 1
                    else:
                        bucket[persona]['failure'] += 1
                    bucket[persona]['total_duration'] += dur

            # 각 페르소나에 대해 값 push (없으면 null 유지)
            for name in persona_names:
                stats = bucket.get(name)
                if not stats:
                    personas[name]["success_rate"].append(None)
                    personas[name]["avg_duration"].append(None)
                    personas[name]["total_calls"].append(0.0)
                else:
                    total = stats['success'] + stats['failure']
                    sr = (stats['success'] / total) if total > 0 else None
                    ad = (stats['total_duration'] / total) if total > 0 else None
                    personas[name]["success_rate"].append(round(sr, 3) if sr is not None else None)
                    personas[name]["avg_duration"].append(round(ad, 2) if ad is not None else None)
                    personas[name]["total_calls"].append(float(total))

            current_ts = next_ts

        result["bins"] = bins
        result["personas"] = personas
        return result

    def _resolve_proxy_port(self) -> int:
        """프록시 포트 결정: outputs/proxy_info.json > ENV(PROXY_PORT) > 8090"""
        try:
            proxy_info = self.repo_root / 'outputs' / 'proxy_info.json'
            if proxy_info.exists():
                # Windows PowerShell이 BOM 추가할 수 있으므로 utf-8-sig 사용
                with open(proxy_info, 'r', encoding='utf-8-sig') as f:
                    info = json.load(f)
                    port = int(info.get('port', 0))
                    if port:
                        return port
        except Exception:
            pass

        try:
            env_port = int(os.getenv('PROXY_PORT', '0'))
            if env_port:
                return env_port
        except Exception:
            pass

        return 8090

    def _load_health_gate_state(self) -> Dict[str, Any]:
        if self.health_gate_state_path.exists():
            try:
                with open(self.health_gate_state_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "failure_streak": 0,
            "success_streak": 0,
            "cooldown_until": None,
            "gate_open": True,
            "last_updated": None,
        }

    def _save_health_gate_state(self, state: Dict[str, Any]) -> None:
        try:
            self.health_gate_state_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.health_gate_state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _apply_health_gate(self, immediate_pass: bool) -> Dict[str, Any]:
        """Apply hysteresis to the health gate and expose cooldown metadata."""
        failure_limit = int(os.getenv("HEALTH_GATE_FAILURE_LIMIT", "2"))
        recovery_target = int(os.getenv("HEALTH_GATE_RECOVERY_STREAK", "2"))
        cooldown_minutes = float(os.getenv("HEALTH_GATE_COOLDOWN_MINUTES", "15"))

        state = self._load_health_gate_state()
        now = datetime.utcnow()

        cooldown_until_raw = state.get("cooldown_until")
        cooldown_until_dt: Optional[datetime] = None
        if isinstance(cooldown_until_raw, str):
            try:
                cooldown_until_dt = datetime.fromisoformat(cooldown_until_raw)
            except ValueError:
                cooldown_until_dt = None

        gate_open = bool(state.get("gate_open", True))
        failure_streak = int(state.get("failure_streak", 0))
        success_streak = int(state.get("success_streak", 0))
        cooldown_active = False

        if immediate_pass:
            failure_streak = 0
            success_streak += 1

            if cooldown_until_dt and now < cooldown_until_dt:
                cooldown_active = True
                gate_open = False
                success_streak = 0
            elif success_streak >= recovery_target:
                gate_open = True
                cooldown_until_dt = None
                success_streak = recovery_target
        else:
            success_streak = 0
            failure_streak += 1
            if failure_streak >= failure_limit:
                gate_open = False
                if cooldown_minutes > 0:
                    cooldown_until_dt = now + timedelta(minutes=cooldown_minutes)
                    cooldown_active = True

        state.update(
            {
                "failure_streak": failure_streak,
                "success_streak": success_streak,
                "gate_open": gate_open,
                "last_updated": now.isoformat(),
                "cooldown_until": cooldown_until_dt.isoformat() if cooldown_until_dt else None,
            }
        )
        self._save_health_gate_state(state)

        cooldown_until_str = state.get("cooldown_until")
        if cooldown_until_dt is not None and now < cooldown_until_dt:
            cooldown_active = True

        effective_open = gate_open and not cooldown_active

        return {
            "gate_open": effective_open,
            "raw_gate_open": gate_open,
            "immediate_pass": immediate_pass,
            "failure_streak": failure_streak,
            "failure_limit": failure_limit,
            "success_streak": success_streak,
            "recovery_target": recovery_target,
            "cooldown_minutes": cooldown_minutes,
            "cooldown_until": cooldown_until_str,
            "cooldown_active": cooldown_active,
        }

    def get_health_status(self) -> Dict[str, Any]:
        """시스템 헬스 상태 평가 (AGI + Lumen + Proxy + System)"""
        recent_hours = float(os.getenv('HEALTH_RECENT_HOURS', '1.0'))
        metrics = self.get_realtime_metrics(hours=recent_hours)

        # 임계값 (환경변수나 설정에서 가져올 수 있음)
        # 기존 핵심 기준치 + UI/퍼소나 관련 경고 기준을 함께 제공하여 프론트가 하드코딩 없이 동작하도록 함
        THRESHOLDS = {
            'min_confidence': float(os.getenv('AGI_MIN_CONFIDENCE', '0.60')),
            'min_quality': float(os.getenv('AGI_MIN_QUALITY', '0.65')),
            'max_second_pass_rate': float(os.getenv('AGI_MAX_SECOND_PASS_RATE', '2.0')),
            # UI/Alert 보조 임계값 (대시보드가 우선 사용)
            'agi_success_warning_pct': float(os.getenv('AGI_SUCCESS_WARNING_PCT', '70')),
            'replan_rate_warning_pct': float(os.getenv('AGI_REPLAN_WARNING_PCT', '10')),
            'agi_avg_duration_warn_s': float(os.getenv('AGI_AVG_DURATION_WARN_S', '10')),
            'agi_inactive_threshold_hours': float(os.getenv('AGI_INACTIVE_THRESHOLD_HOURS', '2')),
            # Persona 전용 임계값
            'persona_success_warning_pct': float(os.getenv('PERSONA_SUCCESS_WARNING_PCT', '60')),
            'persona_success_critical_pct': float(os.getenv('PERSONA_SUCCESS_CRITICAL_PCT', '50')),
            'persona_avg_duration_s': float(os.getenv('PERSONA_AVG_DURATION_S', '10')),
        }

        # 최소 샘플 정책
        MIN_SAMPLES = {
            'confidence': int(os.getenv('MIN_CONFIDENCE_SAMPLES', '5')),
            'quality': int(os.getenv('MIN_QUALITY_SAMPLES', '5')),
        }

        samples = metrics['metrics'].get('samples', {'confidence': 0, 'quality': 0})

        confidence_ok = True
        quality_ok = True
        notes: Dict[str, Any] = {}

        if samples['confidence'] >= MIN_SAMPLES['confidence']:
            confidence_ok = metrics['metrics']['avg_confidence'] >= THRESHOLDS['min_confidence']
        else:
            notes['confidence'] = f"insufficient_samples({samples['confidence']}<{MIN_SAMPLES['confidence']})"

        if samples['quality'] >= MIN_SAMPLES['quality']:
            quality_ok = metrics['metrics']['avg_quality'] >= THRESHOLDS['min_quality']
        else:
            notes['quality'] = f"insufficient_samples({samples['quality']}<{MIN_SAMPLES['quality']})"

        health_checks = {
            'confidence_ok': confidence_ok,
            'quality_ok': quality_ok,
            'second_pass_ok': metrics['metrics']['second_pass_rate'] <= THRESHOLDS['max_second_pass_rate'],
        }

        # External services 상태 - 병렬 호출로 최적화
        proxy_port = self._resolve_proxy_port()

        with ThreadPoolExecutor(max_workers=3) as executor:
            # 3개 서비스를 동시에 체크
            futures = {
                executor.submit(self._check_lumen_gateway): 'lumen',
                executor.submit(self._check_local_proxy, proxy_port): 'proxy',
                executor.submit(self._check_system_resources): 'system'
            }

            # 결과 수집
            external_results = {}
            for future in as_completed(futures):
                service_name = futures[future]
                try:
                    external_results[service_name] = future.result()
                except Exception as e:
                    # 개별 서비스 실패 시 에러 상태 반환
                    external_results[service_name] = {
                        'ok': False,
                        'error': f'Exception: {str(e)[:100]}'
                    }

        lumen_status = external_results['lumen']
        proxy_status = external_results['proxy']
        system_status = external_results['system']

        health_checks['lumen_ok'] = lumen_status['ok']
        # Proxy는 옵션 서비스이므로 health 판정에서 제외
        # health_checks['proxy_ok'] = proxy_status['ok']  
        health_checks['system_ok'] = system_status['ok']

        immediate_pass = all(health_checks.values())
        gate_snapshot = self._apply_health_gate(immediate_pass)
        overall_healthy = gate_snapshot["gate_open"] and gate_snapshot["immediate_pass"]

        # Information Flow 추가
        flow_data = self.get_information_flow_score(hours=recent_hours)
        flow_healthy = flow_data['flow_score'] > 0.4  # Moderate 이상이면 OK
        
        return {
            'healthy': overall_healthy and flow_healthy,
            'checks': health_checks,
            'thresholds': THRESHOLDS,
            'current_values': {
                'confidence': metrics['metrics']['avg_confidence'],
                'quality': metrics['metrics']['avg_quality'],
                'second_pass_rate': metrics['metrics']['second_pass_rate'],
            },
            'policy': {
                'recent_hours': recent_hours,
                'min_samples': MIN_SAMPLES,
                'samples': samples,
                'notes': notes,
                'resolved_proxy_port': proxy_port,  # Show the resolved port
            },
            'external_services': {
                'lumen': lumen_status,
                'proxy': proxy_status,
                'system': system_status,
            },
            'information_flow': {
                'healthy': flow_healthy,
                'score': flow_data['flow_score'],
                'status': flow_data['status'],
                'components': flow_data['components'],
                'recommendation': flow_data['recommendation'],
            },
            'filters': self._filters_snapshot(),
            'health_gate': gate_snapshot,
        }

    @ttl_cache(ttl_seconds=60.0)
    def _check_lumen_gateway(self) -> Dict[str, Any]:
        """Lumen gateway 헬스 체크 (HTTP ping) - 60초 캐싱"""
        lumen_url = os.getenv('LUMEN_GATEWAY_URL', 'https://lumen-gateway-x4qvsargwa-uc.a.run.app/chat')
        timeout_sec = int(os.getenv('LUMEN_TIMEOUT_SEC', '20'))

        try:
            import requests
            response = requests.post(
                lumen_url,
                json={'message': 'ping'},
                timeout=timeout_sec
            )
            response_data = response.json()
            ok = response.status_code == 200 and response_data.get('success', False)
            return {
                'ok': ok,
                'status_code': response.status_code,
                'response_preview': str(response_data)[:200],
            }
        except Exception as e:
            return {
                'ok': False,
                'error': str(e)[:200],
            }

    @ttl_cache(ttl_seconds=60.0)
    def _check_local_proxy(self, port: int = 8090) -> Dict[str, Any]:
        """Local proxy 포트 listening 확인 - 60초 캐싱"""
        try:
            # PowerShell check_port.ps1과 동일한 로직 (파이썬 버전)
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stdout
            port_pattern = f':{port}'
            listening = port_pattern in output

            return {
                'ok': listening,
                'port': port,
                'status': 'active' if listening else 'not_listening',
            }
        except Exception as e:
            return {
                'ok': False,
                'port': port,
                'error': str(e)[:100],
            }

    @ttl_cache(ttl_seconds=60.0)
    def _check_system_resources(self) -> Dict[str, Any]:
        """시스템 리소스 모니터링 (CPU, Memory, Disk) - 60초 캐싱"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # 임계값 (환경변수에서 가져올 수 있음)
            cpu_warn = float(os.getenv('SYSTEM_CPU_WARN', '80.0'))
            mem_warn = float(os.getenv('SYSTEM_MEM_WARN', '85.0'))
            disk_warn = float(os.getenv('SYSTEM_DISK_WARN', '90.0'))

            ok = (
                cpu_percent < cpu_warn and
                memory.percent < mem_warn and
                disk.percent < disk_warn
            )

            return {
                'ok': ok,
                'cpu_percent': round(cpu_percent, 1),
                'memory_percent': round(memory.percent, 1),
                'disk_percent': round(disk.percent, 1),
                'warnings': {
                    'cpu': cpu_percent >= cpu_warn,
                    'memory': memory.percent >= mem_warn,
                    'disk': disk.percent >= disk_warn,
                }
            }
        except ImportError:
            return {
                'ok': True,  # psutil 없으면 건너뛰기
                'note': 'psutil not installed, skipping system checks'
            }
        except Exception as e:
            return {
                'ok': False,
                'error': str(e)[:100],
            }

    def get_information_flow_score(self, hours: float = 1.0) -> Dict[str, Any]:
        """정보이론 기반 AI 리듬 분석
        
        기존 메트릭을 활용하여:
        - 엔트로피 (패턴 다양성)
        - 상호정보량 (맥락 활용도)  
        - 채널 품질 (SNR)
        를 계산하여 "흐름" 상태 진단
        
        Args:
            hours: 분석 시간 윈도우
            
        Returns:
            flow_score: 0.0-1.0 (흐름 건강도)
            entropy: 0.0-1.0 (패턴 다양성)
            mutual_info: 0.0-1.0 (맥락 활용도)
            channel_quality: 0.0-1.0 (신호 품질)
            diversity: 0.0-1.0 (행동 다양성)
            recommendation: 권장사항
        """
        import math
        
        # 기존 메트릭 활용
        metrics = self.get_realtime_metrics(hours=hours)
        
        # 1. 엔트로피 계산 (패턴 다양성)
        entropy_score = self._calculate_entropy(metrics)
        
        # 2. 상호정보량 (맥락 활용도)
        mutual_info = self._calculate_mutual_information(metrics)
        
        # 3. 채널 품질 (SNR: Signal-to-Noise Ratio)
        channel_quality = self._calculate_channel_quality(metrics)
        
        # 4. 패턴 다양성 (행동 분포)
        diversity = self._calculate_pattern_diversity(metrics)
        
        # 종합 흐름 점수
        flow_score = (
            entropy_score * 0.3 +
            mutual_info * 0.3 +
            channel_quality * 0.2 +
            diversity * 0.2
        )
        
        # 권장사항 생성
        recommendation = self._generate_flow_recommendation(
            flow_score, entropy_score, mutual_info, diversity
        )
        
        return {
            'flow_score': round(flow_score, 3),
            'components': {
                'entropy': round(entropy_score, 3),
                'mutual_info': round(mutual_info, 3),
                'channel_quality': round(channel_quality, 3),
                'diversity': round(diversity, 3),
            },
            'status': 'flowing' if flow_score > 0.6 else 'stagnant' if flow_score < 0.4 else 'moderate',
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat(),
        }
    
    def _calculate_entropy(self, metrics: Dict[str, Any]) -> float:
        """엔트로피 계산 (패턴 다양성)
        
        낮은 엔트로피 = 예측 가능 (고인 물)
        높은 엔트로피 = 다양함 (흐르는 물)
        """
        import math
        
        # Persona 사용 패턴 분석
        personas = metrics.get('persona_performance', {})
        if not personas:
            return 0.5  # 중립
        
        # 각 persona의 호출 횟수
        counts = [p.get('total_calls', 0) for p in personas.values()]
        total = sum(counts)
        if total == 0:
            return 0.5
        
        # Shannon Entropy
        entropy = 0.0
        for count in counts:
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        # Normalize (0-1)
        max_entropy = math.log2(len(personas)) if len(personas) > 1 else 1.0
        normalized = entropy / max_entropy if max_entropy > 0 else 0.5
        
        return min(1.0, max(0.0, normalized))
    
    def _calculate_mutual_information(self, metrics: Dict[str, Any]) -> float:
        """상호정보량 계산 (맥락 활용도)
        
        높은 상호정보량 = 맥락에 잘 반응
        낮은 상호정보량 = 맥락 무시
        """
        # 성공률과 Persona의 상관관계
        personas = metrics.get('persona_performance', {})
        if not personas or len(personas) < 2:
            return 0.5
        
        # 각 Persona의 성공률 차이가 크면 맥락 의존적
        success_rates = [p.get('success_rate', 0.5) for p in personas.values()]
        if not success_rates:
            return 0.5
        
        mean = sum(success_rates) / len(success_rates)
        variance = sum((x - mean) ** 2 for x in success_rates) / len(success_rates)
        std_dev = variance ** 0.5
        
        # 정규화 (높은 분산 = 맥락 의존적)
        normalized = min(1.0, std_dev * 2)  # 0-0.5 범위를 0-1로 확장
        
        return normalized
    
    def _calculate_channel_quality(self, metrics: Dict[str, Any]) -> float:
        """채널 품질 (SNR) 계산
        
        높은 품질 = 낮은 에러율, 높은 성공률
        낮은 품질 = 높은 에러율, 불안정
        """
        # Persona별 평균 성공률
        personas = metrics.get('persona_performance', {})
        if not personas:
            return 0.5
        
        success_rates = [p.get('success_rate', 0.0) for p in personas.values()]
        if not success_rates:
            return 0.5
        
        avg_success = sum(success_rates) / len(success_rates)
        return avg_success  # 이미 0-1 범위
    
    def _calculate_pattern_diversity(self, metrics: Dict[str, Any]) -> float:
        """패턴 다양성 계산
        
        높은 다양성 = 여러 패턴 사용
        낮은 다양성 = 한 패턴에 편향
        """
        personas = metrics.get('persona_performance', {})
        if not personas:
            return 0.5
        
        # Gini 계수 역수 (1 - Gini)
        counts = sorted([p.get('total_calls', 0) for p in personas.values()], reverse=True)
        n = len(counts)
        total = sum(counts)
        
        if total == 0 or n == 0:
            return 0.5
        
        gini_sum = 0
        for i, count in enumerate(counts):
            gini_sum += (n - i) * count
        
        gini = (2 * gini_sum) / (n * total) - (n + 1) / n
        diversity = 1.0 - gini
        
        return min(1.0, max(0.0, diversity))
    
    def _generate_flow_recommendation(
        self, 
        flow_score: float,
        entropy: float,
        mutual_info: float,
        diversity: float
    ) -> str:
        """흐름 상태 기반 권장사항 생성"""
        
        if flow_score > 0.7:
            return "✅ Optimal flow state. Continue current rhythm."
        
        issues = []
        
        if entropy < 0.3:
            issues.append("Low entropy (pattern repetition)")
        
        if mutual_info < 0.3:
            issues.append("Low context utilization")
        
        if diversity < 0.3:
            issues.append("Low pattern diversity")
        
        if issues:
            action = "Consider: "
            if "pattern" in str(issues):
                action += "Explore new approaches. "
            if "context" in str(issues):
                action += "Increase contextual awareness. "
            if "diversity" in str(issues):
                action += "Vary action patterns. "
            
            return f"⚠️ Flow issues detected: {', '.join(issues)}. {action}"
        
        return "🔄 Moderate flow. Room for improvement in pattern variation."


def main():
    """CLI 인터페이스 - JSON 출력"""
    import sys
    
    collector = MetricsCollector()

    # 명령줄 인자 처리
    hours = 1.0
    if len(sys.argv) > 1:
        try:
            hours = float(sys.argv[1])
        except ValueError:
            pass

    # 통합 메트릭 수집
    output = {
        "timestamp": datetime.now().isoformat(),
        "time_window_hours": hours,
        "metrics": collector.get_realtime_metrics(hours=hours),
        "health": collector.get_health_status(),
        "timeline": collector.get_timeline_data(hours=min(hours * 6, 24), interval_minutes=30),
        "persona_timeline": collector.get_persona_timeline_data(hours=min(hours * 6, 24), interval_minutes=30),
    }

    # JSON 출력 - ASCII로 인코딩 (PowerShell 호환)
    print(json.dumps(output, indent=2, ensure_ascii=True))


if __name__ == '__main__':
    main()

