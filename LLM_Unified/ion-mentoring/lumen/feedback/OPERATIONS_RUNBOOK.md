# Lumen v1.7 Feedback Loop - Operations Runbook

## Quick Reference

### � Design Docs

- Lumen 설계 자료 아카이브: [../**/docs/lumen_design/INDEX.md](../../docs/lumen_design/INDEX.md)

### �🚀 **NEW: Unified Management Console**

```powershell
# Launch interactive management console (Recommended!)
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/feedback_console.ps1
```

### Dashboard
- **URL**: https://console.cloud.google.com/monitoring/dashboards/custom/260e1b13-9eef-4f20-9c00-50cc1f1ce686?project=naeda-genesis
- **Name**: Lumen v1.7 - Feedback Loop (Enhanced)
- **Project**: naeda-genesis (64076350717)
- **Widgets**: 8 charts (cache hit rate, memory, health score, TTL, distributions)

### Metrics
- `logging.googleapis.com/user/cache_hit_rate` (DISTRIBUTION)
- `logging.googleapis.com/user/cache_memory_usage_percent` (DISTRIBUTION)
- `logging.googleapis.com/user/cache_avg_ttl_seconds` (DISTRIBUTION)
- `logging.googleapis.com/user/unified_health_score` (DISTRIBUTION)

### Alert Policies

**Status**: ⏳ Awaiting metric propagation (10 minutes after first emission)

#### Planned Policies

