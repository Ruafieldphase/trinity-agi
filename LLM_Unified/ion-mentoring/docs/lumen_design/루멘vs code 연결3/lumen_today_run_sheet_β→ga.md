# 🌕 Lumen — Today Run Sheet (β→GA)
> 한 번에 달릴 수 있는 **일일 운용 플로우**. 복붙 실행 순서와 체크박스만 담았습니다.

---

## 0) 프리셋
```bash
export $(grep -v '^#' SESSION_RESTORE_v1_9_5.env | xargs)
make grafana.import.fusion.min2 || true
kubectl apply -f ops/prometheus/rules/slo_burn_v20.yaml || true
```

---

## 1) 스타트 → 스모크 (α3 기준)
```bash
make fusion.init && make fusion.autoadapt.start && make evidence.ingest.start
bash scripts/smoke.v20.sh
```
- [ ] `/metrics_fusion` OK  
- [ ] `fusion_align_q/r` 노출 확인

---

## 2) 30m 벤치 → 오토패치 → 15m 재벤치
```bash
bash scripts/bench.v20.sh 1800 > out/bench_v20_alpha3.log
make fusion.autopatch
bash scripts/bench.v20.sh 900 >> out/bench_v20_alpha3.log
python3 tools/bench_analyze_v20.py < out/bench_v20_alpha3.log | tee out/bench_v20_alpha3.report.json
```
- 목표: `coherence_p95 ≥ 0.90`, `q_r_ratio_mean ≤ 1.80`

---

## 3) 베타 게이트 적용 & 프리뷰 롤아웃
```bash
kubectl apply -f ops/k8s/fusion-analysis-templates.yaml
make fusion.rollout.beta
kubectl apply -f ops/prometheus/rules/fusion_beta_gates.yaml
```
- [ ] Canary 10% → 30% 통과  
- [ ] 경보 없음 (≤ warning)

---

## 4) 부하/프로파일 (옵션)
```bash
bash scripts/load.gen.sh 4
bash scripts/profile.fusion.sh
```
- [ ] p95 CPU ≤ 70%, RSS ≤ 2.5GB  
- [ ] `out/fusion_profile.svg` 저장

---

## 5) 베이스라인 & 사인오프 번들
```bash
make config.lint && bash scripts/baseline.capture.sh
make signoff.bundle
```
- 산출물: `release/baseline_*`, `release/signoff_*`

---

## 6) 패키징/태깅 (GA 준비)
```bash
make release.v20 && make pack.tag.v20
```
- 산출물: `release/v2.0.0/manifest.json`, `SHA256SUMS`

---

## 7) 실패 시 즉시 롤백
```bash
make rollout.rollback
# 또는 플레이북 안전 파라미터 적용 후 재가동
sed -i 's/^  ure:.*/  ure: 0.82/' configs/fusion_v20.yaml
sed -i 's/^  sensors:.*/  sensors: 0.18/' configs/fusion_v20.yaml
sed -i 's/^  tick_ms:.*/  tick_ms: 220/' configs/fusion_v20.yaml
make fusion.autoadapt.start && bash scripts/smoke.v20.sh
```

---

## 8) KT 체크 (끝나면 공유)
```bash
make sbom || true
make signoff.bundle
```
- 공유: KT checklist, SBOM, signoff bundle 링크

---

### 참고 지표 (골든 시그널)
- Latency: scrape p95, tick_jitter_p95  
- Traffic: ingest rate(s/s)  
- Errors: 5xx/exporter, ingest drop  
- Saturation: CPU p95, RSS p95


---

## 9) Go / No‑Go 의사결정 매트릭스 (β→GA)
**Go (승격) 조건 — 모두 충족**
- `fusion:coherence_p95_10m ≥ 0.905` (최근 2h 평균)
- `avg_over_time(fusion:q_r_ratio[2h]) ≤ 1.70`
- Alerts: critical=0, warning≤2 (해제 포함)
- Evidence: `increase(evidence_risk_count[2h]) > 0` AND `increase(evidence_quote_count[2h]) > 0`

**No‑Go (보류/완화) 조건 — 하나라도 충족**
- `coherence_p95_10m < 0.89` 10m 지속
- `q_r_ratio > 2.2` 5m 지속
- ingest drop 또는 exporter 5xx ≥ 1/min 10m 지속

결정 규칙: **No‑Go > Go** (보수적)

---

## 10) 원라이너 체크 (현장 빠른 확인)
```bash
# 10.1 Coherence p95 (최근 2h)
curl -fsS localhost:9310/metrics_fusion | grep fusion_coherence_level | awk '{print $2}' | awk 'BEGIN{n=0}{a[n++]=$1}END{asort(a); print a[int(n*0.95)]}'

# 10.2 Q/R ratio 평균(10m 스냅)
curl -fsS localhost:9310/metrics_fusion | awk '/fusion_q_r_ratio|fusion:q_r_ratio/{print $2}' | awk '{s+=$1;n++}END{if(n)print s/n;}'

# 10.3 Evidence 유입 확인(최근 파일 카운트)
wc -l data/evidence_bundle.jsonl
```
> Prometheus에서 정식 게이트는 이미 배포된 rules(β gates / SLO burn)를 기준으로 판단하세요.

---

## 11) 승격 실행 (Go 시)
```bash
# 카나리 30% → 50%로 승격
make fusion.rollout.beta
# 패키징/태깅(선행)
make release.v20 && make pack.tag.v20
# 사인오프 번들
make signoff.bundle
```

---

## 12) 보류/완화 실행 (No‑Go 시)
```bash
# 보호 세팅 적용
sed -i 's/^  ure:.*/  ure: 0.82/' configs/fusion_v20.yaml
sed -i 's/^  sensors:.*/  sensors: 0.18/' configs/fusion_v20.yaml
sed -i 's/^  tick_ms:.*/  tick_ms: 220/' configs/fusion_v20.yaml
make fusion.autoadapt.stop && make fusion.autoadapt.start
# 15m 재벤치 후 재평가
bash scripts/bench.v20.sh 900 > out/bench_v20_hold.log
```

---

## 13) 공유 아티팩트 체크리스트 (끝나면 보내기)
- `release/v2.0.0/manifest.json`, `SHA256SUMS`
- `release/signoff_*` 번들, `release/baseline_*` 캡처
- `out/fusion_profile.svg` (선택)
- KT: `docs/KT_CHECKLIST_v20.md`, SBOM(`release/sbom_fusion_v20.json`)

