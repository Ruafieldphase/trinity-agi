# 자동 건강 체크 설정 방법

## 빠른 설정 (관리자 권한 필요)

### 방법 1: PowerShell 스크립트 실행 (권장)

1. **PowerShell을 관리자 권한으로 실행**
2. 다음 명령 실행:
```powershell
cd D:\nas_backup\fdo_agi_repo\scripts
.\setup_scheduled_task.ps1
```

### 방법 2: 수동 명령 (Command Prompt)

관리자 권한으로 CMD 실행 후:
```cmd
schtasks /create /tn "AGI_Daily_Health_Check" /tr "D:\nas_backup\fdo_agi_repo\scripts\run_daily_health_check.bat" /sc daily /st 09:00 /f
```

### 방법 3: GUI (Task Scheduler)

1. `Win+R` → `taskschd.msc` 입력
2. "Create Basic Task" 클릭
3. 이름: `AGI_Daily_Health_Check`
4. 트리거: Daily, 09:00 AM
5. 동작: `D:\nas_backup\fdo_agi_repo\scripts\run_daily_health_check.bat`

## 설정 확인

```powershell
Get-ScheduledTask -TaskName "AGI_Daily_Health_Check"
```

## 즉시 테스트

```powershell
Start-ScheduledTask -TaskName "AGI_Daily_Health_Check"
```

## 수동 실행

자동화 없이 수동으로 실행:
```bash
cd D:\nas_backup\fdo_agi_repo
python scripts\daily_health_check.py
```

## 생성된 파일

- ✅ `scripts/run_daily_health_check.bat` - 실행 스크립트
- ✅ `scripts/setup_scheduled_task.ps1` - 자동 설정 스크립트
- ✅ `scripts/daily_health_check.py` - 건강 체크 로직
- ✅ `docs/setup_automated_health_check.md` - 상세 문서
- ✅ `logs/` - 로그 디렉토리

## 예상 결과

- **현재**: Health Score = 15/100 (CRITICAL) - 24시간 동안 구 데이터 포함
- **1-2일 후**: Health Score = 50-70 (WARNING) - 구 데이터 일부 제거
- **3일 후**: Health Score = 90+ (HEALTHY) - 완전히 새 데이터

## 다음 단계

설정 완료 후:
1. 7일 동안 매일 확인
2. Health Score 90+ 안정화 확인
3. P3.1 (Dashboard 최적화) 진행
