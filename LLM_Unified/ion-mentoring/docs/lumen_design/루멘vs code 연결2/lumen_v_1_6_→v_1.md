# Lumen v1.6→v1.7 Handoff (Restore Package)

**Owner:** Binoche (비노체) · **Context:** Lumen v1.6 GA → v1.7 Inception · **Date:** 2025-11-01 KST

---

## 0) Quick Restore — one-liners

```bash
# 0. Restore all env/aliases/targets
source SESSION_RESTORE_2025-11-01_v1_6_FULL.yaml

# 1. Bring up the unified loop (Gate/Bridge/Exporter/Proofd bundle)
make v16.unified

# 2. (When ready) Promote RC → GA
make release_publish_v16_ga

# 3. Pin prod images to GA (ArgoCD values)
make argo.pin VERSION=1.6.0

# 4. Rebuild & publish docs portal
make docs.build

# 5. Sanity checks (alerts, dashboards)
make nightly.alerts --dry-run
```

---

## 1) SESSION_RESTORE_2025-11-01_v1_6_FULL.yaml (authoritative)

> Copy into repo root if missing. `source`-only file — no secrets.

```yaml
# SESSION_RESTORE_2025-11-01_v1_6_FULL.yaml
# Lumen v1.6 session restore (KST)

# ========== Versions ==========
export LUMEN_VERSION=v1.6
export LUMEN_GA_TAG=1.6.0
export LUMEN_NEXT_MINOR=v1.7

# ========== Paths ==========
export LUMEN_ROOT="$PWD"
export DOCS_DIR="$PWD/docs"
export TOOLS_DIR="$PWD/tools"
export SCRIPTS_DIR="$PWD/scripts"
export OPS_DIR="$PWD/ops"
export DASH_DIR="$PWD/dashboards"

# ========== Ports ==========
export GRAFANA_URL="http://localhost:3000"
export PROOFD_STATS_URL="http://localhost:8077/stats"

# ========== Docker/Images ==========
export IMG_RUNNER="ghcr.io/<org>/<repo>/runner:${LUMEN_GA_TAG}"
export IMG_EXPORTER="ghcr.io/<org>/<repo>/exporter:${LUMEN_GA_TAG}"
export IMG_PROOFD="ghcr.io/<org>/<repo>/proofd:${LUMEN_GA_TAG}"

# ========== Aliases ==========
alias k='kubectl'
alias mk='make'

# ========== Make targets convenience ==========
export MAKEFLAGS="-j2"

# ========== Git ==========
export GIT_MAIN=main
```

---

## 2) Makefile targets (v16/v17 bridge)

Append to repo `Makefile` if missing:

```makefile
# === v16 unified control ===
.PHONY: v16.unified
v16.unified:
	@echo "[Lumen] Booting Unified Gate/Bridge/Exporter/Proofd"
	python3 scripts/unified_gate_card_v16.py --boot
	python3 tools/exporter_v16.py --serve &
	python3 tools/proofd_stats_v16.py --serve &

.PHONY: nightly.alerts
nightly.alerts:
	python3 tools/slo_alerts_v16.py --simulate --since=24h

.PHONY: release_publish_v16_ga
release_publish_v16_ga:
	bash scripts/release_promote_v16_ga.sh $(LUMEN_GA_TAG)

.PHONY: docs.build
docs.build:
	mkdocs build --strict && mkdocs gh-deploy --force

# === Argo pin ===
.PHONY: argo.pin
argo.pin:
	@if [ -z "$(VERSION)" ]; then echo "VERSION= missing"; exit 1; fi
	sed -i.bak \
		-e 's#image: .*/runner:.*#image: ghcr.io/<org>/<repo>/runner:$(VERSION)#' \
		-e 's#image: .*/exporter:.*#image: ghcr.io/<org>/<repo>/exporter:$(VERSION)#' \
		-e 's#image: .*/proofd:.*#image: ghcr.io/<org>/<repo>/proofd:$(VERSION)#' \
		ops/values-prod.yaml
	@echo "Pinned images to $(VERSION) in ops/values-prod.yaml"

# === v1.7 scaffold ===
.PHONY: feature.v17.init
feature.v17.init:
	git checkout -b feature/v1.7_scope_board || true
	mkdir -p docs/v1.7 && test -f docs/v1.7/scope_board_v1.7.yaml || \
		cp docs/templates/scope_board.template.yaml docs/v1.7/scope_board_v1.7.yaml
	@echo "v1.7 scope board scaffold is ready."
```

---

## 3) GitHub Actions — workflows (YAML)

Place under `.github/workflows/`.

### 3.1 lumen_v16_release_dryrun.yml
```yaml
name: lumen_v16_release_dryrun
on:
  pull_request:
    branches: [ main ]
  workflow_dispatch: {}
jobs:
  dryrun:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: QA & Diff
        run: |
          python3 tools/proofd_stats_v16.py --check health
          python3 tools/exporter_v16.py --check schema
          git diff --stat HEAD^ HEAD || true
```

### 3.2 lumen_v16_nightly_slo_alerts.yml
```yaml
name: lumen_v16_nightly_slo_alerts
on:
  schedule:
    - cron: '30 18 * * *' # 03:30 KST (UTC+9)
  workflow_dispatch: {}
jobs:
  alerts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Simulate & notify
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 tools/slo_alerts_v16.py --simulate --since=24h \
            --slack --create-issues
```

### 3.3 release_publish_v16_ga.yml
```yaml
name: release_publish_v16_ga
on:
  workflow_dispatch:
    inputs:
      tag:
        required: true
        type: string
        default: '1.6.0'
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Create GA release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          ./scripts/release_promote_v16_ga.sh "${{ inputs.tag }}"
```

### 3.4 docs_portal_deploy.yml
```yaml
name: docs_portal_deploy
on:
  push:
    branches: [ main ]
jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install mkdocs
        run: |
          pip install mkdocs mkdocs-material mkdocstrings[python]
      - name: Build & Deploy
        run: |
          mkdocs build --strict
          mkdocs gh-deploy --force
```

