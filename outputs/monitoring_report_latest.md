# Monitoring Report

**Generated**: 2025-11-01 21:45:33
**Time Window**: Last 24 hours
**Data Points**: 209 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.68%  |  Alerts: 3  |  Warnings: 1  |  Spikes: 52

  Alert Severity:
    [!] Critical: 3  |  [*] Warning: 0  |  [i] Info: 53

  Local LLM:     99.52% avail  |  45.09ms mean
  Cloud AI:      99.52% avail  |  271.45ms mean
  Lumen Gateway: 100% avail  |  235.37ms mean
  Resonance Policy: mode=observe policy=quality-first | allow=0 warn=3 block=0

  --- vs Previous Period (24h ago) ---
  Local:   Latency 97.6%  |  Avail =
  Cloud:   Latency 4.8%  |  Avail 0.5%
  Gateway: Latency 9.9%  |  Avail ▲0.5%
```

---

## Report Configuration

- **Time Window**: Last 24 hours
- **Peak Hours**: -
- **Sparkline Length**: 30
- **Data Points**: 209 snapshots

---

## Overall Health

- **Status**: EXCELLENT
- **Average Availability**: 99.68%
- **Alerts**: 3
- **Warnings**: 1
- **Spikes**: 52

---

## Performance Snapshot

- **Systems Considered**: 6
- **Overall Success**: 75.0%  |  **Effective**: 90.0%
- **Bands**: Excellent=4  Good=0  Needs=1  NoData=1
- **Top Attention**: Orchestration (50.0%)
- See: performance_dashboard_latest.md
---

## Channel Statistics

### Local LLM (LM Studio)

| Metric | Value |
|--------|-------|
| Availability | 99.52% |
| Mean Latency | 45.09 ms |
| Median Latency | 20 ms |
| Min Latency | 17 ms |
| Max Latency | 3030 ms |
| 95th Percentile | 28 ms |
| Std Deviation | +/- 251.1 ms |
| Spike Count | 16 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 209 |

Trend: -- DEGRADING (short 320.9ms vs long 170.95ms; n=10/20)
Sparkline (last 30):                         @     
Hourly Latency Sparkline:              *         @

Time-of-day Baselines: Peak mean 39.59 ms (+/- 196.75) [n=108] | Off-peak mean 50.96 ms (+/- 299.43) [n=101]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 99.52% |
| Mean Latency | 271.45 ms |
| Median Latency | 271 ms |
| Min Latency | 219 ms |
| Max Latency | 336 ms |
| 95th Percentile | 302 ms |
| Std Deviation | +/- 19.78 ms |
| Spike Count | 18 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 209 |

Trend: == STABLE (short 256.4ms vs long 249.05ms; n=10/20)
Sparkline (last 30): @*%++%%+%*+**   . .. .. ***+**
Hourly Latency Sparkline: %%     %%%%%%#%%%%%%%@##

Time-of-day Baselines: Peak mean 271.1 ms (+/- 18.44) [n=108] | Off-peak mean 271.83 ms (+/- 21.2) [n=101]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 235.37 ms |
| Median Latency | 220 ms |
| Min Latency | 210 ms |
| Max Latency | 3043 ms |
| 95th Percentile | 242 ms |
| Std Deviation | +/- 195.37 ms |
| Spike Count | 18 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 209 |

Trend: == STABLE (short 219.9ms vs long 220.2ms; n=10/20)
Sparkline (last 30): --%=:=-=-.@- =:* -:.= %. -=: -
Hourly Latency Sparkline: ==     ==========@======

Time-of-day Baselines: Peak mean 247.55 ms (+/- 271.65) [n=108] | Off-peak mean 222.35 ms (+/- 10.06) [n=101]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 512 |
| Unique Tasks |  |
| Avg Quality | ?占쏙옙 0.701 |
| Success Rate | ?占쏙옙 100% |
| Replan Rate | 40.91% |
| Last Activity | 4.6 minutes ago |

**[WARN] AGI System Alerts:**

- ?占쏙옙 CRITICAL AGI Replan Rate: 40.91% (threshold: 10%)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 0 | 16 |
| Cloud   | 0 | 0 | 0 | 0 | 18 |
| Gateway | 0 | 0 | 0 | 0 | 18 |
| Total   | 0 | 0 | 0 | 0 | 52 |
---

### Alert Severity Details

#### [!] Critical (3)

| Timestamp | Message |
|-----------|---------|
| 12:43:04 | Cloud AI offline (429) |
| 15:08:07 | ALERT: Lumen Gateway latency 3043ms |
| 21:18:09 | Local LLM offline (0) |

#### [i] Info (53)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:                  @  @     @ 
Warnings:  ..     .=-#@ **===--#*.= 
Spikes:    ..     .=-#@ =*===--#*.= 
---

### Availability Trend (hourly)

Local:     @@     @@@@@@@@@@@@@@@@%
Cloud:     @@     @@@@@@@%@@@@@@@@@
Gateway:   @@     @@@@@@@@@@@@@@@@@
---

## Recommendations

- **[CRITICAL]** 3 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **Spikes**: 52 latency spikes detected. Review system load and resource allocation.
- **[HIGH] AGI System**: High replan rate (40.91%).
  - Action: Investigate task complexity and initial planning quality
  - Action: Review rune event logs for replan patterns
  - Action: Consider adjusting AGI planning parameters

---

_Report generated by unified monitoring dashboard_