# Monitoring Report

**Generated**: 2025-10-31 21:54:16
**Time Window**: Last 24 hours
**Data Points**: 212 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.69%  |  Alerts: 4  |  Warnings: 188  |  Spikes: 40

  Alert Severity:
    [!] Critical: 4  |  [*] Warning: 0  |  [i] Info: 419

  Local LLM:     99.53% avail  |  1834.59ms mean
  Cloud AI:      100% avail  |  283.48ms mean
  Lumen Gateway: 99.53% avail  |  261.1ms mean

  --- vs Previous Period (24h ago) ---
  Local:   Latency 10.5%  |  Avail 0.5%
  Cloud:   Latency ▲2.4%  |  Avail =
  Gateway: Latency ▲2.5%  |  Avail 0.5%
```

---

## Report Configuration

- **Time Window**: Last 24 hours
- **Peak Hours**: -
- **Sparkline Length**: 30
- **Data Points**: 212 snapshots

---

## Overall Health

- **Status**: EXCELLENT
- **Average Availability**: 99.69%
- **Alerts**: 4
- **Warnings**: 188
- **Spikes**: 40

---

## Channel Statistics

### Local LLM (LM Studio)

| Metric | Value |
|--------|-------|
| Availability | 99.53% |
| Mean Latency | 1834.59 ms |
| Median Latency | 2060 ms |
| Min Latency | 18 ms |
| Max Latency | 3076 ms |
| 95th Percentile | 2080 ms |
| Std Deviation | +/- 653.31 ms |
| Spike Count | 8 |
| Baseline Alerts | 0 |
| Baseline Warns | 191 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 212 |

Trend: == STABLE (short 21.6ms vs long 21ms; n=10/20)
Sparkline (last 30): %%%%%@                        
Hourly Latency Sparkline: %%%     %%%%%@%%%%%%%#  

Time-of-day Baselines: Peak mean 2073.6 ms (+/- 98.29) [n=107] | Off-peak mean 1591.03 ms (+/- 858.74) [n=105]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 283.48 ms |
| Median Latency | 272 ms |
| Min Latency | 231 ms |
| Max Latency | 1205 ms |
| 95th Percentile | 315 ms |
| Std Deviation | +/- 68.68 ms |
| Spike Count | 15 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 212 |

Trend: == STABLE (short 289.2ms vs long 279.3ms; n=10/20)
Sparkline (last 30):         @             .::. .  
Hourly Latency Sparkline: ###     *#@####**###**##

Time-of-day Baselines: Peak mean 279.7 ms (+/- 26.64) [n=107] | Off-peak mean 287.32 ms (+/- 93.89) [n=105]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 99.53% |
| Mean Latency | 261.1 ms |
| Median Latency | 218 ms |
| Min Latency | 210 ms |
| Max Latency | 5031 ms |
| 95th Percentile | 253 ms |
| Std Deviation | +/- 383.29 ms |
| Spike Count | 17 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 212 |

Trend: == STABLE (short 226.8ms vs long 224.4ms; n=10/20)
Sparkline (last 30): .. .:: :.::. .-.--:-..:.-@%.::
Hourly Latency Sparkline: ---     ------=*-@------

Time-of-day Baselines: Peak mean 298.54 ms (+/- 538) [n=107] | Off-peak mean 222.95 ms (+/- 11.42) [n=105]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 698 |
| Unique Tasks |  |
| Avg Quality | ?뵶 0.697 |
| Success Rate | ?윟 100% |
| Replan Rate | 39.51% |
| Last Activity | 1.2 hours ago |

**[WARN] AGI System Alerts:**

- ?뵶 CRITICAL AGI Replan Rate: 39.51% (threshold: 10%)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 191 | 0 | 0 | 8 |
| Cloud   | 0 | 0 | 0 | 0 | 15 |
| Gateway | 0 | 0 | 0 | 0 | 17 |
| Total   | 0 | 191 | 0 | 0 | 40 |
---

### Alert Severity Details

#### [!] Critical (4)

| Timestamp | Message |
|-----------|---------|
| 08:03:07 | ALERT: Cloud AI latency 1205ms |
| 11:13:26 | Local LLM offline (0) |
| 13:03:10 | ALERT: Lumen Gateway latency 2985ms |
| 15:08:10 | Lumen Gateway offline (0) |

#### [i] Info (419)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:              @  @ @ @       
Warnings:  %@+     .#%%#*%###%%%# . 
Spikes:    =#.       -*.... .*-*--@ 
---

### Availability Trend (hourly)

Local:     @@@     @@@@@%@@@@@@@@@@
Cloud:     @@@     @@@@@@@@@@@@@@@@
Gateway:   @@@     @@@@@@@@@%@@@@@@
---

## Recommendations

- **[CRITICAL]** 4 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **[MEDIUM] Local LLM**: High latency detected (avg 1834.59ms).
  - Action: Check LM Studio process CPU/GPU usage and memory
  - Action: Consider model optimization or hardware upgrade
  - Action: Review recent logs for performance degradation patterns
- **Spikes**: 40 latency spikes detected. Review system load and resource allocation.
- **[MEDIUM] AGI System**: Low quality score (0.697).
  - Action: Review recent AGI task outputs for errors
  - Action: Check persona LLM configuration and prompts
  - Action: Verify synthesis/antithesis/thesis pipeline
- **[HIGH] AGI System**: High replan rate (39.51%).
  - Action: Investigate task complexity and initial planning quality
  - Action: Review rune event logs for replan patterns
  - Action: Consider adjusting AGI planning parameters

---

_Report generated by unified monitoring dashboard_