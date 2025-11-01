# Monitoring Quick Start (ASCII)

필수 구성 요소를 빠르게 띄우고, 상태/리포트를 확인하는 최소 절차입니다.

## 1) 핵심 프로세스 시작

```powershell
# Task Queue Server
cd C:\workspace\agi\LLM_Unified\ion-mentoring
.\.venv\Scripts\python.exe task_queue_server.py --port 8091

# Monitoring Daemon
cd C:\workspace\agi\fdo_agi_repo
.\.venv\Scripts\python.exe monitoring\monitoring_daemon.py --server http://127.0.0.1:8091 --interval 5

# RPA Worker (작업 처리)
cd C:\workspace\agi\fdo_agi_repo
.\.venv\Scripts\python.exe integrations\rpa_worker.py --server http://127.0.0.1:8091 --interval 0.5
```

## 2) 빠른 상태 확인 (Quick Status)

```powershell
# 선택 채널(18090) 숨김 + 성능 요약 포함
.\scripts\quick_status.ps1 -HideOptional -Perf

# 선택 채널 포함하여 표시 (Local2 등)
.\scripts\quick_status.ps1 -Perf
```

출력 예시: `[Perf] Effective 90.0% (Systems 6) | E=4 G=0 N=1 ND=1 | Top: Orchestration (50.0%)`

**참고**: Optional 채널(예: Local2, 포트 18090)은 전체 헬스 계산에서 제외되며, `-HideOptional` 플래그로 콘솔 출력에서 숨길 수 있습니다.

## 3) 성능 대시보드 생성

```powershell
# 기본 스크립트
.\scripts\generate_performance_dashboard.ps1 -WriteLatest -ExportJson -ExportCsv

# 프로필 간편 실행 (ops-daily / ops-focus)
.\scripts\dashboard_ops_daily.ps1 -Open
.\scripts\dashboard_ops_focus.ps1 -Open

# 산출물 유효성 검증
.\scripts\validate_performance_dashboard.ps1 -VerboseOutput
```

산출물 위치:

- Markdown: `outputs\performance_dashboard_latest.md`
- JSON: `outputs\performance_metrics_latest.json`
- CSV: `outputs\performance_metrics_latest.csv`

## 4) 모니터링 리포트 생성 (성능 스냅샷 포함)

```powershell
.\scripts\generate_monitoring_report.ps1 -Hours 24
```

생성 후 확인:

- 리포트(MD): `outputs\monitoring_report_latest.md` (섹션: "Performance Snapshot")
- 메트릭(JSON): `outputs\monitoring_metrics_latest.json`
- 대시보드(HTML): `outputs\monitoring_dashboard_latest.html`

**Phase 5.5: 자율 오케스트레이션 대시보드**

```powershell
# 모니터링 + 오케스트레이션 통합 대시보드 생성
python .\scripts\generate_autonomous_dashboard.py --open

# 또는 VS Code Task 실행
# "Monitoring: Generate Autonomous Dashboard (with Orchestration)"
```

산출물:

- `outputs\autonomous_dashboard_latest.html` - 채널 건강도, 라우팅 추천, 복구 상태 포함

오케스트레이션 브리지는 모니터링 메트릭을 읽어서:

- 채널별 건강도 (EXCELLENT/GOOD/DEGRADED/POOR/OFFLINE)
- 라우팅 추천 (Primary/Fallback)
- 자동 복구 트리거 (DEGRADED 채널 감지 시)

를 제공합니다.

## 5) Realtime Pipeline (자동화된 시뮬레이션 + 요약)

### 빠른 시작

VS Code에서 워크스페이스를 열면 **"Auto: Bring-up on VS Code Open (safe)"** 작업이 자동 실행되어:

- Task Queue Server (8091) 확인/시작
- RPA Worker 확인/시작
- Lumen Health Probe 실행
- Monitoring Report (24h) 생성
- Realtime Pipeline 빌드 → 요약 → 자동 열기

