# Phase 4 Canary Deployment Dashboard Setup

This guide explains how to deploy and use the Phase 4 Canary Deployment Dashboard for monitoring the 5% canary rollout.

## Dashboard Overview

The Phase 4 Canary Dashboard provides **side-by-side comparison** of:

1. **Request Rate**: Canary vs Legacy traffic volume
2. **Error Rate**: 5xx errors with SLO threshold (< 0.5% increase)
3. **Latency Percentiles**: P50, P95, P99 comparison with thresholds
4. **Resource Utilization**: Memory and CPU usage comparison
5. **Auto-scaling**: Active instance counts for both services
6. **Response Code Distribution**: 2xx, 4xx, 5xx breakdown for canary
7. **Live Logs**: Real-time canary service logs

## Prerequisites

- Google Cloud SDK installed and authenticated
- `ion-api` (legacy) service deployed to Cloud Run
- `ion-api-canary` service deployed (using `deploy_phase4_canary.ps1`)
- Sufficient permissions to create Cloud Monitoring dashboards

## Quick Start

### Deploy Dashboard

```powershell
# Navigate to ion-mentoring directory
cd D:\nas_backup\LLM_Unified\ion-mentoring

# Deploy dashboard using gcloud CLI
gcloud monitoring dashboards create --config-from-file=monitoring/phase4_canary_dashboard.json

# Expected output:
# Created [https://console.cloud.google.com/monitoring/dashboards/custom/DASHBOARD_ID].
```

### Access Dashboard

After deployment, the dashboard will be accessible at:

```text
https://console.cloud.google.com/monitoring/dashboards?project=naeda-genesis
```

Or directly via the specific dashboard ID (check command output).

## Dashboard Panels Explained

### 1. Request Rate - Canary vs Legacy

- **Purpose**: Monitor traffic distribution between canary and legacy services
- **Expected**: Canary should receive ~5% of total traffic
- **What to look for**:
  - Canary request rate should be ~5% of legacy rate
  - Traffic patterns should be similar (peaks and valleys aligned)
  - No sudden drops in canary traffic (indicates routing issues)

### 2. Error Rate - Canary vs Legacy

- **Purpose**: Detect increased error rates in canary deployment
- **SLO Threshold**: < 0.5% increase over legacy error rate
- **What to look for**:
  - Canary error rate should be similar to or lower than legacy
  - Yellow threshold triggers at 0.5% increase (SLO warning)
  - Any sustained increase above threshold requires investigation

### 3. P50/P95/P99 Latency - Canary vs Legacy

- **Purpose**: Compare response time performance
- **SLO Threshold**: P95 < 10% increase over legacy
- **What to look for**:
  - **P50**: Should be very close between canary and legacy
  - **P95**: Yellow at 500ms, Red at 1000ms
  - **P99**: Red threshold at 2000ms
  - Latency spikes in canary but not legacy indicate performance issues

### 4. Memory Utilization - Canary vs Legacy

- **Purpose**: Monitor memory consumption and detect leaks
- **Thresholds**:
  - Yellow: 80% utilization (approaching limit)
  - Red: 90% utilization (critical, potential OOM)
- **What to look for**:
  - Canary memory should be stable and similar to legacy
  - Gradual increase over time indicates memory leak
  - Sudden spikes indicate inefficient code paths

### 5. CPU Utilization - Canary vs Legacy

- **Purpose**: Monitor CPU usage and identify performance bottlenecks
- **Thresholds**:
  - Yellow: 80% utilization
  - Red: 90% utilization
- **What to look for**:
  - Similar CPU patterns between canary and legacy
  - Higher canary CPU may indicate inefficient Phase 4 algorithms
  - Sustained high CPU may trigger auto-scaling

### 6. Active Instances - Canary vs Legacy

- **Purpose**: Verify auto-scaling behavior
- **What to look for**:
  - Canary instances should scale based on traffic (~5% of legacy)
  - Instance count should increase during peak traffic
  - Max 10 instances configured for canary (safety limit)

### 7. Response Code Distribution - Canary

- **Purpose**: Understand response patterns for canary traffic
- **What to look for**:
  - Majority should be 2xx (success)
  - 4xx indicates client errors (expected for invalid requests)
  - 5xx indicates server errors (investigate immediately)

### 8. Canary Deployment Logs

