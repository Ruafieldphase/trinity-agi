# Monitoring Thresholds Configuration

Location: `d:\nas_backup\config\monitoring_thresholds.json`

This file controls alerting and UI thresholds for the monitoring dashboard and AGI system. All values have sensible defaults; you can tune them without modifying scripts.

## Keys

- AGI.thresholds.min_quality (float 0..1)
- AGI.thresholds.min_confidence (float 0..1)
- AGI.thresholds.min_success_rate_percent (percent 0..100)
- AGI.thresholds.replan_rate_percent (percent 0..100)
- AGI.thresholds.max_avg_duration_sec (seconds)
- AGI.thresholds.inactive_hours (hours)

### Evidence Gate (Forced) thresholds

- AGI.thresholds.evidence_forced_warn_percent (percent 0..100)
- AGI.thresholds.evidence_forced_crit_percent (percent 0..100)
- AGI.thresholds.evidence_forced_ma_window (integer window size for moving average overlay, default 5)

### Persona thresholds

- AGI.thresholds.persona.low_success_warn_percent (percent 0..100)
- AGI.thresholds.persona.low_success_crit_percent (percent 0..100)
- AGI.thresholds.persona.slow_duration_sec (seconds)

## Usage

- The report generator loads this JSON and injects thresholds into metrics output (AGI.Thresholds and AGI.Health.thresholds[_ui]).
- The HTML dashboard reads these thresholds to color badges, show warnings, and render moving-average overlays.
- If the file is missing, defaults are used automatically.

## Tips

- Start with warn=70 and crit=50 for forced success; adjust after a week of baseline data.
- Increasing `evidence_forced_ma_window` smooths noisy success sequences but may hide short-term regressions.
