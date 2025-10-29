# Lumen v1.5 — Final Release Notes (Template)

## Overview
Brief description of Streaming + Maturity layer and operational autonomy.

## New
- Streaming adapters (Kafka/Loki)
- Maturity exporter & dashboards
- Unified Feedback Graph
- Helm chart (security/guardrails) & CI gates
- Autoscaling (KEDA/HPA + custom metrics)
- TLS, OAuth2 Proxy, tenant isolation

## Breaking/Important Changes
- Required env vars / ports
- Helm values keys that changed
- Default security contexts & probes

## Ops
- SLO target: 99.7% (prod), error budget 0.3%
- Alerting: FastBurn, SlowBurn, MaturityDrop
- Runbooks: incident + rollback links

## Upgrade Path
- From v1.4 using session restore
- Canary analysis steps & thresholds

## Evidence
- Proof bundle artifact checksum & link
