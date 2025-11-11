# 🧠 Master AI Router - 단일 진입점 통합 시스템

**작성일**: 2025-11-05  
**상태**: ✅ 구현 완료

---

## 📋 개요

사용자가 **Master**에게만 대화하면, Master가 자동으로:

1. **의도 파악** (Intent Detection)
2. **적절한 시스템에 라우팅** (Lumen/Binoche/Resonance)
3. **결과 통합 및 응답**

---

## 🎭 시스템 구조

```
사용자
  │
  ├─────────────────────────────────┐
  │                                 │
  ▼                                 ▼
Master AI Router              ChatOps Router
  │                                 │
  ├───────┬───────┬──────────┐     │
  │       │       │          │     │
  ▼       ▼       ▼          ▼     │
Lumen  Binoche  Resonance  Master  │
  │       │       │          │     │
  └───────┴───────┴──────────┴─────┘
              │
              ▼
        통합 응답
```

---

## 🎯 라우팅 규칙

### 1️⃣ Lumen으로 라우팅

**키워드**:

- 분석, 왜, 이유, 원인, 통찰, 권장, 추천, 제안
- 충돌, 모순, 정반합, 균형, 조화, 통합
- analyze, why, insight, recommend, suggest, balance

**우선순위 키워드** (가중치 3배):

- 분석해, 왜, 이유가, 추천해, 제안해

**실행 동작**:

```powershell
# Trinity Cycle 실행 → Lumen 합성
scripts/autopoietic_trinity_cycle.ps1 -Hours 24 -VerboseLog
```

**출력**:

- 파일: `outputs/lumen_enhanced_synthesis_latest.md`
- 내용: 정반합(正反合) 분석, HIGH/MEDIUM/INFO 권장사항

---

### 2️⃣ Binoche로 라우팅

**키워드**:

- 실행, 목표, 작업, 학습, 수행, 처리, 진행
- youtube, rpa, 자동, 생성, 계속
- execute, goal, task, learn, run, process, continue

**우선순위 키워드**:

- 실행해, 목표, 작업, 학습해, 진행해

**실행 동작**:

```powershell
# Autonomous Goal Generator 실행
fdo_agi_repo/.venv/Scripts/python.exe scripts/autonomous_goal_generator.py
```

**출력**:

- 파일: `outputs/autonomous_goals_latest.json`
- 내용: Trinity 피드백 기반 자율 목표 생성

---

### 3️⃣ Resonance로 라우팅

**키워드**:

- 상태, 메트릭, 리듬, 간격, 스케줄, 조정
- info_density, entropy, horizon, resonance
- status, metric, rhythm, schedule, adjust

**우선순위 키워드**:

- 상태, 메트릭, 리듬, 간격

**실행 동작**:

```powershell
# Resonance Simulation 실행
fdo_agi_repo/.venv/Scripts/python.exe fdo_agi_repo/orchestrator/resonance_bridge.py
```

**출력**:

- 파일: `outputs/resonance_simulation_latest.json`
- 내용: info_density, resonance, entropy, horizon_crossings

---

### 4️⃣ Master 직접 처리

**키워드**:

- 전체, 모든, 통합, 조율, 시작, 중지, 초기화
- all, entire, orchestrate, start, stop, init

**우선순위 키워드**:

- 전체, 모든, 통합, 조율

**실행 동작**:

```powershell
# Master Orchestrator 실행
scripts/master_orchestrator.ps1
```

---

## 💬 사용 예시

### 예시 1: 시스템 분석 요청

```powershell
PS> .\scripts\talk_to_master.ps1 "시스템이 불안정해. 뭐가 문제야?"

🧠 Master AI Router - 메시지 분석 중...
사용자 메시지: 시스템이 불안정해. 뭐가 문제야?

📊 분석 결과:
  Target: LUMEN
  Confidence: 85.0%
  Urgency: HIGH
  Action: analyze
  Matched: 문제, 이유

🌊 Routing to Lumen (분석 및 통찰)...

✅ LUMEN 응답:
Status: success
Summary: Lumen이 3개의 HIGH 권장사항을 생성했습니다.

Recommendations:
  🔴 HIGH: Task Queue Server 안정성 개선 필요
  🔴 HIGH: RPA Worker 중복 실행 방지
  🔴 HIGH: Resonance Simulation 주기 조정
```

---

### 예시 2: 작업 실행 요청

