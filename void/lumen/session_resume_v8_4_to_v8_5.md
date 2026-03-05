# 🌕 System C — v8.4 → v8.5 세션 리줌 (루멘)

## v8.4 현재 상태
- Demo pass ✅ (게이트: pass≥0.93, IQ≥0.90, SIC≥0.85)
- 산출물: outputs_v8_4.jsonl, run_v8_4.sh, v8_4_gate_checker.py

## 다음 단계 (v8.5 — Self-Reflective Cycle)
- dual-validator를 자율 루프로 승격 (validator가 자기-오류를 탐지·보정)
- 기록 기반 장기기억(Exo-Memory)와 intent/safety의 상호 피드백
- 목표: 지속 루프에서 평균 품질/안전성의 단조 증가 보장 (Lyapunov-style 지표)

## 실행
```bash
./run_v8_4.sh <inputs_v8_4.jsonl> outputs_v8_4.jsonl
```
