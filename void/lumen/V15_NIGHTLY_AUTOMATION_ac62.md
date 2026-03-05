# Nightly Self-Check Automation (v1.5)

## GitHub Actions (KST 03:00 매일)
- 워크플로: `.github/workflows/lumen_v15_nightly_selfcheck.yaml`
- 아티팩트: `logs/**`, `V15_MATURITY_SPECTRUM.md`, `Maturity_Spectrum_v1_5_alpha.json`

## Argo CronWorkflow
- 매일 03:00 KST, 컨테이너 이미지 `ghcr.io/<owner>/lumen:v1.5-rc`로 실행
- `lumen-webhooks` 시크릿에 `SLACK_WEBHOOK_URL`, `DISCORD_WEBHOOK_URL` 넣어두면 카드 발송

## 로컬 크론 예시 (Ubuntu)
```
crontab -e
# 매일 03:05 KST에 실행 (서버 타임존에 맞춰 조정)
5 3 * * * cd /path/to/repo && /bin/bash -lc 'source SESSION_RESTORE_2025-10-24_v1_4_FULL.yaml && bash scripts/self_check_v15.sh >> logs/cron_selfcheck.log 2>&1'
```
