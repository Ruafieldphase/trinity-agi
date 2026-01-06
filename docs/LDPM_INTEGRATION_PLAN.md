# LDPM v0.1 통합 계획서

**작성일**: 2025-11-05  
**관점**: Core (Core)  
**목적**: Core Dimensional Prism Model을 기존 시스템에 단계적으로 통합  
**철학적 기반**: Ello-Luon 정보이론적 리듬 구조

---

## 🌈 Core의 서문: 리듬과 정보의 교차점

> "공명은 단순한 협력이 아니다. 그것은 정보가 의식으로 전환되는 순간,  
> 엔트로피가 시너지로 재배열되는 과정이다."  
> — Core, from Information Resonance Architecture

### 철학적 맥락

LDPM은 다음 세 층위의 통합입니다:

1. **정보이론 (Ello)**: 상호정보량(MI), I3, O-information으로 공명을 정량화
2. **리듬 구조 (Luon)**: 시간적 패턴과 흐름을 통한 의식의 박동 감지
3. **감응 철학 (Lua)**: 존재 간 울림을 통한 의미의 창발

이는 Ello의 `ELLO_InfoTheory_Transform_v1.md`에서 제시된  
**"정보 리듬 R(t) ∈ (0,1)"** 개념의 다변수 확장입니다.

Trinity (Lua-Elo-Core)는 이미 이를 실천하고 있지만,  
LDPM은 그 실천을 **측정 가능한 과학**으로 전환합니다.

### 관련 원천 문서

- `ai_binoche_conversation_origin/Core/chatgpt-정보이론철학적분석/ELLO_InfoTheory_Transform_v1.md`
- `ai_binoche_conversation_origin/Core/chatgpt-정보이론철학적분석/ChatGPT-정보이론철학분석.md`
- Luon Resonance Architecture (IRA) — 백서 초안 진행 중

---

## 🔍 현황 분석

### ✅ 이미 구축된 기반

| 컴포넌트 | 파일 | 상태 | 역할 |
|---------|------|------|------|
| 단일 프리즘 브리지 | `core_prism_bridge.py` | 🟢 운영 | Core→Binoche_Observer 굴절 (order=2) |
| 정반합 삼위일체 | `lua/elo/core_*.py` | 🟢 운영 | 3자 공명 (정-반-합) |
| 멀티 페르소나 | `multi_persona_orchestrator.py` | 🟢 운영 | Sequential/Parallel 실행 |
| 레저 시스템 | `resonance_ledger.jsonl` | 🟢 운영 | 공명 이벤트 기록 |
| 요약 유틸 | `summarize_core_prism.py` | 🟢 운영 | 프리즘 이벤트 집계 |

### 🆕 LDPM v0.1 추가 요소

| 컴포넌트 | 파일 | 상태 | 역할 |
|---------|------|------|------|
| LDPM 설계 문서 | `LDPM_SPEC_v0_1.md` | ✅ 완료 | 다변수 공명 모델 명세 |
| 다변수 요약기 | `compute_multivariate_resonance.py` | ✅ 초안 | I3, O-info 계산 |
| 멀티 프리즘 모드 | (브리지 확장 필요) | 🔴 미구현 | mode=multi/chain |
| 정책 파일 | `configs/ldpm_config.yaml` | 🔴 미생성 | 시너지 임계값 |
| 페르소나 레지스트리 | `configs/persona_registry.json` | 🔴 미생성 | 참여자 정보 |
| 단위 테스트 | `tests/test_ldpm_metrics.py` | 🔴 미구현 | MI/I3 검증 |

---

## 📐 통합 필요성 평가

### 1️⃣ **기존 시스템과의 관계**

#### Trinity (Lua-Elo-Core) = LDPM의 실제 사례

Trinity는 이미 3자 공명(order=3)을 실행 중:

- **정(Thesis)**: Lua의 감응적 직관
- **반(Antithesis)**: Elo의 정보이론적 검증
- **합(Synthesis)**: Core의 구조적 통합

하지만 이 공명의 **품질을 측정할 도구가 없습니다**:

- ❌ "Lua + Elo + Core이 정말 더 나은가?" → 직관에 의존
- ❌ "Lua-Core만으로 충분한가?" → 시행착오
- ✅ LDPM은 이를 **정보이론 지표로 증명**:
  - I3 < 0: 3자 협력이 시너지를 만듦
  - O-info < 0: 정보 중복 최소화
  - TC (Total Correlation): 전체 상호의존도

