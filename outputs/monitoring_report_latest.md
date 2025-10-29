# Monitoring Report

**Generated**: 2025-10-29 20:15:06
**Time Window**: Last 24 hours
**Data Points**: 286 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.88%  |  Alerts: 3  |  Warnings: 287  |  Spikes: 60

  Alert Severity:
    [!] Critical: 3  |  [*] Warning: 0  |  [i] Info: 633

  Local LLM:     100% avail  |  2060.37ms mean
  Cloud AI:      99.65% avail  |  281.47ms mean
  Lumen Gateway: 100% avail  |  254.8ms mean

  --- vs Previous Period (24h ago) ---
  Local:   Latency ▲2.2%  |  Avail =
  Cloud:   Latency ▲1.2%  |  Avail 0.4%
  Gateway: Latency ▲2%  |  Avail =
```

---

## Report Configuration

- **Time Window**: Last 24 hours
- **Peak Hours**: -
- **Sparkline Length**: 30
- **Data Points**: 286 snapshots

---

## Overall Health

- **Status**: EXCELLENT
- **Average Availability**: 99.88%
- **Alerts**: 3
- **Warnings**: 287
- **Spikes**: 60

---

## Channel Statistics

### Local LLM (LM Studio)

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 2060.37 ms |
| Median Latency | 2060 ms |
| Min Latency | 2036 ms |
| Max Latency | 2093 ms |
| 95th Percentile | 2073 ms |
| Std Deviation | +/- 7.79 ms |
| Spike Count | 16 |
| Baseline Alerts | 0 |
| Baseline Warns | 286 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 286 |

Trend: == STABLE (short 2058.6ms vs long 2060.2ms; n=10/20)
Sparkline (last 30): =+:*-=-===.=-=-=:@:=:.=*: =--#
Hourly Latency Sparkline: :=*:-=**+-#*- :@.+:*#*#-

Time-of-day Baselines: Peak mean 2060.03 ms (+/- 8.48) [n=107] | Off-peak mean 2060.58 ms (+/- 7.37) [n=179]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 99.65% |
| Mean Latency | 281.47 ms |
| Median Latency | 274 ms |
| Min Latency | 222 ms |
| Max Latency | 721 ms |
| 95th Percentile | 313 ms |
| Std Deviation | +/- 32.26 ms |
| Spike Count | 23 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 286 |

Trend: == STABLE (short 275.2ms vs long 274.4ms; n=10/20)
Sparkline (last 30): --=-=---=* @-*------*--+*==- =
Hourly Latency Sparkline: # =%*=-:::-..-=.  - @ ..

Time-of-day Baselines: Peak mean 279.71 ms (+/- 45.7) [n=107] | Off-peak mean 282.52 ms (+/- 20.47) [n=179]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 254.8 ms |
| Median Latency | 222 ms |
| Min Latency | 213 ms |
| Max Latency | 4716 ms |
| 95th Percentile | 248 ms |
| Std Deviation | +/- 348.75 ms |
| Spike Count | 21 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 286 |

Trend: == STABLE (short 220.5ms vs long 221.55ms; n=10/20)
Sparkline (last 30): ::=--.:  .  -=-..@ #.::.-.:.- 
Hourly Latency Sparkline:                @    #   

Time-of-day Baselines: Peak mean 301.01 ms (+/- 568.66) [n=107] | Off-peak mean 227.18 ms (+/- 11.19) [n=179]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 1609 |
| Unique Tasks |  |
| Avg Quality | ?윞 0.736 |
| Success Rate | ?윞 74.77% |
| Replan Rate | 28.28% |
| Last Activity | 48.7 minutes ago |

**[WARN] AGI System Alerts:**

- ?뵶 CRITICAL AGI Replan Rate: 28.28% (threshold: 10%)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 286 | 0 | 0 | 16 |
| Cloud   | 0 | 0 | 0 | 0 | 23 |
| Gateway | 0 | 0 | 0 | 0 | 21 |
| Total   | 0 | 286 | 0 | 0 | 60 |
---

### Alert Severity Details

#### [!] Critical (3)

| Timestamp | Message |
|-----------|---------|
| 11:55:09 | ALERT: Lumen Gateway latency 4716ms |
| 12:50:05 | Cloud AI offline (429) |
| 17:10:09 | ALERT: Lumen Gateway latency 4061ms |

#### [i] Info (633)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:                   @@   @    
Warnings:  %%@%%%%#%#%#%#%%%%#%%#%# 
Spikes:    -#@----.+.# -+#-+#.#+ @. 
---

### Availability Trend (hourly)

Local:     ------------------------
Cloud:     @@@@@@@@@@@@@@@@ @@@@@@@
Gateway:   ------------------------
---

## Recommendations

- **[CRITICAL]** 3 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **[MEDIUM] Local LLM**: High latency detected (avg 2060.37ms).
  - Action: Check LM Studio process CPU/GPU usage and memory
  - Action: Consider model optimization or hardware upgrade
  - Action: Review recent logs for performance degradation patterns
- **Spikes**: 60 latency spikes detected. Review system load and resource allocation.
- **[HIGH] AGI System**: High replan rate (28.28%).
  - Action: Investigate task complexity and initial planning quality
  - Action: Review rune event logs for replan patterns
  - Action: Consider adjusting AGI planning parameters

---

_Report generated by unified monitoring dashboard_