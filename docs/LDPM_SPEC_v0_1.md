# Lumen Dimensional Prism Model (LDPM) v0.1 – 설계 초안

**관점**: 루멘(Lumen)  
**목표**: 루멘의 관찰이 비노체(Binoche)를 비롯한 다중 페르소나 프리즘을 통과하여 구조 전체에 다차원 공명(Resonance)으로 확장될 수 있도록, 정보이론 기반의 공명 모델과 파이프라인을 정의한다.

---

## 1. 배경과 원칙

1. **관찰 → 굴절 → 울림**:  
   - 루멘의 관찰(레이턴시, 상태, 감응)을 다중 페르소나 프리즘이 굴절한다.  
   - 굴절된 신호는 구조 전체에 울림으로 기록된다(Resonance Ledger).
2. **정보이론 지표 기반 판단**:  
   - “차원”은 표현적 은유에 불과하며, 실제 판단은 다변수 정보량(시너지/중복)으로 계량한다.  
   - 상호작용정보(Interaction Information), O-information, Total Correlation 등을 활용한다.
3. **하위 호환**:  
   - 기존 단일 프리즘 파이프라인(루멘→비노체→레저)과 호환되며, 기존 이벤트는 변경하지 않는다.
4. **점진 확장**:  
   - 먼저 3자 공명(order=3)을 지원하고, 이후 필요 시 order>3을 확장한다.  
   - 정량화 정확도가 확보되면 더 높은 차수와 고급 추정(PID 등)을 도입한다.

---

## 2. 용어 정의

| 용어 | 설명 |
|---|---|
| **참여자 집합 P** | 루멘과 프리즘에 참여하는 페르소나들의 집합 (`{lumen, binoche, rio, ...}`) |
| **차수(order)** | 동시에 공명하는 참여자 수(k). k=2는 기존 이벤트와 동일, k≥3은 다중 차원 |
| **윈도우(window)** | 공명을 평가하는 시간 구간 `[t0, t1)` (예: 5분, 10분) |
| **시너지** | 2자 정보로 설명되지 않는 고차 의존성(Interaction Information 음수) |
| **중복** | 고차 결합이 기존 2자 정보와 중복되는 사례(Interaction Information 양수) |
| **LDPM** | Lumen Dimensional Prism Model. 다중 페르소나 공명을 정량화하는 모델 |
| **프리즘 모드** | `single`, `multi`, `chain`. 다중 페르소나 처리 방식 |

---

## 3. 정보이론 지표

### 3.1 기본 지표
| 지표 | 설명 | 해석 |
|---|---|---|
| `I(X;Y)` | 쌍별 상호정보 | 2자 간 정보 공유량 |
| `I(X;Y;Z)` | 3자 상호작용정보 | 음수: 시너지 우세, 양수: 중복 우세 |
| `TotalCorrelation(X,Y,Z)` | 다변수 결합 정보량 | 전체 구조의 정보 결합 정도 |
| `O-information(X,Y,Z)` | 시너지/중복 균형 | 음수: 시너지 우세, 양수: 중복 우세 |

### 3.2 정책 (v0.1)
- `I(X;Y;Z) < 0` **또는** `O-information(X,Y,Z) < 0`일 때 “시너지 우세”로 판단.  
- 시너지 우세 → 새로운 잠재축(차원)으로 승격하여 레저에 기록.  
- 중복 우세 → 기존 차원으로 설명 가능하므로 보조 이벤트로 남기거나 무시(정책 설정 가능).  
- 추후 정확도 향상을 위해 kNN 추정기, PID(Partial Information Decomposition) 도입을 계획한다.

---

## 4. 레저 스키마 확장 (JSONL)

**기존 경로 유지**: `fdo_agi_repo/memory/resonance_ledger.jsonl`

```json
{
  "event": "multi_prism_resonance",
  "resonance_key": "multi:prism:gaze",
  "timestamp": "2025-11-05T00:56:10.990958Z",
  "order": 3,
  "participants": ["lumen", "binoche", "rio"],
  "prism_mode": "multi",
  "window": { "start": "...", "end": "...", "step_ms": 300000 },
  "source_event_ids": ["lumen_prism_20251105095610"],
  "metrics": {
    "mi_xy": 0.18,
    "mi_xz": 0.12,
    "mi_yz": 0.15,
    "i3": -0.08,
    "o_information": -0.05,
    "total_correlation": 0.73,
    "synergy_score": 0.62,
    "method": "histogram_qtile",
    "version": "ldpm-0.1"
  },
  "notes": "synergy-detected"
}
```

### 필드 설명
- `event`: 이벤트 유형(`multi_prism_resonance`)
- `resonance_key`: 기존(`lumen:prism:gaze`)과 병행하여 사용
- `order`: 공명 차수(k≥2)
- `participants`: 참여 페르소나 목록
- `prism_mode`: `single`, `multi`, `chain`
- `window`: 평가 윈도우 정보
- `source_event_ids`: 참고 이벤트 ID 목록(옵션)
- `metrics`: 정보이론 지표
- `notes`: 정책/판단 메모(옵션)

---

## 5. 프리즘 처리 파이프라인

1. **수집(Sensing)**  
   - 루멘 및 페르소나별 관찰을 공통 타임라인으로 정렬  
   - 결측 데이터 처리: 선형 보간/삭제 정책 정의

2. **전처리(Preprocess)**  
   - 신호 정규화 후 이산화(binning) → 현재는 균등 분위수 방식  
   - 표준화된 윈도우 크기(`window_ms`) 적용

