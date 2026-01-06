# Core Prism Bridge - Core의 시선이 구조에 울림으로

## 개요

Core(Core)의 관찰 시선을 비노체(Binoche_Observer) 프리즘으로 굴절시켜 구조 전체에 지속적인 울림(Resonance)을 전파하는 시스템입니다.

```
Core 관찰 → 비노체 프리즘 → 구조 울림 → 지속적 전파
   ↓           ↓             ↓          ↓
 레이턴시    품질 해석    증폭 조정   메모리 보존
```

## 핵심 컴포넌트

### 1. CorePrismBridge (`fdo_agi_repo/orchestrator/core_prism_bridge.py`)

Core의 시선을 프리즘으로 변환하는 핵심 브리지:

- **프리즘 굴절 (Refraction)**: Core 신호를 비노체 관점으로 해석
- **울림 생성 (Resonance)**: 구조 전체에 전파될 울림 이벤트 생성
- **지속성 보장**: 캐시와 Resonance Store를 통한 울림 보존

```python
bridge = CorePrismBridge(
    persona_path="outputs/binoche_persona.json",
    core_latency_path="outputs/core_latency_latest.json"
)

result = bridge.process_core_observation(core_signal)
```

### 2. 자동화 스크립트

#### `scripts/run_core_prism_bridge.ps1`

Core MD → JSON 변환 → 프리즘 처리 → 캐시 저장까지 전체 파이프라인:

```powershell
# 기본 실행
.\scripts\run_core_prism_bridge.ps1

# 캐시 열기
.\scripts\run_core_prism_bridge.ps1 -OpenCache

# 커스텀 경로
.\scripts\run_core_prism_bridge.ps1 `
    -CoreMd "custom\Core.md" `
    -PersonaPath "custom\persona.json" `
    -SummaryHours 48
```

> 2025-11-05 09:09 KST 기준으로 하위 스크립트(`convert_core_md_to_json.ps1` 등)가 정상 종료할 때 `$LASTEXITCODE`가 비어 있어도 0으로 처리되도록 보강되어, 재실행 시 불필요한 실패를 방지합니다.
- 09:56 재실행 결과: `core_prism_20251105095610`, 증폭 1.0, 레저 이벤트 2건 누적(품질 게이트 PASS).

#### `scripts/convert_core_md_to_json.ps1`

Core 레이턴시 리포트 MD를 JSON으로 변환:

```powershell
.\scripts\convert_core_md_to_json.ps1 `
    -InputMd "outputs\core_latency_latest.md" `
    -OutputJson "outputs\core_latency_latest.json"
```

#### `scripts/summarize_core_prism.py`

표준 레저(`fdo_agi_repo/memory/resonance_ledger.jsonl`)에서 프리즘 이벤트를 요약해 간단한 리포트를 생성합니다:

```powershell
python scripts/summarize_core_prism.py
```

출력: `outputs/core_prism_summary.json`, `outputs/core_prism_summary.md`

## 작동 원리

### 1단계: Core 관찰 수집

Core이 시스템을 관찰하며 생성한 레이턴시 데이터:

```json
{
  "avg_latency_ms": 336,
  "p50_latency_ms": 351,
  "p90_latency_ms": 420,
  "success_rate": 1.0,
  "observations": [
    {
      "endpoint": "/api/v2/recommend/personalized",
      "latency_ms": 336,
      "success": true,
      "timestamp": "2025-11-05T00:07:29Z"
    }
  ]
}
```

### 2단계: 비노체 프리즘 굴절

비노체의 품질 기준과 선호도로 Core 신호를 해석:

```json
{
  "prism_refraction": {
    "original_core": { "latency_ms": 336, "success": true },
    "refracted_at": "2025-11-05T00:08:01Z",
    "prism_filters": {
      "quality_gate": true
    },
    "resonance_amplification": 1.0,
    "binoche_interpretation": {
      "quality_meets_standard": true,
      "aligns_with_preferences": false,
      "estimated_approval_rate": 0.0
    }
  }
}
```

### 3단계: 구조 울림 생성

Resonance Store에 이벤트를 기록하여 구조 전체에 전파:

```python
resonance_event = Event(
    task_id=f"core_prism_{timestamp}",
    event_type="core_observation_refracted",
    data={
        "core_signal": core_signal,
        "prism_refraction": prism_signal,
        "amplification": amplification
    }
)
```

### 4단계: 캐시 및 지속성

최근 100개 프리즘 이벤트를 캐시에 유지:

- **위치**: `fdo_agi_repo/outputs/core_prism_cache.json`
- **구조**: 타임스탬프, Core 신호, 프리즘 굴절, 울림 ID
- **크기 제한**: 최근 100개 (자동 순환)

## 통합 포인트

### Resonance Store 연결

```python
from orchestrator.resonance_bridge import get_resonance_store

