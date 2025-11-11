# 터미널 종료 안전 가이드 ✅

**결론: 터미널을 종료해도 데이터는 안전합니다!**

---

## 🛡️ **현재 시스템 구조**

### PowerShell Background Jobs (현재 세션 한정)

```
현재 실행 중:
- AGI_Lumen_24h     (ID: 13) - RUNNING
- AGI_Trinity_24h   (ID: 15) - Completed  
- AGI_Dashboard_24h (ID: 17) - RUNNING
```

**⚠️ 중요**: PowerShell **Background Job**은 **현재 PowerShell 세션**에만 존재합니다.

---

## 💾 **데이터 보존 상태**

### ✅ **안전하게 저장되는 것**

1. **로그 파일** (디스크에 실시간 저장)

   ```
   ✅ outputs\fullstack_24h_monitoring.jsonl  (8시간+ 누적)
   ✅ outputs\lumen_24h_latest.json
   ✅ outputs\gateway_optimization_log.jsonl
   ```

2. **상태 스냅샷** (주기적 자동 저장)

   ```
   ✅ outputs\quick_status_*.json
   ✅ outputs\autopoietic_loop_report_*.md
   ```

3. **학습 모델** (파일 시스템에 저장)

   ```
   ✅ fdo_agi_repo\outputs\bqi_pattern_model.json
   ✅ fdo_agi_repo\outputs\ensemble_weights.json
   ```

### ❌ **터미널 종료 시 사라지는 것**

1. **PowerShell Background Jobs**
   - 현재 세션의 메모리에만 존재
   - 터미널 닫으면 Job도 종료됨
   - **BUT**: 로그 파일은 남아있음!

2. **실시간 화면 출력**
   - 터미널 스크롤 버퍼만 사라짐
   - 데이터 자체는 파일에 저장됨

---

## 🔄 **터미널 종료 후 복구 방법**

### 시나리오 1: **VS Code 터미널만 닫음** (VS Code는 열려있음)

```powershell
# 새 터미널 열고 확인
Get-Job | Format-Table Id, Name, State

# 출력 예시:
# Id  Name              State
# 13  AGI_Lumen_24h     Running
# 17  AGI_Dashboard_24h Running
```

**✅ Job은 살아있음** (같은 PowerShell 인스턴스)

### 시나리오 2: **VS Code 전체 종료**

```powershell
# VS Code 재실행 후
Get-Job  # ❌ 비어있음 (새 PowerShell 세션)

# ✅ 복구 방법
.\scripts\resume_24h_productions.ps1
```

**자동 실행**: `.vscode\tasks.json`의 `runOn: folderOpen` 설정으로 자동 재개

### 시나리오 3: **Windows 재부팅**

```powershell
# 재부팅 후 VS Code 열면
# ✅ 자동 실행: tasks.json → resume_24h_productions.ps1

# 수동 확인:
.\scripts\check_system_after_restart.ps1
```

---

## 📊 **로그 데이터 확인 방법**

### 1. 최근 활동 확인 (터미널 없이)

```powershell
# Lumen 24h 로그
Get-Content outputs\lumen_24h_latest.json | ConvertFrom-Json

# Orchestrator 로그 (최근 3줄)
Get-Content outputs\fullstack_24h_monitoring.jsonl -Tail 3

# Gateway 최적화 로그
Get-Content outputs\gateway_optimization_log.jsonl -Tail 5
```

### 2. Dashboard HTML 생성

```powershell
# 최신 데이터로 대시보드 재생성
.\scripts\unified_realtime_dashboard.ps1 -Once -OpenBrowser
```

### 3. 누적 통계 보기

```powershell
# 24시간 요약
.\scripts\summarize_realtime_pipeline.ps1 -Lookback 24 -Open
```

---

## 🎯 **권장 워크플로우**

### **옵션 A: 안전하게 끄고 싶을 때**

```powershell
# 1. 상태 저장
.\scripts\save_session_with_changes.ps1

# 2. VS Code 종료
# (터미널 닫기 전 Job 상태는 자동 저장됨)

# 3. 다음 세션에서 자동 재개
# → tasks.json이 자동 실행
```