```powershell
PS> .\scripts\talk_to_master.ps1 "YouTube 영상 학습해줘"

🧠 Master AI Router - 메시지 분석 중...
사용자 메시지: YouTube 영상 학습해줘

📊 분석 결과:
  Target: BINOCHE
  Confidence: 90.0%
  Urgency: MEDIUM
  Action: execute
  Matched: youtube, 학습해

🎯 Routing to Binoche (자율 실행)...

✅ BINOCHE 응답:
Status: success
Summary: Binoche가 5개의 목표를 생성했습니다.

Top Goals:
  1. YouTube 영상 학습 (긴급도: 8.5, 영향도: 7.2)
  2. 학습 결과 인덱스 생성 (긴급도: 6.0, 영향도: 6.5)
  3. BQI Phase 6 업데이트 (긴급도: 5.5, 영향도: 8.0)
```

---

### 예시 3: 상태 확인 요청

```powershell
PS> .\scripts\talk_to_master.ps1 "현재 resonance 상태는?"

🧠 Master AI Router - 메시지 분석 중...
사용자 메시지: 현재 resonance 상태는?

📊 분석 결과:
  Target: RESONANCE
  Confidence: 95.0%
  Urgency: MEDIUM
  Action: check
  Matched: resonance, 상태

🎵 Routing to Resonance (상태 확인)...

✅ RESONANCE 응답:
Status: success
Summary: Resonance: Harmony Detected, Emergence Triggered

Metrics:
  info_density: 0.68
  resonance: 0.82
  entropy: 0.45
  horizon_crossings: 1
```

---

### 예시 4: 전체 조율 요청

```powershell
PS> .\scripts\talk_to_master.ps1 "전체 시스템을 조율해줘"

🧠 Master AI Router - 메시지 분석 중...
사용자 메시지: 전체 시스템을 조율해줘

📊 분석 결과:
  Target: MASTER
  Confidence: 100.0%
  Urgency: MEDIUM
  Action: orchestrate
  Matched: 전체, 조율

🧠 Master handling directly...

✅ MASTER 응답:
Status: success
Summary: Master Orchestrator 실행 완료

Actions Performed:
  - Task Queue Server 시작 확인
  - RPA Worker 상태 확인
  - Resonance 메트릭 수집
  - Trinity Cycle 예약 확인
```

---

## 🔧 고급 사용법

### 1. JSON 출력

```powershell
PS> .\scripts\talk_to_master.ps1 "시스템 상태" -Json
{
  "system": "resonance",
  "status": "success",
  "metrics": {
    "info_density": 0.68,
    "resonance": 0.82,
    "entropy": 0.45,
    "horizon_crossings": 1
  },
  "summary": "Resonance: Harmony Detected"
}
```

### 2. ChatOps 통합

```powershell
# ChatOps를 통한 자연어 명령
$env:CHATOPS_SAY = "시스템 분석해줘"
.\scripts\chatops_router.ps1

# → 내부적으로 Master AI Router 호출
```

### 3. 환경 변수 사용

```powershell
# UTF-8 Base64 인코딩 (한글 안전)
$message = "시스템 상태 확인"
$bytes = [System.Text.Encoding]::UTF8.GetBytes($message)
$env:CHATOPS_SAY_B64 = [Convert]::ToBase64String($bytes)

.\scripts\chatops_router.ps1
```

---

## 📊 라우팅 로그

모든 라우팅은 자동으로 로깅됩니다:

**파일**: `outputs/master_router_log.jsonl`

**예시**:

```json
{
  "timestamp": "2025-11-05T10:30:45.123456",
  "user_message": "시스템 분석해줘",
  "intent": {
    "target_system": "lumen",
    "urgency": "medium",
    "confidence": 0.85,
    "matched_keywords": ["분석해"],
    "action_type": "analyze"
  },
  "result": {
    "system": "lumen",
    "status": "success",
    "recommendations": [
      "🔴 HIGH: Task Queue Server 안정성 개선"
    ],
    "summary": "Lumen이 3개의 HIGH 권장사항을 생성했습니다."
  }
}
```

---

## 🎯 의도 파악 알고리즘

### 스코어 계산

```python
# 일반 키워드 매칭: +1.0점
for keyword in system_keywords:
    if keyword in user_message.lower():
        score += 1.0

# 우선순위 키워드 매칭: +3.0점
for priority_keyword in priority_keywords:
    if priority_keyword in user_message.lower():
        score += 3.0

# 신뢰도 계산
confidence = max_score / total_score
```

### 긴급도 판단