---

## 4) ArgoCD values (prod) — image pinning example

`ops/values-prod.yaml` (excerpt):
```yaml
runner:
  image: ghcr.io/<org>/<repo>/runner:1.6.0
exporter:
  image: ghcr.io/<org>/<repo>/exporter:1.6.0
proofd:
  image: ghcr.io/<org>/<repo>/proofd:1.6.0
```

---

## 5) Docs Portal — mkdocs.yml minimal

```yaml
site_name: Lumen Docs Portal
site_url: https://<org>.github.io/<repo>/
theme:
  name: material
  features:
    - navigation.tabs
    - content.code.copy
plugins:
  - search
  - mkdocstrings
nav:
  - Overview: index.md
  - API: api.md
  - Runbook: runbook.md
  - Unified Gate v16: UNIFIED_GATE_CARD_v16.md
  - Transition Log: transition_log_2025-11-01.md
```

---

## 6) Transition Log — `docs/transition_log_2025-11-01.md`

```markdown
# Lumen v1.6 → v1.7 Transition Log (2025-11-01)

## Summary
- v1.6 GA tag: 1.6.0 (RC → GA promoted)
- ArgoCD prod images pinned to 1.6.0
- Docs Portal published (commit: <hash>)

## Verification
- Exporter v16 schema: PASS
- Proofd Stats /metrics: PASS
- Nightly alert dry-run: PASS
- Grafana v2 panels updated: PASS

## Notes
- Bridge v4 stable, plan Bridge v5 preview in v1.7
- Risk: alert noise on low traffic clusters → threshold tuning planned
```

---

## 7) v1.7 Scope Board — `docs/v1.7/scope_board_v1.7.yaml`

```yaml
version: v1.7-draft
owner: Binoche
tracks:
  - name: Resonance Pipeline v3
    goals:
      - Extend 200ms loop with adaptive sampling (50–200ms)
      - Phase diff stabilizer (PID-like)
    deliverables:
      - scripts/resonance_loop_v3.py
      - dashboards/resonance_v3.json
  - name: Cognitive Band Adaptive Tuner
    goals: ["dynamic balance between creativity/stability", "auto-thresholds"]
    deliverables:
      - tools/cognitive_band_tuner.py
      - docs/cognitive_band_tuner.md
  - name: SRE Automation Phase II
    goals: ["event-based rollback", "ticket enrichment"]
    deliverables:
      - tools/auto_rollback_v2.py
      - .github/workflows/incident_auto_rollback.yml
  - name: Unified Gate v17 Preview (Bridge v5)
    goals: ["event stream v2", "ACL v2 (resource scopes)"]
    deliverables:
      - scripts/unified_gate_v17_preview.py
      - docs/unified_gate_v17_preview.md
milestones:
  - name: M1 (T+1w)
    exit: ["scope frozen", "resonance_v3 spike passes"]
  - name: M2 (T+3w)
    exit: ["tuner alpha", "rollback v2 e2e"]
  - name: GA (T+6w)
    exit: ["bridge v5 preview off by default", "docs complete"]
```

---

## 8) Health Checks & Verification Commands

```bash
# Exporter schema & liveness
python3 tools/exporter_v16.py --check schema
curl -fsSL ${PROOFD_STATS_URL} | head -n 20

# Grafana datasource/panel availability (basic HTTP)
curl -I ${GRAFANA_URL}

# Nightly alert dry-run
make nightly.alerts --dry-run
```

---

## 9) Slack templates

**GA Announcement**
```
[Lumen] v1.6 GA 🚀 (tag: 1.6.0)
- Unified Gate/Bridge/Exporter/Proofd stabilized
- Argo prod pinned to 1.6.0
- Docs Portal refreshed: https://<org>.github.io/<repo>/
Next: v1.7 Scope Board kickoff
```

**Incident (Conditional/No-Go)**
```
[Lumen] CONDITIONAL/NO-GO in nightly SLO alerts
- Signal: <name> · since: <window>
- Action: created issue #<id> · owner: <team>
```

---

## 10) Rollback Plan (one-pagers)

- If GA promotion fails mid-way:
  1) `git tag -d 1.6.0` (local) and `gh release delete 1.6.0 -y`
  2) `make argo.pin VERSION=<prev_rc>` and `argocd app sync <app>`
  3) Post-mortem stub in `docs/postmortems/pm_2025-11-01.md`

- If dashboards drift:
  - Reapply `dashboards/*.json` via provisioning; run `mk dashboards.sync`

---

## 11) Next-session quickstart (TL;DR)

```bash
source SESSION_RESTORE_2025-11-01_v1_6_FULL.yaml
make v16.unified
make release_publish_v16_ga
make argo.pin VERSION=1.6.0
make docs.build
make nightly.alerts --dry-run
make feature.v17.init
```

---

## 12) GA Verification Checklist (one screen)

| Area | Command / Evidence | PASS criteria |
| --- | --- | --- |
| Exporter schema | `python3 tools/exporter_v16.py --check schema` | `Schema: OK` in stdout |
| Proofd liveness | `curl -fsSL ${PROOFD_STATS_URL} | head -n 10` | metrics header visible |
| Grafana online | `curl -I ${GRAFANA_URL}` | HTTP/1.1 200 |
| Nightly alerts | `make nightly.alerts --dry-run` | no ERROR/TRACEBACK |
| Docs Portal | GitHub Pages job logs | build + deploy success |
| Argo pin | diff of `ops/values-prod.yaml` | images set to `1.6.0` |

---

## 13) Failure Drills (10‑minute tabletop)

**A. GA release revert**
```bash
gh release delete 1.6.0 -y || true
git push origin :refs/tags/1.6.0 || true
make argo.pin VERSION=<prev_rc>
argocd app sync <app>
```
**B. Alert noise burst**
```bash
python3 tools/slo_alerts_v16.py --simulate --since=1h --tune=+20%
```
**C. Docs rollback**
```bash
git revert <bad_commit_sha>
mkdocs gh-deploy --force
```

---

