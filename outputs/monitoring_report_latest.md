# Monitoring Report

**Generated**: 2025-11-02 14:02:49
**Time Window**: Last 24 hours
**Data Points**: 288 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.77%  |  Alerts: 3  |  Warnings: 0  |  Spikes: 69

  Alert Severity:
    [!] Critical: 3  |  [*] Warning: 0  |  [i] Info: 69

  Local LLM:     99.31% avail  |  42.35ms mean
  Cloud AI:      100% avail  |  267.24ms mean
  Lumen Gateway: 100% avail  |  234.31ms mean
  Resonance Policy: mode=observe active=ops-safety last=quality-first | allow=0 warn=48 block=0
  Last Task: 24024ms
  AGI Eval: min_quality=0.6

  --- vs Previous Period (24h ago) ---
  Local:   Latency 94%  |  Avail 0.7%
  Cloud:   Latency 2.2%  |  Avail ▲0.5%
  Gateway: Latency 3.9%  |  Avail ▲0.5%
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
- **Average Availability**: 99.77%
- **Alerts**: 3
- **Warnings**: 0
- **Spikes**: 69

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
| Availability | 99.31% |
| Mean Latency | 42.35 ms |
| Median Latency | 20 ms |
| Min Latency | 16 ms |
| Max Latency | 3030 ms |
| 95th Percentile | 29 ms |
| Std Deviation | +/- 250.27 ms |
| Spike Count | 24 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 23.3ms vs long 23.15ms; n=10/20)
Sparkline (last 30): :. .  ::@ :.-:.:.  =.  ::*::: 
Hourly Latency Sparkline:        %          @     

Time-of-day Baselines: Peak mean 21.26 ms (+/- 3.61) [n=108] | Off-peak mean 55.01 ms (+/- 316.2) [n=180]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 267.24 ms |
| Median Latency | 271 ms |
| Min Latency | 219 ms |
| Max Latency | 336 ms |
| 95th Percentile | 305 ms |
| Std Deviation | +/- 23.49 ms |
| Spike Count | 22 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 265.3ms vs long 270.1ms; n=10/20)
Sparkline (last 30): *=.+.+.+ +++@ +@+#+++*+*=.++ +
Hourly Latency Sparkline: #**+#@.==::. =#%*=#**+++

Time-of-day Baselines: Peak mean 272.92 ms (+/- 17.23) [n=108] | Off-peak mean 263.84 ms (+/- 26) [n=180]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 234.31 ms |
| Median Latency | 223 ms |
| Min Latency | 210 ms |
| Max Latency | 3043 ms |
| 95th Percentile | 243 ms |
| Std Deviation | +/- 166.34 ms |
| Spike Count | 23 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 227ms vs long 227.7ms; n=10/20)
Sparkline (last 30): .: . .   ..@.. :.=.  ...#-  ..
Hourly Latency Sparkline:  @                      

Time-of-day Baselines: Peak mean 249.38 ms (+/- 271.46) [n=108] | Off-peak mean 225.27 ms (+/- 9.79) [n=180]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 1356 |
| Unique Tasks |  |
| Avg Quality | ?�� 0.712 |
| Success Rate | ?�� 100% |
| Replan Rate | 36.73% |
| Last Activity | 4.4 hours ago |

**[WARN] AGI System Alerts:**

- ?�� CRITICAL AGI Replan Rate: 36.73% (threshold: 10%)
- ?�� WARNING AGI Inactive: 4.4 hours since last activity (threshold: 2h)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 0 | 24 |
| Cloud   | 0 | 0 | 0 | 0 | 22 |
| Gateway | 0 | 0 | 0 | 0 | 23 |
| Total   | 0 | 0 | 0 | 0 | 69 |
---

### Alert Severity Details

#### [!] Critical (3)

| Timestamp | Message |
|-----------|---------|
| 15:08:07 | ALERT: Lumen Gateway latency 3043ms |
| 21:18:09 | Local LLM offline (0) |
| 08:23:16 | Local LLM offline (0) |

#### [i] Info (69)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:     @     @          @      
Warnings:  -::-#:.+@-*..@.-:.:-.--- 
Spikes:    -::-#:.+@-*..@.-:.:-.--- 
---

### Availability Trend (hourly)

Local:     @@@@@@@ @@@@@@@@@@ @@@@@
Cloud:     ------------------------
Gateway:   ------------------------
---

## Recommendations

- **[CRITICAL]** 3 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **Spikes**: 69 latency spikes detected. Review system load and resource allocation.
- **[HIGH] AGI System**: High replan rate (36.73%).
  - Action: Investigate task complexity and initial planning quality
  - Action: Review rune event logs for replan patterns
  - Action: Consider adjusting AGI planning parameters

---

_Report generated by unified monitoring dashboard_