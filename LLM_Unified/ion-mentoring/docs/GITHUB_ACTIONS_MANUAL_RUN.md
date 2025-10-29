# GitHub Actions Manual Run Guide

This guide shows how to manually trigger the CI workflows.

## Prerequisites

- GitHub CLI installed (`gh --version`)
- Authenticated: `gh auth login`

## Trigger Load Test Workflow

```powershell
# From repo root
# Adjust inputs as needed
$workflow = ".github/workflows/load-test.yml"
$inputs = "{ \"profile\": \"light\", \"duration\": \"2m\", \"enforce_slo\": true }"

gh workflow run $workflow --ref main --inputs $inputs
```

## Troubleshooting

- Workflow not found → Check path/name
- Auth failed → Re-run `gh auth login`
- Invalid inputs → Inspect workflow `inputs` schema
