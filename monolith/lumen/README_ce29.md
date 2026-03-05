# 🌙 Lumen — v1.4 Final ➜ v1.5 Preview

> **Start here (one-liner):**
```bash
source SESSION_RESTORE_2025-10-24_v1_4_FULL.yaml
```
로드 후 즉시 사용 가능한 명령:
```
# v1.4
up | up_exp | up_int | auto | link | ci_all | rel
# v1.5 preview
l15.maturity_spectrum | l15.windows | l15.serve_metrics
l15.ingest_kafka | l15.ingest_loki
l15.gate <overall_min> | l15.hint | l15.integrated
dc.v15.up | dc.v15.down
```

## 🧰 핵심 경로
- Preview 자산: `lumen_v1_5_preview_assets/`
- 스크립트/게이트: `scripts/`
- Helm 차트: `helm/lumen-v15-preview/`
- GitOps(App-of-Apps): `argocd/apps/**`
- 모니터링: `grafana/**`, `prometheus_rules/**`
- 자동화: `.github/workflows/**`, `argocd/cron/**`

## 📦 빠른 배포
```bash
# 이미지 (GHCR)
#  - 워크플로 자동: lumen_v15_build_and_release
#  - 수동: ./scripts/build_image_v15.sh

# Helm
helm upgrade --install lumen-v15 ./helm/lumen-v15-preview   --set image.repository=ghcr.io/<owner>/lumen   --set image.tag=v1.5-rc   --set exporter.enabled=true
```

## 🧪 자가점검(Nightly)
- GH Actions: `lumen_v15_nightly_selfcheck.yaml` (03:00 KST)
- Argo CronWorkflow: `argocd/cron/lumen-v15-selfcheck-cronworkflow.yaml`
