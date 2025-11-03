# Monitoring Report

**Generated**: 2025-11-03 10:18:25
**Time Window**: Last 24 hours
**Data Points**: 205 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.67%  |  Alerts: 3  |  Warnings: 1  |  Spikes: 46

  Alert Severity:
    [!] Critical: 3  |  [*] Warning: 0  |  [i] Info: 48

  Local LLM:     99.02% avail  |  36.81ms mean
  Cloud AI:      100% avail  |  270.9ms mean
  Lumen Gateway: 100% avail  |  237.56ms mean
  Resonance Policy: mode=observe active=latency-first last=quality-first | allow=27 warn=59 block=0
  Last Task: 18758ms

  --- vs Previous Period (24h ago) ---
  Local:   Latency 25.1%  |  Avail 0.3%
  Cloud:   Latency ▲1.6%  |  Avail ▲0.4%
  Gateway: Latency ▲1.6%  |  Avail =
```

---

## Report Configuration

- **Time Window**: Last 24 hours
- **Peak Hours**: -
- **Sparkline Length**: 30
- **Data Points**: 205 snapshots

---

## Overall Health

- **Status**: EXCELLENT
- **Average Availability**: 99.67%
- **Alerts**: 3
- **Warnings**: 1
- **Spikes**: 46

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
| Availability | 99.02% |
| Mean Latency | 36.81 ms |
| Median Latency | 20 ms |
| Min Latency | 16 ms |
| Max Latency | 3051 ms |
| 95th Percentile | 38 ms |
| Std Deviation | +/- 211.63 ms |
| Spike Count | 16 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 1 |
| Sample Count | 205 |

Trend: == STABLE (short 21.6ms vs long 21.55ms; n=10/20)
Sparkline (last 30): ...-:   .   . . #:.   @.-.   .
Hourly Latency Sparkline:        @                

Time-of-day Baselines: Peak mean 49.53 ms (+/- 288.84) [n=110] | Off-peak mean 22.08 ms (+/- 6.62) [n=95]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 270.9 ms |
| Median Latency | 272 ms |
| Min Latency | 226 ms |
| Max Latency | 398 ms |
| 95th Percentile | 307 ms |
| Std Deviation | +/- 22.9 ms |
| Spike Count | 15 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 205 |

Trend: == STABLE (short 251.6ms vs long 265.55ms; n=10/20)
Sparkline (last 30):     .. + #:#+@=-.+++-*.-. .  :
Hourly Latency Sparkline: %%%%%%@%%%%%%%#       %%

Time-of-day Baselines: Peak mean 270.69 ms (+/- 19.12) [n=110] | Off-peak mean 271.15 ms (+/- 26.73) [n=95]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 237.56 ms |
| Median Latency | 223 ms |
| Min Latency | 211 ms |
| Max Latency | 2410 ms |
| 95th Percentile | 243 ms |
| Std Deviation | +/- 156.46 ms |
| Spike Count | 15 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 205 |

Trend: == STABLE (short 230.2ms vs long 230.5ms; n=10/20)
Sparkline (last 30): .. :. -..:. ::+.+ @. .:-  *=+-
Hourly Latency Sparkline: ==+===+=+@==++=       =+

Time-of-day Baselines: Peak mean 228.33 ms (+/- 47.21) [n=110] | Off-peak mean 248.24 ms (+/- 224.34) [n=95]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 2702 |
| Unique Tasks |  |
| Avg Quality | ?�� 0.729 |
| Success Rate | ?�� 100% |
| Replan Rate | 32.46% |
| Last Activity | 12.9 minutes ago |

**[WARN] AGI System Alerts:**

- ?�� CRITICAL AGI Replan Rate: 32.46% (threshold: 10%)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 1 | 16 |
| Cloud   | 0 | 0 | 0 | 0 | 15 |
| Gateway | 0 | 0 | 0 | 0 | 15 |
| Total   | 0 | 0 | 0 | 1 | 46 |
---

### Alert Severity Details

#### [!] Critical (3)

| Timestamp | Message |
|-----------|---------|
| 14:38:08 | Local LLM offline (503) |
| 17:53:29 | Local LLM offline (0) |
| 20:03:07 | ALERT: Lumen Gateway latency 2410ms |

#### [i] Info (48)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:        @  @ @               
Warnings:  +-+---++#@.+##        @- 
Spikes:    +-+----+#@.+#+        @- 
---

### Availability Trend (hourly)

Local:     @@@@%@@%@@@@@@@       @@
Cloud:     @@@@@@@@@@@@@@@       @@
Gateway:   @@@@@@@@@@@@@@@       @@
---

## Recommendations

- **[CRITICAL]** 3 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **Spikes**: 46 latency spikes detected. Review system load and resource allocation.
- **[HIGH] AGI System**: High replan rate (32.46%).
  - Action: Investigate task complexity and initial planning quality
  - Action: Review rune event logs for replan patterns
  - Action: Consider adjusting AGI planning parameters

---

_Report generated by unified monitoring dashboard_