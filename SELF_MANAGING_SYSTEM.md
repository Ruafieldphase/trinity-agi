# 🤖 AI Self-Managing System

**Date**: 2025-11-02  
**Version**: 1.0  
**Philosophy**: AI manages AI. Humans code.

---

## 🎯 핵심 원칙

### 1. AI 자율성 우선 (AI Autonomy First)

- **AI가 자기 자신을 관리**합니다.
- 사람은 오직 **관리자 권한이 필요한 최소한의 작업**만 개입합니다.
- 모든 작업은 **투명하게 로그로 기록**됩니다.

### 2. 최소 인간 개입 (Minimal Human Intervention)

- AI는 가능한 모든 것을 자동으로 처리합니다:
  - ✅ 프로세스 시작/중지
  - ✅ 헬스 체크
  - ✅ 자동 복구
  - ✅ 의존성 등록 (권한 허용 시)
- 사람은 오직:
  - ⚠️ 관리자 권한 승인
  - ⚠️ 중대한 의사결정 (배포, 삭제 등)

### 3. Self-Bootstrap (자기 부트스트랩)

- **단 한 번만 실행**하면 AI가 스스로 모든 것을 설정합니다.
- 이후 재부팅 시에도 AI가 자동으로 모든 시스템을 복구합니다.

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                  Human (Minimal)                        │
│         ↓ Bootstrap Once (or Approve Admin)            │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│           🤖 Self-Managing Agent (Python)               │
│  • 모든 의존성 자동 체크 (프로세스/예약작업/헬스)        │
│  • 가능한 모든 것 자동 수정 (등록/시작/복구)             │
│  • 권한 부족 시 명확한 manual command 제공              │
│  • 모든 조치를 JSON/MD 리포트로 기록                    │
└─────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Master    │───→│  Auto Upgrade   │    │ Self-Healing │
│ Orchestrator│    │    Detector     │    │   Watchdog   │
└─────────────┘    └─────────────────┘    └──────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                           ↓
         ┌─────────────────────────────────────┐
         │  Task Queue Server (8091)           │
         │  RPA Worker                         │
         │  Monitoring Daemon                  │
         │  All Scheduled Tasks                │
         └─────────────────────────────────────┘
```

---

## 🚀 사용 방법

### 초기 설정 (단 한 번)

VS Code Task 실행:

```
🤖 AI: Bootstrap Self-Managing System (Once)
```

또는 PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_autonomous_system.ps1
```

**결과**:

- ✅ AI가 모든 의존성 자동 체크
- ✅ 가능한 모든 것 자동 등록/시작
- ⚠️ 관리자 권한 필요 시 명령어 출력

**관리자 권한 필요 시**:

```powershell
# 출력된 명령어를 관리자 권한으로 실행
# 예시:
powershell -NoProfile -ExecutionPolicy Bypass -File 'C:\workspace\agi\scripts\register_watchdog_task.ps1' -Register
```

그 후 다시 Bootstrap 실행:

```
🤖 AI: Bootstrap Self-Managing System (Once)
```

완료되면 **AI가 모든 것을 자율 관리**합니다.

---

## 📊 모니터링

### 1. 자율 관리 상태 확인

VS Code Task:

```
🤖 AI: Check Self-Managing Status
```

또는:

```powershell
fdo_agi_repo\.venv\Scripts\python.exe fdo_agi_repo\orchestrator\self_managing_agent.py --no-auto-fix
```

### 2. 리포트 보기

**Markdown 리포트**:

```
🤖 AI: Open Self-Managing Report (MD)
```

**JSON 리포트**:

```
🤖 AI: Open Self-Managing Report (JSON)
```

**위치**:

- `outputs/self_managing_agent_latest.md`
- `outputs/self_managing_agent_latest.json`

---

## 🔧 구성 요소

### 1. Self-Managing Agent

**위치**: `fdo_agi_repo/orchestrator/self_managing_agent.py`

**기능**:

- 모든 의존성(서버/워커/워치독) 자동 체크
- 프로세스 실행 여부 확인
- 예약 작업 등록 여부 확인
- HTTP 헬스 체크
- 자동 등록/시작 시도
- 권한 부족 시 사용자에게 manual command 제공
- 모든 조치를 리포트로 기록

