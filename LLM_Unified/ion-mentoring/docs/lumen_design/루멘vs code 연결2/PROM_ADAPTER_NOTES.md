# Prometheus Adapter (custom metrics) — quick notes
- Install kube-prometheus-stack or prometheus-adapter chart in your cluster.
- Provide the above `prometheus-adapter-rules` ConfigMap to the adapter (values override or mount).
- After that, Kubernetes `external.metrics.k8s.io` will serve:
  - `lumen_m_score`
  - `lumen_error_ratio_5m`