- **Purpose**: Real-time log streaming for troubleshooting
- **What to look for**:
  - INFO: Normal operations
  - WARNING: Potential issues (e.g., retry attempts)
  - ERROR: Failures requiring immediate attention

## Monitoring Schedule

### 1-Hour Critical Monitoring

**Frequency**: Every 5 minutes  
**Focus**: Error rate and latency  
**Actions**:

- Refresh dashboard every 5 minutes
- Check error rate stays below 0.5% increase
- Verify P95 latency within 10% of legacy
- Monitor for any anomalies in logs

### 6-Hour Extended Monitoring

**Frequency**: Every 30 minutes  
**Focus**: SLO validation and resource utilization  
**Actions**:

- Calculate average error rate over 6-hour window
- Verify at least 1,000 canary requests processed
- Check memory/CPU utilization stays below 80%
- Review response code distribution (>95% should be 2xx)

### 24-Hour Full Cycle Monitoring

**Frequency**: Every 2 hours  
**Focus**: Full daily traffic pattern validation  
**Actions**:

- Validate canary performance during peak hours
- Check auto-scaling behavior during traffic spikes
- Ensure no customer complaints or support tickets
- Calculate final SLO compliance for go/no-go decision

## SLO Calculation with Dashboard

Use these queries in the dashboard to calculate SLOs:

### Error Rate Comparison

```python
# Manual calculation using dashboard data
canary_errors = sum(canary_5xx_count)
canary_requests = sum(canary_request_count)
legacy_errors = sum(legacy_5xx_count)
legacy_requests = sum(legacy_request_count)

canary_error_rate = canary_errors / canary_requests
legacy_error_rate = legacy_errors / legacy_requests
error_rate_diff = abs(canary_error_rate - legacy_error_rate)

# SLO check
if error_rate_diff < 0.005:  # 0.5%
    print("✅ Error rate SLO PASSED")
else:
    print(f"❌ Error rate SLO FAILED: {error_rate_diff:.4f} increase")
```

### Latency Comparison

```python
# Manual calculation using dashboard data
canary_p95 = get_percentile_95(canary_latencies)
legacy_p95 = get_percentile_95(legacy_latencies)
latency_increase_pct = ((canary_p95 - legacy_p95) / legacy_p95) * 100

# SLO check
if latency_increase_pct < 10:  # 10%
    print("✅ Latency SLO PASSED")
else:
    print(f"❌ Latency SLO FAILED: {latency_increase_pct:.2f}% increase")
```

## Alerting Policies

Create alert policies for automated monitoring:

### High Canary Error Rate

```bash
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Phase 4 Canary - High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s \
  --condition-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="ion-api-canary" AND metric.type="run.googleapis.com/request_count" AND metric.labels.response_code_class="5xx"'
```

### High Canary Latency

```bash
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Phase 4 Canary - High P95 Latency" \
  --condition-display-name="P95 > 1000ms" \
  --condition-threshold-value=1000 \
  --condition-threshold-duration=300s \
  --condition-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="ion-api-canary" AND metric.type="run.googleapis.com/request_latencies"'
```

### Memory/CPU Critical

```bash
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Phase 4 Canary - High Memory Usage" \
  --condition-display-name="Memory > 90%" \
  --condition-threshold-value=0.9 \
  --condition-threshold-duration=300s \
  --condition-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="ion-api-canary" AND metric.type="run.googleapis.com/container/memory/utilizations"'
```

## Troubleshooting

### No Canary Data Appearing

**Symptoms**: Canary panels show "No data"

**Solutions**:

1. Verify canary service is deployed:

   ```powershell
   gcloud run services list --filter="ion-api-canary"
   ```

2. Check service is receiving traffic:

   ```powershell
   gcloud run services describe ion-api-canary --format="value(status.url)"
   # Test endpoint
   curl https://ion-api-canary-xxx.run.app/health
   ```

3. Verify traffic routing (application-level via CanaryRouter):

   ```powershell
   # Check environment variable
   gcloud run services describe ion-api-canary --format="value(spec.template.spec.containers[0].env)"
   # Should show CANARY_TRAFFIC_PERCENTAGE=5
   ```

### High Error Rate in Canary

**Symptoms**: Canary error rate significantly higher than legacy

**Solutions**:

1. Check canary logs for specific errors:

   ```powershell
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ion-api-canary AND severity>=ERROR" --limit=50 --format=json
   ```

2. Review Phase 4 feature flags:

   ```powershell
   # Verify Phase 4 env vars
   gcloud run services describe ion-api-canary `
       --format="value(spec.template.spec.containers[0].env[PHASE4_ENABLED])"
   gcloud run services describe ion-api-canary `
       --format="value(spec.template.spec.containers[0].env[CANARY_TRAFFIC_PERCENTAGE])"
   gcloud run services describe ion-api-canary `
       --format="value(spec.template.spec.containers[0].env[DEPLOYMENT_VERSION])"
   ```

3. Test canary endpoint directly:

   ```powershell
   # Bypass router, test canary service directly
   $canaryUrl = "https://ion-api-canary-xxx.run.app"
   Invoke-RestMethod -Uri "$canaryUrl/api/v1/sessions" -Method POST -Body '{"user_id":"test"}' -ContentType "application/json"
   ```

4. If error rate > 5% for 5+ minutes: **Execute rollback immediately**

   ```powershell
   .\scripts\rollback_phase4_canary.ps1 -ProjectId "naeda-genesis"
   ```

### High Latency in Canary

**Symptoms**: Canary P95 > 10% higher than legacy

**Solutions**:

1. Check for resource constraints:

   - Memory utilization > 80%: Increase to 2Gi
   - CPU utilization > 80%: Increase to 4 CPUs

2. Review Vertex AI call latencies:

   ```powershell
   # Check if Phase 4 recommendations are causing delays
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ion-api-canary AND jsonPayload.vertex_ai_latency>1000" --limit=20
   ```

3. Test with Phase 4 features disabled:

   ```powershell
   # Temporarily disable Phase 4 to isolate issue
   gcloud run services update ion-api-canary --set-env-vars PHASE4_ENABLED=false
   ```

### Dashboard Not Updating

**Symptoms**: Dashboard shows stale data or "Loading..."

**Solutions**:

1. Refresh browser (Ctrl+F5)
2. Verify project ID in filter:
   - Check `resource.labels.service_name="ion-api-canary"`
   - Ensure project matches `naeda-genesis`
3. Check Cloud Monitoring API is enabled:

   ```powershell
   gcloud services list --enabled --filter="monitoring.googleapis.com"
   ```

## Dashboard Customization

### Change Time Window

Default: Last 1 hour  
To change:

1. Click **Time Range** dropdown (top right)
2. Select desired range:
   - Last 6 hours (for extended monitoring)
   - Last 24 hours (for full cycle)
   - Custom range

### Add Custom Panel

Example: Add Sentry error count panel

1. Click **Edit Dashboard**
2. Click **Add Widget**
3. Select **Line Chart**
4. Configure query:

   ```text
   resource.type="cloud_run_revision"
   resource.labels.service_name="ion-api-canary"
   jsonPayload.sentry_event="true"
   ```

5. Click **Save**

### Export Dashboard JSON

```powershell
# Get dashboard ID
gcloud monitoring dashboards list --format="value(name)"

# Export to file
gcloud monitoring dashboards describe DASHBOARD_ID --format=json > my_custom_dashboard.json
```

## Next Steps

After dashboard deployment:

1. ✅ Deploy canary service (if not done): `.\scripts\deploy_phase4_canary.ps1`
2. ✅ Open dashboard in browser
3. ✅ Start 1-hour critical monitoring
4. ✅ Set alerts for automated notifications
5. ✅ Document any anomalies in incident log
6. ✅ After 24h validation: Increase canary traffic to 10%

## Additional Resources

- [PHASE4_DEPLOYMENT_OPERATIONS_GUIDE.md](../docs/PHASE4_DEPLOYMENT_OPERATIONS_GUIDE.md) - Full deployment procedures
- [Cloud Monitoring Documentation](https://cloud.google.com/monitoring/docs) - Google Cloud Monitoring guide
- [Canary Deployment Best Practices](https://cloud.google.com/architecture/application-deployment-and-testing-strategies#canary_test_pattern) - Google Cloud architecture patterns

## Contact

- **Slack**: #ion-ops (operations), #ion-dev (development)
- **PagerDuty**: On-call engineer for critical alerts
- **Dashboard Issues**: Create ticket in Jira with dashboard screenshot
