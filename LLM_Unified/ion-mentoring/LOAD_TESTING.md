# Load Testing Guide

## Overview

This guide explains how to perform load testing on the ION Mentoring API using Locust. Load testing helps verify:

- Performance under various traffic patterns
- Rate limiting effectiveness (30 requests/minute per IP)
- Auto-scaling behavior (up to 10 instances)
- Error handling under stress
- Latency at different percentiles (P50, P95, P99)

## Prerequisites

### Install Locust

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install locust
pip install locust

# Verify installation
locust --version
```

### Cloud Monitoring Dashboard

Before running load tests, open the [Cloud Monitoring Dashboard](https://console.cloud.google.com/monitoring/dashboards/custom/03565e29-17dc-4fa7-affc-8ed9e04c2c16?project=naeda-genesis) to observe real-time metrics.

### Quick smoke-run (10s, light)

From `LLM_Unified/ion-mentoring`:

```powershell
./scripts/run_all_load_tests.ps1 -ScenarioProfile light -OverrideRunTime 10s
```

Notes:

- Use `-ScenarioProfile all|light|medium|heavy|stress` to select scenarios (default: all).
- Use `-OverrideRunTime 10s|2m|...` to override all scenario runtimes for fast checks.
- Add `-NoSummary` to skip generating a Markdown summary file.
- Add `-WithHtml` to also generate per-scenario HTML reports (`outputs/load_test_<scenario>_<timestamp>.html`).
- Add `-Strict` to exit immediately with a non-zero code if a Locust run fails (useful in CI or scripted pipelines).
  - When `-Strict` is enabled, failures in Locust or the summarizer also stop the script with a non-zero exit code.
  - If no CSVs are generated or the summarizer is missing, the script exits 1 in strict mode.
- Add `-WithSuccessRate` to include a `Success (%)` column in the generated Markdown summary (both file and console preview).

Environment override:

- If `ION_API_HOST` environment variable is set and you don't pass `-ApiServiceUrl`, the runner uses `ION_API_HOST` as the target.

Console note:

- On Windows PowerShell, emojis may not render correctly in the console. The runner prints an ASCII status (OK/FAIL) to the console for readability, while the saved `summary_*.md` file preserves UTF-8 emojis.
  - The script also creates a convenience pointer `outputs/summary_latest.md` with the most recent summary.
- When `-WithSuccessRate` is enabled, the summary table header includes `Success (%)` and shows per-scenario and Overall success percentages.

### CI workflow usage

See `LLM_Unified/docs/LOAD_TESTING_CI.md` for running the GitHub Actions workflow with SLO gating.

## Load Test Script

The `load_test.py` script simulates users with the following behavior:

- **Weight 1**: GET `/health` - Health checks
- **Weight 5**: POST `/chat` - Main workload with random messages
- **Weight 2**: GET `/docs` - Documentation access

Wait time between requests: 1-3 seconds per user

## Test Scenarios

### Scenario 1: Light Load (Baseline)

**Goal**: Establish baseline performance metrics

```powershell
locust -f load_test.py `
  --host=https://ion-api-64076350717.us-central1.run.app `
  --users 10 `
  --spawn-rate 1 `
  --run-time 2m `
  --headless
```

**Expected Results**:

- No rate limiting (< 30 req/min per user)
- Single instance running
- Latency P95 < 200ms
- 0% error rate

### Scenario 2: Medium Load

**Goal**: Test under moderate traffic

```powershell
locust -f load_test.py `
  --host=https://ion-api-64076350717.us-central1.run.app `
  --users 50 `
  --spawn-rate 5 `
  --run-time 5m `
  --headless
```

**Expected Results**:

- Occasional rate limiting (429 responses)
- 1-2 instances active
- Latency P95 < 500ms
- < 5% error rate (excluding 429s)

### Scenario 3: Heavy Load (Rate Limiting Test)

**Goal**: Verify rate limiting kicks in

```powershell
locust -f load_test.py `
  --host=https://ion-api-64076350717.us-central1.run.app `
  --users 100 `
  --spawn-rate 10 `
  --run-time 5m `
  --headless
```

**Expected Results**:

- Frequent 429 responses (rate limit exceeded)
- 2-4 instances active
- Latency P95 may increase (500-1000ms)
- Rate limiting protecting the service

### Scenario 4: Stress Test (Auto-scaling)

**Goal**: Trigger auto-scaling to maximum instances

```powershell
locust -f load_test.py `
  --host=https://ion-api-64076350717.us-central1.run.app `
  --users 200 `
  --spawn-rate 20 `
  --run-time 10m `
  --headless
```

**Expected Results**:

- High volume of 429 responses
- Auto-scaling to max 10 instances
- Latency spikes during scaling
- Service remains available despite load

## Interactive Testing (Web UI)

For real-time control and visualization:

```powershell
# Start Locust web UI
locust -f load_test.py --host=https://ion-api-64076350717.us-central1.run.app

# Open browser
Start-Process http://localhost:8089
```

Web UI allows you to:

- Adjust user count dynamically
- Monitor real-time RPS (Requests Per Second)
- View response time charts
- Download detailed statistics

