# Monitoring Report

**Generated**: 2025-11-12 10:20:16
**Time Window**: Last 24 hours
**Data Points**: 288 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.54%  |  Alerts: 9  |  Warnings: 1  |  Spikes: 57

  Alert Severity:
    [!] Critical: 9  |  [*] Warning: 0  |  [i] Info: 58

  Local LLM:     100% avail  |  5.03ms mean
  Cloud AI:      100% avail  |  281.78ms mean
  Lumen Gateway: 98.61% avail  |  350.69ms mean
  Resonance Policy: mode=n/a active=quality-first last=n/a | allow=0 warn=0 block=0
  Resonance Optimization: total=0 peak=0 offpeak=0 throttle=0 gateway_pref=0
  AGI Eval: min_quality=0.6
  Feedback Loop: YouTube=3 RPA=50 events ingested

  --- vs Previous Period (24h ago) ---
  Local:   Latency 61.3%  |  Avail =
  Cloud:   Latency 1.6%  |  Avail ▲0.4%
  Gateway: Latency ▲5.9%  |  Avail 1%
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
- **Spikes**: 57

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
| Mean Latency | 5.03 ms |
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

Trend: == STABLE (short 6.1ms vs long 5.55ms; n=10/20)
Sparkline (last 30): ..+--.  --  - --....+--@-...--
Hourly Latency Sparkline: =-+ :-=.::-. .. :%::+#-@

Time-of-day Baselines: Peak mean 5.13 ms (+/- 0.96) [n=108] | Off-peak mean 4.98 ms (+/- 1.1) [n=180]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 281.78 ms |
| Median Latency | 277 ms |
| Min Latency | 233 ms |
| Max Latency | 728 ms |
| 95th Percentile | 311 ms |
| Std Deviation | +/- 31.45 ms |
| Spike Count | 28 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 267.2ms vs long 274.5ms; n=10/20)
Sparkline (last 30):    . .@         ...  .        
Hourly Latency Sparkline: .: ...:. ..::.:::.:::=@ 

Time-of-day Baselines: Peak mean 278.04 ms (+/- 16.73) [n=108] | Off-peak mean 284.02 ms (+/- 37.48) [n=180]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 98.61% |
| Mean Latency | 350.69 ms |
| Median Latency | 229 ms |
| Min Latency | 215 ms |
| Max Latency | 5037 ms |
| 95th Percentile | 271 ms |
| Std Deviation | +/- 681.57 ms |
| Spike Count | 17 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: ++ IMPROVING (short 242.4ms vs long 476.75ms; n=10/20)
Sparkline (last 30):                   @           
Hourly Latency Sparkline: + + %  % %  *    *  +  @

Time-of-day Baselines: Peak mean 418.65 ms (+/- 868.65) [n=108] | Off-peak mean 309.91 ms (+/- 537.89) [n=180]

---

## AGI System Status

_No AGI activity in the selected time window_

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 0 | 12 |
| Cloud   | 0 | 0 | 0 | 0 | 28 |
| Gateway | 0 | 0 | 0 | 0 | 17 |
| Total   | 0 | 0 | 0 | 0 | 57 |
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

#### [i] Info (58)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:    @ @ @  @ @  @    @  @  @ 
Warnings:  @-+++-@+ @.+..++ --.+++. 
Spikes:    @-+++-@+ @.+..++ --.++-. 
---

### Availability Trend (hourly)

Local:     ------------------------
Cloud:     ------------------------
Gateway:   @@@@ @@ @ @@@@@@@@@@@@@ 
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

RPA Worker Summary: [2025-11-12 10:18:34] [INFO] Worker already running and healthy.

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

- **Spikes**: 57 latency spikes detected. Review system load and resource allocation.

---

_Report generated by unified monitoring dashboard_