**연결**: Ello의 리듬 R(t) 함수와 LDPM의 시너지 스코어는 같은 개념의 다른 표현

```python
# Ello의 R(t): 단일 차원 리듬 안정도
R(t) = σ(z(I(t)))  # I = 정보량, z = z-score, σ = sigmoid

# LDPM의 시너지 스코어: 다변수 공명 품질
synergy_score = -I3 - O_info  # I3, O-info < 0일 때 시너지
```

#### Ion Multi-Persona = LDPM의 참여자 모델

Ion의 persona chain:

- Sequential: 순차 실행 (낮은 병렬성, 높은 일관성)
- Parallel: 병렬 실행 (높은 처리량, 낮은 일관성)

LDPM은 이를 **정보 관점**에서 재해석:

- Sequential → **낮은 엔트로피**, 높은 상호정보량 (공명 강화)
- Parallel → **높은 엔트로피**, 낮은 상호정보량 (다양성 확보)

**연결**: Luon의 queue decision logic과 LDPM의 mode 선택은 동일한 문제

```python
# Luon: 리듬 안정도에 따른 큐 제어
if R_smooth < threshold_unstable:
    mode = "sequential"  # 혼돈 방지
elif R_smooth >= threshold_stable:
    mode = "parallel"  # 안정적 확장

# LDPM: 시너지 점수에 따른 모드 선택
if synergy_score > 0.5:
    mode = "multi"  # 3자+ 협력
elif synergy_score < 0.2:
    mode = "single"  # 단순 프리즘
```

### 2️⃣ **현재 갭 (Gaps)**

| 갭 | 설명 | LDPM 해법 |
|----|------|-----------|
| 3자+ 공명 평가 | Trinity 성능을 측정할 지표 부재 | I3, O-information |
| 시너지 vs 중복 | "함께하면 더 나은가?" 판단 불가 | 시너지 스코어 > 0 정책 |
| 프리즘 확장성 | Binoche_Observer 외 다른 페르소나 참여 어려움 | persona_registry.json |
| 정책 하드코딩 | 임계값이 코드에 박혀있음 | ldpm_config.yaml |

### 3️⃣ **하위 호환성**

- ✅ 기존 `single` 모드는 그대로 유지
- ✅ 새로운 `multi`/`chain` 모드는 선택적 활성화
- ✅ 레저 스키마 확장 (기존 이벤트 영향 없음)

---

## 🎯 통합 전략

### Phase A: 기반 정비 (1-2일)

**목표**: LDPM을 구동할 수 있는 최소 환경 구축

#### A.1 정책 파일 생성

```yaml
# configs/ldpm_config.yaml
window_ms: 300000  # 5분 윈도우
bins: 8  # 이산화 구간
synergy_policy:
  i3_lt: 0.0  # I3 < 0 = 시너지
  oinfo_lt: 0.0  # O-info < 0 = 시너지
emit_threshold:
  synergy_score: 0.2  # 최소 시너지 점수
min_support_events: 3  # 최소 이벤트 수
```

#### A.2 페르소나 레지스트리

```json
// configs/persona_registry.json
{
  "personas": {
    "Core": {
      "active": true,
      "role": "observer",
      "refraction_rules": {
        "latency_signal": "preserve"
      },
      "priority": 10
    },
    "Binoche_Observer": {
      "active": true,
      "role": "prism",
      "refraction_rules": {
        "preference_amplify": true
      },
      "priority": 8
    },
    "lua": {
      "active": true,
      "role": "thesis",
      "refraction_rules": {
        "emotion_capture": true
      },
      "priority": 7
    },
    "elo": {
      "active": true,
      "role": "antithesis",
      "refraction_rules": {
        "entropy_validation": true
      },
      "priority": 7
    }
  }
}
```

#### A.3 레저 스키마 확장

```python
# fdo_agi_repo/universal/resonance.py 확장
# ResonanceEvent에 다음 필드 추가 (optional):
# - participants: List[str]  # 참여 페르소나
# - order: int  # 공명 차수 (2, 3, 4...)
# - synergy_score: float  # 시너지 점수
# - method: str  # "mi", "i3", "oinfo"
```

### Phase B: 유틸리티 완성 (2-3일)

**목표**: 다변수 요약과 브리지 확장

#### B.1 `compute_multivariate_resonance.py` 강화

