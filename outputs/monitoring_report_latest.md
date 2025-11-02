# Monitoring Report

**Generated**: 2025-11-02 22:40:19
**Time Window**: Last 24 hours
**Data Points**: 290 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.66%  |  Alerts: 4  |  Warnings: 1  |  Spikes: 63

  Alert Severity:
    [!] Critical: 4  |  [*] Warning: 0  |  [i] Info: 64

  Local LLM:     98.97% avail  |  42.66ms mean
  Cloud AI:      100% avail  |  267.78ms mean
  Lumen Gateway: 100% avail  |  233.43ms mean
  Resonance Policy: mode=observe active=latency-first last=quality-first | allow=20 warn=82 block=0
  Last Task: 1330ms

  --- vs Previous Period (24h ago) ---
  Local:   Latency 5.3%  |  Avail 0.6%
  Cloud:   Latency 1.4%  |  Avail ▲0.5%
  Gateway: Latency 1.1%  |  Avail =
```

---

## Report Configuration

- **Time Window**: Last 24 hours
- **Peak Hours**: -
- **Sparkline Length**: 30
- **Data Points**: 290 snapshots

---

## Overall Health

- **Status**: EXCELLENT
- **Average Availability**: 99.66%
- **Alerts**: 4
- **Warnings**: 1
- **Spikes**: 63

---

## Performance Snapshot

- **Systems Considered**: 6
- **Overall Success**: 77.8%  |  **Effective**: 93.3%
- **Bands**: Excellent=4  Good=0  Needs=1  NoData=1
- **Top Attention**: Orchestration (66.7%)
- See: performance_dashboard_latest.md
---

## Channel Statistics

### Local LLM (LM Studio)

| Metric | Value |
|--------|-------|
| Availability | 98.97% |
| Mean Latency | 42.66 ms |
| Median Latency | 21 ms |
| Min Latency | 16 ms |
| Max Latency | 3051 ms |
| 95th Percentile | 31 ms |
| Std Deviation | +/- 250.26 ms |
| Spike Count | 23 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 290 |

Trend: == STABLE (short 22.6ms vs long 21.45ms; n=10/20)
Sparkline (last 30):  . :       .::   . %.@  :##: *
Hourly Latency Sparkline:          @         %    

Time-of-day Baselines: Peak mean 49.72 ms (+/- 291.53) [n=108] | Off-peak mean 38.47 ms (+/- 222.96) [n=182]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 267.78 ms |
| Median Latency | 271 ms |
| Min Latency | 222 ms |
| Max Latency | 398 ms |
| 95th Percentile | 307 ms |
| Std Deviation | +/- 23.97 ms |
| Spike Count | 21 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 290 |

Trend: == STABLE (short 262ms vs long 272.1ms; n=10/20)
Sparkline (last 30): ::=::=:::::::::: :@:- : ::-:  
Hourly Latency Sparkline:  :: :#@#**###=*+**#*#***

Time-of-day Baselines: Peak mean 272.41 ms (+/- 18.37) [n=108] | Off-peak mean 265.03 ms (+/- 26.41) [n=182]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 233.43 ms |
| Median Latency | 222 ms |
| Min Latency | 210 ms |
| Max Latency | 2410 ms |
| 95th Percentile | 244 ms |
| Std Deviation | +/- 131.72 ms |
| Spike Count | 19 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 290 |

Trend: == STABLE (short 220.4ms vs long 220.35ms; n=10/20)
Sparkline (last 30): *.=+@:..*# .%+=== = -*.:-: *-=
Hourly Latency Sparkline:                  .   @  

Time-of-day Baselines: Peak mean 226.89 ms (+/- 47.58) [n=108] | Off-peak mean 237.31 ms (+/- 162.25) [n=182]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 3034 |
| Unique Tasks |  |
| Avg Quality | ?�� 0.724 |
| Success Rate | ?�� 100% |
| Replan Rate | 33.61% |
| Last Activity | 59.5 minutes ago |

**[WARN] AGI System Alerts:**

- ?�� CRITICAL AGI Replan Rate: 33.61% (threshold: 10%)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 0 | 23 |
| Cloud   | 0 | 0 | 0 | 0 | 21 |
| Gateway | 0 | 0 | 0 | 0 | 19 |
| Total   | 0 | 0 | 0 | 0 | 63 |
---

### Alert Severity Details

#### [!] Critical (4)

| Timestamp | Message |
|-----------|---------|
| 08:23:16 | Local LLM offline (0) |
| 14:38:08 | Local LLM offline (503) |
| 17:53:29 | Local LLM offline (0) |
| 20:03:07 | ALERT: Lumen Gateway latency 2410ms |

#### [i] Info (64)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:             @     @   @ @   
Warnings:  -=#.@-=..==.===..*-=@= * 
Spikes:    -=#.@-=..==.===..=-=@= * 
---

### Availability Trend (hourly)

Local:     @@@@@@@@@ @@@@@ @@@ @@@@
Cloud:     ------------------------
Gateway:   ------------------------
---

## Recommendations

- **[CRITICAL]** 4 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **Spikes**: 63 latency spikes detected. Review system load and resource allocation.
- **[HIGH] AGI System**: High replan rate (33.61%).
  - Action: Investigate task complexity and initial planning quality
  - Action: Review rune event logs for replan patterns
  - Action: Consider adjusting AGI planning parameters

---

_Report generated by unified monitoring dashboard_