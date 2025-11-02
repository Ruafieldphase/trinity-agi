# Monitoring Report

**Generated**: 2025-11-02 16:03:21
**Time Window**: Last 24 hours
**Data Points**: 288 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.65%  |  Alerts: 3  |  Warnings: 0  |  Spikes: 65

  Alert Severity:
    [!] Critical: 3  |  [*] Warning: 0  |  [i] Info: 65

  Local LLM:     98.96% avail  |  42.49ms mean
  Cloud AI:      100% avail  |  266.65ms mean
  Lumen Gateway: 100% avail  |  224.26ms mean
  Resonance Policy: mode=observe active=ops-safety last=quality-first | allow=1 warn=50 block=0
  Last Task: 147ms
  AGI Eval: min_quality=0.6

  --- vs Previous Period (24h ago) ---
  Local:   Latency 90.9%  |  Avail 1.0%
  Cloud:   Latency 2.6%  |  Avail ▲0.5%
  Gateway: Latency 4.5%  |  Avail =
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
- **Alerts**: 3
- **Warnings**: 0
- **Spikes**: 65

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
| Availability | 98.96% |
| Mean Latency | 42.49 ms |
| Median Latency | 21 ms |
| Min Latency | 16 ms |
| Max Latency | 3030 ms |
| 95th Percentile | 30 ms |
| Std Deviation | +/- 250.26 ms |
| Spike Count | 22 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 21.9ms vs long 22.2ms; n=10/20)
Sparkline (last 30): +::: .: = ... @     .- :. :   
Hourly Latency Sparkline:      %          @       

Time-of-day Baselines: Peak mean 21.63 ms (+/- 4.12) [n=108] | Off-peak mean 55.01 ms (+/- 316.2) [n=180]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 266.65 ms |
| Median Latency | 271 ms |
| Min Latency | 219 ms |
| Max Latency | 336 ms |
| 95th Percentile | 305 ms |
| Std Deviation | +/- 23.27 ms |
| Spike Count | 22 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 277.2ms vs long 274.8ms; n=10/20)
Sparkline (last 30): .+= ==++= .+@ *==++++==-=%+#+=
Hourly Latency Sparkline: **%@.+=:-. **%#+##*+*++#

Time-of-day Baselines: Peak mean 271.34 ms (+/- 16.91) [n=108] | Off-peak mean 263.84 ms (+/- 26) [n=180]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 224.26 ms |
| Median Latency | 222 ms |
| Min Latency | 210 ms |
| Max Latency | 267 ms |
| 95th Percentile | 240 ms |
| Std Deviation | +/- 9.1 ms |
| Spike Count | 21 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 219.1ms vs long 220.2ms; n=10/20)
Sparkline (last 30): @.:-=.:*: =-: =:.=.=::. =::.:.
Hourly Latency Sparkline: .--..:@ #:+#+#*=::..+=: 

Time-of-day Baselines: Peak mean 222.57 ms (+/- 7.57) [n=108] | Off-peak mean 225.27 ms (+/- 9.79) [n=180]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 1450 |
| Unique Tasks |  |
| Avg Quality | ?�� 0.713 |
| Success Rate | ?�� 100% |
| Replan Rate | 36.57% |
| Last Activity | 27 minutes ago |

**[WARN] AGI System Alerts:**

- ?�� CRITICAL AGI Replan Rate: 36.57% (threshold: 10%)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 0 | 22 |
| Cloud   | 0 | 0 | 0 | 0 | 22 |
| Gateway | 0 | 0 | 0 | 0 | 21 |
| Total   | 0 | 0 | 0 | 0 | 65 |
---

### Alert Severity Details

#### [!] Critical (3)

| Timestamp | Message |
|-----------|---------|
| 21:18:09 | Local LLM offline (0) |
| 08:23:16 | Local LLM offline (0) |
| 14:38:08 | Local LLM offline (503) |

#### [i] Info (65)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:         @          @     @  
Warnings:   -@..+@-*..@.+..:-::--:. 
Spikes:     -@..+@-*..@.+..:-::--:. 
---

### Availability Trend (hourly)

Local:     @@@@@ @@@@@@@@@@ @@@@@ @
Cloud:     ------------------------
Gateway:   ------------------------
---

## Recommendations

- **[CRITICAL]** 3 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **Spikes**: 65 latency spikes detected. Review system load and resource allocation.
- **[HIGH] AGI System**: High replan rate (36.57%).
  - Action: Investigate task complexity and initial planning quality
  - Action: Review rune event logs for replan patterns
  - Action: Consider adjusting AGI planning parameters

---

_Report generated by unified monitoring dashboard_