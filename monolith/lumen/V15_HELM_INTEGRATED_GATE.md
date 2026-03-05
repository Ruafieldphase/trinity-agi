# Helm Hooks — Integrated Gate (v1.9 × v1.5)

이 차트는 **배포 전(pre) / 후(post)** 훅 Job으로 통합 게이트를 실행합니다.  
게이트 실패 시 훅 Job이 실패되어 릴리즈가 중단되며, 옵션에 따라 **자동 롤백**(Helm/ArgoCD 스켈레톤)도 시도합니다.

## Values
```yaml
gate:
  enabled: true
  maturity:
    overallMin: 0.60
    senseMin: 0.45
    feedbackMin: 0.45
    releaseMin: 0.45
    penalty: 0.10
  roi:
    env: "prod"
    service: "api"
  flipback:
    platform: "none"   # helm|argocd|none
    target: "previous"
  hooks:
    pre: true
    post: true
```

## Requirements
- 이미지에 다음 스크립트 포함 필요:
  - `scripts/integrated_gate_v19_v15.py`
  - `scripts/helm_rollback_v19.sh`, `scripts/argocd_rollback_v19.sh` (옵션)

## 사용 예
```bash
helm upgrade --install lumen-v15 ./helm/lumen-v15-preview   --set image.repository=ghcr.io/<org>/lumen   --set image.tag=v1.5-rc   --set gate.enabled=true   --set gate.roi.env=prod --set gate.roi.service=api   --set gate.maturity.overallMin=0.65   --set gate.flipback.platform=helm --set gate.flipback.target=previous
```

> 참고: 훅이 실패하면 해당 릴리즈는 실패 상태가 되며, Helm 자체 롤백은 별도로 수행해야 합니다.  
> 본 훅은 컨테이너 내부에서 제공된 스크립트를 호출해 **사이드 롤백**을 시도합니다(스켈레톤). 실제 롤백 명령은 주석 해제 후 사용하세요.
