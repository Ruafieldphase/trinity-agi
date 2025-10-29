# 📊 Log Analysis Automation

Automated error pattern detection and log analysis for ION API and Lumen Gateway.

## 🎯 Features

- **Automated Log Export**: Cloud Run ERROR+ logs automatically exported to BigQuery
- **Pattern Detection**: Identifies recurring error patterns and trends
- **Anomaly Detection**: Detects unusual error spikes
- **Root Cause Analysis**: Groups errors by type, service, and affected endpoints
- **Actionable Insights**: Generates specific recommendations for fixing issues

## 📁 File Structure

```
monitoring/
├── setup_log_analysis.py        # Infrastructure setup (BigQuery + Log Sink)
├── analyze_error_patterns.py    # Error pattern analysis script
└── README_LOG_ANALYSIS.md        # This file
```

## 🚀 Quick Start

### 1. Setup Infrastructure (One-time)

```bash
cd d:\nas_backup\LLM_Unified
.\.venv\Scripts\python ion-mentoring\monitoring\setup_log_analysis.py --project naeda-genesis
```

**What it does**:
- Creates BigQuery dataset `cloud_run_logs`
- Creates Cloud Logging sink `cloud-run-logs-sink`
- Grants permissions for log export
- Filters: ERROR+ logs from `ion-api` and `lumen-gateway`

**Output**:

```
✅ BigQuery Dataset: cloud_run_logs
✅ Log Sink: cloud-run-logs-sink
✅ Service Account: serviceAccount:cloud-logs@system.gserviceaccount.com
⏳ Logs will start flowing to BigQuery within 1-2 minutes
```

### 2. Wait for Logs (5-10 minutes)

Logs accumulate gradually. First logs appear within 1-2 minutes, but wait 5-10 minutes for meaningful analysis.

**Check status**:

```bash
.\.venv\Scripts\python ion-mentoring\monitoring\setup_log_analysis.py --project naeda-genesis --verify-only
```

### 3. Analyze Error Patterns

```bash
cd d:\nas_backup\LLM_Unified

# Last 24 hours (default)
.\.venv\Scripts\python ion-mentoring\monitoring\analyze_error_patterns.py --project naeda-genesis

# Last week
.\.venv\Scripts\python ion-mentoring\monitoring\analyze_error_patterns.py --project naeda-genesis --hours 168

# Custom output
.\.venv\Scripts\python ion-mentoring\monitoring\analyze_error_patterns.py \
  --project naeda-genesis \
  --output weekly_errors.md \
  --json weekly_errors.json
```

## 📊 Analysis Output

### Markdown Report (`error_analysis_report.md`)

```markdown
# 🔍 Error Pattern Analysis Report

**Analysis Period**: 24 hours
**Total Errors**: 14,571
**Error Rate**: 607.13 errors/hour
**Unique Patterns**: 3

## Service Breakdown
| Service | Error Count | Percentage |
|---------|-------------|------------|
| ion-api | 14,571 | 100.0% |

## Top Error Patterns

### 1. 503_SERVICE_UNAVAILABLE (14,564 occurrences)
**Message**: Lumen Gateway unavailable: Client error '404 Not Found' for url ...

- **Severity**: ERROR
- **Service**: ion-api
- **First Seen**: 2025-10-22 08:17:25 UTC
- **Last Seen**: 2025-10-23 08:17:25 UTC

**Affected Paths**:
- `/api/lumen/chat`
- `/api/lumen/personas`
- `/api/lumen/health`

## 💡 Recommendations
- 🔥 **Priority**: Fix '503_SERVICE_UNAVAILABLE' (14,564 occurrences, 99.9% of errors)
- 🔍 **High 404 Rate**: 14,564 not found errors (99.9%) - review endpoint configurations
- 📍 **Hotspot**: '/api/lumen/chat' has 7,282 errors - investigate this endpoint
```

### JSON Data (`error_analysis_report.json`)

```json
{
  "total_errors": 14571,
  "error_rate": 607.13,
  "unique_patterns": 3,
  "top_patterns": [
    {
      "error_type": "503_SERVICE_UNAVAILABLE",
      "message": "Lumen Gateway unavailable: Client error '404 Not Found'...",
      "count": 14564,
      "affected_service": "ion-api",
      "affected_paths": ["/api/lumen/chat", "/api/lumen/personas", ...]
    }
  ]
}
```

## 🔍 What Gets Analyzed

| Metric | Description | Purpose |
|--------|-------------|---------|
| **Error Patterns** | Grouped by message, service, and path | Identify recurring issues |
| **Service Breakdown** | Error count per service | Isolate problematic service |
| **Severity Distribution** | ERROR vs CRITICAL vs others | Prioritize by severity |
| **Hourly Distribution** | Error count per hour | Detect time-based patterns |
| **Anomalies** | Spikes > 3x baseline | Alert on unusual events |
| **Top Endpoints** | Most error-prone paths | Focus investigation |

## 🎯 Error Classification

| Type | Detection Pattern | Example |
|------|-------------------|---------|
| `404_NOT_FOUND` | "404" or "not found" in message | Lumen Gateway unavailable: 404 Not Found |
| `503_SERVICE_UNAVAILABLE` | "503" or "unavailable" | Service temporarily unavailable |
| `500_INTERNAL_ERROR` | "500" or "internal server" | Internal server error |
| `TIMEOUT` | "timeout" in message | Request timeout after 30s |
| `CONNECTION_ERROR` | "connection" in message | Connection refused |
| `OTHER` | All other errors | Uncategorized errors |

