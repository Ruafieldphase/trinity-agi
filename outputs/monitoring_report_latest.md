# Monitoring Report

**Generated**: 2025-11-02 03:25:07
**Time Window**: Last 24 hours
**Data Points**: 262 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.75%  |  Alerts: 3  |  Warnings: 1  |  Spikes: 71

  Alert Severity:
    [!] Critical: 3  |  [*] Warning: 0  |  [i] Info: 72

  Local LLM:     99.62% avail  |  40.32ms mean
  Cloud AI:      99.62% avail  |  264.61ms mean
  Lumen Gateway: 100% avail  |  233.45ms mean
  Resonance Policy: mode=observe policy=quality-first | allow=0 warn=9 block=0

  --- vs Previous Period (24h ago) ---
  Local:   Latency 97.6%  |  Avail ▲0.1%
  Cloud:   Latency 6.5%  |  Avail 0.4%
  Gateway: Latency 11.6%  |  Avail ▲0.5%
```

---

## Report Configuration

- **Time Window**: Last 24 hours
- **Peak Hours**: -
- **Sparkline Length**: 30
- **Data Points**: 262 snapshots

---

## Overall Health

- **Status**: EXCELLENT
- **Average Availability**: 99.75%
- **Alerts**: 3
- **Warnings**: 1
- **Spikes**: 71

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
| Availability | 99.62% |
| Mean Latency | 40.32 ms |
| Median Latency | 20 ms |
| Min Latency | 17 ms |
| Max Latency | 3030 ms |
| 95th Percentile | 29 ms |
| Std Deviation | +/- 224.36 ms |
| Spike Count | 23 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 262 |

Trend: == STABLE (short 22.6ms vs long 22ms; n=10/20)
Sparkline (last 30): .  ..-*.....:..=.:.....: .-:@.
Hourly Latency Sparkline:        *         @      

Time-of-day Baselines: Peak mean 39.59 ms (+/- 196.75) [n=108] | Off-peak mean 40.82 ms (+/- 242.49) [n=154]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 99.62% |
| Mean Latency | 264.61 ms |
| Median Latency | 268 ms |
| Min Latency | 219 ms |
| Max Latency | 336 ms |
| 95th Percentile | 301 ms |
| Std Deviation | +/- 22.92 ms |
| Spike Count | 24 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 262 |

Trend: == STABLE (short 232ms vs long 233.3ms; n=10/20)
Sparkline (last 30): .%#:+=:=-:#.:+:.-: .:.  : .::@
Hourly Latency Sparkline:   %%%%%%%%%%%%%@%#%#####

Time-of-day Baselines: Peak mean 271.1 ms (+/- 18.44) [n=108] | Off-peak mean 260.06 ms (+/- 24.65) [n=154]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 233.45 ms |
| Median Latency | 220 ms |
| Min Latency | 210 ms |
| Max Latency | 3043 ms |
| 95th Percentile | 245 ms |
| Std Deviation | +/- 174.52 ms |
| Spike Count | 24 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 262 |

Trend: == STABLE (short 226.6ms vs long 225.75ms; n=10/20)
Sparkline (last 30): #--*-= =.=--=+-=@#=.@.:%#=:=*%
Hourly Latency Sparkline:   =========@============

Time-of-day Baselines: Peak mean 247.55 ms (+/- 271.65) [n=108] | Off-peak mean 223.56 ms (+/- 10.53) [n=154]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 665 |
| Unique Tasks |  |
| Avg Quality | ?占쏙옙 0.703 |
| Success Rate | ?占쏙옙 100% |
| Replan Rate | 40.5% |
| Last Activity | 5.4 hours ago |

**[WARN] AGI System Alerts:**

- ?占쏙옙 CRITICAL AGI Replan Rate: 40.5% (threshold: 10%)
- ?占쏙옙 WARNING AGI Inactive: 5.4 hours since last activity (threshold: 2h)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 0 | 23 |
| Cloud   | 0 | 0 | 0 | 0 | 24 |
| Gateway | 0 | 0 | 0 | 0 | 24 |
| Total   | 0 | 0 | 0 | 0 | 71 |
---

### Alert Severity Details

#### [!] Critical (3)

| Timestamp | Message |
|-----------|---------|
| 12:43:04 | Cloud AI offline (429) |
| 15:08:07 | ALERT: Lumen Gateway latency 3043ms |
| 21:18:09 | Local LLM offline (0) |

#### [i] Info (72)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:             @ @     @       
Warnings:    -=@==*.*#=--*#.==@=*-= 
Spikes:      -=@===.*#=--*#.==@=*-= 
---

### Availability Trend (hourly)

Local:       @@@@@@@@@@@@@@@%@@@@@@
Cloud:       @@@@@@@%@@@@@@@@@@@@@@
Gateway:     @@@@@@@@@@@@@@@@@@@@@@
---

## Recommendations

- **[CRITICAL]** 3 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **Spikes**: 71 latency spikes detected. Review system load and resource allocation.
- **[HIGH] AGI System**: High replan rate (40.5%).
  - Action: Investigate task complexity and initial planning quality
  - Action: Review rune event logs for replan patterns
  - Action: Consider adjusting AGI planning parameters

---

_Report generated by unified monitoring dashboard_