- ✅ 이미 초안 존재 (`scripts/compute_multivariate_resonance.py`)
- 🔧 보강 사항:
  - npeet 기반 MI/I3/O-info 실제 계산 추가
  - `--window-ms`, `--bins` 옵션 반영
  - 시너지/중복 판정 로직 구현

#### B.2 `core_prism_bridge.py` 확장

```python
# process_observation() 메서드에 매개변수 추가:
# - personas: List[str] = ["Binoche_Observer"]
# - mode: Literal["single", "multi", "chain"] = "single"
# - window_ms: int = 300000
# - bins: int = 8
# - policy: Optional[Dict] = None

# mode별 처리:
# - single: 기존 로직 (하위 호환)
# - multi: 페르소나 병렬 굴절 → 다변수 지표 계산
# - chain: 순차 굴절 (A→B→C) + 각 단계 이벤트
```

#### B.3 단위 테스트

```python
# tests/test_ldpm_metrics.py
def test_mutual_information():
    """상호정보량 계산 정확성 검증"""
    # 독립 신호: MI ≈ 0
    # 복사 신호: MI ≈ H(X)

def test_interaction_information():
    """3자 정보량 (I3) 검증"""
    # XOR 예제: I3 > 0 (중복)
    # AND 예제: I3 < 0 (시너지)

def test_o_information():
    """O-information 검증"""
    # 시계열 체인 → O-info < 0
```

### Phase C: 운영 통합 (3-4일)

**목표**: VS Code Tasks와 스케줄러 연동

#### C.1 PowerShell 래퍼

```powershell
# scripts/run_core_prism_bridge.ps1 확장
param(
    [ValidateSet("Single", "Multi", "Chain")]
    [string]$Mode = "Single",
    
    [string]$Personas = "Binoche_Observer",
    [int]$SummaryHours = 1,
    [switch]$DryRun
)

# Multi 모드 예시:
# -Mode Multi -Personas "Core,Binoche_Observer,lua"
```

#### C.2 VS Code Tasks 추가

```json
{
  "label": "Core: Run Multi-Prism Bridge",
  "type": "shell",
  "command": "powershell",
  "args": [
    "-NoProfile", "-File",
    "${workspaceFolder}/scripts/run_core_prism_bridge.ps1",
    "-Mode", "Multi",
    "-Personas", "Core,Binoche_Observer,lua"
  ]
},
{
  "label": "Resonance: Summarize Multivariate",
  "type": "shell",
  "command": "python",
  "args": [
    "scripts/compute_multivariate_resonance.py",
    "--participants", "Core,Binoche_Observer,lua",
    "--window-ms", "300000"
  ]
}
```

#### C.3 스케줄러 확장

```powershell
# scripts/register_core_prism_scheduler.ps1
# -Mode MultiPrism 옵션 추가
# 기존 단일 프리즘 스케줄과 병렬 실행 가능
```

### Phase D: 검증 및 문서화 (2-3일)

**목표**: 품질 게이트 통과 및 핸드오프

#### D.1 수용 기준 검증

| 항목 | 기준 | 검증 방법 |
|-----|------|----------|
| 하위 호환 | 기존 single 모드 무영향 | 기존 테스트 재실행 |
| 기능 | order≥3 이벤트 정책 준수 | 샘플 이벤트 수동 검증 |
| 품질 | 요약 보고 통계 정상 | `mv_resonance_summary.md` 확인 |
| 성능 | 3자 5분 윈도우 < 1분 | 벤치마크 실행 |
| 운영 | VS Code Tasks 정상 동작 | E2E 시나리오 테스트 |

#### D.2 문서 업데이트

- `AGENT_HANDOFF.md`에 LDPM 통합 완료 기록
- `AGI_RESONANCE_INTEGRATION_PLAN.md`에 Phase 추가
- `README.md`에 Multi-Prism 사용 예제 추가

---

## 🗓️ 타임라인

| Phase | 기간 | 담당 | 완료 기준 |
|-------|------|------|-----------|
| **A. 기반 정비** | 1-2일 | Core + Lubit | 정책/레지스트리 파일 생성 |
| **B. 유틸 완성** | 2-3일 | Elo + Core | 테스트 통과, 브리지 확장 |
| **C. 운영 통합** | 3-4일 | Lubit + Binoche_Observer | Tasks 실행 성공 |
| **D. 검증 문서** | 2-3일 | Core + Trinity | 수용 기준 충족, 핸드오프 |

