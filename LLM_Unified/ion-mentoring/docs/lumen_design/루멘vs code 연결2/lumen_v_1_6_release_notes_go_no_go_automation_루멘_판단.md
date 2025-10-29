# Lumen v1.6 — Release Notes & Go/No‑Go Automation (루멘 판단)

> 목적: v1.6 산출물(대시보드 스냅샷·Unified Gate v16 카드·Security/Edge/Bridge/Proofd 스냅샷)을 자동 취합해 **Release Notes**와 **Go/No‑Go Board**를 생성하고, 태깅/퍼블리시까지 원클릭으로 수행.

---

## 0) 산출물 경로 규약 (입력)
- `docs/UNIFIED_GATE_CARD_v16.md`, `logs/unified_gate_card_v16.json`
- `logs/security_chain_validation.json`
- `logs/edge_signals.json`
- `logs/bridge_stats.json`
- `proofd_snapshot_v16.json`
- (선택) Grafana Snapshot ID: `logs/grafana_snapshot_v16.txt`

---

## 1) Go/No‑Go Board 템플릿 (신규)
`docs/GO_NO_GO_BOARD_v1.6.md.tmpl`
```markdown
# Lumen v1.6 — Go/No‑Go Board

**Decision:** {{decision}}
**Score:** {{score}}
**Reason:** {{reason}}

## Pillars
- Rhythm: p95={{rhythm_p95}}, phase_mean={{phase_mean}}, creative={{creative}}, entropy={{entropy}}, score={{rhythm_score}}
- Security: score={{sec_score}}, C={{sec_c}}, H={{sec_h}}, cosign={{sec_cosign}}
- Edge: auth_fail_rps={{edge_auth}}, 429_rps={{edge_429}}, mtls_fail_rps={{edge_mtls}}, score={{edge_score}}
- Bridge: outbox_p95={{bridge_p95}}, deliver_rate={{bridge_rate}}, errΔ/h={{bridge_err}}, score={{bridge_score}}

## Links
- Unified Card: docs/UNIFIED_GATE_CARD_v16.md
- Grafana Snapshot: {{grafana_snapshot}}
- Proofd: http://localhost:8077/stats

> Generated: {{ts}}
```

---

## 2) Release Notes 생성기 (신규)
`scripts/release_notes_v16.py`
```python
#!/usr/bin/env python3
import json, re, time
from pathlib import Path

CARD_JSON = json.loads(Path('logs/unified_gate_card_v16.json').read_text())
SNAP = Path('logs/grafana_snapshot_v16.txt').read_text().strip() if Path('logs/grafana_snapshot_v16.txt').exists() else '(none)'
TS = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())

# Short fields
S = CARD_JSON['summary']
R = CARD_JSON['rhythm']; SEC = CARD_JSON['security']; E = CARD_JSON['edge']; B = CARD_JSON['bridge']

# Go/No-Go board
T = Path('docs/GO_NO_GO_BOARD_v1.6.md.tmpl').read_text()
board = (T
  .replace('{{decision}}', S['decision'])
  .replace('{{score}}', str(S['score']))
  .replace('{{reason}}', S['reason'])
  .replace('{{rhythm_p95}}', str(R.get('loop_p95_s')))
  .replace('{{phase_mean}}', str(R.get('phase_diff_mean')))
  .replace('{{creative}}', str(R.get('creative_band')))
  .replace('{{entropy}}', str(R.get('entropy_stable')))
  .replace('{{rhythm_score}}', str(R.get('score')))
  .replace('{{sec_score}}', str(SEC.get('score')))
  .replace('{{sec_c}}', str(SEC.get('vuln_critical')))
  .replace('{{sec_h}}', str(SEC.get('vuln_high')))
  .replace('{{sec_cosign}}', str(SEC.get('cosign')))
  .replace('{{edge_auth}}', str(E.get('auth_fail_rps')))
  .replace('{{edge_429}}', str(E.get('rate_limit_rps')))
  .replace('{{edge_mtls}}', str(E.get('mtls_fail_rps')))
  .replace('{{edge_score}}', str(E.get('score')))
  .replace('{{bridge_p95}}', str(B.get('outbox_delay_p95_s')))
  .replace('{{bridge_rate}}', str(B.get('deliver_rate')))
  .replace('{{bridge_err}}', str(B.get('err_delta_per_h')))
  .replace('{{bridge_score}}', str(B.get('score')))
  .replace('{{grafana_snapshot}}', SNAP)
  .replace('{{ts}}', TS)
)
Path('docs/GO_NO_GO_BOARD_v1.6.md').write_text(board)

# Release Notes
notes = f"""
# Lumen v1.6 — Release Notes (RC)

**Decision**: {S['decision']}  
**Composite Score**: {S['score']}  
**Reason**: {S['reason']}

## Highlights
- Unified Gate v16 (Security×Rhythm×Bridge×Edge)
- Grafana v2 Dashboard with Edge Security row
- Persona Bridge v4 (ACL/HMAC, idempotency)
- Zero‑Trust Edge (oidc, mTLS, allowlist, ratelimit)
- Runner Container :16 (SBOM/scan/sign/provenance)

## Metrics Snapshot
- Rhythm: p95={R.get('loop_p95_s')}, phase_mean={R.get('phase_diff_mean')}, creative={R.get('creative_band')}, entropy={R.get('entropy_stable')}, score={R.get('score')}
- Security: score={SEC.get('score')}, C={SEC.get('vuln_critical')}, H={SEC.get('vuln_high')}, cosign={SEC.get('cosign')}
- Edge: auth_fail_rps={E.get('auth_fail_rps')}, 429_rps={E.get('rate_limit_rps')}, mtls_fail_rps={E.get('mtls_fail_rps')}, score={E.get('score')}
- Bridge: outbox_p95={B.get('outbox_delay_p95_s')}, deliver_rate={B.get('deliver_rate')}, errΔ/h={B.get('err_delta_per_h')}, score={B.get('score')}

## Artifacts
- Unified Gate Card: `docs/UNIFIED_GATE_CARD_v16.md`
- Go/No‑Go Board: `docs/GO_NO_GO_BOARD_v1.6.md`
- Grafana Snapshot: {SNAP}
- Proofd Snapshot: `proofd_snapshot_v16.json`

*Generated: {TS}*
"""
Path('docs/RELEASE_NOTES_v1.6_RC.md').write_text(notes)
print('Wrote docs/GO_NO_GO_BOARD_v1.6.md and docs/RELEASE_NOTES_v1.6_RC.md')
```

