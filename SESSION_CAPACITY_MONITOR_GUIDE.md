# 📊 Session Capacity Monitor & Auto-Handoff System

**생성일**: 2025-11-02  
**상태**: 🟢 Production Ready

---

## 🎯 목적

AI 대화 세션은 토큰 제한이 있어 긴 작업 중 용량 한계에 도달하면 중단됩니다.  
이 시스템은 **자동으로 세션 용량을 모니터링**하고, 임계값 도달 시:

1. ✅ **자동 경고** - 명확한 메시지 출력
2. 💾 **대화 저장** - 현재까지의 작업 내용 보존
3. 📄 **Handoff 문서 생성** - 다음 세션용 컨텍스트
4. 🔄 **새 세션 가이드** - 작업 이어가기 방법 안내

---

## 🚀 사용 방법

### 1️⃣ 현재 세션 상태 확인

```powershell
# 빠른 확인
.\scripts\session_capacity_monitor.ps1 -CheckOnly
```

**출력 예시**:

```
📊 현재 용량: 45.2%
   임계값: 80%
   상태: 🟢 NORMAL
```

### 2️⃣ VS Code Task로 확인

**Tasks: Run Task** → **🔍 Session: Check Capacity**

### 3️⃣ 자동 모니터링 (백그라운드)

```powershell
# 5분마다 자동 체크
.\scripts\session_capacity_monitor.ps1 -AutoMonitor
```

또는 VS Code Task:  
**🔄 Session: Auto-Monitor Loop** (백그라운드)

### 4️⃣ 강제 Handoff 생성

작업을 마무리하고 새 세션으로 전환하려면:

```powershell
.\scripts\session_capacity_monitor.ps1 -SaveHandoff
```

또는 VS Code Task:  
**💾 Session: Force Save & Handoff**

---

## 📊 용량 추정 알고리즘

세션 용량은 다음 4가지 지표로 추정됩니다:

| 지표 | 가중치 | 위험 임계값 | 기준 |
|------|--------|-------------|------|
| **대화 턴 수** | 40% | 50+ turns | 많은 대화 = 높은 토큰 |
| **경과 시간** | 30% | 60+ 분 | 긴 시간 = 많은 컨텍스트 |
| **생성 파일** | 20% | 40+ 파일 | 많은 파일 = 많은 내용 |
| **명령 실행** | 10% | 100+ 명령 | 많은 실행 = 많은 출력 |

**용량 계산**:

```
Capacity = (TurnScore × 0.4) + (TimeScore × 0.3) + 
           (FileScore × 0.2) + (CmdScore × 0.1)
```

### 상태 레벨

- 🟢 **NORMAL** (0-79%): 안전, 계속 작업
- 🟡 **WARNING** (80-89%): 주의, 곧 전환 필요
- 🔴 **CRITICAL** (90-100%): 위험, 즉시 전환 권장

---

## 🔄 새 세션으로 전환하기

### 경고 메시지를 받았을 때

```
⚠️  SESSION CAPACITY WARNING
📊 현재 세션 용량: 85.3%
🟡 상태: WARNING - 곧 새 세션 전환 필요
```

### 전환 단계

#### 1️⃣ 현재 세션 마무리

- 중요 작업 완료
- 파일 저장 확인
- 열려 있는 터미널 종료

#### 2️⃣ 새 세션 시작

**방법 A**: VS Code 명령

```
Ctrl+Shift+P → "GitHub Copilot: New Chat"
```

**방법 B**: 수동으로 Chat 패널 닫고 다시 열기

#### 3️⃣ 작업 이어가기

새 세션에서 다음 중 하나 입력:

```
이전 세션 핸드오프 확인하고 작업 이어가기
```

또는:

```
handoff_latest.md 파일 읽고 다음 작업 계속
```

또는:

```
outputs/session_memory/handoff_latest.md 열어서 컨텍스트 확인
```

---

## 📄 Handoff 문서 구조

`outputs/session_memory/handoff_latest.md` 포함 내용:

### 1. 세션 통계

- 세션 ID
- 시작/종료 시각
- 대화 턴, 파일, 명령 수
- 용량 상태

### 2. 현재 작업 상태

- 진행 중인 작업
- 최근 완료 작업
- 생성/수정된 파일

### 3. 다음 세션 작업

- 즉시 실행할 명령
- 중요 컨텍스트
- 참고 문서 링크

### 4. 전환 가이드

- 새 세션 시작 방법
- 작업 이어가기 프롬프트

---

## 🎯 실전 시나리오

### 시나리오 1: 긴 구현 작업 중

**상황**:

- 복잡한 기능 구현 중
- 여러 파일 생성
- 많은 대화 턴

**모니터링**:

```powershell
# 주기적으로 확인
.\scripts\session_capacity_monitor.ps1 -CheckOnly

# 출력: 📊 현재 용량: 78%
```

**조치**:

- 아직 안전 (80% 미만)
- 현재 작업 완료 후 전환 준비

### 시나리오 2: 경고 수신

**경고 메시지**:

```
🟡 WARNING - 용량 85.3%
📄 Handoff 문서 자동 생성됨
```

**조치**:

1. 현재 작업 **빠르게 마무리**
2. 중요한 내용 **저장 확인**
3. **새 세션 전환**

