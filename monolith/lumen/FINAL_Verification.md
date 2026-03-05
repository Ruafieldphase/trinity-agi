# LUON — Final Verification (Go/No-Go)

## Preflight
- [ ] `.env` 작성 및 로드 확인
- [ ] VS Code: **Luon: Healthcheck (CLIs)** 통과
- [ ] **Luon: Prod Validate (.env + tools)** 통과
- [ ] KPI 표준화 파일 `autodemo/kpi_adapted.csv` 존재 & 스키마 OK

## Canary & SLO
- [ ] Stage-1(5%) 평가 리포트 생성 (`Stage1_Eval.md`)
- [ ] **Canary Orchestrate → 10%** 성공 (또는 자동 롤백 확인)
- [ ] SLO 모니터/가드 경보 수신 확인(Slack/Email)
- [ ] Day/Night 정책 동작 확인(야간 롤백 또는 breach-only)

## Flags & Rollback
- [ ] `tools/luon/luon_feature_flags.yaml` 경로 문서화
- [ ] `enable_live` 토글 즉시 반영 확인
- [ ] **rollback_live_off.(ps1|sh)** 수동 롤백 성공

## Reporting
- [ ] `luon_dashboard_plus.html` 열람시 통계/이미지 로드 정상
- [ ] 감사 로그(`luon_audit_log.jsonl`) 생성 및 보관 경로 확인

## Decision
- [ ] GO / [ ] HOLD / [ ] ROLLBACK
