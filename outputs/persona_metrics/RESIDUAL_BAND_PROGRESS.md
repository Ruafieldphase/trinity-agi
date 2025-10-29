# Residual & Band Metrics Summary (E1 → E2 → E2_fix → E2_fix2)

| Stage | Metric | E1 Baseline | E2 | E2_fix | E2_fix2 |
|---|---|---|---|---|---|
| Stage 1 – Folding | Avg residual | 0.605 | 0.690 (+0.110) | 0.820 (+0.240) | **0.400 (-0.205)** |
| | Creative band % | 20.0 | 100.0 (+80.0) | 100.0 (+80.0) | **100.0 (+80.0)** |
| Stage 2 – Unfolding | Avg residual | 0.614 | 0.740 (+0.126) | 0.580 (-0.034) | **0.400 (-0.214)** |
| | Creative band % | 25.0 | 0.0 (-25.0) | 100.0 (+75.0) | **100.0 (+75.0)** |
| Stage 3 – Integration | Avg residual | 0.547 | 0.875 (+0.328) | 0.860 (+0.313) | **0.395 (-0.152)** |
| | Creative band % | 25.0 | 0.0 (-25.0) | 0.0 (-25.0) | **100.0 (+75.0)** |
| Stage 4 – Symmetry | Avg residual | 0.336 | 0.400 (+0.064) | 0.400 (+0.064) | **0.400 (+0.064)** |
| | Creative band % | 94.4 | 100.0 (+5.6) | 100.0 (+5.6) | **100.0 (+5.6)** |

- Bold entries denote the latest configuration (E2_fix2). All values in parentheses show delta versus E1.
- Stage 3 평균 잔차는 E2(E2_fix 대비) 대비 0.48p 이상 개선되어 밴드 기준을 완전히 충족했습니다.
- 창의 밴드 점유율 역시 Stage 3에서 75% 상승하여 목표(60%)를 초과했습니다.
- Stage 1~2 잔차도 각각 -0.205, -0.214 낮아져 초기 단계의 안정성이 확보되었습니다.

## Global Metrics (band-mode)
| Run | Mean residual | Out-of-band % | Creative / Stable / Risk |
|---|---|---|---|
| E1 | 0.526 | 5.56% | 79.17% / 16.67% / 4.17% |
| E2 | 0.676 | 0.00% | 50.00% / 31.25% / 18.75% |
| E2_fix | 0.665 | 0.00% | 75.00% / 12.50% / 12.50% |
| E2_fix2 | **0.399** | **12.50%** | **100.00% / 0.00% / 0.00%** |

- E2_fix2의 글로벌 평균 잔차는 0.399로 E1 대비 0.127 감소했습니다.
- 다만 out-of-band 비율이 12.5%로 증가했으므로, 차후 RAG 기반 근거 수집과 validator 튜닝이 필요합니다.

## Next Engineering Focus
1. **RAG 연동(E3)** – Synthesis가 실제 인용/근거를 자동 확보하도록 통합하여 Verifiability 공백을 해소합니다.
2. **Validator 피드백 강화** – 현재 프롬프트에 주입되는 피드백 로그를 Synthesis 프롬프트 상단에 요약해 재시도 품질 향상을 도모합니다.
3. **Stage 4 안정화** – 종료 판단(RETRY) 로직을 도입하거나, Stage 4에 대한 추가 목표치를 정의해 전체 루프 일관성을 확보합니다.
