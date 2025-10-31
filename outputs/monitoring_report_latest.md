# Monitoring Report

**Generated**: 2025-10-31 19:52:24
**Time Window**: Last 24 hours
**Data Points**: 214 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.69%  |  Alerts: 4  |  Warnings: 213  |  Spikes: 40

  Alert Severity:
    [!] Critical: 4  |  [*] Warning: 0  |  [i] Info: 467

  Local LLM:     99.53% avail  |  2054.14ms mean
  Cloud AI:      100% avail  |  284.09ms mean
  Lumen Gateway: 99.53% avail  |  260.19ms mean

  --- vs Previous Period (24h ago) ---
  Local:   Latency =  |  Avail 0.5%
  Cloud:   Latency ▲4.5%  |  Avail =
  Gateway: Latency 0.7%  |  Avail 0.5%
```

---

## Report Configuration

- **Time Window**: Last 24 hours
- **Peak Hours**: -
- **Sparkline Length**: 30
- **Data Points**: 214 snapshots

---

## Overall Health

- **Status**: EXCELLENT
- **Average Availability**: 99.69%
- **Alerts**: 4
- **Warnings**: 213
- **Spikes**: 40

---

## Channel Statistics

### Local LLM (LM Studio)

| Metric | Value |
|--------|-------|
| Availability | 99.53% |
| Mean Latency | 2054.14 ms |
| Median Latency | 2060 ms |
| Min Latency | 20 ms |
| Max Latency | 3076 ms |
| 95th Percentile | 2080 ms |
| Std Deviation | +/- 156.54 ms |
| Spike Count | 8 |
| Baseline Alerts | 0 |
| Baseline Warns | 214 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 214 |

Trend: == STABLE (short 1855.9ms vs long 1958.4ms; n=10/20)
Sparkline (last 30): %%%%%%%%%%%%%@%%%%%%%%%%%%%%% 
Hourly Latency Sparkline: %%%%%     %%%%%@%%%%%%%#

Time-of-day Baselines: Peak mean 2073.6 ms (+/- 98.29) [n=107] | Off-peak mean 2034.68 ms (+/- 197.01) [n=107]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 284.09 ms |
| Median Latency | 272 ms |
| Min Latency | 231 ms |
| Max Latency | 1205 ms |
| 95th Percentile | 312 ms |
| Std Deviation | +/- 71.49 ms |
| Spike Count | 14 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 214 |

Trend: == STABLE (short 269ms vs long 269.4ms; n=10/20)
Sparkline (last 30): @-.=::+-.=.- .* :.:.. ... -=.:
Hourly Latency Sparkline: #####     ##@##########*

Time-of-day Baselines: Peak mean 279.7 ms (+/- 26.64) [n=107] | Off-peak mean 288.48 ms (+/- 97.58) [n=107]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 99.53% |
| Mean Latency | 260.19 ms |
| Median Latency | 217 ms |
| Min Latency | 210 ms |
| Max Latency | 5031 ms |
| 95th Percentile | 249 ms |
| Std Deviation | +/- 381.55 ms |
| Spike Count | 18 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 214 |

Trend: == STABLE (short 216.2ms vs long 217.3ms; n=10/20)
Sparkline (last 30): -:+-=-@::@%:#.-:#- .:-.-=.:== 
Hourly Latency Sparkline: -----     ------=*-@----

Time-of-day Baselines: Peak mean 298.54 ms (+/- 538) [n=107] | Off-peak mean 221.83 ms (+/- 11.13) [n=107]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 239 |
| Unique Tasks |  |
| Avg Quality | ?뵶 0.693 |
| Success Rate | ?윟 100% |
| Replan Rate | 39.61% |
| Last Activity | 0.8 minutes ago |

**[WARN] AGI System Alerts:**

- ?뵶 CRITICAL AGI Replan Rate: 39.61% (threshold: 10%)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 214 | 0 | 0 | 8 |
| Cloud   | 0 | 0 | 0 | 0 | 14 |
| Gateway | 0 | 0 | 0 | 0 | 18 |
| Total   | 0 | 214 | 0 | 0 | 40 |
---

### Alert Severity Details

#### [!] Critical (4)

| Timestamp | Message |
|-----------|---------|
| 08:03:07 | ALERT: Cloud AI latency 1205ms |
| 11:13:26 | Local LLM offline (0) |
| 13:03:10 | ALERT: Lumen Gateway latency 2985ms |
| 15:08:10 | Lumen Gateway offline (0) |

#### [i] Info (467)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:                @  @ @ @     
Warnings:  %%%@*      ##%#*####%#%# 
Spikes:    *==@.       -=-... .*.#- 
---

### Availability Trend (hourly)

Local:     @@@@@     @@@@@%@@@@@@@@
Cloud:     @@@@@     @@@@@@@@@@@@@@
Gateway:   @@@@@     @@@@@@@@@%@@@@
---

## Recommendations

- **[CRITICAL]** 4 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **[MEDIUM] Local LLM**: High latency detected (avg 2054.14ms).
  - Action: Check LM Studio process CPU/GPU usage and memory
  - Action: Consider model optimization or hardware upgrade
  - Action: Review recent logs for performance degradation patterns
- **Spikes**: 40 latency spikes detected. Review system load and resource allocation.
- **[MEDIUM] AGI System**: Low quality score (0.693).
  - Action: Review recent AGI task outputs for errors
  - Action: Check persona LLM configuration and prompts
  - Action: Verify synthesis/antithesis/thesis pipeline
- **[HIGH] AGI System**: High replan rate (39.61%).
  - Action: Investigate task complexity and initial planning quality
  - Action: Review rune event logs for replan patterns
  - Action: Consider adjusting AGI planning parameters

---

_Report generated by unified monitoring dashboard_