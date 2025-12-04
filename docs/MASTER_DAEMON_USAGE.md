# AGI Master Daemon - 통합 제어 시스템

## 🎯 개요

**하나의 프로세스**로 모든 AGI 작업을 제어하는 통합 시스템입니다.

### 이전 시스템의 문제점

- ❌ 26개의 Scheduled Task가 따로 실행
- ❌ Startup 폴더에 5개의 파일 흩어짐
- ❌ 각각 독립적으로 실행되어 제어 어려움
- ❌ 창이 계속 떠서 방해됨

### Master Daemon의 장점

- ✅ **하나의 프로세스**만 관리하면 됨
- ✅ **중앙 집중식 제어** (start/stop/restart)
- ✅ **통합 로깅** (모든 작업을 한 곳에서 확인)
- ✅ **자동 재시작** (작업이 중단되면 자동 복구)
- ✅ **창 관리** (모든 창을 자동으로 숨김)

---

## 🚀 빠른 시작

### 1. 마이그레이션 (기존 시스템 정리)

```powershell
# Dry-run으로 먼저 확인
.\scripts\migrate_to_master_daemon.ps1 -DryRun

# 실제 마이그레이션 실행
.\scripts\migrate_to_master_daemon.ps1 -Force
```

### 2. 기본 사용법

```powershell
# 상태 확인
.\agi.ps1 status

# 시작
.\agi.ps1 start

# 중지
.\agi.ps1 stop

# 재시작
.\agi.ps1 restart

# 로그 보기 (마지막 50줄)
.\agi.ps1 logs

# 로그 실시간 모니터링 (tail -f)
.\agi.ps1 logs -Follow

# 설치 (부팅 시 자동 실행)
.\agi.ps1 install

# 제거
.\agi.ps1 uninstall
```

---

## 📁 구조

```
C:\workspace\agi\
├── agi.ps1                          ← 메인 컨트롤러 (여기서 모든 것 제어)
├── config\
│   └── master_daemon_config.json   ← 모든 작업 설정
├── scripts\
│   ├── master_daemon.ps1            ← 실제 데몬 프로세스
│   └── migrate_to_master_daemon.ps1 ← 마이그레이션 스크립트
└── outputs\
    ├── master_daemon.log            ← 통합 로그
    └── master_daemon.pid            ← 프로세스 ID
```

---

## ⚙️ 설정 (config/master_daemon_config.json)

### 작업 추가/수정/삭제

```json
{
  "tasks": {
    "my_new_task": {
      "enabled": true,              // true/false로 켜고 끄기
      "type": "continuous",         // continuous, interval, daily
      "script": "scripts/my_script.ps1",
      "args": ["-Param", "Value"],
      "restartOnFail": true,        // 실패 시 자동 재시작
      "hidden": true                // 항상 숨김
    }
  }
}
```

### 작업 타입

1. **continuous**: 계속 실행 (예: 서버, 워커)
2. **interval**: 주기적 실행 (예: 5분마다)
3. **daily**: 매일 특정 시각 (예: 아침 8시)

### Python 스크립트 실행

```json
{
  "my_python_task": {
    "enabled": true,
    "type": "continuous",
    "script": "path/to/script.py",
    "pythonVenv": "path/to/.venv/Scripts/python.exe",
    "args": ["--port", "8091"],
    "restartOnFail": true,
    "hidden": true
  }
}
```

---

## 🔧 고급 사용법

### 특정 작업만 켜기/끄기

```powershell
# config/master_daemon_config.json 편집
code config\master_daemon_config.json

# "enabled": false 로 변경 후 저장

# 재시작
.\agi.ps1 restart
```

### 작업별 로그 확인

```powershell
# 통합 로그에서 특정 작업만 필터링
Get-Content outputs\master_daemon.log | Select-String "task_queue_server"
```

### 수동 디버깅

```powershell
# Master Daemon을 foreground로 실행 (디버깅용)
.\scripts\master_daemon.ps1 -Start

# Ctrl+C로 중지
```

---

## 🛡️ 창 관리

Master Daemon은 다음을 자동으로 처리합니다:

1. 모든 작업을 `-WindowStyle Hidden`으로 실행
2. 30초마다 visible window 검사
3. 발견 시 자동으로 kill (설정에서 끄기 가능)

```json
{
  "windowManagement": {
    "enforceHidden": true,    // 강제 숨김 활성화
    "monitorInterval": 30,    // 검사 주기 (초)
    "autoHide": true          // 자동 숨김
  }
}
```

---

## 📊 모니터링

### 상태 확인

```powershell
.\agi.ps1 status
```

출력 예시:

```
=== AGI Master Daemon Status ===
✓ Daemon is RUNNING
  PID: 12345
  CPU: 10.2s
  Memory: 45.3 MB
```

### Health Check

```powershell
# 모든 endpoint 확인
Get-Content config\master_daemon_config.json | ConvertFrom-Json | 
    Select-Object -ExpandProperty healthChecks | 
    Select-Object -ExpandProperty endpoints | 
    ForEach-Object { 
        try { 
            Invoke-RestMethod $_ -TimeoutSec 2 
            Write-Host "✓ $_" -ForegroundColor Green 
        } catch { 
            Write-Host "✗ $_" -ForegroundColor Red 
        } 
    }
```

---

## 🐛 문제 해결

### Daemon이 시작되지 않음

```powershell
# 로그 확인
.\agi.ps1 logs

# 수동 실행으로 에러 확인
.\scripts\master_daemon.ps1 -Start
```

### 작업이 실행되지 않음

1. 설정 확인:

```powershell
code config\master_daemon_config.json
```

2. `"enabled": true` 인지 확인

3. 스크립트 경로가 올바른지 확인

4. 재시작:

```powershell
.\agi.ps1 restart
```

### 창이 계속 뜸

1. Window Management 확인:

```json
"windowManagement": {
  "enforceHidden": true
}
```

2. 재시작:

```powershell
.\agi.ps1 restart
```

---

## 📝 Migration Checklist

마이그레이션 후 확인 사항:

- [ ] `.\agi.ps1 status` 실행 시 RUNNING 표시
- [ ] 기존 Scheduled Tasks 모두 제거됨
- [ ] Startup 폴더 정리됨
- [ ] 로그온 후 자동 시작됨
- [ ] 창이 뜨지 않음
- [ ] 모든 서비스 정상 동작 (Task Queue, RPA Worker 등)

---

## 🎓 Best Practices

1. **설정 변경 시 항상 재시작**

   ```powershell
   .\agi.ps1 restart
   ```

2. **로그를 정기적으로 확인**

   ```powershell
   .\agi.ps1 logs
   ```

3. **중요한 작업은 `restartOnFail: true` 설정**

4. **부팅 시 자동 시작 활성화**

   ```powershell
   .\agi.ps1 install
   ```

5. **변경 전 Dry-run 실행**

   ```powershell
   .\scripts\migrate_to_master_daemon.ps1 -DryRun
   ```

---

## 🚦 Next Steps

1. **마이그레이션 실행**

   ```powershell
   .\scripts\migrate_to_master_daemon.ps1 -Force
   ```

2. **상태 확인**

   ```powershell
   .\agi.ps1 status
   ```

3. **로그 모니터링**

   ```powershell
   .\agi.ps1 logs -Follow
   ```

4. **재부팅 후 검증**
   - 자동 시작 확인
   - 창이 뜨지 않는지 확인
   - 모든 서비스 정상 동작 확인

---

**이제 하나의 명령으로 모든 것을 제어할 수 있습니다!** 🚀
