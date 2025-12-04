# 🎯 Copilot ↔ Comet 실전 활용 시나리오

**버전**: Phase 7a  
**날짜**: 2025-10-28

---

## 📊 시나리오 1: 모니터링 자동화

### 사용자 요청 (자연어)
>
> "지난 24시간 AGI 시스템 성능 요약해줘"

### Copilot 실행 순서

1. **배치 계산 요청**

   ```powershell
   .\.venv\Scripts\python.exe scripts\send_batch_calc.py
   ```

2. **결과 대기 (12초)**

   ```powershell
   Start-Sleep -Seconds 12
   ```

3. **결과 조회 및 보고서 생성**

   ```powershell
   .\.venv\Scripts\python.exe scripts\fetch_and_format_result.py <task_id> --format markdown
   ```

### 예상 출력

```markdown
## 작업 결과

| 항목 | 값 |
|------|-----|
| success_rate | 84.7 |
| error_rate | 15.3 |
| avg_response | 1.2 |
| cache_hit | 92.3 |
```

---

## 🔄 시나리오 2: 주기적 헬스체크

### 사용자 요청
>
> "시스템 상태 확인해줘"

### 실행

```powershell
# Ping 테스트
.\.venv\Scripts\python.exe scripts\send_ping.py

# 결과 즉시 확인 (2초 대기)
Start-Sleep -Seconds 2
.\.venv\Scripts\python.exe scripts\fetch_and_format_result.py <task_id> --format table
```

### 예상 출력

```
============================================================
  message             : pong
  worker              : comet-extension
  timestamp           : 2025-10-28T13:45:00.123Z
  extension_version   : 2.0.0
============================================================
```

---

## 📈 시나리오 3: 로그 분석 자동화

### 사용자 요청
>
> "최근 에러 로그를 대문자로 변환해서 저장해줘"

### 실행 (핸들러 구현 후)

```powershell
# 1. 텍스트 변환 요청
.\.venv\Scripts\python.exe scripts\send_text_transform.py "error: connection timeout"

# 2. 결과 조회
Start-Sleep -Seconds 8
.\.venv\Scripts\python.exe scripts\fetch_and_format_result.py <task_id> --format json > outputs\processed_log.json
```

---

## 🚀 시나리오 4: 완전 자동화 워크플로우

### PowerShell 자동화 스크립트

**`scripts/auto_monitoring_workflow.ps1`**:

```powershell
# 자동 모니터링 워크플로우
# 사용법: .\scripts\auto_monitoring_workflow.ps1

Write-Host "🤖 Copilot ↔ Comet 자동 협업 시작" -ForegroundColor Green

# 1. Ping 헬스체크
Write-Host "`n[1/3] 헬스체크 중..." -ForegroundColor Cyan
$pingTaskId = & .\.venv\Scripts\python.exe scripts\send_ping.py | Select-String "Task ID: (\S+)" | ForEach-Object { $_.Matches.Groups[1].Value }

Start-Sleep -Seconds 3

$pingResult = & .\.venv\Scripts\python.exe scripts\fetch_and_format_result.py $pingTaskId --format json | ConvertFrom-Json

if ($pingResult.status -eq "success") {
    Write-Host "✅ Comet 정상 작동 중" -ForegroundColor Green
} else {
    Write-Host "❌ Comet 응답 없음" -ForegroundColor Red
    exit 1
}

# 2. 배치 계산 실행
Write-Host "`n[2/3] 통계 계산 중..." -ForegroundColor Cyan
$calcTaskId = & .\.venv\Scripts\python.exe scripts\send_batch_calc.py | Select-String "Task ID: (\S+)" | ForEach-Object { $_.Matches.Groups[1].Value }

Start-Sleep -Seconds 12

# 3. 결과 보고서 생성
Write-Host "`n[3/3] 보고서 생성 중..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe scripts\fetch_and_format_result.py $calcTaskId --format markdown > outputs\monitoring_auto_report.md

Write-Host "`n✅ 자동 워크플로우 완료!" -ForegroundColor Green
Write-Host "📊 보고서: outputs\monitoring_auto_report.md" -ForegroundColor Yellow
```

---

## 🎯 VS Code Task 등록

**`.vscode/tasks.json`** 추가:

```json
{
  "label": "🤖 Comet: Auto Monitoring",
  "type": "shell",
  "command": "powershell",
  "args": [
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "${workspaceFolder}/fdo_agi_repo/scripts/auto_monitoring_workflow.ps1"
  ],
  "group": "test",
  "presentation": {
    "reveal": "always",
    "panel": "new"
  }
}
```

---

## 📊 실전 활용 체크리스트

### ✅ 즉시 사용 가능

- [x] Ping 헬스체크
- [x] 단순 계산 (곱셈)
- [x] 결과 조회 및 포맷팅

### 🔄 핸들러 구현 필요 (Comet Extension)

- [ ] 텍스트 변환 (`data_transform`)
- [ ] 배치 계산 (`batch_calculation`)
- [ ] 모니터링 보고서 (`monitoring_report`)

### 🚀 고급 기능 (향후)

- [ ] 파일 처리 (CSV → JSON)
- [ ] API 호출 (외부 서비스 연동)
- [ ] 우선순위 큐
- [ ] 작업 취소 기능

---

## 💡 실전 팁

### 1. 빠른 디버깅

```powershell
# 작업 파일 직접 확인
Get-Content outputs\task_queue\tasks\<task_id>.json

# 결과 파일 직접 확인
Get-Content outputs\task_queue\results\<task_id>.json
```

### 2. 대기 중인 작업 확인

```powershell
ls outputs\task_queue\tasks\*.json | Measure-Object | Select-Object Count
```

### 3. 최근 결과 확인

```powershell
ls outputs\task_queue\results\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

---

## 🎊 다음 단계

1. **Comet Extension에 핸들러 구현**
   - `COMET_핸들러_확장_가이드.md` 참고

2. **자동화 워크플로우 테스트**
   - `auto_monitoring_workflow.ps1` 실행

3. **실전 시나리오 확장**
   - 새로운 작업 타입 추가
   - 복잡한 데이터 처리 구현

**협업 시스템 실전 배포 준비 완료!** 🚀
