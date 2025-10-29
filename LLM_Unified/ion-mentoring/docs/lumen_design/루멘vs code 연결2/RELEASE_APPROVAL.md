# Lumen v1.5 Release Approval Criteria

## Mandatory pass conditions
- `lumen_m_score >= 0.45` (median over last 15m or point-in-time via exporter)
- `lumen_h_eff <= 0.72`
- No `LumenFastBurn` alert firing

## Evidence bundle (attach to PR)
- Grafana screenshots: Maturity & SLO dashboards (last 24h)
- `graph_feedback_unified.json` (timestamped)
- Exported Prometheus rules hash (slo/alerts) + SBOM artifact

## CI Gate
- Workflow: `lumen_release_gate` must pass with environment-specific thresholds
  - Stage: `m_score_min=0.45, h_eff_max=0.72`
  - Prod:  `m_score_min=0.48, h_eff_max=0.70`

## Rollback plan
- Helm rollback to previous release
- Disable Kafka topics hook (featureFlags.enableKafkaTopicsHook=false)
- Set STREAM_BUFFER_WINDOW_MS back to last-known-stable
