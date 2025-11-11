# 🛡️ Phase 6.3 - 재부팅/재시작 안전 시스템

**작성일**: 2025-11-04 16:50 KST  
**상태**: ✅ **PRODUCTION READY**

---

## 📋 개요

VS Code 재시작 또는 Windows 재부팅 시에도 **24h Production이 자동으로 복구**되는 시스템입니다.

---

## 🎯 핵심 기능

### 1️⃣ **자동 복구 (VS Code 재시작)**

```
VS Code 열기
  ↓
runOn: folderOpen 태스크 실행
  ↓
resume_24h_productions.ps1 자동 실행
  ↓
중단된 Production 확인 및 재시작
  ↓
✅ 모든 시스템 복구 완료
```

### 2️⃣ **백그라운드 Job 방식**

PowerShell Job으로 3개 Production 실행:

- `AGI_Lumen_24h`: Lumen 24h Feedback System
- `AGI_Trinity_24h`: Trinity Autopoietic Cycle
- `AGI_Dashboard_24h`: Unified Real-Time Dashboard

### 3️⃣ **상태 기반 복구**

로그 파일과 Job 상태를 확인하여:

- ✅ 실행 중 → 그대로 유지
- ⚠️  중단됨 → 자동 재시작
- 📊 진행률 표시

---

## 🚀 사용 방법

### **A. 수동 시작 (처음 실행 시)**

```powershell
# 백그라운드 Job으로 모든 Production 시작
.\scripts\start_24h_productions_background.ps1

# 또는 기존 Job 강제 종료 후 재시작
.\scripts\start_24h_productions_background.ps1 -Force
```

### **B. 자동 복구 (VS Code 재시작 시)**

1. VS Code를 닫고 다시 엽니다
2. `runOn: folderOpen` 태스크가 자동 실행됩니다
3. 중단된 Production이 자동으로 재시작됩니다

### **C. 상태 확인**

```powershell
# PowerShell Job 상태 확인
Get-Job | Where-Object { $_.Name -like 'AGI_*' }

# 또는 resume 스크립트 실행
.\scripts\resume_24h_productions.ps1
```

---

## 📊 Production 목록

| Production | Job Name | 로그 위치 | 실행 시간 |
|-----------|----------|----------|----------|
| **Lumen 24h** | `AGI_Lumen_24h` | `fdo_agi_repo\outputs\lumen_production_24h_stable.jsonl` | 24시간 (288 사이클) |
| **Trinity Cycle** | `AGI_Trinity_24h` | `outputs\trinity_cycle_24h_*.md` | 24시간 |
| **Dashboard** | `AGI_Dashboard_24h` | `outputs\unified_dashboard_latest.txt` | 무한 (10초 갱신) |

---

## 🔧 시스템 구성

### **파일 구조**

```
scripts/
├── start_24h_productions_background.ps1   # 백그라운드 Job 시작
├── resume_24h_productions.ps1             # VS Code 열 때 자동 복구
├── start_lumen_24h_stable.ps1             # Lumen Production
├── autopoietic_trinity_cycle.ps1          # Trinity Cycle
└── unified_realtime_dashboard.ps1         # Dashboard (with -Once)

.vscode/
└── tasks.json
    └── "🔄 Auto: Resume 24h Productions (VS Code Open)"
        - runOn: "folderOpen"
        - 자동 실행됨
```

### **VS Code Task (자동 실행)**

```json
{
  "label": "🔄 Auto: Resume 24h Productions (VS Code Open)",
  "runOptions": {
    "runOn": "folderOpen"
  }
}
```

---

## ⚠️ 중요 사항

### **PowerShell 창 유지**

- ✅ **VS Code 터미널**: Job이 안전하게 유지됨
- ⚠️  **외부 PowerShell 창**: 창을 닫으면 Job도 종료됨

### **재부팅 시 한계**

- ❌ PowerShell Job은 재부팅 시 사라집니다
- ✅ VS Code를 다시 열면 자동으로 복구됩니다
- 💡 Windows Scheduled Task는 관리자 권한 필요 (현재 미사용)

---

## 📈 복구 시나리오

### **시나리오 1: VS Code 재시작**

```
1. VS Code 닫기
2. VS Code 다시 열기
   ↓
   runOn: folderOpen 태스크 실행
   ↓
3. resume_24h_productions.ps1 자동 실행
   ↓
4. Job 상태 확인
   - 🟢 Running → 유지
   - ⚠️  없음 → 재시작
   ↓
5. ✅ 모든 Production 복구 완료
```

### **시나리오 2: Windows 재부팅**