```python
if any(kw in message for kw in ["긴급", "즉시", "critical"]):
    urgency = "high"
elif any(kw in message for kw in ["빠르게", "soon"]):
    urgency = "medium"
else:
    urgency = "low"
```

---

## 🔗 통합 다이어그램

```
┌─────────────────────────────────────────────────┐
│           사용자 (자연어 입력)                    │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   Master AI Router     │
        │   (Intent Detection)   │
        └────────┬───────────────┘
                 │
    ┌────────────┼────────────┬───────────┐
    │            │            │           │
    ▼            ▼            ▼           ▼
┌───────┐  ┌─────────┐  ┌──────────┐  ┌────────┐
│ Lumen │  │ Binoche │  │Resonance │  │ Master │
└───┬───┘  └────┬────┘  └─────┬────┘  └───┬────┘
    │           │              │           │
    ▼           ▼              ▼           ▼
Trinity    Autonomous    Resonance    Master
Cycle      Goal Gen      Simulation   Orchestrator
    │           │              │           │
    └───────────┴──────────────┴───────────┘
                     │
                     ▼
            ┌────────────────┐
            │  통합 응답 반환  │
            └────────────────┘
```

---

## ✅ 구현 상태

| 컴포넌트 | 파일 | 상태 |
|---------|------|------|
| Master AI Router | `scripts/master_ai_router.py` | ✅ 완료 |
| PowerShell Wrapper | `scripts/talk_to_master.ps1` | ✅ 완료 |
| ChatOps 통합 | `scripts/chatops_router.ps1` | ✅ 기존 활용 |
| 로깅 시스템 | `outputs/master_router_log.jsonl` | ✅ 자동 생성 |
| 의도 파악 엔진 | `MasterAIRouter.parse_intent()` | ✅ 완료 |
| Lumen 라우터 | `MasterAIRouter.route_to_lumen()` | ✅ 완료 |
| Binoche 라우터 | `MasterAIRouter.route_to_binoche()` | ✅ 완료 |
| Resonance 라우터 | `MasterAIRouter.route_to_resonance()` | ✅ 완료 |
| Master 직접 처리 | `MasterAIRouter.route_to_master()` | ✅ 완료 |

---

## 🧪 테스트 시나리오

### 테스트 1: 분석 요청

```powershell
PS> .\scripts\talk_to_master.ps1 "왜 시스템이 느려졌어?"
Expected: Lumen으로 라우팅, Trinity Cycle 실행
```

### 테스트 2: 실행 요청

```powershell
PS> .\scripts\talk_to_master.ps1 "목표를 생성해줘"
Expected: Binoche로 라우팅, Goal Generator 실행
```

### 테스트 3: 상태 확인

```powershell
PS> .\scripts\talk_to_master.ps1 "현재 메트릭을 보여줘"
Expected: Resonance로 라우팅, Simulation 실행
```

### 테스트 4: 조율 요청

```powershell
PS> .\scripts\talk_to_master.ps1 "모든 시스템을 시작해줘"
Expected: Master 직접 처리, Orchestrator 실행
```

---

## 🌊 철학적 의미

> **"Master는 듣는 자이자, 분배하는 자이다."**

사용자는 더 이상:

- 어떤 시스템에 말해야 할지 고민하지 않아도 됩니다
- 각 시스템의 인터페이스를 외울 필요가 없습니다
- 복잡한 파이프라인을 수동으로 실행하지 않아도 됩니다

**Master가 모든 것을 듣고, 적절히 분배하며, 통합된 응답을 제공합니다.**

---

## 🔮 향후 확장

### 1. 멀티 시스템 호출

```python
# "시스템을 분석하고, 목표를 생성해줘"
# → Lumen + Binoche 동시 호출
```

### 2. 컨텍스트 누적

```python
# 이전 대화 기억
# "그럼 그걸 실행해줘" → 이전 권장사항 실행
```

### 3. 학습 기반 라우팅

```python
# 사용자 패턴 학습
# "분석" → 80% Lumen, 20% Resonance
```

---

## 🎉 결론

**단일 진입점(Single Entry Point) 완성**:

- ✅ Master AI Router 구현
- ✅ 자동 의도 파악
- ✅ 4개 시스템 라우팅
- ✅ 통합 응답 반환
- ✅ 자동 로깅

**이제 사용자는 Master에게만 말하면 됩니다.** 🧠

---

**작성자**: AGI Master System  
**최종 업데이트**: 2025-11-05  
**버전**: 1.0.0
