# v1.9 — PR Automations & Grafana Annotations Push

## PR Gate (Extended)
- Workflow: `.github/workflows/lumen_v19_pr_gate_extended.yaml`
- Checks:
  - Readiness v2 report (attached + PR comment)
  - ROI Gate (env=stage, thresholds from `docs/roi_thresholds_v19.example.yaml`)
  - On failure: ❌ in comment + `do-not-merge` label

## Grafana Annotations Push
- Workflow: `.github/workflows/lumen_v19_push_grafana_annotations.yaml`
- Triggers: after **Autotune on Drift** or **Incident Feedback**; also manual
- Action: rebuild annotations JSON then push to Grafana
- Secrets: `GRAFANA_URL`, `GRAFANA_API_KEY`