## 🚨 Anomaly Detection

**Algorithm**:

```python
baseline_rate = total_errors / hours
spike_threshold = baseline_rate * 3

for hour, count in hourly_distribution.items():
    if count > spike_threshold:
        alert("Spike detected at {hour}: {count} errors")
```

**Example Alert**:

```
🚨 Spike detected at 2025-10-23 06:00: 1,250 errors (3.2x baseline)
```

## 💡 Automated Recommendations

The analyzer generates context-aware recommendations:

1. **Top Priority**: Fix the most frequent error pattern
2. **High 404 Rate**: When >50% of errors are 404, suggests endpoint review
3. **Service Availability**: When >10 503 errors, suggests health check
4. **Hotspot Detection**: Identifies specific endpoints needing attention

## 🔧 Advanced Usage

### Query BigQuery Directly

```sql
-- Top 10 error messages (last 24 hours)
SELECT
  jsonPayload.message as error,
  COUNT(*) as count
FROM `naeda-genesis.cloud_run_logs.cloud_run_revision_*`
WHERE severity = 'ERROR'
  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY error
ORDER BY count DESC
LIMIT 10
```

### Custom Time Ranges

```bash
# Last 6 hours
python analyze_error_patterns.py --project naeda-genesis --hours 6

# Last 30 days
python analyze_error_patterns.py --project naeda-genesis --hours 720
```

### Cleanup Infrastructure

```bash
# Warning: This deletes all log data!
python setup_log_analysis.py --project naeda-genesis --cleanup
```

## 📈 Retention & Costs

| Setting | Value | Notes |
|---------|-------|-------|
| **Dataset Retention** | 30 days | Tables auto-expire after 30 days |
| **Log Filter** | severity>=ERROR | Only ERROR, CRITICAL exported |
| **Estimated Size** | ~10 MB/day | Depends on error volume |
| **Estimated Cost** | < $0.01/day | BigQuery storage + queries |

## 🐛 Troubleshooting

### No tables found

**Symptom**: `⚠️  No log tables found`

**Solutions**:
1. Wait 5-10 minutes for logs to accumulate
2. Verify logs are being generated:

   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=10
   ```

3. Check sink status:

   ```bash
   gcloud logging sinks describe cloud-run-logs-sink
   ```

### Permission denied

**Symptom**: `❌ Failed to grant permissions`

**Solution**: Manually grant permissions:

```bash
gcloud projects add-iam-policy-binding naeda-genesis \
  --member='serviceAccount:cloud-logs@system.gserviceaccount.com' \
  --role='roles/bigquery.dataEditor'
```

### Query timeout

**Symptom**: `❌ Error querying patterns: Timeout`

**Solutions**:
1. Reduce time range: `--hours 6`
2. Check BigQuery quota limits
3. Wait for table optimization (first queries are slow)

## 📝 Integration with Daily Reports

The log analysis complements the daily operations report:

| Tool | Purpose | Frequency |
|------|---------|-----------|
| **Daily Report** | Real-time metrics (requests, latency, errors) | Daily |
| **Log Analysis** | Deep error investigation | On-demand / Weekly |

**Combined Workflow**:
1. Daily report detects high error rate (e.g., 18.68% 4xx)
2. Log analysis identifies root cause (Lumen Gateway 404)
3. Fix issue based on specific endpoint details
4. Daily report verifies fix success

## 🚀 Future Enhancements

### Phase 2: Automated Alerting (2-3h)
- Email/Slack notifications for critical patterns
- Threshold-based alerts (e.g., >100 errors/hour)
- Integration with Cloud Monitoring Alerts

### Phase 3: ML-Based Clustering (4-6h)
- Automatic error categorization using embeddings
- Similar error detection
- Trend prediction

### Phase 4: Root Cause Graph (3-4h)
- Visualize error dependencies
- Service interaction map
- Trace analysis integration

## 📚 Resources

- **BigQuery Console**: https://console.cloud.google.com/bigquery?project=naeda-genesis&d=cloud_run_logs
- **Cloud Logging**: https://console.cloud.google.com/logs
- **Sink Configuration**: https://console.cloud.google.com/logs/storage

## 🎓 Key Learnings

### Current Findings (2025-10-23)

**Issue**: ION API 18.68% 4xx error rate

**Root Cause** (from log analysis):

```
Lumen Gateway unavailable: Client error '404 Not Found' 
for url 'https://lumen-gateway-production-64076350717.us-central1.run.app/chat'
```

**Problem**: ION API is calling wrong Lumen Gateway URL
- Expected: `https://lumen-gateway-production-64076350717.us-central1.run.app/api/v1/chat`
- Actual: `https://lumen-gateway-production-64076350717.us-central1.run.app/chat`

**Fix**: Update ION API environment variable `LUMEN_GATEWAY_URL` or route configuration

**Impact**: Fixing this will eliminate 99.9% of current errors (14,564 out of 14,571)

---

*Generated by ION Log Analysis System v1.0*
