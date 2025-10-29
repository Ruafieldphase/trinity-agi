# CI/CD Load Testing Strategy

This document describes how load testing is automated in GitHub Actions for Ion Mentoring.

## Workflow Overview

- Schedule: Daily at 03:00 UTC
- Manual Trigger: Via GitHub Actions UI or script
- Artifacts: CSV/HTML/JSON results saved per run
- Notifications: Optional Slack webhook

## SLO Gates

- P95 latency < 500ms
- Error rate < 1%
- Minimum requests > 10

## Files

- Workflow: `.github/workflows/load-test.yml`
- Orchestrator Scripts: `scripts/run_all_load_tests.ps1`, `scripts/run_extended_load_tests.ps1`

## Local Reproduction

```powershell
# Run the light profile for 10s
python -m locust -f load_test.py --host=https://your-api.run.app --users 10 --spawn-rate 1 --run-time 10s --headless
```
