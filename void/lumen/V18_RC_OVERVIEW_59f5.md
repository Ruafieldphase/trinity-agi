# Lumen v1.8 — RC (Adaptive Policy → Gate → Ledger)

## 요약
- 레저 기반 임계치 자동 산출(adaptive policy) → 게이트 실행 → 통과 시 레저 적재 / 실패 시 롤백

## 실행
```bash
# 세션 복원
source lumen_v1_8_assets/SESSION_RESTORE_2025-10-24_v1_8_RC.yaml
l8.rc.run
```

## GH Actions
- `lumen_v18_rc_pipeline`: policy 산출 → 스택 기동 → 게이트 → (성공) 레저 적재 → 아티팩트 업로드
