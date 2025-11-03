# Monitoring Report

**Generated**: 2025-11-03 17:49:29
**Time Window**: Last 24 hours
**Data Points**: 205 snapshots

---

## Executive Summary

```
  HEALTH: EXCELLENT
  Availability: 99.67%  |  Alerts: 3  |  Warnings: 0  |  Spikes: 42

  Alert Severity:
    [!] Critical: 3  |  [*] Warning: 0  |  [i] Info: 43

  Local LLM:     99.02% avail  |  51.06ms mean
  Cloud AI:      100% avail  |  268.11ms mean
  Lumen Gateway: 100% avail  |  235.51ms mean
  Resonance Policy: mode=observe active=latency-first last=quality-first | allow=22 warn=29 block=0
  Last Task: 1079ms

  --- vs Previous Period (24h ago) ---
  Local:   Latency ▲20.1%  |  Avail ▲0.1%
  Cloud:   Latency ▲0.4%  |  Avail =
  Gateway: Latency ▲4.2%  |  Avail =
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
- **Warnings**: 0
- **Spikes**: 42

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
| Mean Latency | 51.06 ms |
| Median Latency | 20 ms |
| Min Latency | 16 ms |
| Max Latency | 3051 ms |
| 95th Percentile | 40 ms |
| Std Deviation | +/- 296.67 ms |
| Spike Count | 11 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 1 |
| Sample Count | 205 |

Trend: == STABLE (short 21.1ms vs long 22.45ms; n=10/20)
Sparkline (last 30): .  ..   .. @  . ..  .   .    .
Hourly Latency Sparkline: %                @      

Time-of-day Baselines: Peak mean 76.08 ms (+/- 404.13) [n=110] | Off-peak mean 22.08 ms (+/- 6.62) [n=95]

### Cloud AI (ion-api)

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 268.11 ms |
| Median Latency | 271 ms |
| Min Latency | 223 ms |
| Max Latency | 398 ms |
| 95th Percentile | 307 ms |
| Std Deviation | +/- 24.17 ms |
| Spike Count | 18 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 205 |

Trend: == STABLE (short 272.7ms vs long 268.1ms; n=10/20)
Sparkline (last 30): =----*=*== = *@-= -=#--+=====-
Hourly Latency Sparkline: %@%%%%%#      %%##%%%%%%

Time-of-day Baselines: Peak mean 265.48 ms (+/- 21.49) [n=110] | Off-peak mean 271.15 ms (+/- 26.73) [n=95]

### Lumen Gateway

| Metric | Value |
|--------|-------|
| Availability | 100% |
| Mean Latency | 235.51 ms |
| Median Latency | 224 ms |
| Min Latency | 212 ms |
| Max Latency | 2410 ms |
| 95th Percentile | 242 ms |
| Std Deviation | +/- 152.87 ms |
| Spike Count | 13 |
| Baseline Alerts | 0 |
| Baseline Warns | 0 |
| Adaptive Alerts | 0 |
| Adaptive Warns | 0 |
| Sample Count | 205 |

Trend: == STABLE (short 220.2ms vs long 221.1ms; n=10/20)
Sparkline (last 30): -:-=-:+:*.-#-=+=+ :@ --:.+%-.@
Hourly Latency Sparkline: +=@==++=      =++=======

Time-of-day Baselines: Peak mean 224.52 ms (+/- 8.4) [n=110] | Off-peak mean 248.24 ms (+/- 224.34) [n=95]

---

## AGI System Status

| Metric | Value |
|--------|-------|
| Total Events | 1584 |
| Unique Tasks |  |
| Avg Quality | ?�� 0.733 |
| Success Rate | ?�� 0% |
| Replan Rate | 31.21% |
| Last Activity | 1.8 hours ago |

**[WARN] AGI System Alerts:**

- ?�� CRITICAL AGI Success Rate: 0% (threshold: 70%)
- ?�� CRITICAL AGI Replan Rate: 31.21% (threshold: 10%)

---

## Alerts Summary

| Channel | Baseline Alerts | Baseline Warns | Adaptive Alerts | Adaptive Warns | Spikes |
|---------|------------------|----------------|------------------|----------------|--------|
| Local   | 0 | 0 | 0 | 1 | 11 |
| Cloud   | 0 | 0 | 0 | 0 | 18 |
| Gateway | 0 | 0 | 0 | 0 | 13 |
| Total   | 0 | 0 | 0 | 1 | 42 |
---

### Alert Severity Details

#### [!] Critical (3)

| Timestamp | Message |
|-----------|---------|
| 17:53:29 | Local LLM offline (0) |
| 20:03:07 | ALERT: Lumen Gateway latency 2410ms |
| 11:48:11 | Local LLM offline (0) |

#### [i] Info (43)

_Minor alerts and informational messages. See JSON output for full details._

---

### Alerts Trend (hourly)

Alerts:    @ @              @       
Warnings:  -@=.#-=       -#..=-..*. 
Spikes:    -@=.#.=       -#..=-..*. 
---

### Availability Trend (hourly)

Local:     %@@@@@@@      @@@%@@@@@@
Cloud:     @@@@@@@@      @@@@@@@@@@
Gateway:   @@@@@@@@      @@@@@@@@@@
---

## Recommendations

## Policy Snapshot (Latest)

# Policy A/B Snapshot

Generated: 2025-11-03 16:05:07
Lines analyzed (ledger): 15987

## Ledger-Based Counts
- quality-first: count=159 allow=41 warn=118 block=0 avg=20446ms p95=34001ms

## Synthetic Re-Evaluation
- quality-first: n=112 allow=41 warn=71 avg=18628ms p95=34012ms
- latency-first: n=112 allow=41 warn=71 avg=18628ms p95=34012ms

Auto Stabilizer Summary: 2025-11-03T17:47:51.223716 Micro-Reset triggered (success=True, dry_run=True, fear=0.500)

- **[CRITICAL]** 3 critical alert(s) detected
  - Action: Review critical alerts immediately in 'Alert Severity Details' section
  - Action: Check system availability and response times
  - Action: Verify all services are online and responsive

- **Spikes**: 42 latency spikes detected. Review system load and resource allocation.
- **[HIGH] AGI System**: High replan rate (31.21%).
  - Action: Investigate task complexity and initial planning quality
  - Action: Review rune event logs for replan patterns
  - Action: Consider adjusting AGI planning parameters

---

_Report generated by unified monitoring dashboard_