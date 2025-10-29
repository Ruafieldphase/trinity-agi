
# Lumen v1.4 — Production Security Checklist

## Secrets & Identity
- [ ] Rotate `BRIDGE_SECRET` (vault-managed) and Slack secrets
- [ ] Grafana admin password + API key (least privilege)
- [ ] Unique `PROOF_SALT` per env

## Network
- [ ] Auto‑Remediation (8089) ingress → Bridge only
- [ ] Context‑Store (8085) cluster-internal / TLS
- [ ] Decision links TTL ≤ 15m; no reuse

## Supply Chain
- [ ] Pin image digests; SBOM + scan on CI
- [ ] Actions OIDC; secrets minimal

## Data & Audit
- [ ] Proof ledger persisted + backups
- [ ] Approval decisions append with voters snapshot
- [ ] Centralized logs; PII review

## Observability
- [ ] Tune thresholds; runbooks linked in annotations
- [ ] Chaos drill `ProofChainBroken`

## Change Management
- [ ] Quorum/allowlist reviewed per severity
- [ ] Staged rollout via Helm values (stg→prod)

## Incident Response
- [ ] Break‑glass approver flow
- [ ] Auto‑Remediation cooldown + manual override
- [ ] Post‑incident review template
