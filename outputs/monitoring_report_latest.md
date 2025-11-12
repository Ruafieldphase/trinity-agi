# Monitoring Report

**Generated**: 2025-11-12 09:49:34
**Time Window**: Last 24 hours
**Data Points**: 288 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.54%  |  Alerts: 9  |  Warnings: 1  |  Spikes: 58

  Alert Severity:
    [!] Critical: 9  |  [*] Warning: 0  |  [i] Info: 59

  Local LLM:     100% avail  |  5.02ms mean
  Cloud AI:      100% avail  |  282.08ms mean
  Lumen Gateway: 98.61% avail  |  350.75ms mean
  Resonance Policy: mode=n/a active=quality-first last=n/a | allow=0 warn=0 block=0
  Resonance Optimization: total=0 peak=0 offpeak=0 throttle=0 gateway_pref=0
  Feedback Loop: YouTube=3 RPA=50 events ingested

  --- vs Previous Period (24h ago) ---
  Local:   Latency 61.4%  |  Avail =
  Cloud:   Latency 1.6%  |  Avail ▲0.4%
  Gateway: Latency ▲6.1%  |  Avail 1%
```

---

## Report Configuration

- **Time Window**: Last 24 hours
- **Peak Hours**: -
- **Sparkline Length**: 30
- **Data Points**: 288 snapshots

---

## Overall Health

- **Status**: EXCELLENT
- **Average Availability**: 99.54%
- **Alerts**: 9
- **Warnings**: 1
- **Spikes**: 58

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
| Mean Latency | 5.02 ms |
| Median Latency | 5 ms |
| Min Latency | 4 ms |
| Max Latency | 15 ms |
| 95th Percentile | 7 ms |
| Std Deviation | +/- 1.05 ms |
| Spike Count | 12 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: -- DEGRADING (short 6ms vs long 5.45ms; n=10/20)
Sparkline (last 30): .@......=--.  --  - --....=--#
Hourly Latency Sparkline: :%-. +--:-:-  . .:@--#=@

Time-of-day Baselines: Peak mean 5.1 ms (+/- 0.96) [n=108] | Off-peak mean 4.98 ms (+/- 1.1) [n=180]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 282.08 ms |
| Median Latency | 276 ms |
| Min Latency | 234 ms |
| Max Latency | 728 ms |
| 95th Percentile | 311 ms |
| Std Deviation | +/- 31.1 ms |
| Spike Count | 28 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 285.9ms vs long 304.45ms; n=10/20)
Sparkline (last 30): .  .        @                 
Hourly Latency Sparkline: .: :  ..: ..= ::. :::-@:

Time-of-day Baselines: Peak mean 278.85 ms (+/- 15.09) [n=108] | Off-peak mean 284.02 ms (+/- 37.48) [n=180]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 98.61% |
| Mean Latency | 350.75 ms |
| Median Latency | 229 ms |
| Min Latency | 215 ms |
| Max Latency | 5037 ms |
| 95th Percentile | 285 ms |
| Std Deviation | +/- 681.57 ms |
| Spike Count | 18 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: -- DEGRADING (short 713.6ms vs long 471.75ms; n=10/20)
Sparkline (last 30):                         @     
Hourly Latency Sparkline: + + %  %  %  *    *  + @

Time-of-day Baselines: Peak mean 418.82 ms (+/- 868.63) [n=108] | Off-peak mean 309.91 ms (+/- 537.89) [n=180]

---

## AGI System Status

_No AGI activity in the selected time window_

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 0 | 12 |
| Cloud   | 0 | 0 | 0 | 0 | 28 |
| Gateway | 0 | 0 | 0 | 0 | 18 |
| Total   | 0 | 0 | 0 | 0 | 58 |
---

### Alert Severity Details

#### [!] Critical (9)

| Timestamp | Message |
|-----------|---------|
| 10:24:11 | ALERT: Lumen Gateway latency 3008ms |
| 12:29:11 | ALERT: Lumen Gateway latency 3008ms |
| 14:34:11 | Lumen Gateway offline (0) |
| 17:44:12 | Lumen Gateway offline (0) |
| 19:59:13 | Lumen Gateway offline (0) |

_... and 4 more critical alerts_

#### [i] Info (59)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:    @ @ @  @  @  @    @  @ @ 
Warnings:  @+-#-++-+#.---+-. -+.@-- 
Spikes:    @+-#-++-+#.---+-. -+.@.- 
---

### Availability Trend (hourly)

Local:     ------------------------
Cloud:     ------------------------
Gateway:   @@@@ @@ @@ @@@@@@@@@@@@ 
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

RPA Worker Summary: [2025-11-12 09:47:53] [INFO] Worker already running and healthy.

RPA Worker Alert: Restart limit reached for RPA worker ensure job. (timestamp=2025-11-03T18:45:23.2234157+09:00, recent_restarts=3/3, window_seconds=600)

## Resource Optimizer Summary

# Resource Optimizer Summary

**Dry Run**: True
**Budget Config**: C:\workspace\agi\configs\resource_budget.json
**Metrics Source**: C:\workspace\agi\outputs\performance_metrics_latest.json

## Recommendations
- All metrics within budget thresholds.

- **[CRITICAL]** 9 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **Spikes**: 58 latency spikes detected. Review system load and resource allocation.

---

_Report generated by unified monitoring dashboard_