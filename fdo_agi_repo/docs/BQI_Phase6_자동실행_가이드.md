# BQI Phase 6 자동 실행 가이드

**날짜**: 2025-10-28  
**주제**: 절전 모드와 Scheduled Task 자동 실행

---

## ❓ 질문: 새벽에 절전 모드일 때 자동 실행이 가능한가요?

**답**: 기본 설정으로는 **안 됩니다.** 하지만 두 가지 방법이 있습니다.

---

## 📌 해결책 1: StartWhenAvailable (권장)

### 동작 방식

- ✅ 컴퓨터가 **켜져 있으면** 정확히 03:05에 실행
- ✅ 컴퓨터가 **절전/꺼져 있으면** 다음 부팅/깨어날 때 실행
- ✅ **관리자 권한 불필요**
- ✅ **BIOS 설정 불필요**

### 등록 방법

```powershell
cd d:\nas_backup\fdo_agi_repo
.\scripts\register_bqi_phase6_scheduled_task.ps1 -Register
```

### 장점

- 간단하고 안전
- 대부분의 사용자에게 충분
- 매일 컴퓨터를 사용한다면 데이터가 자동으로 축적됨

### 단점

- 정확히 03:05에 실행되지는 않을 수 있음 (다음 깨어날 때 실행)

---

## 🌙 해결책 2: WakeFromSleep (고급)

### 동작 방식

- ✅ 컴퓨터를 **절전 모드에서 깨워서** 03:05에 실행
- ⚠️ **관리자 권한 필요**
- ⚠️ **BIOS 'Wake Timers' 설정 필요**

### 등록 방법

```powershell
# PowerShell을 관리자로 실행 후:
cd d:\nas_backup\fdo_agi_repo
.\scripts\register_bqi_phase6_scheduled_task.ps1 -Register -WakeFromSleep
```

### BIOS 설정 확인

```powershell
# Wake timer 지원 확인
.\scripts\check_wake_timer_support.ps1

# 현재 wake 가능한 장치 확인
powercfg /devicequery wake_armed
```

### 장점

- 정확히 03:05에 실행 보장
- 24시간 무인 모니터링에 적합

### 단점

- 관리자 권한 필요
- BIOS 설정 필요
- 일부 시스템에서 지원 안 될 수 있음

---

## 💡 권장 사항

### 일반 사용자 (권장)

```powershell
# 기본 모드 사용
.\scripts\register_bqi_phase6_scheduled_task.ps1 -Register
```

**이유**:

- 매일 컴퓨터를 사용한다면 충분
- 아침에 컴퓨터를 켤 때 자동 실행
- 관리자 권한 불필요

### 서버/24시간 운영

```powershell
# Wake mode 사용
.\scripts\register_bqi_phase6_scheduled_task.ps1 -Register -WakeFromSleep
```

**이유**:

- 정확한 시간에 실행 필요
- 절전 모드에서도 깨워서 실행

---

## 🔧 현재 설정 확인

### Scheduled Task 상태

```powershell
.\scripts\register_bqi_phase6_scheduled_task.ps1
```

### Wake Timer 지원 확인

```powershell
.\scripts\check_wake_timer_support.ps1
```

### 수동 실행 (테스트)

```powershell
.\scripts\run_bqi_learner.ps1 -VerboseLog
```

---

## 📊 비교표

| 항목 | StartWhenAvailable | WakeFromSleep |
|------|-------------------|---------------|
| 절전 시 실행 | ❌ 다음 부팅 시 | ✅ 절전에서 깨움 |
| 관리자 권한 | ❌ 불필요 | ✅ 필요 |
| BIOS 설정 | ❌ 불필요 | ✅ 필요 |
| 정확한 시간 | ⚠️ 근사 | ✅ 정확 |
| 안정성 | ✅ 높음 | ⚠️ 시스템 의존 |
| 배터리 영향 | ❌ 없음 | ⚠️ 약간 |

---

## 🎯 결론

**대부분의 경우 기본 모드(StartWhenAvailable)로 충분합니다!**

- ✅ 매일 컴퓨터를 사용하면 데이터가 축적됨
- ✅ 간단하고 안전
- ✅ 관리자 권한 불필요

**WakeFromSleep은 특수한 경우에만:**

- 24시간 무인 서버
- 정확한 시간에 실행 필수
- BIOS 설정 가능한 환경

---

## 📝 추가 팁

### 로그 확인

```powershell
# 마지막 실행 로그
code d:\nas_backup\fdo_agi_repo\outputs\bqi_learner_last_run.txt

# Task Scheduler GUI
taskschd.msc
```

### 실행 시간 변경

```powershell
# 예: 오후 2시로 변경
.\scripts\register_bqi_phase6_scheduled_task.ps1 -Register -Time "14:00"
```

### 제거

```powershell
.\scripts\register_bqi_phase6_scheduled_task.ps1 -Unregister
```

---

**참고**: 현재 설정은 **StartWhenAvailable 모드**로 등록되어 있습니다. 다음 부팅/깨어날 때 자동으로 실행됩니다. 🚀
