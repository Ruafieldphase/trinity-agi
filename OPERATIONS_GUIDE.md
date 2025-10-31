# 🚀 Gitko AGI 운영 가이드

**최종 업데이트**: 2025-10-31  
**버전**: Phase 5 완료

---

## 📋 목차

1. [시스템 시작](#시스템-시작)
2. [상태 확인](#상태-확인)
3. [일상 운영](#일상-운영)
4. [트러블슈팅](#트러블슈팅)
5. [백업 및 복구](#백업-및-복구)

---

## 🚀 시스템 시작

### 전체 시스템 시작 (원클릭)

```powershell
# 모든 서비스 자동 시작
.\scripts\start_phase5_system.ps1

# 확인
# Task Queue Server: http://127.0.0.1:8091
# Web Dashboard: http://127.0.0.1:8000
```

### 개별 서비스 시작

```powershell
# 1. Task Queue Server (먼저 실행)
cd LLM_Unified\ion-mentoring
.\.venv\Scripts\python.exe task_queue_server.py --port 8091

# 2. Web Dashboard
cd fdo_agi_repo
python monitoring\web_server.py

# 3. RPA Worker (옵션)
cd fdo_agi_repo
.venv\Scripts\python.exe integrations\rpa_worker.py --server http://127.0.0.1:8091
```

---

## 📊 상태 확인

### 빠른 헬스 체크

```powershell
# Task Queue Server
curl http://127.0.0.1:8091/api/health

# Web Dashboard  
curl http://127.0.0.1:8000/api/health

# 통합 상태
.\scripts\quick_status.ps1
```

### 포트 사용 확인

```powershell
# 포트 8091 확인
netstat -ano | findstr ":8091"

# 포트 8000 확인
netstat -ano | findstr ":8000"
```

### PowerShell Job 확인

```powershell
# 실행 중인 Job 확인
Get-Job | Format-Table Id, Name, State

# Job 로그 확인
Receive-Job -Id 1 -Keep

# Job 종료
Stop-Job -Id 1
Remove-Job -Id 1
```

---

## 🔧 일상 운영

### YouTube 학습 실행

```powershell
# 수동 실행
.\scripts\run_youtube_learner.ps1 -Url "https://youtube.com/watch?v=..." -MaxFrames 3

# 결과 확인
.\scripts\youtube_learner_index.ps1 -Open
```

### RPA 작업 실행

```powershell
# 스모크 테스트
.\scripts\run_smoke_e2e_ocr.ps1

# 결과 확인
Invoke-RestMethod -Uri 'http://127.0.0.1:8091/api/results' | ConvertTo-Json
```

### 모니터링 리포트 생성

```powershell
# 24시간 리포트
.\scripts\generate_monitoring_report.ps1 -Hours 24

# 7일 리포트
.\scripts\generate_monitoring_report.ps1 -Hours 168

# 결과 열기
code .\outputs\monitoring_report_latest.md
```

---

## 🔍 트러블슈팅

### 서버가 시작되지 않는 경우

**증상**: `curl` 명령이 실패하거나 연결 거부

**해결 방법**:

```powershell
# 1. 포트가 이미 사용 중인지 확인
netstat -ano | findstr ":8091"
netstat -ano | findstr ":8000"

# 2. 프로세스 종료 (PID는 위 명령 결과에서 확인)
taskkill /PID <PID> /F

# 3. 재시작
.\scripts\start_phase5_system.ps1
```

### Web Dashboard가 데이터를 표시하지 않는 경우

**증상**: 차트나 메트릭이 "--" 또는 비어있음

**해결 방법**:

```powershell
# 1. 메트릭 파일 존재 확인
Test-Path .\fdo_agi_repo\outputs\monitoring_metrics.jsonl

# 2. 파일이 없으면 생성
New-Item -ItemType File -Path .\fdo_agi_repo\outputs\monitoring_metrics.jsonl -Force

# 3. 테스트 데이터 생성
.\scripts\test_monitoring_success_path.ps1 -TaskCount 5 -Duration 0.3
```

### Job이 응답하지 않는 경우

**증상**: `Get-Job`에서 Running 상태지만 작동하지 않음

**해결 방법**:

```powershell
# 1. Job 강제 종료
Get-Job | Stop-Job
Get-Job | Remove-Job

# 2. 프로세스 직접 종료
Get-Process python* | Stop-Process -Force

# 3. 재시작
.\scripts\start_phase5_system.ps1
```

### Python 의존성 에러

**증상**: `ModuleNotFoundError: No module named 'fastapi'`

**해결 방법**:

```powershell
# 1. 가상환경 활성화 확인
cd fdo_agi_repo
.\.venv\Scripts\Activate.ps1

# 2. 의존성 재설치
pip install -r requirements_rpa.txt

# 3. FastAPI 직접 설치
pip install fastapi uvicorn
```

---

## 💾 백업 및 복구

### 중요 파일 백업

```powershell
# 백업 디렉토리 생성
$backupDir = ".\backups\$(Get-Date -Format 'yyyy-MM-dd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force

# 1. 메모리 파일
Copy-Item .\fdo_agi_repo\memory\* -Destination $backupDir\memory -Recurse

# 2. 출력 파일
Copy-Item .\fdo_agi_repo\outputs\* -Destination $backupDir\outputs -Recurse

# 3. 설정 파일
Copy-Item .\configs\* -Destination $backupDir\configs -Recurse
```

### 복구

```powershell
# 백업에서 복구
$backupDir = ".\backups\2025-10-31_205500"  # 백업 디렉토리

Copy-Item $backupDir\memory\* -Destination .\fdo_agi_repo\memory\ -Force -Recurse
Copy-Item $backupDir\outputs\* -Destination .\fdo_agi_repo\outputs\ -Force -Recurse
Copy-Item $backupDir\configs\* -Destination .\configs\ -Force -Recurse
```

---

## 📊 모니터링 메트릭

### 주요 지표

| 메트릭 | 정상 범위 | 경고 임계값 |
|--------|----------|-----------|
| 성공률 | > 90% | < 80% |
| 평균 응답 시간 | < 5초 | > 10초 |
| 큐 크기 | < 10 | > 50 |
| 워커 수 | ≥ 1 | = 0 |

### 메트릭 파일 위치

```
fdo_agi_repo/outputs/
├── monitoring_metrics.jsonl       # 원시 메트릭 데이터
├── monitoring_events.jsonl        # 이벤트 로그
├── monitoring_report_latest.md    # 리포트 (Markdown)
├── monitoring_metrics_latest.json # 리포트 (JSON)
└── monitoring_dashboard_latest.html # 대시보드 (HTML)
```

---

## 🔐 보안 고려사항

### 기본 설정 (개발 환경)

현재 시스템은 **localhost에서만 접근 가능**합니다:

- Task Queue Server: `127.0.0.1:8091`
- Web Dashboard: `127.0.0.1:8000`

### 프로덕션 배포 시 추가 필요

```powershell
# 1. HTTPS 설정
# 2. 인증/인가 (JWT, OAuth)
# 3. CORS 정책 강화
# 4. Rate Limiting
# 5. 로그 암호화
```

---

## 📞 지원 및 문의

### 문서

- [Phase 5 완료 요약](PHASE_5_FINAL_SUMMARY.md)
- [Phase 5 완료 리포트](PHASE_5_COMPLETION_REPORT.md)
- [프로젝트 README](README.md)

### 빠른 참조

```powershell
# 시스템 시작
.\scripts\start_phase5_system.ps1

# 상태 확인
.\scripts\quick_status.ps1

# 리포트 생성
.\scripts\generate_monitoring_report.ps1 -Hours 24

# 브라우저 접속
Start-Process http://127.0.0.1:8000
```

---

## ✅ 체크리스트

### 매일

- [ ] Web Dashboard 접속 확인 (<http://127.0.0.1:8000>)
- [ ] 성공률 > 90% 확인
- [ ] 워커 상태 확인

### 매주

- [ ] 7일 모니터링 리포트 생성
- [ ] 메모리 파일 백업
- [ ] 오래된 로그 정리 (14일 이상)

### 매월

- [ ] 전체 시스템 백업
- [ ] 성능 메트릭 분석
- [ ] 의존성 업데이트 검토

---

**작성**: GitHub Copilot  
**최종 업데이트**: 2025-10-31  
**버전**: Phase 5 완료