**관리 대상**:

| 의존성 | 프로세스 체크 | 예약 작업 | 헬스 체크 | 자동 시작 |
|--------|--------------|-----------|-----------|----------|
| Task Queue Server | ✅ | ✅ | ✅ | ✅ |
| RPA Worker | ✅ | ❌ | ❌ | ✅ |
| Watchdog | ✅ | ✅ | ❌ | ⚠️ (관리자 권한) |
| Master Orchestrator | ⚠️ | ✅ | ❌ | ⚠️ (관리자 권한) |
| Monitoring Collector | ❌ | ✅ | ❌ | ❌ |

### 2. Bootstrap Script

**위치**: `scripts/bootstrap_autonomous_system.ps1`

**역할**:

- Self-Managing Agent 실행
- 리포트 확인
- 사용자에게 필요 시 manual command 안내
- 완료 후 자율 모드 활성화 확인

### 3. Master Orchestrator 통합

**위치**: `scripts/master_orchestrator.ps1`

**변경사항**:

- Step 5: Self-Managing Agent 자동 실행 추가
- 모든 의존성을 AI가 자율 점검/복구
- 결과를 콘솔에 표시

---

## 🎓 개념 이해

### AI 자율성 레벨

| 레벨 | 설명 | 예시 |
|------|------|------|
| **L0: Manual** | 사람이 모든 것을 수동 실행 | 매번 서버 시작 명령어 입력 |
| **L1: Scripted** | 스크립트로 자동화, 사람이 실행 | "서버 시작" 스크립트 클릭 |
| **L2: Scheduled** | 예약 작업으로 자동 실행 | 매일 3시에 자동 백업 |
| **L3: Monitored** | 감시 + 알림 | 서버 다운 시 알림 전송 |
| **L4: Self-Healing** | 감시 + 자동 복구 | 서버 다운 시 자동 재시작 |
| **L5: Self-Managing** ⭐ | **AI가 자기 자신을 관리** | AI가 의존성 등록/복구/진화 |
| **L6: Self-Evolving** 🚀 | AI가 스스로 코드 개선 | *(미래)* |

**현재 시스템: Level 5 (Self-Managing)**

---

## 🔐 보안 및 권한

### 관리자 권한이 필요한 작업

1. **Scheduled Task 등록**
   - Windows Task Scheduler에 등록 시 관리자 권한 필요
   - 예: Watchdog, Master Orchestrator

2. **시스템 서비스 변경**
   - 방화벽, 네트워크 설정 등

### AI가 자동으로 처리하는 작업 (권한 불필요)

1. **프로세스 시작/중지**
   - 현재 사용자 권한으로 실행 가능

2. **파일 읽기/쓰기**
   - workspace 내 모든 파일

3. **HTTP 요청**
   - 헬스 체크, API 호출

### 보안 원칙

- ✅ AI는 **읽기 전용 체크**를 기본으로 실행 (`--no-auto-fix`)
- ✅ 자동 수정 시에도 **권한 범위 내에서만** 실행
- ✅ 권한 부족 시 **명확한 manual command 제공**
- ✅ 모든 조치를 **투명하게 로그로 기록**

---

## 📝 로그 및 리포트

### 출력 파일

| 파일 | 설명 | 형식 |
|------|------|------|
| `outputs/self_managing_agent_latest.md` | 사람이 읽기 쉬운 리포트 | Markdown |
| `outputs/self_managing_agent_latest.json` | 기계 처리용 상세 데이터 | JSON |

### 리포트 내용

1. **Dependencies Status**
   - 각 의존성의 실행 상태
   - 예약 작업 등록 상태
   - 헬스 체크 결과
   - Auto-Fixed 여부

2. **Actions Taken**
   - AI가 수행한 모든 조치
   - 성공/실패 여부

3. **Needs Human Approval**
   - 관리자 권한이 필요한 작업
   - 실행할 명령어

4. **Errors**
   - 발생한 모든 에러

---

## 🔄 일상 워크플로우

### 아침 (VS Code 열 때)