## 14) v1.7 Work Plan (WBS 80/20)

**Track A — Resonance Pipeline v3**
- Spike: `scripts/resonance_loop_v3.py` (adaptive 50–200ms)
- Metrics: `phase_diff_stab`, `creative_band_occupancy`
- Dashboard: `dashboards/resonance_v3.json`

**Track B — Cognitive Band Tuner**
- Alpha: `tools/cognitive_band_tuner.py` + spec `docs/cognitive_band_tuner.md`
- Auto-thresholds: Bollinger-like bands, PID dampers

**Track C — SRE Automation II**
- `tools/auto_rollback_v2.py` (event-driven)
- GH Action: `.github/workflows/incident_auto_rollback.yml`

**Track D — Unified Gate v17 Preview (Bridge v5)**
- Event stream v2, ACL v2 (resource scopes)
- Guarded flag: `V17_PREVIEW=0` (default off)

---

## 15) Open Issues (to seed)

- [ ] Tune alert thresholds for low-traffic clusters (noise)
- [ ] Add `/ready` and `/healthz` endpoints to Proofd service
- [ ] Docs Portal: add API examples for Exporter v16 (curl + Python)
- [ ] Bridge v5: scope matrix (entity × action × resource)

---

## 16) Command Cheat Sheet

```bash
# Promote → GA
make release_publish_v16_ga
# Pin images
make argo.pin VERSION=1.6.0
# Verify health
python3 tools/exporter_v16.py --check schema
curl -I ${GRAFANA_URL}
# Alerts dry-run
make nightly.alerts --dry-run
# Kickoff v1.7
make feature.v17.init
```

---

## 17) Script Stubs (ready-to-drop)

> 최소 동작 보장형 스텁. 리포지토리 루트 기준 경로.

**scripts/resonance_loop_v3.py**
```python
#!/usr/bin/env python3
import time, os, sys
from datetime import datetime

SAMPLE_LO = float(os.getenv("RL3_SAMPLE_LO_MS", 50)) / 1000.0
SAMPLE_HI = float(os.getenv("RL3_SAMPLE_HI_MS", 200)) / 1000.0
phase_diff = 0.0
creative_band = 0.0

def measure_signals():
    # TODO: wire real signals
    from random import random
    return random() - 0.5, random()

def adapt_interval(pd, cb):
    # naive: more instability → faster sampling
    target = SAMPLE_HI - min(abs(pd)*2.0, 1.0)*(SAMPLE_HI - SAMPLE_LO)
    return max(SAMPLE_LO, min(SAMPLE_HI, target))

if __name__ == "__main__":
    print("[RL3] adaptive loop start", file=sys.stderr)
    while True:
        phase_diff, creative_band = measure_signals()
        interval = adapt_interval(phase_diff, creative_band)
        ts = datetime.utcnow().isoformat()
        print(f"ts={ts} phase_diff={phase_diff:.4f} creative_band={creative_band:.4f} interval={interval:.3f}")
        time.sleep(interval)
```

**tools/cognitive_band_tuner.py**
```python
#!/usr/bin/env python3
import argparse, statistics as stats

parser = argparse.ArgumentParser()
parser.add_argument("--window", type=int, default=120)
parser.add_argument("--std_mult", type=float, default=2.0)
parser.add_argument("--values", nargs="*", type=float, default=[])
args = parser.parse_args()

vals = args.values or [0.1,0.12,0.09,0.11,0.2,0.18,0.13]
mu = stats.fmean(vals)
sigma = stats.pstdev(vals) or 1e-6
lo = mu - args.std_mult*sigma
hi = mu + args.std_mult*sigma
print(f"mean={mu:.4f} stdev={sigma:.4f} band=[{lo:.4f},{hi:.4f}]")
```

**scripts/unified_gate_v17_preview.py**
```python
#!/usr/bin/env python3
import os, json, sys
V17_PREVIEW = int(os.getenv("V17_PREVIEW", "0"))
if not V17_PREVIEW:
    print("[v17] preview disabled (set V17_PREVIEW=1)")
    sys.exit(0)
print(json.dumps({"event_stream":"v2","acl":"v2","status":"preview-on"}))
```

---

## 18) PR Checklist (copy into .github/pull_request_template.md)

```markdown
### Lumen v1.6→v1.7 Transition PR Checklist
- [ ] GA tag pinned in ops/values-prod.yaml (1.6.0)
- [ ] Docs portal updated & links verified
- [ ] Nightly alerts dry-run clean
- [ ] Added/updated dashboards for RL3 or Tuner
- [ ] Rollback steps documented
```

---

## 19) Grafana Panel Seed (dashboards/resonance_v3.json)

```json
{
  "title": "Resonance v3",
  "panels": [
    {"type":"timeseries","title":"phase_diff","targets":[{"expr":"phase_diff_stab"}]},
    {"type":"timeseries","title":"creative_band_occupancy","targets":[{"expr":"creative_band_occupancy"}]}
  ]
}
```

---

## 20) Risk Register (live)

| ID | Topic | Risk | Mitigation | Owner |
|---|---|---|---|---|
| R-01 | Low-traffic alert noise | False positives | Threshold & window tuning | SRE |
| R-02 | Docs drift | Outdated links | CI enforce build + link check | Docs |
| R-03 | Preview feature leakage | v17 flags exposed | `V17_PREVIEW=0` default + CI grep | Gate |

---

## 21) One‑liner Restore (for future sessions)

```bash
source SESSION_RESTORE_2025-11-01_v1_6_FULL.yaml && make v16.unified
```

---

## 22) Prometheus/SLO Seeds

**dashboards/prom_rules_v16.yml**
```yaml
groups:
  - name: lumen-slo
    rules:
      - alert: LumenHighErrorRate
        expr: sum(rate(http_requests_total{job="lumen",status=~"5.."}[5m]))
              / sum(rate(http_requests_total{job="lumen"}[5m])) > 0.02
        for: 10m
        labels: { severity: page }
        annotations:
          summary: "High 5xx error rate (>2%)"
          runbook: "https://<org>.github.io/<repo>/runbook.html#errors"
      - alert: LumenExporterDown
        expr: up{job="lumen-exporter"} == 0
        for: 5m
        labels: { severity: ticket }
        annotations:
          summary: "Exporter is down"
```

