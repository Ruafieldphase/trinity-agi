# v1.5 RC One-shot Checklist

```bash
# 0) 환경: Stage 네임스페이스/모니터링 준비 (ServiceMonitor, Adapter, Grafana)

# 1) 세션 복원 → 프리뷰
source SESSION_RESTORE_2025-10-24_v1_4_FULL.yaml
source SESSION_RESTORE_2025-10-24_v1_5_PREVIEW.yaml

# 2) 값 적용(스테이지)
helm upgrade --install lumen charts/lumen -f charts/lumen/values.stage.yaml -n lumen-stage

# 3) 게이트 실행
python scripts/release_gate.py --metrics-url http://<pod-ip>:9143/metrics       --m-score-min 0.45 --h-eff-max 0.72

# 4) 카나리 분석
kubectl apply -f argo/analysis-template.yaml -n lumen-stage
kubectl apply -f argo/rollout.yaml -n lumen-stage

# 5) 증빙 번들 생성
python scripts/proof_bundle.py --root .

# 6) RC 버전 넘버링 & 릴리즈 노트
./scripts/release_bump_rc.sh v1.5-rc1
gh workflow run lumen_release_notes --ref main -f tag="v1.5-rc1"
```
