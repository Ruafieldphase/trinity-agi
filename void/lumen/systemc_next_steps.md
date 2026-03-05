# System C Next-Step Overview

## Status
- Scope: ELO info-theory → operations (metrics, alerts, CI/PR, Prometheus, rollback) [ChatGPT-Next-session handoff summary.md:16]
- Progress: ~80%, remaining 10% prioritized as below [ChatGPT-Next-session handoff summary.md:19,31-34]

## Remaining Priorities
1. **Corpus Adapter (JSONL)** — Replace ./autodemo/elo_corpus.jsonl with real corpus, apply redaction [ChatGPT-Next-session handoff summary.md:31]
2. **Hybrid Intent Labeler** — rules+small model, shadow evaluation before promote [ChatGPT-Next-session handoff summary.md:32]
3. **RED Integration** — merge info-theory signals into RED policy/cards [ChatGPT-Next-session handoff summary.md:33]
4. **Dispatcher Go-Live** — switch prod commands, dry-run off via canary [ChatGPT-Next-session handoff summary.md:34]

## Supporting Packs (정보이론철학적분석3)
- Autoscaling/Cost Guard: HPA/VPA/KEDA, OpenCost, capacity report [elo_lumen_autoscaling_capacity_cost_guard_pack_2025_10_15_kst.md:1-67]
- Auto Promotion & ChatOps: canary promoter, dispatcher edits, Slack/GitHub Actions integration [elo_lumen_auto_promotion_executor_slack_chat_ops_2025_10_15_kst.md:1-63]
- Additional packs (observability, governance, security, launch runbook 등) follow consistent structure: file tree, Make targets, acceptance criteria.

## Suggested Action Checklist (루빛)
1. Keep data pipeline fresh via scripts/run_luon_pipeline.ps1 and monitor watch logs (logs/luon_watch_keepalive.log).
2. Implement corpus adapter first; once validated, rerun pipeline and update utodemo/elo_corpus.jsonl.
3. Prepare evaluation harness for hybrid labeler (shadow → promote) and plan RED policy updates.
4. Use dispatcher go-live pack to rehearse canary → full rollout; align with launch runbook timelines.
5. Document progress in systemC_integration_plan.md and tick off items in README_watch_restart.md TODO section.

