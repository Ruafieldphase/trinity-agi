# Monitoring Report

**Generated**: 2025-11-14 11:49:35
**Time Window**: Last 24 hours
**Data Points**: 288 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.65%  |  Alerts: 10  |  Warnings: 5  |  Spikes: 54

  Alert Severity:
    [!] Critical: 10  |  [*] Warning: 0  |  [i] Info: 59

  Local LLM:     100% avail  |  4.5ms mean
  Cloud AI:      99.65% avail  |  280.95ms mean
  Lumen Gateway: 99.31% avail  |  392.45ms mean
  Resonance Policy: mode=observe active=quality-first last=quality-first | allow=0 warn=2 block=0
  Resonance Optimization: total=3 peak=3 offpeak=0 throttle=0 gateway_pref=3 primary=[gemini:3]
  Last Task: 21499ms
  Feedback Loop: YouTube=3 RPA=50 events ingested

  --- vs Previous Period (24h ago) ---
  Local:   Latency 8.5%  |  Avail =
  Cloud:   Latency ▲0.3%  |  Avail 0.4%
  Gateway: Latency ▲9%  |  Avail 0.3%
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
- **Average Availability**: 99.65%
- **Alerts**: 10
- **Warnings**: 5
- **Spikes**: 54

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
| Mean Latency | 4.5 ms |
| Median Latency | 4 ms |
| Min Latency | 4 ms |
| Max Latency | 16 ms |
| 95th Percentile | 6 ms |
| Std Deviation | +/- 1.07 ms |
| Spike Count | 11 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 4.3ms vs long 4.45ms; n=10/20)
Sparkline (last 30):     .  @    -                 
Hourly Latency Sparkline: %:..-::+-++  . .=   ..@.

Time-of-day Baselines: Peak mean 4.65 ms (+/- 1.46) [n=108] | Off-peak mean 4.42 ms (+/- 0.74) [n=180]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 99.65% |
| Mean Latency | 280.95 ms |
| Median Latency | 277 ms |
| Min Latency | 234 ms |
| Max Latency | 503 ms |
| 95th Percentile | 313 ms |
| Std Deviation | +/- 19.93 ms |
| Spike Count | 22 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 286.9ms vs long 283.05ms; n=10/20)
Sparkline (last 30): :-. -:-@:+--**.:=:..=*=:::*%:-
Hourly Latency Sparkline:  =--.: --==: =.-:@=*-:==

Time-of-day Baselines: Peak mean 279.19 ms (+/- 14.86) [n=108] | Off-peak mean 282.01 ms (+/- 22.4) [n=180]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 99.31% |
| Mean Latency | 392.45 ms |
| Median Latency | 251 ms |
| Min Latency | 215 ms |
| Max Latency | 5045 ms |
| 95th Percentile | 677 ms |
| Std Deviation | +/- 666.86 ms |
| Spike Count | 21 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: ++ IMPROVING (short 264ms vs long 468.7ms; n=10/20)
Sparkline (last 30):            @                  
Hourly Latency Sparkline: #. #.+.* #    @  *  % # 

Time-of-day Baselines: Peak mean 416.21 ms (+/- 692.7) [n=108] | Off-peak mean 378.19 ms (+/- 652.42) [n=180]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 93 |
| Unique Tasks |  |
| Avg Quality | ?�� 0.831 |
| Success Rate | ?�� 0% |
| Replan Rate | 5.13% |
| Last Activity | 3.6 hours ago |

**[WARN] AGI System Alerts:**

- ?�� CRITICAL AGI Success Rate: 0% (threshold: 70%)
- ?�� WARNING AGI Inactive: 3.6 hours since last activity (threshold: 2h)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 0 | 11 |
| Cloud   | 0 | 0 | 0 | 0 | 22 |
| Gateway | 0 | 0 | 0 | 0 | 21 |
| Total   | 0 | 0 | 0 | 0 | 54 |
---

### Alert Severity Details

#### [!] Critical (10)

| Timestamp | Message |
|-----------|---------|
| 12:29:12 | ALERT: Lumen Gateway latency 4031ms |
| 12:49:08 | Cloud AI offline (429) |
| 15:34:13 | ALERT: Lumen Gateway latency 4014ms |
| 17:39:10 | ALERT: Lumen Gateway latency 3282ms |
| 19:44:12 | ALERT: Lumen Gateway latency 3498ms |

_... and 5 more critical alerts_

#### [i] Info (59)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:    @  = = = =    =  =  = =  
Warnings:  *=*-.-#*-@. .- -*=.- =*= 
Spikes:    @=*=:=@@=@: := =@*:= *@* 
---

### Availability Trend (hourly)

Local:     ------------------------
Cloud:      @@@@@@@@@@@@@@@@@@@@@@@
Gateway:   @@@@@@@@@@@@@@ @@@@@ @@@
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

RPA Worker Summary: [2025-11-14 10:23:53] [INFO] Worker already running and healthy.

RPA Worker Alert: Restart limit reached for RPA worker ensure job. (timestamp=2025-11-03T18:45:23.2234157+09:00, recent_restarts=3/3, window_seconds=600)

## Resource Optimizer Summary

# Resource Optimizer Summary

**Dry Run**: True
**Budget Config**: C:\workspace\agi\configs\resource_budget.json
**Metrics Source**: C:\workspace\agi\outputs\performance_metrics_latest.json

## Recommendations
- All metrics within budget thresholds.

- **[CRITICAL]** 10 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **Spikes**: 54 latency spikes detected. Review system load and resource allocation.

---

_Report generated by unified monitoring dashboard_