resonance_store = get_resonance_store()
bridge = CorePrismBridge(resonance_store=resonance_store)
```

### 파이프라인 통합

```python
from orchestrator.core_prism_bridge import emit_core_gaze_via_prism

# Core 관찰 → 프리즘 → 울림 (원스텝)
result = emit_core_gaze_via_prism(core_signal)
```

## 모니터링 및 분석

### 프리즘 캐시 요약

```bash
python orchestrator/core_prism_bridge.py \
  --Core outputs/core_latency_latest.json \
  --summary 24
```

출력:

```json
{
  "time_range_hours": 24,
  "total_prism_events": 42,
  "avg_amplification": 1.0,
  "quality_pass_rate": 0.95,
  "cache_size": 42,
  "persona_loaded": true,
  "core_data_loaded": true
}
```

### 품질 게이트 통과율

프리즘을 통과한 이벤트 중 품질 기준을 만족한 비율:

- **100%**: 모든 관찰이 품질 기준 충족
- **80-99%**: 대부분 양호, 일부 개선 필요
- **<80%**: 시스템 품질 저하, 조치 필요

### 증폭 계수 (Amplification)

비노체 선호도에 따른 울림 증폭:

- **1.0**: 기본 울림 강도
- **>1.0**: 선호도 높음, 울림 증폭
- **<1.0**: 선호도 낮음, 울림 감쇠 (현재 미구현)

## VS Code Tasks

### Core: Run Prism Bridge

```json
{
  "label": "Core: Run Prism Bridge",
  "type": "shell",
  "command": "powershell",
  "args": [
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "${workspaceFolder}/scripts/run_core_prism_bridge.ps1"
  ],
  "group": "test"
}
```

### Core: Run Prism Bridge (Open Cache)

```json
{
  "label": "Core: Run Prism Bridge (Open Cache)",
  "type": "shell",
  "command": "powershell",
  "args": [
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "${workspaceFolder}/scripts/run_core_prism_bridge.ps1",
    "-OpenCache"
  ],
  "group": "test"
}
```

## 확장 가능성

### 다중 프리즘 지원

여러 페르소나의 프리즘을 통해 다각적 해석:

```python
bridges = [
    CorePrismBridge(persona_path=p)
    for p in persona_paths
]

for bridge in bridges:
    bridge.process_core_observation(signal)
```

### 프리즘 체인

순차적 프리즘 통과로 점진적 정제:

```python
signal_a = bridge_a.refract_core_gaze(core_signal)
signal_b = bridge_b.refract_core_gaze(signal_a)
signal_c = bridge_c.refract_core_gaze(signal_b)
```

### 동적 증폭 조정

실시간 선호도 학습으로 증폭 계수 자동 조정:

```python
amplification = calculate_dynamic_amplification(
    prism_signal,
    recent_feedback,
    persona_preferences
)
```

## 철학적 의미

> "Core의 시선은 객관적 관찰이지만, 비노체의 프리즘을 통과하며 주관적 의미를 얻는다.  
> 이 과정에서 생성된 울림은 구조 전체에 전파되어 지속적인 공명을 만든다.  
> 관찰이 해석으로, 해석이 울림으로, 울림이 기억으로 이어지는 순환."

### 핵심 원리

1. **관찰의 지속성**: Core의 시선은 사라지지 않고 울림으로 보존
2. **해석의 다양성**: 프리즘을 통해 다각적 의미 생성
3. **울림의 전파**: 구조 전체가 관찰의 의미를 공유
4. **기억의 형성**: 반복된 울림이 구조의 패턴으로 고착

## 트러블슈팅

### 프리즘 캐시가 비어있음

**원인**: Core 데이터 없음 또는 처리 실패

**해결**:

```bash
# Core 프로브 먼저 실행
.\scripts\core_quick_probe.ps1

# 그 후 프리즘 브리지
.\scripts\run_core_prism_bridge.ps1
```

### 페르소나 로드 실패

**원인**: `binoche_persona.json` 파일 없음

**해결**:

```bash
# BQI 학습 실행
.\fdo_agi_repo\scripts\run_bqi_learner.ps1 -Phase 6
```

### 증폭 계수가 항상 1.0

**원인**: 선호도 기반 증폭 미구현 (현재 상태)

**해결**: 향후 업데이트 예정 (동적 증폭 알고리즘)

## 다음 단계

1. **자동화 통합**: Core 프로브 후 자동으로 프리즘 처리
2. **실시간 울림**: Core 관찰 즉시 프리즘 굴절
3. **다중 프리즘**: 여러 페르소나의 동시 해석
4. **울림 분석**: 시간별 울림 패턴 시각화
5. **피드백 루프**: 울림 효과를 페르소나 학습에 반영

---

**생성일**: 2025-11-05  
**상태**: ✅ Operational  
**버전**: 1.0.0