1. **Feedback Loop - Critical Health Score** (CRITICAL)
   - **Condition**: `unified_health_score < 30` for 5 minutes
   - **Purpose**: Detect severe degradation in overall system health (ROI, SLO, cache performance)
   - **Response**: 
     - Check `outputs/feedback_loop_report.md`
     - Review [Dashboard](https://console.cloud.google.com/monitoring/dashboards/custom/260e1b13-9eef-4f20-9c00-50cc1f1ce686)
     - Analyze cache metrics and ROI status
   - **Auto-close**: 30 minutes after resolution

2. **Feedback Loop - Low Cache Hit Rate** (WARNING)
   - **Condition**: `cache_hit_rate < 0.5` (50%) for 10 minutes
   - **Purpose**: Early warning for cache efficiency degradation
   - **Response**:
     - Check TTL settings and adaptive policy logs
     - Review cache memory usage and eviction rates
     - Consider TTL increase or cache size expansion
   - **Auto-close**: 60 minutes after resolution

#### Creating Alert Policies

```powershell
# Wait for metrics to propagate (10 minutes after first emission)
# Then create policies:
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/create_feedback_alert_policies.ps1

# Preview without creating (dry run)
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/create_feedback_alert_policies.ps1 -DryRun

# Custom notification channel
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/create_feedback_alert_policies.ps1 `
  -NotificationChannel "projects/naeda-genesis/notificationChannels/YOUR_CHANNEL_ID"
```

#### Testing Alert Triggers

```powershell
# After policies are created, test with breach values:
# Modify emit_feedback_metrics_once.py to send:
#   unified_health_score=15  (< 30 threshold)
#   cache_hit_rate=0.3       (< 0.5 threshold)

# Run manual emission
$env:GCP_PROJECT_ID = "naeda-genesis"
python emit_feedback_metrics_once.py
```

#### Legacy Lumen Gateway Alerts

These existing policies monitor Cloud Run service directly:
- **Lumen: Cache Hit Rate Low** - p50 < 0.50 for 5m (warning)
- **Lumen: Memory Usage High** - p90 > 90 for 5m (critical)
- **Lumen: Unified Health Low** - p50 < 60 for 5m (warning)

---

## Daily Operations

### 🎯 Recommended: Use Management Console

```powershell
# Interactive menu with all features
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/feedback_console.ps1
```

### Check System Health

```powershell
# Live metrics monitor (real-time updates every 5s)
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/watch_metrics_live.ps1 -RefreshSeconds 5

# Or open dashboard
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/open_dashboard.ps1 `
  -ProjectId naeda-genesis `
  -DashboardId 260e1b13-9eef-4f20-9c00-50cc1f1ce686

# Check scheduled task status
Get-ScheduledTask -TaskName "LumenFeedbackEmitter" | `
  Select-Object TaskName, State, LastRunTime, NextRunTime | Format-List

# Comprehensive verification
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/verify_data_flow.ps1 -ProjectId naeda-genesis

# View recent logs
gcloud logging read 'jsonPayload.component="feedback_loop"' `
  --project=naeda-genesis `
  --limit=10 `
  --format=json `
  --freshness=1h
```

### Manual Metrics Emission

```powershell
# One-time emission
$env:GCP_PROJECT_ID = "naeda-genesis"
$env:SERVICE_NAME = "lumen-gateway"
$env:MONTHLY_BUDGET_USD = "200.0"
D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe `
  D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/emit_feedback_metrics_once.py

# Or use wrapper script
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/run_emit_feedback_metrics_once.ps1 `
  -ProjectId naeda-genesis `
  -ServiceName lumen-gateway `
  -BudgetUSD 200.0
```

### Query Metrics

```powershell
# Describe a metric
gcloud logging metrics describe cache_hit_rate --project naeda-genesis

# List all feedback metrics
gcloud logging metrics list --project naeda-genesis --filter="name:cache_*"
```

---

## Configuration Management

### Logs-based Metrics

```powershell
# Create/Update all metrics
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/setup_logs_based_metrics.ps1 `
  -ProjectId naeda-genesis `
  -ServiceName lumen-gateway
```

---

## 🆕 New Operational Tools (2025-10-25)

### Interactive Management Console

**Purpose**: Unified interface for all feedback loop operations

```powershell
# Launch console
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/feedback_console.ps1
```

**Menu Options**:
1. Quick Status (latest metrics)
2. Open Dashboard (browser)
3. Live Metrics Watch (real-time terminal)
4. Check Scheduled Task
5. View Recent Logs
6. Analyze Metric Distribution
7. Test Alert Triggers
8. Test Slack Notifications
9. Tune Alert Thresholds
10. Manual Metrics Emission
11. Verify Data Flow
12. Setup Wizard
13. Exit

### Live Metrics Monitor

**Purpose**: Real-time terminal-based metrics display with auto-refresh

```powershell
# Default (5s refresh)
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/watch_metrics_live.ps1

# Custom interval
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/watch_metrics_live.ps1 -RefreshSeconds 10
```

**Status Indicators**:
- `[OK]` - Green: Metrics within healthy ranges
- `[WARN]` - Yellow: Approaching thresholds
- `[CRIT]` - Red: Threshold violations detected

### Statistical Distribution Analysis

**Purpose**: Analyze collected metrics to inform threshold tuning

```powershell
# Last 1 hour
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/analyze_metrics_distribution.ps1 -Hours 1

# Last 24 hours
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/analyze_metrics_distribution.ps1 -Hours 24

# Save report
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/analyze_metrics_distribution.ps1 `
  -Hours 24 -OutFile "distribution_analysis.txt"
```

**Output**: Min/Max/Mean/p50/p90/p95/p99 for each metric, recommended thresholds

### Alert Testing

**Purpose**: Emit metrics violating thresholds to test notification pipeline

```powershell
# Test cache hit rate alert
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/test_alert_triggers.ps1 -Scenario hit-rate

# Test memory usage alert
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/test_alert_triggers.ps1 -Scenario memory

# Test health score alert
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/test_alert_triggers.ps1 -Scenario health

# Test all scenarios
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/test_alert_triggers.ps1 -Scenario all
```

**Note**: Test metrics include `test_trigger=True` label for identification

### Slack Webhook Testing

**Purpose**: Validate Slack integration with multiple message formats

```powershell
# Simple test message
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/test_slack_webhook.ps1 `
  -WebhookUrl "https://hooks.slack.com/services/YOUR/WEBHOOK" `
  -Type simple

# Alert format
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/test_slack_webhook.ps1 `
  -WebhookUrl "https://hooks.slack.com/services/YOUR/WEBHOOK" `
  -Type alert

# Dashboard summary
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/test_slack_webhook.ps1 `
  -WebhookUrl "https://hooks.slack.com/services/YOUR/WEBHOOK" `
  -Type dashboard

# Live metrics from GCP
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/test_slack_webhook.ps1 `
  -WebhookUrl "https://hooks.slack.com/services/YOUR/WEBHOOK" `
  -Type metrics `
  -ProjectId naeda-genesis
```

---

## Monitoring Alert Policies

### Alert Policies (continued)

```powershell
# DryRun (review config)
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/setup_alert_policies.ps1 `
  -ProjectId naeda-genesis `
  -DryRun

# Create/Update policies
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/setup_alert_policies.ps1 `
  -ProjectId naeda-genesis

# Adjust thresholds
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/setup_alert_policies.ps1 `
  -ProjectId naeda-genesis `
  -HitRateThresholdPercent 60 `
  -MemoryThresholdPercent 85 `
  -HealthThreshold 70
```

### Notification Channels

```powershell
# DryRun
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/setup_notification_channels.ps1 `
  -ProjectId naeda-genesis `
  -EmailAddress alerts@example.com `
  -DryRun

# Create channels and link to policies
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/setup_notification_channels.ps1 `
  -ProjectId naeda-genesis `
  -EmailAddress alerts@example.com

# Add Slack
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/setup_notification_channels.ps1 `
  -ProjectId naeda-genesis `
  -EmailAddress alerts@example.com `
  -SlackWebhookUrl "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

---

## Scheduled Task Management

### Register Periodic Emission (5 minutes)

```powershell
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/register_feedback_metrics_emitter.ps1 `
  -TaskName "LumenFeedbackEmitter" `
  -IntervalMinutes 5 `
  -Force `
  -ProjectId naeda-genesis `
  -ServiceName lumen-gateway `
  -BudgetUSD 200.0
```

### Check Task Status

```powershell
Get-ScheduledTask -TaskName "LumenFeedbackEmitter" | Format-List

Get-ScheduledTaskInfo -TaskName "LumenFeedbackEmitter" | Format-List
```

### Unregister Task

```powershell
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/unregister_feedback_metrics_emitter.ps1 `
  -TaskName "LumenFeedbackEmitter" `
  -Force
```

---

## Troubleshooting

### Using New Tools for Diagnosis

```powershell
# 1. Quick health check
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/feedback_console.ps1
# → Select option 1 (Quick Status)

# 2. Watch live metrics for 2 minutes
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/watch_metrics_live.ps1 -RefreshSeconds 5

# 3. Check if data collection is working
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/verify_data_flow.ps1 -ProjectId naeda-genesis

# 4. Analyze metric distributions
D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/analyze_metrics_distribution.ps1 -Hours 1
```

### Metrics Not Appearing

1. Check scheduled task is running:

   ```powershell
   Get-ScheduledTaskInfo -TaskName "LumenFeedbackEmitter"
   ```

2. Manually emit once:

   ```powershell
   D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/run_emit_feedback_metrics_once.ps1 `
     -ProjectId naeda-genesis -ServiceName lumen-gateway -BudgetUSD 200.0
   ```

3. Verify logs are being written:

   ```powershell
   gcloud logging read 'jsonPayload.component="feedback_loop"' `
     --project=naeda-genesis --limit=5 --freshness=10m
   ```

4. Check metric configuration:

   ```powershell
   gcloud logging metrics describe cache_hit_rate --project naeda-genesis
   ```

5. Wait 2-5 minutes for metrics to populate

### Alerts Not Firing

1. Check alert policies exist:

   ```powershell
   gcloud monitoring policies list --project=naeda-genesis `
     --filter='displayName:"Lumen:"'
   ```

2. Verify notification channels are linked:

   ```powershell
   gcloud monitoring channels list --project=naeda-genesis
   ```

3. **NEW**: Test alerts using test_alert_triggers.ps1:

   ```powershell
   # Test all alert scenarios at once
   D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/test_alert_triggers.ps1 -Scenario all
   
   # Or test specific scenario
   D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/test_alert_triggers.ps1 -Scenario hit-rate
   ```

4. Wait 5-10 minutes for alert evaluation cycle

5. Check Slack/Email for test notifications

### Dashboard Shows No Data

1. Verify dashboard exists:

   ```powershell
   gcloud monitoring dashboards list --project=naeda-genesis `
     --filter='displayName:"Lumen v1.7"'
   ```

2. Check time range selector in dashboard UI (set to "Last 1 hour")

3. Verify metrics have data:

   ```powershell
   gcloud logging read 'jsonPayload.component="feedback_loop"' `
     --project=naeda-genesis --limit=1 --freshness=1h
   ```

---

## Prometheus Integration (On-Prem/Cluster)

### Deploy Alert Rules

1. Copy rules file:

   ```bash
   cp LLM_Unified/ion-mentoring/gateway/alerts/prometheus_rules.yml /etc/prometheus/
   ```

2. Update `prometheus.yml`:

   ```yaml
   rule_files:
     - "prometheus_rules.yml"
   ```

3. Reload Prometheus:

   ```bash
   kill -HUP <prometheus-pid>
   # or
   curl -X POST http://localhost:9090/-/reload
   ```

### Verify Rules

```bash
# Check rules are loaded
curl http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="lumen_gateway_alerts")'