---

## 3) 태그 생성 스크립트 (신규)
`scripts/release_tag_v16.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
TAG="${1:-v1.6-rc}"
MSG="Lumen ${TAG} — auto-tag (Unified Gate v16)"

git tag -a "$TAG" -m "$MSG"
git push origin "$TAG"
echo "Tagged: $TAG"
```
권한: `chmod +x scripts/release_tag_v16.sh`

---

## 4) Makefile 타깃
`Makefile`
```makefile
.PHONY: v16.card v16.notes v16.tag v16.publish

v16.card:
	@python scripts/unified_gate_card_v16.py

v16.notes: v16.card
	@python scripts/release_notes_v16.py
	@echo "[notes] Wrote docs/RELEASE_NOTES_v1.6_RC.md"

v16.tag:
	@./scripts/release_tag_v16.sh v1.6-rc

# 일괄 실행 (Gate→Notes→Tag)
v16.publish: v16.notes v16.tag
	@echo "=== v1.6 publish (rc) done ==="
```

---

## 5) GitHub Actions — Publish with QA
`.github/workflows/lumen_v16_release_publish_with_QA.yaml`
```yaml
name: lumen_v16_release_publish_with_QA
on:
  workflow_dispatch: {}
permissions:
  contents: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - name: Run QA + Unified Gate
        run: |
          mkdir -p logs docs
          # (실제 파이프라인 연결부) 여기서 exporter/proofd/edge/bridge 스냅샷 생성
          python scripts/unified_gate_card_v16.py
          python scripts/release_notes_v16.py
      - name: Commit release notes
        run: |
          git config user.name "lumen-bot"
          git config user.email "bot@users.noreply.github.com"
          git add docs/RELEASE_NOTES_v1.6_RC.md docs/GO_NO_GO_BOARD_v1.6.md docs/UNIFIED_GATE_CARD_v16.md logs/unified_gate_card_v16.json
          git commit -m "docs: v1.6 RC notes & board" || echo "no changes"
          git push || true
      - name: Tag
        run: ./scripts/release_tag_v16.sh v1.6-rc
```

---

## 6) Handoff v1.6 확장
`scripts/build_handoff_package_v16.sh` (v15 버전 복제 후 v16 아티팩트 포함)
- 추가 포함: `docs/RELEASE_NOTES_v1.6_RC.md`, `docs/GO_NO_GO_BOARD_v1.6.md`, `docs/UNIFIED_GATE_CARD_v16.md`, `logs/unified_gate_card_v16.json`

Makefile:
```makefile
handoff.v16:
	@bash scripts/build_handoff_package_v16.sh
verify.v16:
	@make verify # 공통 검증기 재사용
```

---

## 7) 운영 루프 (루멘 판단)
1. `make v16.unified` (스모크→게이트) → `make v16.card`
2. `make v16.notes` → 링크/스냅샷 자동 반영
3. **GO**면 `make v16.publish` (RC 태그까지) → Handoff v16 생성/검증