### **옵션 B: 즉시 재개하고 싶을 때**

```powershell
# VS Code 재시작 후
.\scripts\resume_24h_productions.ps1

# 또는 수동
.\scripts\start_24h_monitoring.ps1
```

### **옵션 C: 로그만 보고 싶을 때**

```powershell
# Job 없이도 가능
code outputs\fullstack_24h_monitoring.jsonl
code outputs\lumen_24h_latest.json

# Dashboard 재생성
.\scripts\unified_realtime_dashboard.ps1 -Once -OpenBrowser
```

---

## 🔍 **실시간 모니터링 재연결**

터미널 종료 후에도 **같은 PowerShell 세션**이면 Job 재연결 가능:

```powershell
# 실시간 로그 스트림 (Ctrl+C로 중지)
Get-Job -Name 'AGI_Lumen_24h' | Receive-Job -Keep -Wait

# 최근 10줄만
Get-Job -Name 'AGI_Lumen_24h' | Receive-Job -Keep | Select-Object -Last 10
```

---

## ⚠️ **주의사항**

### ❌ **하지 말아야 할 것**

1. **`Stop-Job` 명령 실수로 실행**

   ```powershell
   # 이러면 Job 종료됨!
   Get-Job | Stop-Job  # ❌
   ```

2. **PowerShell 강제 종료**
   - 작업 관리자에서 `pwsh.exe` 강제 종료
   - 데이터 손실 가능성 있음

3. **로그 파일 수동 삭제**
   - `outputs\*.jsonl` 삭제하면 이력 손실

### ✅ **안전한 종료 방법**

```powershell
# 1. 상태 확인
Get-Job | Format-Table

# 2. 정상 종료 (선택)
Get-Job -Name 'AGI_*' | Stop-Job

# 3. VS Code 종료
# (또는 그냥 종료 → 다음에 자동 재개)
```

---

## 📈 **누적 데이터 현황**

### 현재 저장된 데이터 (2025-11-04 16:40 기준)

```
✅ fullstack_24h_monitoring.jsonl
   - 시작: 2025-11-04 08:14:32
   - 경과: 8.3시간
   - 샘플: 101개
   - 크기: ~50KB

✅ lumen_24h_latest.json
   - 사이클: 9 / 288
   - 진행률: 3.1%
   - 상태: RUNNING

✅ gateway_optimization_log.jsonl
   - 적응적 타임아웃 테스트 중
   - Off-peak 최적화 모니터링
```

### 예상 완료 시간

- **Lumen 24h**: 2025-11-05 08:14 (내일 아침)
- **Orchestrator 24h**: 2025-11-05 08:14
- **Gateway 24h**: 2025-11-05 22:26 (내일 밤)

---

## 🎓 **결론**

| 질문 | 답변 |
|------|------|
| 터미널 종료해도 되나요? | ✅ **예**, 로그는 안전합니다 |
| 데이터가 날아가나요? | ❌ **아니오**, 파일에 저장됩니다 |
| Job이 계속 실행되나요? | ⚠️ 같은 세션이면 **예**, 재시작하면 **아니오** |
| 복구할 수 있나요? | ✅ **예**, `resume_24h_productions.ps1` 실행 |
| 자동으로 복구되나요? | ✅ **예**, VS Code 열 때 자동 실행 |

**마음 편히 터미널 닫으세요!** 🎉 로그는 안전하게 저장되고 있습니다.

---

## 📞 **긴급 복구 명령**

```powershell
# 1단계: 상태 확인
Get-Job | Format-Table

# 2단계: 로그 확인
Get-Content outputs\fullstack_24h_monitoring.jsonl -Tail 1

# 3단계: 재시작 (필요 시)
.\scripts\resume_24h_productions.ps1

# 4단계: 대시보드 확인
.\scripts\unified_realtime_dashboard.ps1 -Once -OpenBrowser
```

---

**생성일**: 2025-11-04  
**마지막 업데이트**: Phase 6.3 완료 후  
**관련 문서**: `REBOOT_SAFE_SYSTEM_COMPLETE.md`
