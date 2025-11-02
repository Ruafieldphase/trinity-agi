# Monitoring Report

**Generated**: 2025-11-02 07:43:51
**Time Window**: Last 24 hours
**Data Points**: 288 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.77%  |  Alerts: 3  |  Warnings: 1  |  Spikes: 76

  Alert Severity:
    [!] Critical: 3  |  [*] Warning: 0  |  [i] Info: 77

  Local LLM:     99.65% avail  |  38.74ms mean
  Cloud AI:      99.65% avail  |  266.66ms mean
  Lumen Gateway: 100% avail  |  233.47ms mean
  Resonance Policy: mode=observe active=ops-safety last=quality-first | allow=0 warn=15 block=0

  --- vs Previous Period (24h ago) ---
  Local:   Latency 97.3%  |  Avail ▲0.1%
  Cloud:   Latency 5.4%  |  Avail 0.4%
  Gateway: Latency 10.8%  |  Avail ▲0.5%
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
- **Warnings**: 1
- **Spikes**: 76

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
| Availability | 99.65% |
| Mean Latency | 38.74 ms |
| Median Latency | 20 ms |
| Min Latency | 17 ms |
| Max Latency | 3030 ms |
| 95th Percentile | 29 ms |
| Std Deviation | +/- 214.02 ms |
| Spike Count | 24 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 20.8ms vs long 21.45ms; n=10/20)
Sparkline (last 30): ::.-.-:.:@:..:..=.....  .:- ..
Hourly Latency Sparkline:    *         @          

Time-of-day Baselines: Peak mean 39.59 ms (+/- 196.75) [n=108] | Off-peak mean 38.23 ms (+/- 224.28) [n=180]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 99.65% |
| Mean Latency | 266.66 ms |
| Median Latency | 270 ms |
| Min Latency | 219 ms |
| Max Latency | 336 ms |
| 95th Percentile | 304 ms |
| Std Deviation | +/- 23.46 ms |
| Spike Count | 25 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 270.2ms vs long 273.3ms; n=10/20)
Sparkline (last 30): @=%=**-*=-**=+-=-+=+%- ++-:++ 
Hourly Latency Sparkline: **=-#+***+*@-:* .: :*%*+

Time-of-day Baselines: Peak mean 271.1 ms (+/- 18.44) [n=108] | Off-peak mean 264 ms (+/- 25.7) [n=180]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 233.47 ms |
| Median Latency | 221 ms |
| Min Latency | 210 ms |
| Max Latency | 3043 ms |
| 95th Percentile | 244 ms |
| Std Deviation | +/- 166.42 ms |
| Spike Count | 27 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 288 |

Trend: == STABLE (short 227.8ms vs long 227.35ms; n=10/20)
Sparkline (last 30): #:.:@= -:.:..+:.:==.-=..:.:.=+
Hourly Latency Sparkline:        @                

Time-of-day Baselines: Peak mean 247.55 ms (+/- 271.65) [n=108] | Off-peak mean 225.02 ms (+/- 10.12) [n=180]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 650 |
| Unique Tasks |  |
| Avg Quality | ?占쏙옙 0.704 |
| Success Rate | ?占쏙옙 100% |
| Replan Rate | 40% |
| Last Activity | 3.5 minutes ago |

**[WARN] AGI System Alerts:**

- ?占쏙옙 CRITICAL AGI Replan Rate: 40% (threshold: 10%)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 0 | 24 |
| Cloud   | 0 | 0 | 0 | 0 | 25 |
| Gateway | 0 | 0 | 0 | 0 | 27 |
| Total   | 0 | 0 | 0 | 0 | 76 |
---

### Alert Severity Details

#### [!] Critical (3)

| Timestamp | Message |
|-----------|---------|
| 12:43:04 | Cloud AI offline (429) |
| 15:08:07 | ALERT: Lumen Gateway latency 3043ms |
| 21:18:09 | Local LLM offline (0) |

#### [i] Info (77)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:        @  @     @           
Warnings:  *# ++---::*+.-@-+-.#:-.: 
Spikes:    *# -+---::*+.-@-+-.#:-.: 
---

### Availability Trend (hourly)

Local:     @@@@@@@@@@@@@ @@@@@@@@@@
Cloud:     @@@@ @@@@@@@@@@@@@@@@@@@
Gateway:   ------------------------
---

## Recommendations

- **[CRITICAL]** 3 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **Spikes**: 76 latency spikes detected. Review system load and resource allocation.
- **[HIGH] AGI System**: High replan rate (40%).
  - Action: Investigate task complexity and initial planning quality
  - Action: Review rune event logs for replan patterns
  - Action: Consider adjusting AGI planning parameters

---

_Report generated by unified monitoring dashboard_