### 시나리오 3: 작업 일시 중단

**상황**:

- 점심 시간, 회의 등으로 작업 중단
- 나중에 다시 시작

**조치**:

```powershell
# 현재 상태 저장
.\scripts\session_capacity_monitor.ps1 -SaveHandoff
```

**재개 시**:

- 새 세션 시작
- `handoff_latest.md` 확인
- 작업 이어가기

---

## 🛠️ 고급 사용

### 커스텀 임계값

```powershell
# 70%에서 경고
.\scripts\session_capacity_monitor.ps1 -ThresholdPercent 70
```

### 세션 메타데이터 직접 확인

```powershell
# JSON 파일 열기
cat outputs\session_memory\current_session_meta.json | ConvertFrom-Json
```

**출력 예시**:

```json
{
  "session_id": "abc-123-def",
  "start_time": "2025-11-02T12:30:00",
  "turn_count": 42,
  "files_created": 8,
  "commands_executed": 25,
  "capacity_percent": 68.5,
  "warnings_issued": 0
}
```

### Handoff 히스토리

모든 Handoff 문서는 타임스탬프와 함께 보관:

```
outputs/session_memory/
├─ handoff_latest.md           ← 항상 최신
├─ handoff_20251102_123000.md  ← 히스토리
├─ handoff_20251102_150000.md
└─ handoff_20251102_173000.md
```

---

## 🔧 통합 방법

### 다른 스크립트에서 호출

```powershell
# 작업 시작 전 체크
.\scripts\session_capacity_monitor.ps1 -CheckOnly
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  용량 경고! 새 세션 전환 권장" -ForegroundColor Yellow
    exit 1
}

# 실제 작업 실행
.\my_long_task.ps1
```

### Python에서 호출

```python
import subprocess

def check_session_capacity():
    result = subprocess.run(
        ["powershell", "-File", "scripts/session_capacity_monitor.ps1", "-CheckOnly"],
        capture_output=True
    )
    return result.returncode == 0  # True = 정상

if not check_session_capacity():
    print("⚠️  Session capacity warning!")
```

### VS Code Extension Integration

```typescript
// extension.ts
import { exec } from 'child_process';

function checkSessionCapacity(): Promise<boolean> {
    return new Promise((resolve) => {
        exec('powershell -File scripts/session_capacity_monitor.ps1 -CheckOnly',
            (error, stdout) => {
                resolve(!error);
            });
    });
}
```

---

## 📊 모니터링 대시보드 (예정)

**Phase 7 계획**:

- 실시간 용량 게이지
- 히스토리 그래프
- 자동 알림 (토스트)
- VS Code 상태 바 통합

---

## 🎯 Best Practices

### ✅ DO

1. **주기적 확인**
   - 긴 작업 전/후 체크
   - 중요 마일스톤마다 확인

2. **경고 시 즉시 조치**
   - 80% 이상: 작업 마무리 준비
   - 90% 이상: 즉시 전환

3. **Handoff 문서 활용**
   - 새 세션에서 반드시 확인
   - 컨텍스트 유실 방지

4. **히스토리 보관**
   - 타임스탬프 버전 활용
   - 필요 시 과거 세션 참조

### ❌ DON'T

1. **경고 무시하지 말기**
   - 90% 이상은 매우 위험
   - 갑작스런 중단 가능

2. **무분별한 파일 생성**
   - 꼭 필요한 파일만
   - 임시 파일은 정리

3. **Handoff 없이 전환**
   - 컨텍스트 유실
   - 작업 중단 위험

---

## 🔄 Workflow 예시

### 일반적인 작업 흐름

```
1. 세션 시작
   ↓
2. 작업 진행 (파일 생성, 명령 실행)
   ↓
3. [자동] 용량 모니터링
   ↓
4. 용량 80% 도달
   ↓
5. [자동] 경고 메시지 + Handoff 생성
   ↓
6. 현재 작업 마무리
   ↓
7. 새 세션 시작
   ↓
8. Handoff 문서 확인
   ↓
9. 작업 이어가기
```

---

## 📚 관련 문서

- `SELF_CONTINUING_AGENT_IMPLEMENTATION.md` - 자율 실행 시스템
- `PHASE_6_PREDICTIVE_ORCHESTRATION_STATUS.md` - Phase 6 현황
- `outputs/session_memory/conversation_*.md` - 대화 기록들

---

## 🎊 핵심 가치

### "끊김 없는 작업 연속성"

**Before**:

```
작업 중 → 갑자기 중단 → 컨텍스트 유실 → 다시 시작
```

**After**:

```
작업 중 → 경고 수신 → 안전하게 저장 → 새 세션에서 이어가기
```

### 자율성 + 연속성

- **자동 모니터링**: 사용자가 신경 쓰지 않아도 됨
- **스마트 경고**: 적절한 시점에 알림
- **완벽한 Handoff**: 컨텍스트 유실 없음
- **자연스러운 전환**: 끊김 없는 경험

---

**생성일**: 2025-11-02  
**버전**: 1.0  
**상태**: Production Ready ✅

---

이것은 **Self-Aware Agent**의 또 다른 능력입니다:  
**자신의 한계를 인식하고, 사전에 조치하는 능력!** 🎯