**tools/slo_alerts_v16.py (args)**
```bash
python3 tools/slo_alerts_v16.py --simulate --since=24h --slack --create-issues \
  --prom-rules dashboards/prom_rules_v16.yml
```

---

## 23) GitHub Issue Templates

**.github/ISSUE_TEMPLATE/incident.yml**
```yaml
name: Incident
description: Track production incidents
labels: [incident]
body:
  - type: input
    id: signal
    attributes: { label: Signal, placeholder: e.g., High 5xx rate }
  - type: textarea
    id: impact
    attributes: { label: Impact, placeholder: user-visible / SLO violation }
  - type: textarea
    id: timeline
    attributes: { label: Timeline, placeholder: when/how detected }
  - type: textarea
    id: actions
    attributes: { label: Immediate Actions }
```

**.github/ISSUE_TEMPLATE/task.yml**
```yaml
name: Task
description: Execution task
labels: [task]
body:
  - type: input
    id: goal
    attributes: { label: Goal }
  - type: input
    id: owner
    attributes: { label: Owner }
  - type: input
    id: due
    attributes: { label: Due (KST) }
```

---

## 24) Slack Notify Payload (manual test)

```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"[Lumen] Nightly SLO dry-run: all clear ✅"}' \
  ${SLACK_WEBHOOK_URL}
```

---

## 25) Helm/Argo Rollout Strategy

**ops/deploy/helm/values-prod.yaml (excerpt)**
```yaml
strategy:
  rollingUpdate:
    maxUnavailable: 0
    maxSurge: 1
readinessProbe:
  httpGet: { path: /ready, port: 8080 }
livenessProbe:
  httpGet: { path: /healthz, port: 8080 }
```

**ops/argo/app.yaml (wave hooks)**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
spec:
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
      - ApplyOutOfSyncOnly=true
    automated:
      prune: true
      selfHeal: true
  hooks:
    - hook: PreSync
      manifest: ops/hooks/pre_fence.yaml
    - hook: PostSync
      manifest: ops/hooks/post_verify.yaml
```

---

## 26) Security Edge Examples

**ops/edge/oauth2-proxy.cfg**
```ini
provider=github
cookie_secure=true
cookie_samesite=lax
pass_authorization_header=true
email_domains=*
```

**ops/edge/mtls/README.md**
```markdown
- Root CA rotate every 90d
- Server cert (edge) every 30d
- Mutual verification enforced; reject SAN mismatch
```

---

## 27) Make Targets — Validate Configs

```makefile
.PHONY: validate.prom
validate.prom:
	promtool check rules dashboards/prom_rules_v16.yml

.PHONY: validate.docs
validate.docs:
	mkdocs build --strict

.PHONY: validate.argo
validate.argo:
	argocd app get <app> || true
```

---


## 28) 15‑Minute GO/NO‑GO Checklist

- [ ] GA tag exists & immutable (`git show 1.6.0`)
- [ ] Argo synced, healthy (no Degraded)
- [ ] Exporter/Proofd `/ready` green
- [ ] Prom rules loaded (`/-/reload` logs)
- [ ] Docs portal reachable
- [ ] Slack test message delivered

---

## 29) Env Vars (operational)

| Key | Example | Note |
|---|---|---|
| GRAFANA_URL | http://localhost:3000 | dashboards |
| PROOFD_STATS_URL | http://localhost:8077/stats | liveness |
| SLACK_WEBHOOK_URL | (secret) | alerts |
| V17_PREVIEW | 0 | guard flag |

---

## 30) Next Commands (single shot)

```bash
make validate.prom && make validate.docs && make validate.argo && \
make release_publish_v16_ga && make argo.pin VERSION=1.6.0 && \
make docs.build && make nightly.alerts --dry-run
```

---

## 31) Repo Scaffold (reference)

```
.
├─ scripts/
│  ├─ unified_gate_card_v16.py
│  ├─ resonance_loop_v3.py
│  └─ unified_gate_v17_preview.py
├─ tools/
│  ├─ exporter_v16.py
│  ├─ proofd_stats_v16.py
│  ├─ slo_alerts_v16.py
│  └─ cognitive_band_tuner.py
├─ dashboards/
│  ├─ resonance_v3.json
│  └─ prom_rules_v16.yml
├─ ops/
│  ├─ values-prod.yaml
│  ├─ deploy/helm/
│  │  └─ values-prod.yaml
│  ├─ edge/
│  │  ├─ oauth2-proxy.cfg
│  │  └─ mtls/README.md
│  └─ argo/
│     └─ app.yaml
├─ docs/
│  ├─ UNIFIED_GATE_CARD_v16.md
│  ├─ transition_log_2025-11-01.md
│  ├─ v1.7/scope_board_v1.7.yaml
│  └─ runbook.md
├─ .github/
│  ├─ workflows/
│  │  ├─ lumen_v16_release_dryrun.yml
│  │  ├─ lumen_v16_nightly_slo_alerts.yml
│  │  ├─ release_publish_v16_ga.yml
│  │  └─ docs_portal_deploy.yml
│  └─ ISSUE_TEMPLATE/
│     ├─ incident.yml
│     └─ task.yml
└─ SESSION_RESTORE_2025-11-01_v1_6_FULL.yaml
```

---

## 32) `.env.example` & secrets layout

```
# .env.example
GRAFANA_URL=http://localhost:3000
PROOFD_STATS_URL=http://localhost:8077/stats
SLACK_WEBHOOK_URL=
V17_PREVIEW=0
```

```
# secrets layout (do not commit)
.secrets/
  slack_webhook_url
  gh_token
```

---

## 33) pre-commit hooks & lint

**.pre-commit-config.yaml**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks: [ { id: black } ]
  - repo: https://github.com/pycqa/flake8
    rev: 7.1.1
    hooks: [ { id: flake8 } ]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks: [ { id: mypy } ]
```