수동 실행:

```powershell
# 전체 파이프라인 (24h 창, 60자 스파크라인, 요약 자동 열기)
# Tasks: "Realtime: Build → Summarize → Open (24h)"

# 또는 개별 실행
.\scripts\build_realtime_pipeline.ps1 -WindowHours 24
.\scripts\summarize_realtime_pipeline.ps1 -Lookback 24 -SparkLen 60 -Open
```

### 고급 옵션

```powershell
# TrendMode: delta (기본), ma-slope (이동평균 기울기), reg-slope (선형회귀)
# SmoothWindow: 3 (기본, 추세 계산 전 smoothing)
# AsciiSet: basic (기본), dense (더 세밀한 문자 세트)
# AutoScale: 이상치 영향 감소 (p5-p95 클리핑)
# OutJson: 기계 판독 가능한 JSON 요약 출력

.\scripts\summarize_realtime_pipeline.ps1 `
  -Lookback 24 `
  -SparkLen 60 `
  -TrendMode "reg-slope" `
  -SmoothWindow 5 `
  -AsciiSet "dense" `
  -AutoScale `
  -OutJson "outputs\realtime_pipeline_summary_latest.json" `
  -Open
```

### 산출물

- MD 요약: `outputs\realtime_pipeline_summary_latest.md`
- JSON 요약: `outputs\realtime_pipeline_summary_latest.json` (옵션)
- 원본 시뮬레이션: `outputs\realtime_pipeline_status.json`

### 복원력

- 원본 JSON이 없거나 손상된 경우, 마지막으로 성공한 타임스탬프 파일로 자동 폴백
- 요약 MD/JSON에 소스 파일명과 타임스탬프 명시

### VS Code Tasks

- **Realtime: Build Pipeline (24h, no open)** - 시뮬레이션만 실행
- **Realtime: Summarize (24h|spark60) + Open** - 요약만 생성 (MD + JSON)
- **Realtime: Build → Summarize → Open (24h)** - 전체 체인 (권장)
- **Realtime: Open Latest (JSON)** - 원본 시뮬레이션 JSON 열기
- **Realtime: Open Latest Summary (JSON)** - 기계 판독 JSON 요약 열기

## 6) VS Code Tasks (원클릭)

- Performance: Dashboard (ops-daily)
- Performance: Dashboard (ops-focus)
- Performance: Validate Latest Outputs
- Performance: Generate Dashboard (Update latest)
- Performance: Open Latest Dashboard (MD)
- Monitoring: Quick Status (-Perf)
- Monitoring: Generate Report (24h)
- Monitoring: Open Latest Report (MD)
- Monitoring: Open Dashboard (HTML)

Command Palette → "Run Task"에서 실행 가능합니다.

## 참고

- 성능 밴드 기준(기본): `ExcellentAt=90`, `GoodAt=70` (프로필/CLI로 재정의 가능)
- OnlyBands 필터를 사용할 경우 Digest에 "Bands considered"가 표시됩니다.
- 실패 사유 집계는 오류 메시지가 있을 때만 JSON(`TopFailureReasons`)과 MD에 반영됩니다.

## Troubleshooting (요약)

```powershell
# 헬스 체크
curl http://127.0.0.1:8091/api/health
curl http://127.0.0.1:8000/api/health

# 빠른 상태 (성능 포함)
.\scripts\quick_status.ps1 -HideOptional -Perf

# 산출물 위치 확인
dir .\outputs\
```

- Task Queue/웹 대시보드가 응답하지 않으면 포트 바인딩/프로세스 실행 여부를 먼저 확인하세요.
- 성능 대시보드가 비어 있으면 최근 7일 내 테스트 데이터가 없을 수 있습니다. 대시보드 스크립트에 `-AllowEmpty`를 사용하거나 테스트를 먼저 실행하세요.
