# Lumen v1.2.0 — Final Release Notes

**Date:** 2025-10-23  
**Codename:** *Resonance Stabilization*

## Highlights
- **Adaptive tuning**: LinUCB + learned reward mixing (λ), exploration control (α)
- **Safety rail**: env-driven delta clamp, max concurrent adjustments, TTL
- **Promotion**: canary gates (latency/error/coherence/phase) with Slack approval
- **Observability**: Grafana v1.2 Rhythm & v1.3 Fractal dashboards + Prom exporter
- **Docs**: One‑pager, docs build/Pages pipeline, Slack notification

## Breaking/Important
- `stage_matrix.yaml` now embeds `policy.*` per stage
- `safety_guard.py` reads `DELTA_CLAMP` from env
- Approvals can be enforced with `APPROVAL_REQUIRED=1`

## Quickstart
```bash
make stage-dev            # run loop
make autotune             # produce suggested_params.json
python params_apply.py --stage dev --dry-run
make canary-check         # staging gating
APPROVAL_REQUIRED=1 SAFE_APPLY=1 make canary-promote
make infra-up             # Prom+Grafana+Exporter+Alertmanager
```

## Security
- Proof ledger: append-only hash chain (`proof_ledger.jsonl`); `make proof-verify`
- Secrets:
  - `BRIDGE_SIGNING_SECRET` for approval links
  - Slack webhook via file mount in Alertmanager
