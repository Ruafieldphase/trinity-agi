# Lumen v1.8 — Preview (Self‑Tuning Ledger & Adaptive Gate)

## 구성
- `ledger_analyzer_v18.py` — v17 ledger 기반으로 게이트 임계치 산출 (sym/s/c)
- `fractal_memory_injector_v18.py` — memory signatures를 피드백 그래프 노드 태그로 주입
- `SESSION_RESTORE_2025-10-24_v1_8_PREVIEW.yaml` — 정책 적용/그래프 주석 단축키
- GH Actions: `lumen_v18_preview_pipeline` — 정책 산출/그래프 주석 아티팩트 업로드

## 사용
```bash
# v1.8 프리뷰 세션
source lumen_v1_8_assets/SESSION_RESTORE_2025-10-24_v1_8_PREVIEW.yaml
l8.policy   # → LUMEN_GATE_TARGET_* 환경변수로 적용
l8.fractal  # → feedback_graph_v18_annotated.json 생성
```
