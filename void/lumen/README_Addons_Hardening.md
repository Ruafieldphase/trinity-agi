# LUON — K8s Addons & Hardening

## Apply (Kustomize)
```bash
# Base (app)
kubectl apply -k ops/k8s/overlays/demo
# Addons (security/monitoring)
kubectl apply -k ops/k8s/addons
```

## What’s included
- **Pod Security Standards**: namespace labels (baseline)
- **NetworkPolicy**: default allow same-namespace + DNS (harden as needed)
- **LimitRange/ResourceQuota**: sane defaults
- **Prometheus Operator**: ServiceMonitor (exporter) & PodMonitor (scheduler)
- **ImagePullSecrets**: template + patches to wire secret to Deployments

> Replace `<base64-of-dockerconfigjson>` in `image_pull_secret.yaml` with your real base64 content.
> If you’re using Helm, set `registry.image` and `registry.pullSecret` in `values.yaml`.
