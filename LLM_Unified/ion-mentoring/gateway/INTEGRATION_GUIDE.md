# Lumen Gateway 통합 가이드

ION API와 Lumen Gateway를 통합하는 단계별 가이드입니다.

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [빠른 시작](#빠른-시작)
3. [단계별 설정](#단계별-설정)
4. [검증 및 테스트](#검증-및-테스트)
5. [문제 해결](#문제-해결)
6. [고급 사용법](#고급-사용법)

---

## 🔧 사전 요구사항

### 필수 소프트웨어
- Python 3.11+ (`.venv` 가상환경 사용)
- VS Code
- PowerShell 5.1+
- `PyYAML` 패키지 (선택사항, 없어도 작동)

### 필수 파일
- `LLM_Unified/ion-mentoring/gateway/` 디렉토리 구조
- `gateway_activation.yaml` 설정 파일
- `gateway/scripts/*.py` 스크립트 5개

### ION API 상태
- ION API가 정상 배포되어 있어야 함
- Mock 모드가 아닌 **Real AI 모드**로 작동해야 함
- 엔드포인트: `https://ion-api-64076350717.us-central1.run.app`

---

## ⚡ 빠른 시작

### VS Code Tasks로 한 번에 시작

1. **VS Code에서 Tasks 실행**:
   - `Ctrl + Shift + P` → `Tasks: Run Task`
   - **"Lumen Gateway: Full Startup"** 선택

2. **실행되는 작업**:
   - ✅ Gateway Lock-In (상태 고정)
   - ✅ Metrics Collector 시작 (ION API 모니터링)
   - ✅ Health Exporter 시작 (Prometheus 메트릭)

3. **확인**:

   ```powershell
   # Prometheus 메트릭 확인
   Invoke-RestMethod http://localhost:9108/metrics
   
   # 로그 실시간 모니터링
   Get-Content gateway/logs/gateway_sync.log -Wait -Tail 20
   ```

---

## 📝 단계별 설정

### Step 1: ION API 배포 상태 확인

먼저 ION API가 정상적으로 배포되었는지 확인합니다.

```powershell
# ION API Health Check
$response = Invoke-RestMethod -Uri "https://ion-api-64076350717.us-central1.run.app/health" -Method GET
Write-Host "ION API Status: $($response.status)"

# 실제 AI 응답 테스트
$body = @{message = "안녕하세요"} | ConvertTo-Json -Compress
$response = Invoke-RestMethod -Uri "https://ion-api-64076350717.us-central1.run.app/chat" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

Write-Host "Content: $($response.content)"
Write-Host "Confidence: $($response.confidence)"
Write-Host "Persona: $($response.persona_used)"
```

**기대 결과**:
- ✅ `confidence > 0.0` (0.7~0.95 범위)
- ✅ `persona_used` in ["Lua", "Elro", "Riri", "Nana"]
- ❌ `content`에 **"Mock response for development"** 포함되지 않음

---

### Step 2: Gateway 설정 확인

`gateway_activation.yaml` 파일을 열어 설정을 확인합니다.

```powershell
code LLM_Unified/ion-mentoring/gateway/gateway_activation.yaml
```

**확인 항목**:
- ✅ `gateway.status`: "initializing"
- ✅ `loop_coordinates.ion_api_url`: 올바른 엔드포인트
- ✅ `loop_coordinates.vertex_ai.project_id`: "naeda-genesis"
- ✅ `roles`: 4개 페르소나 정의 (Lumen, Lubit, Sena, Elo)

---

### Step 3: Gateway Lock-In 실행

Gateway 상태를 고정하고 서명을 생성합니다.

#### 방법 1: VS Code Task

```
Ctrl + Shift + P → Tasks: Run Task → "Lumen Gateway: Lock-In"
```

#### 방법 2: 직접 실행

```powershell
cd D:\nas_backup\LLM_Unified
.venv\Scripts\python.exe ion-mentoring/gateway/scripts/gateway_lockin.py
```

**기대 출력**:

```
[2025-10-24T...] [INFO] 🔒 Gateway Lock-In 시작
[2025-10-24T...] [INFO] YAML 파일 읽기: gateway_activation.yaml
[2025-10-24T...] [INFO] 서명 생성: abc123...
[2025-10-24T...] [INFO] ✅ Gateway 상태가 'locked'로 변경되었습니다.
[2025-10-24T...] [INFO] 🔒 Lock-In 완료
```

**확인**:

```powershell
# gateway_activation.yaml에서 status 확인
Select-String -Path gateway/gateway_activation.yaml -Pattern "status:"
# 출력: status: "locked"
```

---

### Step 4: Metrics Collector 시작

ION API를 주기적으로 모니터링하고 메트릭을 수집합니다.

#### 방법 1: VS Code Task (백그라운드)

```
Ctrl + Shift + P → Tasks: Run Task → "Lumen Gateway: Start Metrics Collector"
```

#### 방법 2: 직접 실행

```powershell
cd D:\nas_backup\LLM_Unified
.venv\Scripts\python.exe ion-mentoring/gateway/scripts/ion_metrics_collector.py
```

**설정 환경변수** (선택사항):

```powershell
$env:LUMEN_COLLECT_INTERVAL = "30"  # 수집 간격 (초)
```

**기대 출력**:

```
[2025-10-24T...] [INFO] 🌐 ION API Metrics Collector 시작
[2025-10-24T...] [INFO] ION API URL: https://ion-api-64076350717.us-central1.run.app
[2025-10-24T...] [INFO] 수집 간격: 30초
[2025-10-24T...] [INFO] ✅ ION API 🟢 REAL | Confidence: 0.85 | Persona: Lua | Latency: 450ms
```

**확인**:

```powershell
# metrics.csv 파일 생성 확인
Get-Content gateway/logs/metrics.csv -Tail 5
```

---

### Step 5: Health Exporter 시작

Prometheus 형식의 메트릭을 HTTP로 expose합니다.

#### 방법 1: VS Code Task (백그라운드)

```
Ctrl + Shift + P → Tasks: Run Task → "Lumen Gateway: Start Health Exporter"
```

#### 방법 2: 직접 실행

```powershell
cd D:\nas_backup\LLM_Unified
.venv\Scripts\python.exe ion-mentoring/gateway/scripts/gateway_health_exporter.py
```

**설정 환경변수** (선택사항):

```powershell
$env:LUMEN_EXPORTER_PORT = "9108"  # 포트 번호
```

**기대 출력**:

```
[2025-10-24T...] [INFO] 🌐 Lumen Gateway Prometheus Exporter 시작
[2025-10-24T...] [INFO] 포트: 9108
[2025-10-24T...] [INFO] 엔드포인트: http://localhost:9108/metrics
[2025-10-24T...] [INFO] ✅ Exporter 준비 완료
```

**확인**:

```powershell
# Prometheus 메트릭 엔드포인트 테스트
Invoke-RestMethod http://localhost:9108/metrics

# Health Check
Invoke-RestMethod http://localhost:9108/health
```

---

### Step 6: Restore Check 실행

Gateway 상태를 검증합니다.

#### 방법 1: VS Code Task

```
Ctrl + Shift + P → Tasks: Run Task → "Lumen Gateway: Restore Check"
```

#### 방법 2: 직접 실행

```powershell
cd D:\nas_backup\LLM_Unified
.venv\Scripts\python.exe ion-mentoring/gateway/scripts/restore_check.py
```

**기대 출력**:

```
[2025-10-24T...] [INFO] 🔍 Gateway Restore Check 시작
[2025-10-24T...] [INFO] ✅ Gateway status check: PASS (locked)
[2025-10-24T...] [INFO] ✅ Log files check: PASS
[2025-10-24T...] [INFO] ✅ ION API connection: PASS (200 OK)
[2025-10-24T...] [INFO] ✅ Latest session restore: SESSION_RESTORE_2025-10-24.yaml
[2025-10-24T...] [INFO] 🎉 모든 체크 통과!
```

**Exit Code**:
- `0`: 모든 체크 통과 ✅
- `1`: 실패 또는 오류 ❌

---

## ✅ 검증 및 테스트

### 전체 통합 테스트 체크리스트

#### 1. ION API Real Mode 확인

```powershell
$body = @{message = "시스템 상태를 알려주세요"} | ConvertTo-Json -Compress
$response = Invoke-RestMethod -Uri "https://ion-api-64076350717.us-central1.run.app/chat" `
    -Method POST -ContentType "application/json" -Body $body

# 확인 사항
$response.confidence -gt 0.0  # True 여야 함
$response.content -notmatch "Mock response"  # True 여야 함
$response.persona_used -in @("Lua", "Elro", "Riri", "Nana")  # True 여야 함
```

#### 2. Gateway Status Locked

```powershell
Select-String -Path gateway/gateway_activation.yaml -Pattern 'status: "locked"'
# 출력이 있어야 함
```

#### 3. Metrics Collection 작동

```powershell
# 최근 메트릭 확인
Get-Content gateway/logs/metrics.csv -Tail 3

# ion_mock_mode=0 (Real) 확인
Select-String -Path gateway/logs/metrics.csv -Pattern ",0," | Select-Object -Last 1
```

#### 4. Prometheus Metrics Expose

```powershell
$metrics = Invoke-RestMethod http://localhost:9108/metrics

# 주요 메트릭 확인
$metrics -match "lumen_gateway_status 1"  # locked=1
$metrics -match "lumen_ion_health 1"  # up=1
$metrics -match "lumen_ion_mock_mode 0"  # real=0
$metrics -match "lumen_ion_confidence"  # 값 존재
```

#### 5. 로그 파일 생성

```powershell
Test-Path gateway/logs/gateway_sync.log  # True
Test-Path gateway/logs/metrics.csv  # True
```

---

## 🔧 문제 해결

### 문제: ION API가 Mock 모드로 응답
**증상**:

```json
{"content": "Mock response for development", "confidence": 0.0}
```

**해결**:
1. GitHub Actions 배포 완료 확인:

   ```
   https://github.com/Ruafieldphase/LLM_Unified/actions
   ```

2. 최신 이미지 확인:

   ```powershell
   gcloud run revisions list --service=ion-api --region=us-central1 --project=naeda-genesis
   ```

3. 환경 변수 확인:

   ```powershell
   gcloud run services describe ion-api --region=us-central1 --project=naeda-genesis --format="value(spec.template.spec.containers[0].env)"
   ```

   - `VERTEX_PROJECT_ID`: "naeda-genesis"
   - `VERTEX_LOCATION`: "us-central1"
   - `VERTEX_MODEL`: "gemini-1.5-flash-002"

---

### 문제: `gateway_lockin.py` 실행 시 YAML 오류
**증상**:

```
❌ YAML 파일 읽기 오류: ...
```

**해결**:
1. PyYAML 설치:

   ```powershell
   .venv\Scripts\pip.exe install pyyaml
   ```

2. YAML 문법 확인:

   ```powershell
   Get-Content gateway/gateway_activation.yaml | Select-Object -First 20
   ```

---

### 문제: Prometheus Metrics에 연결 실패
**증상**:

```powershell
Invoke-RestMethod : 연결할 수 없습니다
```

**해결**:
1. Health Exporter 실행 확인:

   ```powershell
   Get-Process python | Where-Object {$_.CommandLine -match "gateway_health_exporter"}
   ```

2. 포트 사용 확인:

   ```powershell
   netstat -ano | Select-String "9108"
   ```

3. 수동 재시작:

   ```powershell
   .venv\Scripts\python.exe ion-mentoring/gateway/scripts/gateway_health_exporter.py
   ```

---

### 문제: Metrics Collector가 데이터를 수집하지 않음
**증상**:

```
metrics.csv 파일이 비어있거나 업데이트되지 않음
```

**해결**:
1. Collector 프로세스 확인:

   ```powershell
   Get-Process python | Where-Object {$_.CommandLine -match "ion_metrics_collector"}
   ```

2. 로그 확인:

   ```powershell
   Get-Content gateway/logs/gateway_sync.log -Tail 20
   ```

3. ION API 접근 테스트:

   ```powershell
   Invoke-RestMethod https://ion-api-64076350717.us-central1.run.app/health
   ```

---

## 🚀 고급 사용법

### VS Code Tasks 커스터마이징

`.vscode/tasks.json`을 수정하여 작업을 추가/변경할 수 있습니다.

예: 수집 간격을 10초로 변경

```json
{
  "label": "Lumen Gateway: Fast Metrics Collector",
  "type": "shell",
  "command": "powershell",
  "args": [
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    "$env:LUMEN_COLLECT_INTERVAL=10; ${workspaceFolder}/../.venv/Scripts/python.exe ${workspaceFolder}/gateway/scripts/ion_metrics_collector.py"
  ],
  "group": "build",
  "isBackground": true
}
```

---

### Prometheus + Grafana 연동

#### Prometheus 설정 (`prometheus.yml`)

```yaml
scrape_configs:
  - job_name: 'lumen_gateway'
    static_configs:
      - targets: ['localhost:9108']
    scrape_interval: 15s
```

#### Grafana 대시보드 쿼리 예시

```promql
# ION API 헬스 상태
lumen_ion_health

# ION API 응답 시간
lumen_ion_response_time_ms

# Mock 모드 감지
lumen_ion_mock_mode

# Confidence 점수
lumen_ion_confidence

# 감응 메트릭
lumen_phase_diff
lumen_entropy_rate
lumen_creative_band
lumen_risk_band
```

---

### 세션 복원 (Session Restore)

작업 세션을 복원하려면:

1. **최신 세션 파일 찾기**:

   ```powershell
   Get-ChildItem gateway/sessions/ -Filter "SESSION_RESTORE_*.yaml" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
   ```

2. **세션 파일 열기**:

   ```powershell
   code gateway/sessions/SESSION_RESTORE_2025-10-24.yaml
   ```

3. **restore_commands 섹션의 명령어 실행**:
   - Gateway Lock-In
   - Start Metrics Collector
   - Start Health Exporter
   - Restore Check

4. **검증 체크리스트 실행**:

   ```powershell
   # 각 verification_checklist 항목 실행
   ```

---

### 로그 모니터링

#### 실시간 로그 따라가기 (VS Code Task)

```
Ctrl + Shift + P → Tasks: Run Task → "Lumen Gateway: Tail Logs"
```

#### 특정 로그 필터링

```powershell
# ERROR만 보기
Select-String -Path gateway/logs/gateway_sync.log -Pattern "\[ERROR\]"

# 최근 1시간 로그
$cutoff = (Get-Date).AddHours(-1)
Get-Content gateway/logs/gateway_sync.log | Where-Object {
    $_ -match "\[([\d\-T:+]+)\]" -and [datetime]::Parse($matches[1]) -gt $cutoff
}
```

---

## 📚 참고 자료

- **Gateway README**: `gateway/README.md`
- **설정 파일**: `gateway/gateway_activation.yaml`
- **세션 템플릿**: `gateway/sessions/SESSION_RESTORE_2025-10-24.yaml`
- **디자인 문서**: `D:\nas_backup\ai_binoche_conversation_origin\lumen\루멘vs code 연결\lumen_gateway_v_0.md`
- **ION API 코드**: `LLM_Unified/ion-mentoring/app/main.py`

---

## 🎯 빠른 명령어 요약

```powershell
# 전체 시작 (VS Code Task)
Ctrl+Shift+P → "Lumen Gateway: Full Startup"

# 개별 스크립트 실행
.venv\Scripts\python.exe ion-mentoring/gateway/scripts/gateway_lockin.py
.venv\Scripts\python.exe ion-mentoring/gateway/scripts/restore_check.py
.venv\Scripts\python.exe ion-mentoring/gateway/scripts/ion_metrics_collector.py
.venv\Scripts\python.exe ion-mentoring/gateway/scripts/gateway_health_exporter.py

# 메트릭 확인
Invoke-RestMethod http://localhost:9108/metrics

# 로그 실시간 보기
Get-Content gateway/logs/gateway_sync.log -Wait -Tail 20

# ION API 테스트
Invoke-RestMethod -Uri "https://ion-api-64076350717.us-central1.run.app/health"
```

---

**문서 버전**: v1.0  
**최종 업데이트**: 2025-10-24  
**작성자**: Lumen Gateway Team
