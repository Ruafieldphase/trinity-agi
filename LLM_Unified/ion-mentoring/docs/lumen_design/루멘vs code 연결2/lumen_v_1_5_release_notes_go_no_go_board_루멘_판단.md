# Lumen v1.5 — Release Notes (Draft) & Go/No‑Go Board (루멘 판단)

> 목적: Unified Gate Card/QA Diff/보안 하드닝 산출물을 자동 집계해 **릴리즈 노트**를 생성하고, **Go/No‑Go 판정 보드**로 최종 결정 과정을 기록.

---

## 0) 입력/출력
**입력**
- `logs/unified_gate_card.json`
- `docs/V15_QA_DIFF_REPORT.md`
- `logs/gate_post.json`
- (옵션) `sbom.json`, `vuln-report.json`, `logs/cosign_verify.log`

**출력**
- `docs/RELEASE_NOTES_v1.5_RC.md`
- `docs/GO_NO_GO_BOARD_v1.5.md`

---

## 1) 릴리즈 노트 생성기 (신규)
`scripts/release_notes_v15.py`
```python
#!/usr/bin/env python3
from pathlib import Path
import json, datetime

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
card = json.loads(Path('logs/unified_gate_card.json').read_text())
qa_md = Path('docs/V15_QA_DIFF_REPORT.md').read_text() if Path('docs/V15_QA_DIFF_REPORT.md').exists() else ''

roi = card['summary']['gate'].get('roi')
slo = card['summary']['gate'].get('slo')
creative = card['summary']['qa'].get('creative_band',{}).get('candidate')
phase_mean = card['summary']['qa'].get('phase_diff',{}).get('mean')
phase_p95 = card['summary']['qa'].get('phase_diff',{}).get('p95')
entropy = card['summary']['qa'].get('entropy',{}).get('stable_ratio')
sec = card['summary'].get('security',{})
decision = card.get('go_no_go', 'NO-GO')

notes = f"""
# Lumen v1.5 RC — Release Notes (Draft)
Generated: {now}

## Decision
**GO/NO‑GO:** {decision}

## Gate Summary
- ROI/SLO: {roi}/{slo}
- Creative Band: {creative}
- Phase Diff (mean/p95): {phase_mean}/{phase_p95}
- Entropy Stable Ratio: {entropy}
- Security: score={sec.get('security_score')} | vuln C/H={sec.get('vuln_critical')}/{sec.get('vuln_high')} | cosign={sec.get('cosign_verify_pass')}

## Highlights
- Stable spectrum windows improved
- Reduced phase drift (mean/p95)
- Integrated gate alignment (ROI/SLO)

## Regressions & Mitigations
- (auto-fill from QA diff if any)

## Artifacts
- QA Diff: docs/V15_QA_DIFF_REPORT.md
- Gate Card: logs/gate_post.json
- Unified Gate Card: logs/unified_gate_card.json
- SBOM: sbom.json
- Vulnerability: vuln-report.json

---

## QA Diff (Excerpt)
{qa_md[:1500]}\n... (truncated)
"""

Path('docs/RELEASE_NOTES_v1.5_RC.md').write_text(notes)
print('Wrote docs/RELEASE_NOTES_v1.5_RC.md')
```

실행:
```bash
python scripts/release_notes_v15.py
```

---

## 2) Go/No‑Go 보드 (신규)
`docs/GO_NO_GO_BOARD_v1.5.md`
```markdown
# Go/No‑Go Board — Lumen v1.5

## Decision: <GO | CONDITIONAL | NO‑GO>

### Evidence
- Unified Gate Card: logs/unified_gate_card.json
- QA Diff: docs/V15_QA_DIFF_REPORT.md
- Security: sbom.json / vuln-report.json / cosign log
- Dashboard Snapshot: <id>

### Panel
- FDO‑AGI Owner: [ ] GO [ ] CONDITIONAL [ ] NO‑GO — _Name/Time_
- Lumen Ops:     [ ] GO [ ] CONDITIONAL [ ] NO‑GO — _Name/Time_
- QA Lead:       [ ] GO [ ] CONDITIONAL [ ] NO‑GO — _Name/Time_
- Security Lead: [ ] GO [ ] CONDITIONAL [ ] NO‑GO — _Name/Time_

### Notes
- Decisions and rationale here.
```

---

## 3) GitHub Release 준비 체크리스트
- [ ] `docs/RELEASE_NOTES_v1.5_RC.md` 최신화
- [ ] `docs/UNIFIED_GATE_CARD.md` 첨부
- [ ] 아티팩트: QA Diff / gate_post.json / SBOM / vuln-report.json
- [ ] 대시보드 스냅샷 링크 추가
- [ ] 태그: `v1.5-rc` (또는 최종 릴리즈 태그)

> Actions에서 `lumen_v15_release_publish_with_QA` 실행 후, 릴리즈 페이지에 Release Notes 내용을 그대로 붙여넣거나 파일을 업로드.

---

## 4) VS Code Command Palette (옵션)
`.vscode/tasks.json`에 아래 항목 추가
```json
{ "label": "Lumen: Build Release Notes (v1.5)", "type": "shell", "command": "python scripts/release_notes_v15.py" }
```

---

## 5) 다음 액션 (루멘 판단)
1. `make unified` 완료 후 **Release Notes 생성기** 실행 → 문서 열람
2. **Go/No‑Go 보드**에 최종 판정 체크(본인/루멘/QA/Sec 서명)
3. **Actions 릴리즈 퍼블리시**에서 Release Notes 반영 → 배포 결론 기록