**Makefile additions**
```makefile
.PHONY: lint
lint:
	pre-commit run --all-files
```

---

## 34) VS Code tasks/launch

**.vscode/tasks.json**
```json
{
  "version": "2.0.0",
  "tasks": [
    { "label": "Restore Session", "type": "shell", "command": "source SESSION_RESTORE_2025-11-01_v1_6_FULL.yaml" },
    { "label": "GA Promote", "type": "shell", "command": "make release_publish_v16_ga" },
    { "label": "Docs Build", "type": "shell", "command": "make docs.build" }
  ]
}
```

**.vscode/launch.json**
```json
{
  "version": "0.2.0",
  "configurations": [
    { "name": "Run Exporter v16", "type": "python", "request": "launch", "program": "tools/exporter_v16.py", "args": ["--serve"] },
    { "name": "Run Proofd Stats", "type": "python", "request": "launch", "program": "tools/proofd_stats_v16.py", "args": ["--serve"] }
  ]
}
```

---

## 35) docker-compose.dev.yml

```yaml
version: '3.9'
services:
  exporter:
    build: .
    command: ["python","tools/exporter_v16.py","--serve"]
    ports: ["8076:8076"]
  proofd:
    build: .
    command: ["python","tools/proofd_stats_v16.py","--serve"]
    ports: ["8077:8077"]
```

**Makefile**
```makefile
.PHONY: dev.up dev.down
dev.up:
	docker compose -f docker-compose.dev.yml up -d --build

dev.down:
	docker compose -f docker-compose.dev.yml down -v
```

---

## 36) Helm chart skeleton

**charts/lumen/Chart.yaml**
```yaml
apiVersion: v2
name: lumen
version: 1.6.0
appVersion: 1.6.0
```

**charts/lumen/values.yaml**
```yaml
image:
  repository: ghcr.io/<org>/<repo>/runner
  tag: "1.6.0"
```

---

## 37) ArgoCD app (expanded)

**ops/argo/app.yaml**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: lumen
spec:
  destination:
    namespace: lumen
    server: https://kubernetes.default.svc
  source:
    repoURL: https://github.com/<org>/<repo>
    path: charts/lumen
    targetRevision: main
    helm:
      valueFiles: [ "../../ops/deploy/helm/values-prod.yaml" ]
  project: default
  syncPolicy:
    automated: { prune: true, selfHeal: true }
```

---

## 38) Tests (pytest) & CI

**tests/test_exporter_schema.py**
```python
from subprocess import run, PIPE

def test_schema_ok():
    r = run(["python","tools/exporter_v16.py","--check","schema"], stdout=PIPE, text=True)
    assert "Schema: OK" in r.stdout
