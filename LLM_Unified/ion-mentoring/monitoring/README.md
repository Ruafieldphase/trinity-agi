# Cloud Monitoring Dashboard Setup

This guide explains how to create and configure the Cloud Monitoring dashboard for the ION Mentoring API.

## Dashboard Overview

The dashboard provides real-time monitoring of:

1. **Request Rate**: Total requests per minute
2. **Error Rate**: 5xx errors per minute with thresholds
3. **Latency Metrics**: P50, P95, P99 percentiles
4. **Rate Limiting**: 429 responses tracking
5. **Auto-scaling**: Active instance count
6. **Resource Usage**: Memory and CPU utilization
7. **Response Codes**: Distribution of 2xx, 4xx, 5xx responses
8. **Loop Performance**: Resonance 200?칖s loop latency & adapter success rate (Grafana)

## Prerequisites

- Google Cloud SDK installed
- Authenticated with sufficient permissions
- `ion-api` service deployed to Cloud Run

## Deploy Dashboard

### ??Current Dashboard (Phase 4 - Active)

**Dashboard ID**: `3b6b1242-f2e3-4e98-9af4-d9cbfae87ead`  
**Direct Access**: [Phase 4 Canary Monitoring Dashboard](https://console.cloud.google.com/monitoring/dashboards/custom/3b6b1242-f2e3-4e98-9af4-d9cbfae87ead?project=naeda-genesis)

**Created**: 2025-10-21  
**Configuration**: `simple_dashboard.json` (5 widgets, Canary-focused)

**Monitored Metrics**:

- Request Rate (Canary service)
- 5xx Error Rate
- P95 Latency
- P99 Latency

### Option 1: Using gcloud CLI

```bash
# From repository root
cd ion-mentoring/monitoring

# Create simplified dashboard (recommended)
gcloud monitoring dashboards create --project=naeda-genesis --config-from-file=simple_dashboard.json

# Alternative: Full dashboard with Canary vs Legacy comparison
gcloud monitoring dashboards create --project=naeda-genesis --config-from-file=dashboard.json
```

### Option 2: Using Cloud Console

1. Go to [Cloud Monitoring Dashboards](https://console.cloud.google.com/monitoring/dashboards)
2. Click **Create Dashboard**
3. Click **JSON** (top right)
4. Paste contents of `monitoring/simple_dashboard.json` or `dashboard.json`
5. Click **Apply**
6. Click **Save**

## Dashboard Metrics Explained

### Request Rate

- **Metric**: `run.googleapis.com/request_count`
- **Aggregation**: Rate over 1 minute
- **Purpose**: Monitor traffic patterns and detect spikes

### Error Rate

- **Metric**: `run.googleapis.com/request_count` filtered by `response_code_class="5xx"`
- **Thresholds**:
  - Yellow: > 5% error rate
  - Red: > 10% error rate
- **Purpose**: Detect service degradation

### Latency (P50, P95, P99)

- **Metric**: `run.googleapis.com/request_latencies`
- **P50**: Median latency (50% of requests faster)
- **P95**: 95th percentile (95% of requests faster)
  - Yellow threshold: > 500ms
  - Red threshold: > 1000ms
- **P99**: 99th percentile (99% of requests faster)
- **Purpose**: Identify performance bottlenecks

### Rate Limit Exceeded

- **Metric**: `run.googleapis.com/request_count` filtered by `response_code="429"`
- **Purpose**: Monitor rate limiting effectiveness

### Active Instances

- **Metric**: `run.googleapis.com/container/instance_count`
- **Purpose**: Verify auto-scaling behavior

### Memory/CPU Utilization

- **Metrics**: `run.googleapis.com/container/memory/utilizations` and `cpu/utilizations`
- **Thresholds**:
  - Yellow: > 80%
  - Red: > 90%
- **Purpose**: Detect resource constraints

### Loop Performance (Grafana)

Resonance 猷 ⑦봽 吏 ?쒕뒗 Prometheus/Grafana?먯꽌 ?쒓컖?뷀빀?덈떎. `resonance_prometheus_exporter.py`(湲곕낯 port 9108)瑜??ㅽ뻾?????꾨옒 ?⑤꼸??異붽??섏꽭??

- **Loop Latency**
  - **PromQL**: `resonance_loop_latency_ms`
  - **?⑤꼸**: Single stat ?먮뒗 Line
  - **Thresholds**: ??0?칖s (green), 40??0?칖s (orange), ??0?칖s (red)
- **Adapter Success Rate**
  - **PromQL**: `resonance_adapter_success_rate`
  - **?⑤꼸**: Gauge/Line, 紐 ⑺몴 ??0.97
- **Alert ?덉떆**
  - `resonance_loop_latency_ms > 60` for 1m (warning)
  - `resonance_loop_latency_ms > 80` for 30s (critical)
  - `resonance_adapter_success_rate < 0.97` for 5m (warning)

?먯꽭???댁쁺 ?덉감? ?먮룞???ㅽ겕由쏀듃???ㅼ쓬 臾몄꽌瑜?李멸퀬?섏꽭??

- ?몃? ?뚰겕?ㅽ럹?댁뒪 臾몄꽌: [LOOP_PERFORMANCE_OPERATIONS.md](../../../ai_binoche_conversation_origin/lumen/docs/system_c/v0_8_release/LOOP_PERFORMANCE_OPERATIONS.md)
- ?꾩옱 由 ы룷吏 ?곕━: [OPERATIONAL_RUNBOOK.md](../OPERATIONAL_RUNBOOK.md) ("200?칖s 猷 ⑦봽 ?깅뒫 紐 ⑤땲?곕쭅" ??

## Alerting Policies

Create alert policies for critical metrics:

### High Error Rate Alert

```bash
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="ION API - High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s \
  --condition-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="ion-api" AND metric.type="run.googleapis.com/request_count" AND metric.labels.response_code_class="5xx"'
```

### High Latency Alert

```bash
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="ION API - High Latency" \
  --condition-display-name="P95 latency > 500ms" \
  --condition-threshold-value=500 \
  --condition-threshold-duration=300s \
  --condition-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="ion-api" AND metric.type="run.googleapis.com/request_latencies"'
```

## Viewing Dashboard

1. Go to [Cloud Console Monitoring](https://console.cloud.google.com/monitoring)
2. Click **Dashboards** in left menu
3. Find **ION Mentoring API Dashboard**
4. Dashboard updates automatically every minute

## Dashboard URL

After creation, get the dashboard URL:

```bash
# List all dashboards
gcloud monitoring dashboards list

# Get specific dashboard URL
gcloud monitoring dashboards describe DASHBOARD_ID --format="value(name)"
```

Dashboard will be accessible at:

```text
https://console.cloud.google.com/monitoring/dashboards/custom/DASHBOARD_ID?project=naeda-genesis
```

## Troubleshooting

### No Data Appearing

1. **Check service is receiving traffic**:

   ```bash
   curl https://ion-api-64076350717.us-central1.run.app/health
   ```

2. **Verify metrics are being collected**:

   ```bash
   gcloud monitoring time-series list \
     --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="ion-api"' \
     --limit=5
   ```

3. **Check time range**: Ensure dashboard time range includes recent data

### Permissions Issues

Required roles:

- `roles/monitoring.dashboardEditor` - Create/edit dashboards
- `roles/monitoring.viewer` - View metrics

Grant permissions:

```bash
gcloud projects add-iam-policy-binding naeda-genesis \
  --member="user:YOUR_EMAIL" \
  --role="roles/monitoring.dashboardEditor"
```

## Next Steps

- [ ] Deploy dashboard using gcloud CLI
- [ ] Verify all widgets showing data
- [ ] Create alerting policies
- [ ] Configure notification channels (email, Slack, etc.)
- [ ] Run load tests to see metrics in action

## Windows Scheduled Task: Autonomous 30?몀in Checks
> Run the following commands from the repository root. Replace `pwsh` with `powershell` if needed.

?댁쁺?먭? 留?30 遺꾨쭏???섎룞?쇰줈 ?몃━ 嫄고븯吏  ?딆븘???섎룄濡? ?덈룄???묒뾽 ?ㅼ?以꾨윭??紐 ⑤땲??猷 ⑦봽瑜??깅줉?????덉뒿?덈떎.

- ?깅줉 諛?利됱떆 ?ㅽ뻾(沅뚯옣, ?덉씠???쒗븳 ?꾨줈釉??ы븿):

  ```powershell
  pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\register_monitor_schedule.ps1 -Register -RunNow -WithProbe -IntervalSeconds 1800 -DurationMinutes 1440
  ```

- ?곹깭 ?뺤씤:

  ```powershell
  Get-ScheduledTask -TaskName "ION Monitor Loop" | Get-ScheduledTaskInfo | Format-List *
  ```

- ?깅줉 ?댁젣:

  ```powershell
  pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\register_monitor_schedule.ps1 -Unregister
  ```

濡쒓렇??`LLM_Unified/ion-mentoring/logs/monitor_loop_*.log`???쒖감 ??λ맗?덈떎.

## One?몊hot health check (CLI)

- ?꾩옱 ?곹깭瑜???踰덈쭔 ?뺤씤(醫낅즺肄붾뱶 ?ы븿):

  ```powershell
  pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\check_monitoring_status.ps1 -ReturnExitCode
  ```

- JSON ?ㅻ깄?룹쑝濡????

  ```powershell
  $out = "status_now.json"; pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\check_monitoring_status.ps1 -ReturnExitCode -OutJson $out; Get-Content $out
  ```

## Auto?몉emediation (?덉쟾???④퀎??蹂듦뎄)

?ъ뒪泥댄겕 ?ㅽ뙣 ???ㅼ뒪濡??꾪솕(?뚮컢?끸넂?ш?利앪넂鍮좊Ⅸ 鍮꾧탳???듭뀡)濡ㅻ갚)瑜??섑뻾?⑸땲??

- ?쒕씪?대윴(?ㅼ젣 蹂  寃??놁쓬, 寃곌낵 JSON 湲곕줉):

  ```powershell
  pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\auto_remediation.ps1 -DryRun
  ```

- ?ㅼ젣 蹂듦뎄 ?ㅽ뻾(蹂댁닔?곸쑝濡??숈옉):

  ```powershell
  pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\auto_remediation.ps1
  ```

寃곌낵??`LLM_Unified/ion-mentoring/logs/auto_remediation_*.json`????λ맗?덈떎.

## Manual monitor loop (with/without probe)

- ?꾨줈釉??ы븿 30 遺?猷 ⑦봽 ?쒖옉(湲곗〈 猷 ⑦봽 醫낅즺 ???ъ떆??:

  ```powershell
  pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\start_monitor_loop.ps1 -KillExisting -IncludeRateLimitProbe -IntervalSeconds 1800 -DurationMinutes 1440
  ```

- 猷 ⑦봽 以묐떒留??ㅽ뻾 以묒씤 ?숈씪 ?ㅽ겕由쏀듃 ?몄뒪?댁뒪瑜?醫낅즺):

  ```powershell
  pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\start_monitor_loop.ps1 -KillExisting -StopOnly
  ```

## Logs & artifacts

- 紐 ⑤땲??猷 ⑦봽 濡쒓렇: `LLM_Unified/ion-mentoring/logs/monitor_loop_*.log`
- 媛??뚯감 ?곹깭 JSON: `LLM_Unified/ion-mentoring/logs/status_iter_*.json`
- 由 щ??붿뿉?댁뀡 寃곌낵: `LLM_Unified/ion-mentoring/logs/auto_remediation_*.json`

臾몄옄 ?몄퐫?⑹뿉 ?곕씪 濡쒓렇 ???대え吏 /?뱀닔臾몄옄媛  源 ⑥졇 蹂댁씪 ???덉쑝??湲곕뒫?먮뒗 ?곹뼢 ?놁뒿?덈떎.

## Operations & Maintenance

### Daily Report Generation

**???먮룞 ?ㅽ뻾**: 留ㅼ씪 ?ㅼ쟾 8:00 (Windows Scheduler ?깅줉??  
**?묒뾽 ?대쫫**: `ION Daily Report`  
**異쒕젰 ?꾩튂**: `logs/daily_report_YYYYMMDD_HHMMSS.txt`

吏 ??24?쒓컙(?먮뒗 吏 ???쒓컙)??紐 ⑤땲?곕쭅 寃곌낵瑜?醫낇빀 遺꾩꽍??由 ы룷?몃? ?앹꽦?⑸땲??

```powershell
# ?섎룞 ?ㅽ뻾 (吏??24?쒓컙 由ы룷??
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\generate_daily_report.ps1 -Hours 24

# 吏??6?쒓컙留?遺꾩꽍
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\generate_daily_report.ps1 -Hours 6

# ?뱀젙 寃쎈줈?????
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\generate_daily_report.ps1 -OutputPath ".\reports\today.txt"

# Scheduler ?곹깭 ?뺤씤
Get-ScheduledTask -TaskName "ION Daily Report" | Format-List TaskName, State, @{N='NextRun';E={(Get-ScheduledTaskInfo $_.TaskName).NextRunTime}}
```

由 ы룷?몄뿉???ㅼ쓬 ?댁슜???ы븿?⑸땲??

- ?ъ뒪 泥댄겕 ?붿빟 (?깃났/?ㅽ뙣 鍮꾩쑉, 媛 ?숇쪧)
- ?먮윭??諛?P95 吏 ?곗떆媛??듦퀎
- ?먮룞 蹂듦뎄 ?대젰
- 濡쒓렇 ?뚯씪 ?듦퀎
- ?꾩껜 ?됯? (EXCELLENT/ATTENTION/CRITICAL) 諛?沅뚯옣?ы빆
- ?꾩껜 ?됯? 諛?沅뚯옣?ы빆

### Log Cleanup

?ㅻ옒??濡쒓렇 ?뚯씪???뺣━???붿뒪??怨듦컙??愿  由 ы빀?덈떎:

```powershell
# 7???댁긽 ??濡쒓렇 ??젣 (?쒕씪?대윴)
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\cleanup_old_logs.ps1 -KeepDays 7 -DryRun -Verbose

# ?ㅼ젣 ??젣
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\cleanup_old_logs.ps1 -KeepDays 7

# 30???댁긽 ??濡쒓렇留???젣
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\cleanup_old_logs.ps1 -KeepDays 30
```

?뺢린?곸쑝濡??ㅽ뻾?섎젮硫?Windows ?묒뾽 ?ㅼ?以꾨윭??二쇨컙 ?묒뾽?쇰줈 ?깅줉?섏꽭??

### Locust 寃곌낵 ?붿빟 (?먰겢由?

遺 ?섑뀒?ㅽ듃 寃곌낵(`*_stats.csv`)瑜?Markdown ?쒕줈 ?붿빟?⑸땲??

```powershell
# ?꾩옱 ?대뜑??*_stats.csv瑜??붿빟?섏뿬 肄섏넄 異쒕젰
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\summarize_locust_results.ps1 -InputGlob ".\*.csv"

# ?뚯씪濡????
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\summarize_locust_results.ps1 -InputGlob ".\outputs\*.csv" -OutputPath "ion-mentoring\logs\locust_summary.md"
```

?대??곸쑝濡?`summarize_locust_csv.py`瑜??몄텧?섎ŉ, ?깃났瑜?Overall/ASCII ?곹깭 ?쒖떆瑜?湲곕낯 ?쒖꽦?뷀빀?덈떎.

### Emergency Rollback

**?럳 ?덈젴 ?먮즺**: [`docs/湲닿툒_濡ㅻ갚_?덈젴_媛?대뱶_2025-10-21.md`](../docs/湲닿툒_濡ㅻ갚_?덈젴_媛?대뱶_2025-10-21.md)  
**?덈젴 ?쒓컙**: 15-20 遺?(4 媛??쒕굹由 ъ삤 + ?ㅼ뒿)

湲닿툒 ?곹솴 ??移대굹由?諛고룷瑜?鍮좊Ⅴ 寃?濡ㅻ갚?⑸땲??

```powershell
# Dry-Run (?덉쟾 紐⑤뱶, ?덈젴??
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\emergency_rollback.ps1 -DryRun -SkipConfirmation

# ?꾩옱 ?곹깭 ?뺤씤 ??濡ㅻ갚 (??뷀삎)
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\emergency_rollback.ps1

# 媛뺤젣 濡ㅻ갚 (嫄닿컯 ?곹깭? 臾닿?)
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\emergency_rollback.ps1 -Force

# ?뺤씤 ?놁씠 利됱떆 濡ㅻ갚 (鍮꾩긽 ?곹솴)
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\emergency_rollback.ps1 -SkipConfirmation
```

???ㅽ겕由쏀듃??

1. ?꾩옱 嫄닿컯 ?곹깭 ?뺤씤
2. 濡ㅻ갚 ?ㅽ뻾 (?몃옒??0%濡?
3. 30 珥?? 湲????ы솗??
4. 濡ㅻ갚 ???곹깭 寃  利?

?섎룞 濡ㅻ갚蹂대떎 鍮좊Ⅴ 怨??덉쟾?섍쾶 臾몄젣瑜??꾪솕?????덉뒿?덈떎.

**?좑툘 二쇱쓽**: ?꾨줈?뺤뀡 ?ㅽ뻾 ?꾩뿉 諛섎뱶??`-DryRun` 紐 ⑤뱶濡??덈젴?섏꽭??

### Log Analysis by Time Range

?뱀젙 ?쒓컙???濡쒓렇留?異붿텧??遺꾩꽍?⑸땲??

```powershell
# 理쒓렐 1?쒓컙 濡쒓렇 ?꾪꽣 (?붿빟 ?ы븿)
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\filter_logs_by_time.ps1 -Last 1h -ShowSummary

# 理쒓렐 24?쒓컙 濡쒓렇 ?꾪꽣 (JSON ???
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\filter_logs_by_time.ps1 -Last 24h -OutJson "filtered_logs.json" -ShowSummary

# ?뱀젙 ?좎쭨/?쒓컙 踰붿쐞 ?꾪꽣
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\filter_logs_by_time.ps1 -StartTime "2025-01-20 08:00" -EndTime "2025-01-20 12:00" -ShowSummary

# 吏??30遺꾨쭔 (鍮좊Ⅸ ?먭?)
pwsh -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\scripts\filter_logs_by_time.ps1 -Last 30m -ShowSummary
```

異쒕젰?먮뒗 ?ㅼ쓬???ы븿?⑸땲??

- ?꾪꽣??泥댄겕 嫄댁닔
- ?깃났/?ㅽ뙣 鍮꾩쑉
- ?됯퇏 P95 吏 ?곗떆媛?諛??먮윭??
- 理쒓렐 10 媛?泥댄겕 ??꾨씪??

?댁긽 吏뺥썑媛  諛쒓껄???쒓컙? 瑜?鍮좊Ⅴ 寃?遺꾩꽍?????덉뒿?덈떎.