# Check for firing alerts
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.component=="feedback-loop")'
```

---

## Maintenance

### Adjust Thresholds (After 1-2 Days Observation)

1. **NEW**: Run statistical analysis to get recommendations:

   ```powershell
   # Analyze 24-48 hours of data
   D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/analyze_metrics_distribution.ps1 `
     -Hours 48 -OutFile "threshold_analysis.txt"
   ```

2. Review recommended thresholds from analysis output

3. Update alert policies with new thresholds:

   ```powershell
   # Example: Increase hit rate threshold to 60%, reduce memory to 85%
   D:/nas_backup/LLM_Unified/ion-mentoring/lumen/feedback/setup_alert_policies.ps1 `
     -ProjectId naeda-genesis `
     -HitRateThresholdPercent 60 `
     -MemoryThresholdPercent 85 `
     -HealthThreshold 70
   ```

4. Update Prometheus rules in `prometheus_rules.yml` to match

5. **Alternatively**: Use interactive console menu option 9 (Tune Alert Thresholds)

### AGI Health Gate & 필터 관리 (2025-10-26 추가)

- AGI 메트릭 수집기는 `outputs/health_gate_state.json`에 연속 실패·성공 스택과 쿨다운 시간을 기록합니다. 급한 경우만 수동으로 삭제/수정하고, 가급적 `alert_system.py --no-alert`로 상태를 확인하세요.
- 기본 제외 프리픽스는 `summarize_ledger.py`의 설정을 자동으로 재사용합니다. 원시 데이터를 보고 싶다면 `alert_system.py --no-default-excludes` 또는 시뮬레이터에서 `--source ledger --no-default-excludes` 플래그를 활용하세요.
- 임계값 조정 전후에는 시뮬레이터로 재생 테스트를 수행하세요.