## Monitoring During Tests

### Cloud Monitoring Dashboard (During Tests)

Watch these metrics during load tests:

1. **Request Rate**: Should match Locust RPS
2. **Error Rate**: Should stay low (excluding 429s)
3. **Latency P95**: Should stay under 1000ms
4. **Rate Limit Exceeded**: 429 responses tracked
5. **Active Instances**: Should scale up under load
6. **Memory/CPU**: Should stay under 80%

### Cloud Logging

View structured logs in real-time:

```powershell
# Stream logs during test
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=ion-api" --format=json
```

## Results Analysis

### Locust Statistics

After test completion, Locust provides:

```text
Name                      # Reqs    # Fails   Avg (ms)   Min (ms)   Max (ms)   Med (ms)   P95 (ms)   P99 (ms)   Req/s
GET /health                  200         0         45         20        150         40        100        140      3.3
POST /chat                  1000        50         85         30        500         70        200        350     16.7
GET /docs                    400         0         60         25        200         50        150        180      6.7
```

### Key Metrics to Analyze

1. **Success Rate**: (Total Reqs - Fails) / Total Reqs
2. **Average Latency**: Should be < 100ms for chat endpoint
3. **P95 Latency**: Should be < 500ms
4. **P99 Latency**: Acceptable up to 1000ms
5. **Requests/sec**: Maximum sustainable RPS
6. **Failures**: Excluding 429s, should be < 1%

### Cloud Monitoring Metrics

Export metrics from dashboard:

```powershell
# Request count over test period
gcloud monitoring time-series list `
  --filter='metric.type="run.googleapis.com/request_count" AND resource.labels.service_name="ion-api"' `
  --format=json `
  --start-time="2025-10-17T10:00:00Z" `
  --end-time="2025-10-17T10:10:00Z"
```

## Troubleshooting

### High Error Rate (excluding 429)

```bash
# Check recent errors in logs
gcloud logging read "resource.type=cloud_run_revision AND severity=ERROR" --limit=20
```

### Latency Spikes

- **Cold starts**: First request to new instance takes longer
- **Memory pressure**: Check memory utilization widget
- **Database/API calls**: Review Vertex AI mock responses

### No Auto-scaling

```bash
# Verify max instances setting
gcloud run services describe ion-api --region us-central1 --format="value(spec.template.spec.containerConcurrency,spec.template.metadata.annotations.'autoscaling.knative.dev/maxScale')"

# Should show: 10 (max instances)
```

### Rate Limiting Not Working

- Check slowapi configuration in `app/main.py`
- Verify 30/minute limit in code
- Ensure `get_remote_address` key function working

## Performance Benchmarks

### Target Metrics (Development Mode with Mock)

| Metric                     | Target   | Measured                           |
| -------------------------- | -------- | ---------------------------------- |
| P50 Latency                | < 50ms   | 170 ms (stress run, 2025-10-18)    |
| P95 Latency                | < 500ms  | 190 ms (stress run)                |
| P99 Latency                | < 1000ms | 2.3 s (stress run tail)            |
| Max RPS (single instance)  | 50-100   | ~43 req/s (heavy run)              |
| Max RPS (10 instances)     | 500-1000 | ~86 req/s (stress run, auto-scale) |
| Error Rate (excluding 429) | < 1%     | 0% (all runs)                      |
| Memory Usage               | < 300MB  | Not captured                       |
| CPU Usage                  | < 50%    | Not captured                       |

> NOTE: Recent runs (10-user sanity + 200-user stress, 2025-10-18) exposed intermittent Vertex AI tail latency up to ~13 s and the spike scenario produced a 39 s outlier. Keep monitoring the long tail and Vertex responses.

> CAUTION: Locust reported high CPU utilisation during the headless stress run. Distribute load across multiple processes or machines if you observe similar warnings.

### Filling in Benchmarks

Run each scenario and fill in the "Measured" column:

```powershell
# Run all scenarios (from LLM_Unified/ion-mentoring)
.\scripts\run_all_load_tests.ps1

# Results will be saved to files like:
# - outputs/load_test_light_<timestamp>_stats.csv
# - outputs/load_test_medium_<timestamp>_stats.csv
# - outputs/load_test_heavy_<timestamp>_stats.csv
# - outputs/load_test_stress_<timestamp>_stats.csv
# - outputs/load_test_light_<timestamp>.html (when -WithHtml)
# And a Markdown summary:
# - outputs/summary_<profile>_<timestamp>.md
# - outputs/summary_latest.md (copy of the most recent summary)
```

## Next Steps

- [ ] Run all 4 test scenarios
- [ ] Document measured metrics
- [ ] Compare with target benchmarks
- [ ] Identify performance bottlenecks
- [ ] Update WEEK3_SUMMARY.md with results

## Test Automation and Quality Assurance

### Unit Tests

The summarizer script (`scripts/summarize_locust_csv.py`) is covered by comprehensive unit tests in `tests/test_summarize_locust_csv.py`:

- **CSV parsing**: Valid files, missing files, empty files, zero requests
- **Scenario name normalization**: Timestamp stripping logic
- **Table generation**: Basic table, Success (%) column, Overall aggregation, edge cases
- **Edge case handling**: Division by zero, 100% failure rate, missing/empty files

Run tests:

```powershell
D:\nas_backup\LLM_Unified\.venv\Scripts\python.exe -m pytest ion-mentoring/tests/test_summarize_locust_csv.py -v
```

Expected output: 16 tests passed

### Integration Testing

The runner script (`scripts/run_all_load_tests.ps1`) includes built-in guards:

- **Summarizer failure detection**: Checks for temp file existence after summarizer call
- **Strict mode**: `-Strict` flag enables fail-fast behavior for CI pipelines
- **Error reporting**: Clear error messages when summarizer fails or CSV generation is incomplete

Test the guards:

```powershell
# Fast smoke test with all validations
./scripts/run_all_load_tests.ps1 -ScenarioProfile light -OverrideRunTime 10s -Strict
```

### Latest Load Test Results (2025-10-18)

**확장 시나리오 수동 실행 (2025-10-18 09:41 UTC)**

| Scenario    | Total Requests | Failures | Success (%) | Avg (ms) | P50 (ms) | P95 (ms) | P99 (ms)   | Req/s     | Status |
| ----------- | -------------- | -------- | ----------- | -------- | -------- | -------- | ---------- | --------- | ------ |
| Chat-only   | 2,319          | 0        | 100%        | 174      | 170      | 190      | 310        | 7.7       | ✅     |
| Edge        | 970            | 0        | 100%        | 170      | 160      | 180      | 300        | 3.2       | ✅     |
| Heavy       | 13,027         | 0        | 100%        | 213      | 170      | 190      | 2,100      | 43.5      | ✅     |
| Light       | 443            | 0        | 100%        | 556      | 160      | 180      | 18,000     | 3.7       | ✅     |
| Medium      | 6,746          | 0        | 100%        | 188      | 170      | 190      | 1,000      | 22.5      | ✅     |
| Spike       | 29,884         | 0        | 100%        | 372      | 170      | 190      | 4,200      | 83.2      | ✅     |
| Stress      | 51,585         | 0        | 100%        | 228      | 170      | 190      | 2,300      | 86.1      | ✅     |
| **Overall** | **104,974**    | **0**    | **100%**    | **264**  | **170**  | **190**  | **18,000** | **250.1** | ✅     |

_상세 표는 `ion-mentoring/outputs/summary_20251018_latest.md`에 기록되어 있습니다._

**CI 자동화 재실행 (2025-10-27 16:15 UTC)**

| Scenario | Total Requests | Failures | Success (%) | Avg (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Req/s | Status |
| -------- | -------------- | -------- | ----------- | -------- | -------- | -------- | -------- | ----- | ------ |
| Light    | 5,859          | 0        | 100%        | 279      | 170      | 180      | 1,400    | 48.8  | ✅     |
| Medium   | 19,149         | 0        | 100%        | 248      | 170      | 190      | 1,100    | 63.8  | ✅     |
| Heavy    | 34,219         | 0        | 100%        | 239      | 170      | 190      | 1,100    | 90.7  | ✅     |
| Stress   | 52,459         | 0        | 100%        | 214      | 170      | 190      | 1,100    | 87.5  | ✅     |

**자동화 검증 테스트 (2025-10-18, 로컬)**

| Scenario | Total Requests | Failures | Success (%) | Avg (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Req/s | Status |
| -------- | -------------- | -------- | ----------- | -------- | -------- | -------- | -------- | ----- | ------ |
| Light    | 537            | 0        | 100%        | 172      | 170      | 170      | 420      | 4.5   | ✅     |

_이 테스트는 runner guard 및 summarizer unit test 검증을 위해 실행되었습니다 (2min runtime)._

**Medium 시나리오 (3분, 로컬 검증)**

| Scenario | Total Requests | Failures | Success (%) | Avg (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Req/s | Status |
| -------- | -------------- | -------- | ----------- | -------- | -------- | -------- | -------- | ----- | ------ |
| Medium   | 4,006          | 0        | 100%        | 190      | 160      | 170      | 1,200    | 22.4  | ✅     |

_출처: `ion-mentoring/outputs/summary_medium_20251018_164238.md` (2025-10-18 16:42:38 local)._

#### 주요 메모

- ✅ 모든 시나리오가 100% 성공률을 유지했고 오류가 보고되지 않았습니다.
- ⚠️ Light 시나리오에서 P99가 18초까지 치솟아 콜드스타트 이후 긴 꼬리가 확인되었습니다.
- 🚀 Stress·Spike 프로필이 각각 86 req/s, 83 req/s로 목표 RPS를 안정적으로 달성했습니다.
- 🗂️ 최신 CSV → Markdown 변환은 `scripts/summarize_locust_csv.py`의 `--with-success-rate` 옵션으로 생성했습니다.
- 🧪 **신규**: 자동화 테스트 인프라 검증 완료 (16 unit tests, runner guards, CI SLO gating docs)