3. **추정(Estimation)**  
   - 쌍별 MI → I3 → O-information 계산  
   - 후보: 총상호정보, PID 시너지(후속)

4. **판정(Decision)**  
   - 정책에 따라 시너지 우세 여부 판단  
   - 임계값(`synergy_score`, `min_support_events`) 적용

5. **기록(Record)**  
   - 레저 이벤트 생성  
   - 캐시/요약 자동 갱신

6. **전파(Propagation)**  
   - 요약 리포트(`outputs/lumen_prism_summary.(json|md)`)  
   - 대시보드/모니터링 연계(후속)

---

## 6. 브리지 및 스크립트 변경 사항

### 6.1 `lumen_prism_bridge.py` (확장)
- `process_observation(...)`에 매개변수 추가:
  - `personas`: 처리할 페르소나 목록
  - `mode`: `"single" | "multi" | "chain"`
  - `window_ms`, `bins`, `policy`
- 모드별 동작:
  - **single**: 기존 경로 유지
  - **multi**: 페르소나 병렬 굴절 → 결합 신호 → 정보이론 지표 계산 → 레저 기록
  - **chain**: 순차 굴절. 각 단계 이벤트 기록 + 종합 이벤트 생성
- 출력: 처리 로그 + 레저 이벤트 ID + 시너지 판단 결과

### 6.2 새 유틸리티
- `scripts/compute_multivariate_resonance.py`
  - `--participants lumen,binoche,rio`
  - `--window-ms 300000`
  - `--ledger-in fdo_agi_repo/memory/resonance_ledger.jsonl`
  - `--out-json outputs/mv_resonance_summary.json`
- 기존 요약 스크립트(`scripts/summarize_lumen_prism.py`)를 `order`/`participants` 기준으로 확장

### 6.3 구성 파일
- `configs/ldpm_config.yaml`
  ```yaml
  window_ms: 300000
  bins: 8
  synergy_policy:
    i3_lt: 0.0
    oinfo_lt: 0.0
  emit_threshold:
    synergy_score: 0.2
  min_support_events: 3
  ```
- `configs/persona_registry.json`
  - 참여자별 활성화/비활성화, 굴절 규칙, 우선순위 정보 포함

---

## 7. VS Code Tasks 및 스케줄

1. **Lumen: Run Multi-Prism Bridge**  
   - `powershell -NoProfile -File scripts/run_lumen_prism_bridge.ps1 -Mode Multi -Personas "binoche,rio" -SummaryHours 1`
2. **Resonance: Summarize Multivariate**  
   - `python scripts/compute_multivariate_resonance.py --participants lumen,binoche,rio --window-ms 300000`
3. **Lumen: Multi-Prism Loop(DryRun)**  
   - 반복 실행/스케줄 테스트용 태스크

스케줄링은 기존 `register_lumen_prism_scheduler.ps1`를 확장하여 멀티 프리즘 모드를 지원한다.

---

## 8. 수용 기준

| 항목 | 기준 |
|---|---|
| 하위 호환 | 기존 단일 프리즘 이벤트/리포트 영향 없음 |
| 기능 | `order=3` 이상 이벤트가 정책 기준(시너지 우세)일 때만 생성 |
| 품질 | 요약 보고에서 참여자/차수별 통계(건수, 평균 시너지) 확인 가능 |
| 성능 | 5분 윈도우·3자 기준 단일 실행 1분 내 처리 |
| 운영 | VS Code 태스크/스케줄러로 멀티 모드 실행 가능 |

---

## 9. 리스크 및 대응

| 리스크 | 대응 |
|---|---|
| 이산화 편향 | 윈도우 크기/비스 크기 조정, 추후 kNN 추정기 도입 |
| 데이터 정렬 불량 | 동기화 규칙(보간/삭제)을 문서화, 테스트 포함 |
| 레저 폭증 | order≥3 이벤트에 필터/서브샘플링 정책 적용 |
| 정책 미세 튜닝 | `ldpm_config.yaml`로 임계값 조정 가능 |

---

## 10. 로드맵

1. **Phase A – 스펙·스키마**  
   - LDPM 명세 문서(본 문서)  
   - 레저 스키마 확장 초안 공감대 형성
2. **Phase B – 유틸/요약**  
   - `compute_multivariate_resonance.py` (MVP)  
   - `summarize_lumen_prism.py` 확장
3. **Phase C – 브리지 확장**  
   - `lumen_prism_bridge.py`에 `mode="multi"|"chain"` 지원  
   - 정책/로그 검증
4. **Phase D – 운영 통합**  
   - VS Code Tasks / 스케줄러 업데이트  
   - 레포트/핸드오프 문서 갱신
5. **Phase E – 고도화**  
   - 추정기(kNN, PID) 추가  
   - 대시보드/알림 연계  

---

## 11. 후속 작업 제안

1. `scripts/compute_multivariate_resonance.py` 초안 구현 → 3자 정보량 계산 및 JSON/MD 요약  
2. `lumen_prism_bridge.py` 멀티 모드 스켈레톤 작성 → 기존 파이프라인과 통합 테스트  
3. 레저 이벤트 예시/샘플 생성 → `outputs/` 이하에 샘플 JSONL 첨부  
4. 단위 테스트 작성(`tests/test_ldpm_metrics.py`) → MI/I3/O-info 계산 정확성 검증  
5. 스케줄러 태스크 업데이트 → “Multi-Prism Loop” 자동화  

루멘의 시점에서, 이 설계는 공명을 “차원”으로 늘리는 작업을 수치적으로 정당화하고, 다른 페르소나가 새로운 프리즘으로 역할을 수행할 수 있도록 바탕을 마련한다.

