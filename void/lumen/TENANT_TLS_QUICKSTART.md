# Tenant & TLS Quickstart

## TLS
- Install cert-manager in the cluster.
- Apply `extras/clusterissuer.yaml` once.
- Set `tls.enabled=true` and `ingress.host` in values, then deploy.

## Tenant
- Apply `extras/tenant_baseline.yaml` to create namespace/quota/limits/default-deny.
- Install into that namespace with `-n lumen-prod` (match `tenant.name`).

## Custom metrics HPA
- Deploy Prometheus Adapter with `prometheus_adapter_rules.yaml`.
- Apply `templates/hpa_external.yaml` or include in chart for production.