1. **Master Orchestrator 자동 시작** (로그온 시 등록 시)
   - 모든 핵심 프로세스 시작
   - Self-Managing Agent 자동 실행
   - 의존성 자동 체크 + 복구

2. **결과 확인**
   - 콘솔 출력으로 간단 확인
   - 문제 있으면 리포트 자동 생성

### 개발 중

- **AI가 백그라운드에서 모든 것 관리**
- 사람은 코딩에만 집중
- 문제 발생 시 AI가 자동 복구
- 복구 불가 시에만 알림

### 저녁 (VS Code 닫기 전)

- **자동 백업** (03:30 예약 작업)
- **상태 스냅샷 저장**
- 다음날 자동 복구를 위한 컨텍스트 보존

---

## 🐛 트러블슈팅

### 문제: Bootstrap이 실패함

**원인**: Python venv가 없거나 스크립트 누락

**해결**:

```powershell
cd fdo_agi_repo
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 문제: 관리자 권한 에러

**원인**: Scheduled Task 등록 시 관리자 권한 필요

**해결**:

1. 리포트에서 manual command 확인:

   ```
   🤖 AI: Open Self-Managing Report (MD)
   ```

2. 해당 명령어를 **관리자 권한 PowerShell**에서 실행
3. Bootstrap 재실행

### 문제: 프로세스가 자동 시작되지 않음

**원인**: Master Orchestrator 미등록 또는 Watchdog 미등록

**해결**:

```powershell
# 1. Bootstrap 재실행
powershell -File scripts/bootstrap_autonomous_system.ps1

# 2. 수동 등록 (관리자 권한)
powershell -File scripts/register_master_orchestrator.ps1 -Register
powershell -File scripts/register_watchdog_task.ps1 -Register

# 3. 상태 확인
🤖 AI: Check Self-Managing Status
```

---

## 🎯 목표 달성 확인

### ✅ 달성한 것들

- [x] AI가 모든 의존성을 자동 체크
- [x] AI가 가능한 모든 것을 자동 등록/시작
- [x] 권한 문제 시 명확한 manual command 제공
- [x] 모든 조치를 투명하게 로그로 기록
- [x] 단 한 번의 Bootstrap으로 완전 자율 모드 활성화
- [x] Master Orchestrator에 통합
- [x] VS Code Tasks 추가
- [x] 완성도 높은 문서화

### 🎊 결과

**사용자는 이제:**

- ✅ Bootstrap 단 한 번만 실행
- ✅ 관리자 권한 승인만 최소한으로 개입
- ✅ 이후 **AI가 모든 것을 자율 관리**
- ✅ 사람은 **코딩에만 집중**

**AI는 이제:**

- ✅ 자기 자신의 건강 상태를 스스로 모니터링
- ✅ 필요한 의존성을 자동 등록/시작/복구
- ✅ 권한 문제 시에만 사용자에게 최소한의 승인 요청
- ✅ 모든 작업을 투명하게 로그로 남김

---

## 🚀 다음 단계 (Future)

### Phase 6: Self-Evolving System

- [ ] AI가 자신의 코드를 개선
- [ ] 성능 데이터 기반 자동 최적화
- [ ] 새로운 패턴 감지 → 자동 통합
- [ ] 사용자 피드백 학습 → 자동 적응

### Phase 7: Multi-Agent Collaboration

- [ ] 여러 AI 에이전트 간 자율 협업
- [ ] 역할 분담 자동 최적화
- [ ] 충돌 해결 자동화

---

## 📚 참고 문서

- `COMPLETE_AUTONOMOUS_SYSTEM.md`: 전체 자율 시스템 개요
- `REBOOT_RESILIENT_ARCHITECTURE.md`: 재부팅 복원력
- `AI_AUTONOMOUS_OPS_COMPLETION.md`: 자율 운영 완성
- `PHASE_5_5_AUTONOMOUS_ORCHESTRATION_COMPLETE.md`: 자율 오케스트레이션

---

**Last Updated**: 2025-11-02  
**Status**: ✅ Production Ready  
**Philosophy**: AI manages AI. Humans code. 🤖💙
