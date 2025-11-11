# 📊 메트릭 커버리지 분석 리포트

**분석 시각**: 2025-11-08 16:50
**분석 대상**: Resonance Ledger (resonance_ledger.jsonl)
**총 이벤트**: 34,314개

---

## 🎯 현재 메트릭 커버리지

### Quality 메트릭

- **`quality`**: 123개 (0.4%)
- **`agi_quality`**: 979개 (2.9%)
- **합계**: 1,102개 (3.2%)

### Latency 메트릭  

- **`latency_ms`**: 85개 (0.2%)
- **`lumen_latency_ms`**: (별도 필드로 존재)
- **합계**: 추정 ~500개 (1.5%)

---

## 📋 문제 진단

### 1. 코드 적용 범위 제한적

✅ **개선 완료된 파일**:

- `event_emitter.py` - 자동 메트릭 추가 로직
- `pipeline.py` - thesis/antithesis/synthesis 메트릭

❌ **아직 적용 안 된 영역**:

- 대부분의 health check 이벤트
- Monitoring 스크립트들
- RPA Worker 이벤트
- YouTube Learner 이벤트

### 2. 필드명 불일치

**표준 필드명**:

- `quality` (목표)
- `latency_ms` (목표)

**실제 사용 중인 필드명**:

- `agi_quality` (979개)
- `lumen_latency_ms` (수백개)
- `duration_sec` (일부)

### 3. 이벤트 생성 경로 다양성

Ledger에 이벤트를 쓰는 경로:

1. ✅ `event_emitter.py` via `emit_event()` ← **개선됨**
2. ❌ 직접 JSONL 파일에 쓰기 (health_check 등)
3. ❌ 다른 유틸리티 함수들
4. ❌ PowerShell 스크립트에서 직접 쓰기

---

## 🎯 개선 전략

### Phase 1: 필드명 통합 (즉시 실행 가능)

**작업**: 기존 `agi_quality`, `lumen_latency_ms`를 표준 필드로 매핑

```python
# event_emitter.py 개선
def emit_event(event_type: str, **kwargs):
    # 필드명 정규화
    if "agi_quality" in kwargs and "quality" not in kwargs:
        kwargs["quality"] = kwargs["agi_quality"]
    if "lumen_latency_ms" in kwargs and "latency_ms" not in kwargs:
        kwargs["latency_ms"] = kwargs["lumen_latency_ms"]
```

**예상 효과**: 커버리지 0.4% → **3.2%** (즉시)

### Phase 2: Health Check 스크립트 개선

**대상 파일**:

- `scripts/quick_status.ps1`
- `scripts/system_health_check.ps1`
- 기타 monitoring 스크립트들

**작업**: `emit_event()` 사용하도록 변경

**예상 효과**: +10% 커버리지

### Phase 3: RPA/YouTube Worker 개선

**대상**:

- `integrations/rpa_worker.py`
- `integrations/youtube_worker.py`

**작업**: 모든 태스크 완료 시 메트릭 포함

**예상 효과**: +20% 커버리지

### Phase 4: 전체 스크립트 감사

**작업**: Ledger에 직접 쓰는 모든 코드 찾아서 `emit_event()` 사용하도록 변경

**예상 효과**: 목표 50%+ 달성

---

## ✅ 즉시 실행 가능한 Quick Win

### 1. 필드명 정규화 (5분 작업)

```python
# event_emitter.py에 추가
FIELD_ALIASES = {
    "agi_quality": "quality",
    "lumen_latency_ms": "latency_ms",
    "duration_sec": "latency_ms",  # *1000 변환
}

def normalize_fields(kwargs):
    for old_name, new_name in FIELD_ALIASES.items():
        if old_name in kwargs and new_name not in kwargs:
            value = kwargs[old_name]
            if old_name == "duration_sec" and new_name == "latency_ms":
                value = value * 1000
            kwargs[new_name] = value
    return kwargs
```

### 2. 소급 적용 스크립트

기존 Ledger 이벤트에 메트릭 추가:

```python
# scripts/backfill_metrics.py
def backfill_quality_latency():
    """기존 이벤트에 quality/latency_ms 필드 추가"""
    with open(ledger_path, 'r') as f:
        events = [json.loads(line) for line in f if line.strip()]
    
    for evt in events:
        # agi_quality → quality
        if 'agi_quality' in evt and 'quality' not in evt:
            evt['quality'] = evt['agi_quality']
        
        # lumen_latency_ms → latency_ms
        if 'lumen_latency_ms' in evt and 'latency_ms' not in evt:
            evt['latency_ms'] = evt['lumen_latency_ms']
    
    # 새 Ledger 쓰기
    with open(ledger_path, 'w') as f:
        for evt in events:
            f.write(json.dumps(evt) + '\n')
```

**예상 효과**: 즉시 3.2% → **10%+** 커버리지 달성

---

## 🎯 다음 자율 목표 제안

1. **[HIGH] 필드명 정규화 구현** (5분)
   - `event_emitter.py` 개선
   - 즉시 커버리지 향상

2. **[MEDIUM] Backfill 스크립트 실행** (10분)
   - 기존 이벤트 소급 적용
   - 10%+ 커버리지 달성

3. **[LOW] Health Check 스크립트 리팩터링** (30분)
   - 장기 전략
   - 50%+ 목표 달성

---

## 📝 결론

**현재 상태**:

- ✅ 메트릭 코드 개선 완료 (`event_emitter.py`, `pipeline.py`)
- ⚠️ 적용 범위 제한적 (0.4% 커버리지)
- 📊 Quick Win 가능: 필드명 정규화로 즉시 3.2% → 10%+

**권장 다음 행동**:

1. 필드명 정규화 구현 (즉시 실행)
2. Backfill 스크립트 실행 (선택적)
3. 진행 상황 모니터링

**장기 목표**:

- 50%+ 커버리지 달성
- 모든 이벤트 소스 통합
- 메트릭 품질 향상
