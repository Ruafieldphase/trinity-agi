# Lumen — Quick Start (New Session)

> Use this page when you open a new session/window to continue working on Lumen v1.4 → v1.5 Preview.

---

## 1) One-liner to restore environment

```bash
# run this in the repo root to restore session environment variables and helpers
source SESSION_RESTORE_2025-10-24_v1_4_FULL.yaml
```

This will expose convenient shell functions and variables such as `up`, `l15.integrated`, `dc.v15.up`, etc.

---

## 2) Project layout (important paths)

- `SESSION_RESTORE_2025-10-24_v1_4_FULL.yaml` — session bootstrap (source this first)
- `scripts/` — all helper scripts and gates
  - `integrated_gate_v19_v15.py` — integrated gate (ROI/SLO × Maturity)
  - `maturity_diff_v15.py` — QA diff/report tool
  - `gate_result_card_v15.py`, `incident_notifier_v19.py` — notification cards
  - `self_check_v15.sh` — nightly/self-check runner
  - `release_tag_v15.sh` — local tag helper
- `lumen_v1_5_preview_assets/` — maturity exporter and spectrum calculators
- `helm/lumen-v15-preview/` — helm chart with pre/post gate hooks
- `.github/workflows/` — CI/CD + nightly + release workflows
- `argocd/` — App-of-Apps + CronWorkflow manifests
- `grafana/`, `prometheus_rules/` — dashboard & alert rules
- `docs/` — all generated guides & release notes

---

## 3) Quick health-check sequence (one-shot)

Run this in a fresh terminal after sourcing the session file:

```bash
# bring up preview docker stack (local dev preview)
dc.v15.up

# start exporter
l15.serve_metrics

# compute maturity
l15.maturity_spectrum

# run integrated gate (local)
l15.integrated

# publish gate card (if webhooks set)
python scripts/gate_result_card_v15.py
```

Check Grafana at `http://localhost:3000` and Proofd stats at `http://localhost:8077/stats`.

---

## 4) QA / Release quick flow

- Dry-run QA (recommended before tagging):

```bash
# run on PR or locally
# produces: logs/gate_pre.json, logs/gate_post.json, docs/V15_QA_DIFF_REPORT.md
python .github/workflows/lumen_v15_release_dryrun.yaml # or run the scripts directly
```

- If QA PASS → tag and publish

```bash
# create and push tag
./scripts/release_tag_v15.sh v1.5-rc
# then run release workflow (Actions UI): lumen_v15_release_publish_with_QA
```

---

## 5) Useful commands (from session file)

- `up`, `up_exp`, `up_int` — boot v1.4 core stack
- `auto`, `link` — auto-remediation and approval link
- `l15.serve_metrics`, `l15.ingest_kafka`, `l15.ingest_loki` — run preview components
- `l15.maturity_spectrum`, `l15.windows` — compute spectrum & windows
- `l15.integrated` — run integrated gate locally
- `dc.v15.up`, `dc.v15.down` — bring docker preview stack up/down
- `./scripts/self_check_v15.sh` — run the full self-check locally
- `./scripts/release_tag_v15.sh <tag>` — create & push annotated tag

---

## 6) Next recommended steps (pick one)

1. **Smoke test (recommended)**: run Quick health-check sequence and confirm metrics/dashboards.  
2. **Dry-run QA**: trigger `lumen_v15_release_dryrun` on your PR (or run scripts locally).  
3. **Publish RC**: after PASS, push `v1.5-rc` tag and run `lumen_v15_release_publish_with_QA`.  
4. **Harden pipeline**: add cosign SBOM & vulnerability-scan gates (optional next task).

---

## 7) Where to find logs & artifacts

- `logs/` — self-check and gate logs
- `docs/V15_QA_DIFF_REPORT.md` — QA diff report (used as release notes summary)
- Workflow artifacts appear on GitHub Actions runs for nightlies and release workflows

---

If you want, I can also open a fresh canvas per component (Dashboard / Helm / QA) with step-by-step tasks. Which would you like me to open next?