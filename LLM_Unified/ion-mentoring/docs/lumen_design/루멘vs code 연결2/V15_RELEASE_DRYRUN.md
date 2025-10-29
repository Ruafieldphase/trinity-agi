# v1.5 — Release Dry-Run (No Publish)

## 목적
- 릴리즈 전 **Dual-Gate QA**를 미리 실행하고, 결과를 아티팩트로 남기며
- PR인 경우 댓글로 요약을 남깁니다. 실제 릴리즈는 수행하지 않습니다.

## 트리거
- 수동 실행(workflow_dispatch) 또는 `main` 대상으로의 Pull Request

## 산출물
- `logs/gate_pre.json`, `logs/gate_post.json`
- `docs/V15_QA_DIFF_REPORT.md`, `docs/V15_QA_RESULT_CARD.json`, `docs/V15_QA_SUMMARY.txt`

## 해석
- `PASS` → 릴리즈 퍼블리셔 워크플로(`lumen_v15_release_publish_with_QA`) 실행 후보
- `FAIL` → 게이트/스펙트럼/룰 점검 후 재시도
