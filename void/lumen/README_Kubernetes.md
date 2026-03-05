# LUON on Kubernetes

## Kustomize (quick)
```bash
kubectl apply -k ops/k8s/overlays/demo
kubectl -n luon get deploy,svc,cronjob
```

## Helm
```bash
helm install luon ops/k8s/helm/luon --namespace luon --create-namespace
```

## Argo CD
- `ops/k8s/argocd/luon-app.yaml`를 Argo CD에 등록 (repo URL/경로 수정)

> 기본 이미지는 `luon/exporter:local`. CI/CD에서 실제 레지스트리로 빌드/푸시 후 값만 바꿔주면 됨.
