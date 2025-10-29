# v1.6 Persistence & Helm Tests

## Persistence
- PVC: `templates/v16_pvc.yaml` (enabled when `v16.persistence.enabled=true`)
- Mount: both v16 Enricher/Adapter mount `/data` for shared files/sockets.

## Values
```yaml
v16:
  persistence:
    enabled: true
    size: 5Gi
    storageClass: standard
```

## Helm Unit Tests
- Location: `charts/lumen/tests/*`
- CI: `lumen_helm_unittest` runs on PRs touching charts.
