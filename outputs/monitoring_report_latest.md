# Monitoring Report

**Generated**: 2025-11-15 11:54:14
**Time Window**: Last 24 hours
**Data Points**: 270 snapshots

---

## Executive Summary

```
  HEALTH: GOOD
  Availability: 99.38%  |  Alerts: 5  |  Warnings: 0  |  Spikes: 48

  Alert Severity:
    [!] Critical: 5  |  [*] Warning: 0  |  [i] Info: 48

  Local LLM:     99.26% avail  |  4.91ms mean
  Cloud AI:      100% avail  |  283.55ms mean
  Lumen Gateway: 98.89% avail  |  314.99ms mean
  Resonance Policy: mode=observe active=quality-first last=quality-first | allow=7 warn=0 block=0
  Resonance Optimization: total=7 peak=0 offpeak=7 throttle=7 gateway_pref=7 primary=[local_llm:7]
  Last Task: 4524ms
  AGI Eval: min_quality=0.6
  Feedback Loop: YouTube=3 RPA=50 events ingested

  --- vs Previous Period (24h ago) ---
  Local:   Latency ▲9.1%  |  Avail 0.7%
  Cloud:   Latency ▲0.9%  |  Avail ▲0.4%
  Gateway: Latency 19.7%  |  Avail 0.4%
```

---

## Report Configuration

- **Time Window**: Last 24 hours
- **Peak Hours**: -
- **Sparkline Length**: 30
- **Data Points**: 270 snapshots

---

## Overall Health

- **Status**: GOOD
- **Average Availability**: 99.38%
- **Alerts**: 5
- **Warnings**: 0
- **Spikes**: 48

---

## Performance Snapshot

- **Systems Considered**: 6
- **Overall Success**: 83.3%  |  **Effective**: 100.0%
- **Bands**: Excellent=5  Good=0  Needs=0  NoData=1
- See: performance_dashboard_latest.md
---

## Channel Statistics

### Local LLM (LM Studio)

| Metric | Value |
|--------|-------|
| Availability | 99.26% |
| Mean Latency | 4.91 ms |
| Median Latency | 5 ms |
| Min Latency | 4 ms |
| Max Latency | 47 ms |
| 95th Percentile | 6 ms |
| Std Deviation | +/- 2.72 ms |
| Spike Count | 13 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 270 |

Trend: == STABLE (short 5.4ms vs long 5.35ms; n=10/20)
Sparkline (last 30):     ..-   =..*. .. . .@ -.....
Hourly Latency Sparkline: @===+++=+++++++==++==++ 

Time-of-day Baselines: Peak mean 5.24 ms (+/- 4.57) [n=90] | Off-peak mean 4.74 ms (+/- 0.82) [n=180]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 283.55 ms |
| Median Latency | 280 ms |
| Min Latency | 232 ms |
| Max Latency | 466 ms |
| 95th Percentile | 314 ms |
| Std Deviation | +/- 20.33 ms |
| Spike Count | 16 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 270 |

Trend: == STABLE (short 276ms vs long 280ms; n=10/20)
Sparkline (last 30): :::-::-::@ :=+:-::=-.++ :: -:-
Hourly Latency Sparkline: @%%%%%%%%%%%%%%%%%%%%%# 

Time-of-day Baselines: Peak mean 282.78 ms (+/- 25.64) [n=90] | Off-peak mean 283.93 ms (+/- 17.13) [n=180]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 98.89% |
| Mean Latency | 314.99 ms |
| Median Latency | 243 ms |
| Min Latency | 215 ms |
| Max Latency | 5038 ms |
| 95th Percentile | 349 ms |
| Std Deviation | +/- 504.03 ms |
| Spike Count | 19 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 270 |

Trend: -- DEGRADING (short 742ms vs long 497.8ms; n=10/20)
Sparkline (last 30):                      @        
Hourly Latency Sparkline: ----=----%=@---------%- 

Time-of-day Baselines: Peak mean 314.53 ms (+/- 506.28) [n=90] | Off-peak mean 315.22 ms (+/- 504.31) [n=180]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 245 |
| Unique Tasks |  |
| Avg Quality | ?�� 0.834 |
| Success Rate | ?�� 0% |
| Replan Rate | 4.65% |
| Last Activity | 18.4 hours ago |

**[WARN] AGI System Alerts:**

- ?�� CRITICAL AGI Success Rate: 0% (threshold: 70%)
- ?�� CRITICAL AGI Inactive: 18.4 hours since last activity (threshold: 2h)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 0 | 13 |
| Cloud   | 0 | 0 | 0 | 0 | 16 |
| Gateway | 0 | 0 | 0 | 0 | 19 |
| Total   | 0 | 0 | 0 | 0 | 48 |
---

### Alert Severity Details

#### [!] Critical (5)

| Timestamp | Message |
|-----------|---------|
| 12:49:21 | Local LLM offline (503) |
| 20:44:31 | Local LLM offline (503) |
| 20:59:15 | Lumen Gateway offline (0) |
| 23:04:15 | Lumen Gateway offline (0) |
| 09:44:16 | Lumen Gateway offline (0) |

#### [i] Info (48)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:    @       @@ @         @   
Warnings:  ++.---+.+---# .-++ .@+   
Spikes:    ++.---+.+---# .-++ .@+   
---

### Availability Trend (hourly)

Local:     %@@@@@@@%@@@@@@@@@@@@@@ 
Cloud:     @@@@@@@@@@@@@@@@@@@@@@@ 
Gateway:   @@@@@@@@@%@%@@@@@@@@@%@ 
---

## Recommendations

## Policy Snapshot (Latest)

# Policy A/B Snapshot

Generated: 2025-11-09 09:44:49
Lines analyzed (ledger): 34908

## Ledger-Based Counts
- quality-first: count=45 allow=35 warn=10 block=0 avg=11925ms p95=50297ms

## Synthetic Re-Evaluation
- quality-first: n=31 allow=25 warn=6 avg=10445ms p95=26316ms
- latency-first: n=31 allow=25 warn=6 avg=10445ms p95=26316ms

Auto Stabilizer Summary: 2025-11-04T16:52:51.900363 Micro-Reset triggered (success=True, dry_run=True, fear=0.500)

RPA Worker Summary: [2025-11-15 11:53:22] [INFO] Worker already running and healthy.

RPA Worker Alert: Restart limit reached for RPA worker ensure job. (timestamp=2025-11-03T18:45:23.2234157+09:00, recent_restarts=3/3, window_seconds=600)

## Resource Optimizer Summary

# Resource Optimizer Summary

**Dry Run**: True
**Budget Config**: C:\workspace\agi\configs\resource_budget.json
**Metrics Source**: C:\workspace\agi\outputs\performance_metrics_latest.json

## Recommendations
- All metrics within budget thresholds.

- **[CRITICAL]** 5 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **Spikes**: 48 latency spikes detected. Review system load and resource allocation.

---

_Report generated by unified monitoring dashboard_