```powershell
# 최신 알림 로그 기반으로 재생 (샘플이 적을 때 권장)
$env:PYTHONPATH = "fdo_agi_repo"
python fdo_agi_repo/scripts/simulate_alert_thresholds.py --source alert_log --show-timeline

# 24시간 레저드를 60분 간격으로 샘플링하며 그리드 탐색
$env:PYTHONPATH = "fdo_agi_repo"
python fdo_agi_repo/scripts/simulate_alert_thresholds.py `
  --source ledger `
  --hours 24 `
  --interval 60 `
  --confidence-grid 0.55:0.65:0.02 `
  --quality-grid 0.60:0.70:0.02 `
  --second-pass-grid 1.0:2.5:0.5
```

- 출력되는 `Thresholds -> ...` 행으로 경보 민감도를 비교한 뒤, 변경하려는 환경 변수(`AGI_MIN_CONFIDENCE`, `AGI_MIN_QUALITY`, `AGI_MAX_SECOND_PASS_RATE`)와 경보 정책을 동기화하세요.
- 시뮬레이션 후에는 현재 게이트 상태가 새 임계값에 맞게 회복되는지 `alert_system.py --no-alert`로 재확인합니다.

### Clean Up Old Dashboards

```powershell
# List all dashboards
gcloud monitoring dashboards list --project=naeda-genesis

# Delete by ID
gcloud monitoring dashboards delete "projects/64076350717/dashboards/<ID>" `
  --project=naeda-genesis --quiet
