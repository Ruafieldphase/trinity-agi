# Monitoring Report

**Generated**: 2025-11-11 19:49:36
**Time Window**: Last 24 hours
**Data Points**: 282 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.53%  |  Alerts: 11  |  Warnings: 1  |  Spikes: 62

  Alert Severity:
    [!] Critical: 11  |  [*] Warning: 0  |  [i] Info: 63

  Local LLM:     100% avail  |  12.84ms mean
  Cloud AI:      99.65% avail  |  286.87ms mean
  Lumen Gateway: 98.94% avail  |  347.06ms mean
  Resonance Policy: mode=n/a active=quality-first last=n/a | allow=0 warn=0 block=0
  Resonance Optimization: total=0 peak=0 offpeak=0 throttle=0 gateway_pref=0
  Feedback Loop: YouTube=3 RPA=50 events ingested

  --- vs Previous Period (24h ago) ---
  Local:   Latency 16.1%  |  Avail ▲0.4%
  Cloud:   Latency ▲2.5%  |  Avail 0.4%
  Gateway: Latency ▲13.8%  |  Avail 0.7%
```

---

## Report Configuration

- **Time Window**: Last 24 hours
- **Peak Hours**: -
- **Sparkline Length**: 30
- **Data Points**: 282 snapshots

---

## Overall Health

- **Status**: EXCELLENT
- **Average Availability**: 99.53%
- **Alerts**: 11
- **Warnings**: 1
- **Spikes**: 62

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
| Availability | 100% |
| Mean Latency | 12.84 ms |
| Median Latency | 5 ms |
| Min Latency | 4 ms |
| Max Latency | 2048 ms |
| 95th Percentile | 9 ms |
| Std Deviation | +/- 121.63 ms |
| Spike Count | 14 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 282 |

Trend: == STABLE (short 5.1ms vs long 5.1ms; n=10/20)
Sparkline (last 30): --*     - @-- ------------@- -
Hourly Latency Sparkline:             @           

Time-of-day Baselines: Peak mean 5.01 ms (+/- 0.88) [n=108] | Off-peak mean 17.7 ms (+/- 154.81) [n=174]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 99.65% |
| Mean Latency | 286.87 ms |
| Median Latency | 277 ms |
| Min Latency | 234 ms |
| Max Latency | 2124 ms |
| 95th Percentile | 314 ms |
| Std Deviation | +/- 111.13 ms |
| Spike Count | 28 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 282 |

Trend: == STABLE (short 271.3ms vs long 275.15ms; n=10/20)
Sparkline (last 30): ==+=-=#=+#=%=:==@=-----==-=+ =
Hourly Latency Sparkline:        ..   @           

Time-of-day Baselines: Peak mean 277.47 ms (+/- 15.6) [n=108] | Off-peak mean 292.7 ms (+/- 140.78) [n=174]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 98.94% |
| Mean Latency | 347.06 ms |
| Median Latency | 229 ms |
| Min Latency | 19 ms |
| Max Latency | 5037 ms |
| 95th Percentile | 271 ms |
| Std Deviation | +/- 648.42 ms |
| Spike Count | 20 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 282 |

Trend: == STABLE (short 226.9ms vs long 225.15ms; n=10/20)
Sparkline (last 30):     @                         
Hourly Latency Sparkline:   + + # + @   + = %  %  

Time-of-day Baselines: Peak mean 374.07 ms (+/- 744.47) [n=108] | Off-peak mean 330.3 ms (+/- 582.57) [n=174]

---

## AGI System Status

_No AGI activity in the selected time window_

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 0 | 14 |
| Cloud   | 0 | 0 | 0 | 0 | 28 |
| Gateway | 0 | 0 | 0 | 0 | 20 |
| Total   | 0 | 0 | 0 | 0 | 62 |
---

### Alert Severity Details

#### [!] Critical (11)

| Timestamp | Message |
|-----------|---------|
| 21:54:11 | ALERT: Lumen Gateway latency 3332ms |
| 23:59:11 | ALERT: Lumen Gateway latency 3217ms |
| 02:04:12 | ALERT: Lumen Gateway latency 4288ms |
| 04:09:11 | ALERT: Lumen Gateway latency 3478ms |
| 06:14:13 | ALERT: Lumen Gateway latency 4081ms |

_... and 6 more critical alerts_

#### [i] Info (63)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:      = = = = = @ = = =  =   
Warnings:  ----= @=*.--.-#=-*-==-=* 
Spikes:    ----= @=*.-- -#=-*-==-=* 
---

### Availability Trend (hourly)

Local:     ------------------------
Cloud:     @@@@@@@@@@@@ @@@@@@@@@@@
Gateway:   @@@@@@@@@@@@ @@@@@ @@ @@
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

RPA Worker Summary: [2025-11-11 19:44:43] [INFO] Worker already running and healthy.

RPA Worker Alert: Restart limit reached for RPA worker ensure job. (timestamp=2025-11-03T18:45:23.2234157+09:00, recent_restarts=3/3, window_seconds=600)

## Resource Optimizer Summary

# Resource Optimizer Summary

**Dry Run**: True
**Budget Config**: C:\workspace\agi\configs\resource_budget.json
**Metrics Source**: C:\workspace\agi\outputs\performance_metrics_latest.json

## Recommendations
- All metrics within budget thresholds.

- **[CRITICAL]** 11 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **Spikes**: 62 latency spikes detected. Review system load and resource allocation.

---

_Report generated by unified monitoring dashboard_