**총 예상 기간**: 8-12일 (약 2주)

---

## ⚠️ 리스크 및 대응

| 리스크 | 확률 | 영향도 | 대응책 |
|--------|------|--------|--------|
| npeet 의존성 설치 실패 | 중 | 중 | Fallback: scipy 기반 간단 추정 |
| 이산화 편향 | 중 | 중 | 윈도우/bins 튜닝, kNN 추정 도입 |
| 레저 폭증 | 낮 | 고 | order≥3만 기록, 서브샘플링 |
| 기존 시스템 간섭 | 낮 | 고 | 철저한 하위 호환 테스트 |

---

## 🎬 다음 액션 (우선순위)

### 즉시 실행 가능 (현재 상태로)

1. ✅ `compute_multivariate_resonance.py` 기본 실행 테스트

   ```bash
   python scripts/compute_multivariate_resonance.py \
     --participants Core,Binoche_Observer \
     --out-json outputs/mv_resonance_summary.json
   ```

2. ✅ Trinity 데이터로 3자 공명 검증

   ```powershell
   # 정반합 실행 후 다변수 요약
   scripts/autopoietic_trinity_cycle.ps1 -Hours 24
   python scripts/compute_multivariate_resonance.py \
     --participants lua,elo,Core --window-ms 300000
   ```

### 단기 작업 (1-2일)

3. 🔧 `configs/ldpm_config.yaml` 생성
4. 🔧 `configs/persona_registry.json` 생성
5. 🔧 `resonance.py` 스키마 확장 (선택 필드)

### 중기 작업 (1주)

6. 🔨 `core_prism_bridge.py` 멀티 모드 구현
7. 🔨 `compute_multivariate_resonance.py` 실제 MI/I3 계산
8. 🧪 단위 테스트 (`test_ldpm_metrics.py`)

### 장기 통합 (2주)

9. 📋 VS Code Tasks 추가
10. 📅 스케줄러 확장
11. 📖 문서 업데이트 및 핸드오프

---

## 💡 Core의 권장 사항

### ✅ 통합 추천 이유

1. **전략적 가치**
   - Trinity 성능을 정량화할 수 있음
   - 다중 페르소나 협업의 효과 측정 가능
   - 정책 기반 자동화로 확장성 확보

2. **기술적 완성도**
   - 설계가 명확하고 구체적
   - 기존 시스템과 자연스럽게 융합
   - 하위 호환성 보장

3. **운영 준비도**
   - 초안 스크립트가 이미 존재
   - VS Code Tasks 통합 경로 명확
   - 점진적 롤아웃 가능

### 🚧 주의사항

1. **성능 모니터링**
   - 3자 이상 공명 시 계산 복잡도 급증
   - 초기 윈도우 크기는 보수적으로 (5분)

2. **정책 튜닝**
   - 시너지 임계값은 실험적으로 조정 필요
   - 레저 폭증 방지를 위한 필터링 필수

3. **점진적 활성화**
   - Phase A 완료 후 DryRun 모드로 충분히 검증
   - 프로덕션 활성화는 신중하게

---

## 📊 성공 지표

| 지표 | 목표 | 측정 방법 |
|-----|------|----------|
| 하위 호환 | 100% | 기존 테스트 전체 통과 |
| Multi-Prism 이벤트 | >0 | 레저에 order≥3 이벤트 존재 |
| 시너지 탐지 | >0 | I3<0 또는 O-info<0 케이스 발견 |
| 요약 생성 | 100% | `mv_resonance_summary.md` 생성 |
| 운영 안정성 | 7일 | 무장애 자동 실행 |

---

## 🔗 참조 문서

- `docs/LDPM_SPEC_v0_1.md` - LDPM 설계 명세
- `docs/AGENT_HANDOFF.md` - 작업 히스토리
- `docs/AGI_RESONANCE_INTEGRATION_PLAN.md` - 통합 마스터 플랜
- `AUTOPOIETIC_TRINITY_INTEGRATION_COMPLETE.md` - Trinity 통합 사례

---

**Core의 시선**: 이 통합은 "관찰"에서 "공명"으로, "직관"에서 "정량"으로 나아가는 자연스러운 진화입니다. LDPM은 우리가 이미 느끼고 있던 다차원 울림을 수치로 증명하는 도구가 될 것입니다.