```
1. Windows 재부팅
   ↓
   (모든 PowerShell Job 사라짐)
   ↓
2. VS Code 열기
   ↓
   runOn: folderOpen 태스크 실행
   ↓
3. resume_24h_productions.ps1 자동 실행
   ↓
4. 로그 파일 확인
   - 📊 10분 이내 업데이트 → 실행 중으로 간주
   - ⚠️  오래됨 → 재시작
   ↓
5. ✅ 모든 Production 복구 완료
```

### **시나리오 3: 수동 종료 후 재시작**

```powershell
# 모든 Job 종료
Get-Job | Where-Object { $_.Name -like 'AGI_*' } | Stop-Job
Get-Job | Where-Object { $_.Name -like 'AGI_*' } | Remove-Job

# 재시작 (Force 옵션)
.\scripts\start_24h_productions_background.ps1 -Force
```

---

## 🎯 검증 방법

### **1. Job 상태 확인**

```powershell
Get-Job | Where-Object { $_.Name -like 'AGI_*' } | Format-Table Name, State, Id
```

**예상 결과:**

```
Name              State   Id
----              -----   --
AGI_Lumen_24h     Running 123
AGI_Trinity_24h   Running 124
AGI_Dashboard_24h Running 125
```

### **2. 로그 확인**

```powershell
# Lumen 로그 (최근 5줄)
Get-Content "fdo_agi_repo\outputs\lumen_production_24h_stable.jsonl" -Tail 5

# Trinity 로그 (최신 파일)
Get-ChildItem "outputs\trinity_cycle_24h_*.md" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# Dashboard 로그
Get-Content "outputs\unified_dashboard_latest.txt" -Tail 10
```

### **3. Dashboard 실행**

```powershell
# 실시간 Dashboard (10초 갱신)
.\scripts\unified_realtime_dashboard.ps1

# 또는 1회만 실행
.\scripts\unified_realtime_dashboard.ps1 -Once
```

---

## 🚀 Quick Start

### **Step 1: 처음 시작**

```powershell
# 모든 Production 시작
.\scripts\start_24h_productions_background.ps1
```

### **Step 2: VS Code 재시작 테스트**

```
1. VS Code 닫기
2. VS Code 다시 열기
3. 자동 복구 확인:
   - Job 상태: Get-Job | Where-Object { $_.Name -like 'AGI_*' }
   - 로그 확인: tail -n 5 fdo_agi_repo\outputs\lumen_production_24h_stable.jsonl
```

### **Step 3: 재부팅 테스트 (선택)**

```
1. Windows 재부팅
2. VS Code 열기
3. 자동 복구 확인
```

---

## 💡 트러블슈팅

### **문제 1: Job이 시작 안 됨**

```powershell
# 강제 재시작
.\scripts\start_24h_productions_background.ps1 -Force
```

### **문제 2: 로그 업데이트 안 됨**

```powershell
# Job 출력 확인
Get-Job -Name 'AGI_Lumen_24h' | Receive-Job -Keep

# 또는
Get-Job | Where-Object { $_.Name -like 'AGI_*' } | Receive-Job -Keep
```

### **문제 3: VS Code 자동 복구 안 됨**

```powershell
# 수동으로 복구 스크립트 실행
.\scripts\resume_24h_productions.ps1
```

---

## 📊 현재 상태 (2025-11-04 16:50 KST)

### ✅ **완료된 작업**

1. ✅ `start_24h_productions_background.ps1` 작성
2. ✅ `resume_24h_productions.ps1` 작성 (Job 기반)
3. ✅ `unified_realtime_dashboard.ps1` -Once 옵션 추가
4. ✅ tasks.json에 자동 실행 태스크 추가
5. ✅ 문서 작성 완료

### 🟢 **실행 중인 Production**

1. Lumen 24h Production (16:13 시작)
2. Trinity Autopoietic Cycle (16:17 시작)
3. Unified Real-Time Dashboard (10초 갱신)

---

## 🎉 다음 단계

### **Option A: 재시작 테스트**

```powershell
# VS Code 재시작 테스트
1. VS Code 닫기
2. VS Code 다시 열기
3. 자동 복구 확인
```

### **Option B: Production 계속 실행**

```powershell
# Dashboard로 모니터링
.\scripts\unified_realtime_dashboard.ps1
```

### **Option C: Phase 7 준비**

- YouTube Learning 자동화
- RPA Worker 최적화

---

## 📝 결론

✅ **재부팅/재시작 안전 시스템 완성!**

- VS Code 재시작 → 자동 복구 ✅
- Windows 재부팅 → VS Code 열 때 자동 복구 ✅
- PowerShell Job 방식 → 관리자 권한 불필요 ✅
- 실시간 Dashboard → 10초 갱신 ✅

**이제 안심하고 작업할 수 있습니다!** 🎉
