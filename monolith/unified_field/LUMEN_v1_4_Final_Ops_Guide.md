# Lumen v1.4 — Final Ops Guide (Detect → Approve → Remediate → Prove → Observe)

```
Prometheus <- Exporters (9109/9111/9112)
     |              |
     v              |
 Alertmanager ----> Approval Bridge (8080) --(Proof append)--> Proofd (8077)
     |                             \
     |                              \--(Decision Hook)--> Auto-Remediation (8089)
     v
 Grafana (3000)  <---- annotations ----/
```

Profiles: base, ops, exporters, interactive

Cheatsheet:
- `make up-ops && make up-exp && make up-int`
- Auto-remediation: `docker compose -f docker/docker-compose.autoremediation.override.yml up -d`
- Link mode (approve→auto): `docker compose -f docker/docker-compose.linkmode.override.yml up -d`

Endpoints: Grafana(3000), Prom(9090), AM(9093), Bridge(8080), Proofd(8077), Context(8085), Slack(8086), Auto(8089)

Day‑2:
- Rotate secrets, tune thresholds, set `GRAFANA_API_KEY`, enable persistence, lock webhook ingress, review quorum.
