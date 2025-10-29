# v1.5 — ArgoCD App-of-Apps

## 구조
- **root-app** (`argocd/apps/root-app.yaml`): children 디렉토리를 소스로 읽어 하위 앱을 일괄 관리
- children:
  - `lumen-v15-preview.yaml`: Helm 차트(ingestor/exporter + helm hooks) 배포
  - `lumen-monitoring.yaml`: Kustomize로 Prometheus 룰/ Grafana 대시보드 ConfigMap 배포

## 사용
```bash
# 1) repoURL/targetRevision 수정
#   - argocd/apps/root-app.yaml
#   - argocd/apps/children/*.yaml

# 2) (옵션) values 조정 — lumen-v15-preview Application 내 helm.values 섹션

# 3) 등록
kubectl apply -n argocd -f argocd/apps/root-app.yaml

# 4) 동기화
# ArgoCD UI/CLI에서 lumen-v15-root → Sync
```

## 참고
- 모니터링 네임스페이스가 없다면 자동 생성(CreateNamespace=true).  
- Prometheus Operator 환경에서 룰 ConfigMap을 Rule CR로 변환하려면 별도 오퍼레이터 구성이 필요.