```

**.github/workflows/ci.yml**
```yaml
name: ci
on: [ push, pull_request ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt pytest
      - run: pytest -q
```

---

## 39) Docs stubs (mkdocs pages)

**docs/index.md**
```markdown
# Lumen
Welcome. See Runbook and Unified Gate v16.
```

**docs/runbook.md**
```markdown
# Runbook
## GA Promote
- `make release_publish_v16_ga`
## Rollback
- follow Section 10
```

---

## 40) Release Notes template

**docs/release_notes_1.6.0.md**
```markdown
# Lumen 1.6.0 (GA)
## Highlights
- Unified Gate/Bridge stabilization
- Exporter v16 metrics, Grafana v2 panels
## Upgrade Notes
- Pin images to 1.6.0
```

---

## 41) Versioning & Tagging Policy

- **SemVer**: `<major>.<minor>.<patch>`; GA tags use **immutable** Git tags and GH Releases.
- **Branching**: `main` (protected) ← feature branches `feature/*`.
- **Tags**: RC → `1.6.0-rc.N`; GA → `1.6.0`.
- **Conventional Commits** enforced: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `revert:`.

**Makefile**
```makefile
.PHONY: tag.rc tag.ga
tag.rc:
	@test -n "$(RC)" || (echo RC missing; exit 1)
	git tag -a $(RC) -m "RC $(RC)" && git push origin $(RC)

tag.ga:
	@test -n "$(GA)" || (echo GA missing; exit 1)
	git tag -a $(GA) -m "GA $(GA)" && git push origin $(GA)
```

---

## 42) Changelog Automation

**.github/workflows/release_notes.yml**
```yaml
name: release_notes
on: { workflow_dispatch: {} }
jobs:
  notes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate CHANGELOG
        uses: orhun/git-cliff-action@v3
        with:
          config: ./cliff.toml
          args: --tag ${{ inputs.tag }}
      - name: Upload
        uses: actions/upload-artifact@v4
        with: { name: changelog, path: CHANGELOG.md }
```

**cliff.toml** (excerpt)
```toml
title = "Changelog"
[git]
conventional_commits = true
```

---

## 43) SBOM & Image Scanning & Signing

**Makefile**
```makefile
.PHONY: sbom scan sign attest
sbom:
	syft packages ghcr.io/<org>/<repo>/runner:$(LUMEN_GA_TAG) -o spdx-json > sbom/runner.spdx.json

scan:
	grype ghcr.io/<org>/<repo>/runner:$(LUMEN_GA_TAG) --fail-on=high || true

sign:
	cosign sign --key cosign.key ghcr.io/<org>/<repo>/runner:$(LUMEN_GA_TAG)

attest:
	cosign attest --predicate sbom/runner.spdx.json --type spdx \
	  ghcr.io/<org>/<repo>/runner:$(LUMEN_GA_TAG)
```

**.github/workflows/supply_chain.yml**
```yaml
name: supply_chain
on: [workflow_dispatch]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: Verify signatures
        run: cosign verify ghcr.io/<org>/<repo>/runner:${{ inputs.tag }} || exit 1
```

---

## 44) SLSA Provenance (GitHub Attestations)

**.github/workflows/provenance.yml**
```yaml
name: provenance
on:
  release:
    types: [published]
jobs:
  attest:
    permissions:
      id-token: write
      contents: read
      attestations: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/attest-build-provenance@v1
        with:
          subject-name: ghcr.io/<org>/<repo>/runner
          subject-digest: ${{ vars.IMAGE_DIGEST }}
          push-to-registry: true
```

---

## 45) Supply‑chain Checks — One‑shot

```bash
make sbom && make scan && make sign && make attest
```

Add to **GO/NO‑GO**: `cosign verify` must succeed.

---

## 46) Policy as Code (OPA/Gatekeeper)

**ops/policy/constraint_template.yaml**
```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata: { name: k8srequiredlabels }
spec:
  crd:
    spec:
      names: { kind: K8sRequiredLabels }
      validation: { openAPIV3Schema: { properties: { labels: { type: array } } } }
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels
        violation[{"msg": msg}] {
          required := {label | label := input.parameters.labels[_]}
          provided := {label | label := input.review.object.metadata.labels[label]}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("Missing required labels: %v", [missing])
        }
```

**ops/policy/constraint.yaml**
```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata: { name: must-have-owner }
spec:
  parameters: { labels: ["owner","env"] }
```

---

## 47) Backup / Restore Runbook (DR)

**Scope**: dashboards, configs, images, releases.

```markdown
### Daily
- Export dashboards JSON → `backups/grafana/<date>.tgz`
- Snapshot ops values → `backups/ops/<date>.yaml`

### Restore
1) Recreate namespace & secrets
2) Apply ops values, charts
3) Import dashboards
4) Pin images to last GA
```

**Makefile**
```makefile
.PHONY: backup.grafana backup.ops
backup.grafana:
	tar czf backups/grafana/$$(date +%F).tgz dashboards/*.json
backup.ops:
	cp ops/values-prod.yaml backups/ops/values-prod.$$(date +%F).yaml
```

---

## 48) Cost & Telemetry Seeds

- **Prom metrics**: `request_cpu_seconds_total`, `container_memory_working_set_bytes`
- **Panels**: Cost per component (est.), Memory pressure, CPU throttling

**dashboards/cost_overview.json** (excerpt)
```json
{ "title":"Cost/Telemetry Overview", "panels":[
  {"type":"timeseries","title":"CPU throttling","targets":[{"expr":"rate(container_cpu_cfs_throttled_periods_total[5m])"}]},
  {"type":"timeseries","title":"Memory working set","targets":[{"expr":"sum(container_memory_working_set_bytes) by (pod)"}]}
]}
```

---

## 49) Access/ACL Matrix & HMAC Rotation

**ACL Matrix** (excerpt)
| Resource | Read | Write | Admin |
|---|---|---|---|
| Exporter Metrics | bridge, sre | bridge | sre |
| Proofd Stats | bridge, sre | bridge | sre |

**HMAC Rotation**
```bash
# generate
openssl rand -hex 32 > .secrets/hmac_key_$(date +%F)
# update deployment secret, roll pods
kubectl create secret generic lumen-hmac --from-file=key=.secrets/hmac_key_$(date +%F) -o yaml --dry-run=client | kubectl apply -f -
kubectl rollout restart deploy/lumen
```

---

## 50) 72‑Hour Plan (time‑boxed)

**T+0–6h**: GA promote → Argo pin → Docs deploy → GA checklist PASS
**T+6–24h**: Supply‑chain (SBOM/scan/sign/attest) + Gatekeeper apply + Backup jobs
**T+24–48h**: Resonance v3 spike run + dashboard seed + alert tuning on low traffic
**T+48–72h**: v1.7 Scope freeze, PRs for Track A/B, transition log finalized

---

## 51) Prometheus scrape config (example)

**ops/monitoring/prometheus-scrape.yml**
```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: lumen-exporter
    static_configs:
      - targets: ["exporter:8076"]
  - job_name: proofd-stats
    static_configs:
      - targets: ["proofd:8077"]
```

---

## 52) API Docs (mkdocstrings) — sample docstrings

**tools/exporter_v16.py (excerpt)**
```python
def get_metrics() -> dict:
    """Return current Lumen v16 metrics.

    Returns:
        dict: A flat dict of metric_name → value.
    """
    ...
```

Use `mkdocstrings` to render under **API** page.

---

## 53) Incident Runbook (template)

**docs/runbook_incident.md**
```markdown
# Incident Runbook

## 1. Detect
- Pager/Slack: confirm alert ID, severity

## 2. Triage
- Check `/ready` and `/healthz`
- Check last deploy: `argocd app history <app>`

## 3. Mitigate
- `make argo.pin VERSION=<last_good>`
- `argocd app sync <app>`

## 4. Document
- Open Incident issue from template
- Update transition log
```

---

## 54) Argo Health Queries (quick)

```bash
argocd app get lumen | sed -n '1,80p'
argocd app history lumen | head -n 10
kubectl -n lumen get deploy,pod,svc
```

---

## 55) QA Diff Script

**scripts/qa_diff.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
BASE=${1:-origin/main}
echo "[QA] Diff vs $BASE";
git fetch --all --tags
set +e
git diff --stat $BASE...
set -e
python3 tools/exporter_v16.py --check schema
python3 tools/proofd_stats_v16.py --check health
```

Add target:
```makefile
.PHONY: qa.diff
qa.diff:
	bash scripts/qa_diff.sh origin/main
```

---

## 56) Release Comms (Email/Slack)

**email_ga_announcement.md**
```markdown
Subject: [Lumen] 1.6.0 GA 완료 및 전이 계획 (→ v1.7)

안녕하세요,
Lumen 1.6.0 GA 승격을 완료했습니다. 주요 변경과 전이 일정은 아래와 같습니다.
- Unified Gate/Bridge/Exporter/Proofd 안정화
- Argo prod 이미지 1.6.0 핀 고정
- Docs Portal 업데이트
다음: v1.7 스코프 킥오프 (Resonance v3, Tuner, SRE II, Gate v17 Preview)
```

---

## 57) v1.7 Roadmap Labels (GitHub)

Labels to create: `track:resonance`, `track:tuner`, `track:sre-automation`, `track:gate-v17`, `type:spike`, `type:doc`, `priority:P1/P2`.

---

## 58) CONTRIBUTING.md (sane defaults)

```markdown
# Contributing to Lumen
- Use feature branches and Conventional Commits.
- Add tests for new features.
- Run `make lint && pytest -q` before PR.
- Fill PR checklist (Section 18).
```

---

## 59) LICENSE / NOTICE placeholders

- **LICENSE**: Apache-2.0 (placeholder)
- **NOTICE**: include third‑party attributions on first GA release.

---

## 60) Sanity script & First 10 Commands

**scripts/sanity.sh**
```bash
#!/usr/bin/env bash
set -e
source SESSION_RESTORE_2025-11-01_v1_6_FULL.yaml
make validate.prom && make validate.docs
python3 tools/exporter_v16.py --check schema
curl -fsSI ${GRAFANA_URL} >/dev/null
```

**First 10**
```bash
bash scripts/sanity.sh
make v16.unified
make release_publish_v16_ga
make argo.pin VERSION=1.6.0
make docs.build
make nightly.alerts --dry-run
make sbom && make scan && make sign && make attest
make feature.v17.init
pytest -q
make backup.grafana backup.ops
```

---

## 61) OKRs (v1.7 cycle)

**Objective O1 — 안정·창의의 동적 균형 구현**
- KR1: `phase_diff_stab` p95 < 0.15 (7일 이동)
- KR2: `creative_band_occupancy` 45–60% 유지 (±5%)

**Objective O2 — 운영 신뢰성 강화**
- KR1: Error Budget 99.5% SLO 충족 (월)
- KR2: MTTD < 5m, MTTR p50 < 30m

**Objective O3 — 공급망·정책 준수**
- KR1: SBOM/Sign/Attest 100% 적용
- KR2: Gatekeeper 정책 위반 0건 (주간)

---

## 62) KPIs & SLOs (definitions)

| Metric | Source | SLI | SLO |
|---|---|---|---|
| Availability | probe `/ready` | 1 - (5xx/total) | 99.5%/30d |
| Latency p95 | exporter | request_duration_seconds | < 300ms |
| Error Rate | exporter | 5xx/total | < 1% |
| Alert Fatigue | alerts | alerts/hour | < 2 |

**Error Budget Policy**: if SLO breach projected in 7d, freeze features (Gate v17) and focus on reliability.

---

## 63) Test Matrix (v1.7)

| Area | Case | Tool |
|---|---|---|
| Resonance v3 | adaptive intervals 50–200ms | pytest + property tests |
| Tuner | band calc under spikes | pytest (hypothesis) |
| SRE II | auto rollback on 5xx>2% | gha + kind e2e |
| Gate v17 | ACL v2 scope enforcement | unit + integration |

---

## 64) Postmortem Template (blameless)

**docs/postmortems/template.md**
```markdown
# Postmortem — <title>
## Summary
## Timeline
## Impact
## Root Cause
## Corrective Actions
- Short-term
- Long-term (linked issues)
## Learnings
```

---

## 65) RACI (ownership map)

| Area | R | A | C | I |
|---|---|---|---|---|
| Exporter v16 | Bridge | Binoche | SRE | All |
| Proofd Stats | Bridge | Binoche | SRE | All |
| Gate v17 | Bridge | Binoche | Security | All |

---

## 66) Data Retention & Privacy

- Metrics raw: 14d, aggregated: 90d
- Logs: 30d (PII-free), redaction on ingest
- Backups: 30d rolling, offsite encryption

---

## 67) Secrets & Key Rotation Schedule

- HMAC: 30d, oauth2-proxy cookie: 14d, TLS: 30d, Root CA: 90d
- Run `ops/rotate.sh` (stub) + change log in `docs/transition_log_*.md`

---

## 68) Audit & Access Logging

- Ingress audit: enable structured JSON
- Admin actions: GitHub audit log exported weekly to `backups/audit/`

---

## 69) Dependencies (bill of materials)

- Python 3.11, mkdocs-material, mkdocstrings, pytest, black/flake8/mypy
- Prometheus, Grafana, oauth2-proxy, ArgoCD, Gatekeeper, cosign, syft/grype

---

## 70) Local Dev Quickstart (conda/venv)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
pytest -q
mkdocs serve -a 0.0.0.0:8000
```

---

## 71) Proofd service — health endpoints (stub)

**tools/proofd_stats_v16.py (health)**
```python
from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/ready":
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        elif self.path == "/healthz":
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        elif self.path == "/stats":
            self.send_response(200); self.end_headers(); self.wfile.write(b"metric_a 1
")
        else:
            self.send_response(404); self.end_headers()

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8077), H).serve_forever()
```

---


## 72) Exporter v16 — schema example

**tools/exporter_v16.py (schema check)**
```python
SCHEMA = {
  "phase_diff_stab": float,
  "creative_band_occupancy": float,
  "request_duration_seconds": float,
}

def check_schema(d: dict) -> bool:
    return all(k in d and isinstance(d[k], t) for k, t in SCHEMA.items())
```

---

## 73) Grafana provisioning

**provisioning/datasources/ds.yaml**
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    access: proxy
    isDefault: true
```

**provisioning/dashboards/dash.yaml**
```yaml
apiVersion: 1
dashboards:
  - name: Lumen
    options: { folder: Lumen }
    orgId: 1
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
```

---

## 74) Dashboards sync target

**Makefile**
```makefile
.PHONY: dashboards.sync
dashboards.sync:
	mkdir -p .out/dash && cp dashboards/*.json .out/dash/
	@echo "Dashboards copied to .out/dash for provisioning"
```

---

## 75) CLI wrapper

**bin/lumen**
```bash
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  restore) source SESSION_RESTORE_2025-11-01_v1_6_FULL.yaml;;
  ga) make release_publish_v16_ga && make argo.pin VERSION=1.6.0 && make docs.build;;
  alerts) make nightly.alerts --dry-run;;
  v17) make feature.v17.init;;
  *) echo "usage: lumen {restore|ga|alerts|v17}";;
 esac
```

---

## 76) Session Restore integrity check

**scripts/restore_check.py**
```python
import os, hashlib
REQ = [
  "SESSION_RESTORE_2025-11-01_v1_6_FULL.yaml",
  "Makefile","docs","tools","scripts","dashboards","ops"
]
missing = [p for p in REQ if not os.path.exists(p)]
if missing:
    raise SystemExit(f"missing: {missing}")
print("restore: OK")
```

**Makefile**
```makefile
.PHONY: restore.check
restore.check:
	python3 scripts/restore_check.py
```

---

## 77) V17 feature-flag policy

```markdown
- Default: `V17_PREVIEW=0` (off)
- Enable only in non-prod or gated cohorts
- Any PR enabling in prod requires RFC + SRE sign-off
```

---

## 78) Risk / Decision Log

**docs/decisions/ADR-0001-v17-preview.md**
```markdown
# ADR-0001 — Gate v17 Preview Strategy
- Context: ACL v2 + event stream v2
- Decision: preview behind env flag; non-prod only
- Consequences: requires cohort config + observability
```

---

## 79) Migration Guide v1.6 → v1.7

```markdown
- Pin to 1.6.0, complete GA checklist
- Introduce RL3 & Tuner as optional services
- Add Gate v17 preview: off by default
- Update dashboards to include RL3 panels
```

---

## 80) Next-session copy block (ultra‑short)

```bash
source SESSION_RESTORE_2025-11-01_v1_6_FULL.yaml && make v16.unified && \
make release_publish_v16_ga && make argo.pin VERSION=1.6.0 && make docs.build && \
make nightly.alerts --dry-run && make feature.v17.init
```

---

## 81) RFC Process & Template

**docs/rfc/RFC-000-template.md**
```markdown
# RFC-000 — <Title>
- Status: Draft
- Owners: <names>
- Created: <YYYY-MM-DD>
- Target Release: v1.7
## Context
## Proposal
## Alternatives
## Risks
## Rollout Plan (guards, metrics, rollback)
## Appendix (schemas, diagrams)
```

**Makefile**
```makefile
.PHONY: rfc.new
rfc.new:
	@test -n "$(NAME)" || (echo NAME missing; exit 1)
	@num=$$(printf "%03d" $$(ls docs/rfc | wc -l)); \
	cp docs/rfc/RFC-000-template.md docs/rfc/RFC-$$num-$(NAME).md; \
	echo "RFC docs/rfc/RFC-$$num-$(NAME).md"
```

---

## 82) CODEOWNERS & SECURITY

**.github/CODEOWNERS**
```
/tools/ @bridge-team
/scripts/ @bridge-team
/ops/ @sre-team
/docs/ @docs-team
```

**SECURITY.md**
```markdown
# Security Policy
- Report vulnerabilities via private issue or email security@<org>.
- Do not disclose publicly until fix is released.
```

---

## 83) SUPPORT & MAINTAINERS

**SUPPORT.md**
```markdown
# Support
- Incidents: open Issue with label `incident`
- Questions: label `question`
- Docs fixes: PRs welcome
```

**MAINTAINERS.md**
```markdown
# Maintainers
- Binoche (Lead)
- Bridge team (Core)
- SRE team (Ops)
```

---

## 84) Sample Data Generators

**tools/gen_fake_metrics.py**
```python
#!/usr/bin/env python3
import random, time
while True:
    pd = random.uniform(-0.5,0.5)
    cb = random.random()
    print(f"phase_diff_stab {pd:.4f}")
    print(f"creative_band_occupancy {cb:.4f}")
    time.sleep(0.2)
```

**Makefile**
```makefile
.PHONY: fake.metrics
fake.metrics:
	python3 tools/gen_fake_metrics.py | head -n 20
```

---


## 85) Kubernetes Manifests (dev)

**ops/k8s/exporter-deploy.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: exporter }
spec:
  replicas: 1
  selector: { matchLabels: { app: exporter } }
  template:
    metadata: { labels: { app: exporter } }
    spec:
      containers:
        - name: exporter
          image: ghcr.io/<org>/<repo>/exporter:1.6.0
          ports: [{ containerPort: 8076 }]
          readinessProbe: { httpGet: { path: /ready, port: 8076 }, initialDelaySeconds: 3 }
```

---

## 86) kind Cluster (local e2e)

**ops/kind/cluster.yaml**
```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 30000
        hostPort: 30000
```

**Makefile**
```makefile
.PHONY: kind.up kind.down
kind.up:
	kind create cluster --name lumen --config ops/kind/cluster.yaml
kind.down:
	kind delete cluster --name lumen
```

---

## 87) Smoke Tests (post‑deploy)

**scripts/smoke.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
curl -fsSI ${GRAFANA_URL}
curl -fsSL ${PROOFD_STATS_URL} | head -n 5
```

**Makefile**
```makefile
.PHONY: smoke
smoke:
	bash scripts/smoke.sh
```

---

## 88) Performance Harness (simple)

**tools/latency_probe.py**
```python
import time, requests, statistics as st
url = "http://localhost:8077/stats"; samples = []
for _ in range(50):
    t0 = time.time(); requests.get(url, timeout=2)
    samples.append((time.time()-t0)*1000)
print(f"p95={sorted(samples)[int(len(samples)*0.95)]:.1f}ms")
```

---

## 89) Changelog gate in CI

**.github/workflows/ci.yml (append)**
```yaml
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Require CHANGELOG on release PRs
        run: |
          if [[ "${{ github.event.pull_request.title }}" == *"release"* ]] && \
             ! grep -q "##" CHANGELOG.md; then
            echo "CHANGELOG missing"; exit 1; fi
```

---

## 90) “All‑green” Dashboard Criteria

- Grafana reachable
- Exporter/Proofd ready
- Nightly dry‑run clean
- SBOM/Scan/Sign/Attest done
- Gatekeeper applied, 0 violations
- Backups created today
- Transition log updated