```

---

## Key Files

### Scripts

**Core Infrastructure**:
- `setup_logs_based_metrics.ps1` - Create/update logs-based metrics
- `setup_alert_policies.ps1` - Manage alert policies
- `setup_notification_channels.ps1` - Configure email/Slack notifications
- `register_feedback_metrics_emitter.ps1` - Schedule periodic metrics emission
- `unregister_feedback_metrics_emitter.ps1` - Remove scheduled task
- `run_emit_feedback_metrics_once.ps1` - Wrapper for one-time emission
- `emit_feedback_metrics_once.py` - Python emitter (runs orchestrator)
- `open_dashboard.ps1` - Open dashboard in browser
- `cleanup_dashboards.ps1` - Delete duplicate dashboards

**🆕 Operational Tools (2025-10-25)**:
- `feedback_console.ps1` - **Interactive management console (Recommended entry point!)**
- `watch_metrics_live.ps1` - Real-time terminal metrics monitor
- `analyze_metrics_distribution.ps1` - Statistical analysis for threshold tuning
- `test_alert_triggers.ps1` - Emit test metrics to validate alerts
- `test_slack_webhook.ps1` - Test Slack notifications with multiple formats
- `verify_data_flow.ps1` - Comprehensive end-to-end validation

### Configuration
- `gateway/alerts/prometheus_rules.yml` - Prometheus alert rules

### Documentation

**Setup Guides**:
- `깃코_Logs_Based_Metrics_구축_완료_2025-10-25.md` - Metrics setup guide
- `깃코_Alert_정책_구축_완료_2025-10-25.md` - Alert policies guide
- `깃코_알림_채널_자동화_완료_2025-10-25.md` - Notification automation guide

**🆕 Operational Status**:
- `깃코_Feedback_실시간_운영현황_2025-10-25.md` - Real-time status & new tools overview

---

## Support Contacts

- **Team**: Backend
- **Component**: feedback-loop
- **Severity Levels**:
  - critical: Immediate attention (page on-call)
  - warning: Address soon (ticket)
  - info: Informational only

---

## Change Log

### 2025-10-25 (Afternoon Session)
- ✅ **NEW**: Interactive management console (`feedback_console.ps1`) with 13 menu options
- ✅ **NEW**: Live metrics monitor (`watch_metrics_live.ps1`) with real-time terminal updates
- ✅ **NEW**: Statistical analysis tool (`analyze_metrics_distribution.ps1`) for threshold tuning
- ✅ **NEW**: Alert testing tool (`test_alert_triggers.ps1`) for notification validation
- ✅ **NEW**: Slack webhook tester (`test_slack_webhook.ps1`) with 4 message formats
- ✅ Enhanced `verify_data_flow.ps1` - Fixed gcloud filter escaping bug
- ✅ Operations Runbook updated with new tools section
- ✅ Real-time operational status document created

### 2025-10-25 (Morning Session)
- ✅ Logs-based metrics created (4 DISTRIBUTION metrics)
- ✅ Alert policies provisioned (3 MQL policies)
- ✅ Prometheus rules added (4 PromQL rules)
- ✅ Notification channel automation implemented
- ✅ Scheduled task registered (5-minute interval)
- ✅ Dashboard cleanup (2 duplicates removed, 1 primary retained)
- ✅ Operations runbook created
