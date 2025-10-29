# Lumen v1.6 — Release Candidate (RC) — 2025-10-23

## ✨ What’s in v1.6
- **Streaming Enrichment (P1)** — semantic packets & metrics (`semantic_density`, `entropy_score`, avg30)
- **Resonance Adaptation (P2)** — dynamic `window_ms` / `gain_alpha`, resync & auto-tune metrics
- **Memory & History (P3)** — pattern signatures, `entropy_shift` + resync history
- **Helm v1.6** — Enricher/Adapter Deployments/Services/ServiceMonitors, PVC/emptyDir, flags
- **Grafana** — v1.6 dashboards (Enrich&Adapt / Memory&History) + provisioning
- **CI** — smoke, helm-unittest; Preview pipeline

## ✅ Quality Gates (recommended)
- Stage RC gate: `m_score ≥ 0.45`, `h_eff ≤ 0.72`
- Prod RC gate:  `m_score ≥ 0.48`, `h_eff ≤ 0.70`
- Canary analysis: `avg_over_time(lumen_m_score[2m]) ≥ 0.45`

## 📊 Env Threshold Matrix
| ENV   | m_score_min | h_eff_max | errorRatioTarget (HPA/KEDA) | STREAM_BUFFER_WINDOW_MS | SLO |
|-------|-------------:|----------:|-----------------------------:|------------------------:|----:|
| dev   | 0.40         | 0.75      | 0.20                         | 1000                    | 99.0% |
| stage | 0.45         | 0.72      | 0.12                         | 1200                    | 99.5% |
| prod  | 0.48         | 0.70      | 0.10                         | 1500                    | 99.7% |

## 🧪 RC Validation Flow
1) `make p2-smoke` (or CI smoke) → metrics respond on :9151 / :9152  
2) Helm stage deploy with v1.6 flags → ServiceMonitor picks exporters  
3) RC Gate + Argo Rollouts canary → analysis PASS  
4) Memory/History populated → proof bundle attached

## 🗂️ Evidence Bundle (attach to PR)
- `memory_store.json`, `v16_history.csv`  
- `semantic_metrics.csv`, `adaptation_metrics.csv`  
- Grafana dashboard JSON (v1.6), Helm package (`*.tgz`)  
- SBOM (if available), gate logs

## 🔄 Rollback
- `helm rollback lumen <REV>` → smoke/gate recheck

## 🚀 Next
- If RC stable ≥ 48h with no FastBurn, tag final `v1.6.0`.
