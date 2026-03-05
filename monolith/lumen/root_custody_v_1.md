# Root Custody v1.1  
**Ceremony Kit: Printable PDFs + QR Manifest + Auto-Archive Sync**

목적: Root Custody v1.0의 운영 절차를 **인쇄 가능한 키트**로 묶고, 의식 산출물을 **QR/Manifest**로 표준화하며, 기록을 **자동 동기화**해 감사를 쉽게 합니다.

---

## 0) 디렉터리
```
.
├─ custody/
│  ├─ checklists/                  # MD 원본
│  ├─ prints/                      # PDF/QR 출력물 저장
│  ├─ records/                     # ceremony 기록(JSON)
│  └─ tools/                       # 생성 스크립트
├─ controls/
│  ├─ provenance/                  # v1.0에서 사용
│  └─ trust/                       # chain/crl/tlog
└─ .vscode/tasks.json              # 인쇄·동기화 태스크
```

---

## 1) 체크리스트 → PDF 변환기
`custody/tools/print_checklists.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import os, re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT/'custody'/'checklists'
OUT = ROOT/'custody'/'prints'

TITLE_MAP = {
  '01_initial_setup.md': 'Initial Root Setup — Checklist',
  '02_offline_signing.md': 'Offline Signing — Checklist',
  '03_quarterly_audit.md': 'Quarterly Audit — Checklist',
  '04_incident_response.md': 'Incident Response — Checklist',
}

CHK_PAT = re.compile(r"^\- \[ \] (.*)$")


def render_pdf(md_path: Path, pdf_path: Path):
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    W, H = A4
    x, y = 20*mm, H - 25*mm
    title = TITLE_MAP.get(md_path.name, md_path.stem)
    c.setFont('Helvetica-Bold', 16)
    c.drawString(x, y, title); y -= 8*mm
    c.setFont('Helvetica', 10)
    c.drawString(x, y, f"Source: {md_path}"); y -= 6*mm
    c.line(x, y, W-20*mm, y); y -= 6*mm

    for line in md_path.read_text(encoding='utf-8').splitlines():
        m = CHK_PAT.match(line)
        if not m: continue
        text = m.group(1)
        # checkbox square
        c.rect(x, y-3*mm, 4*mm, 4*mm)
        c.drawString(x+6*mm, y, text)
        y -= 7*mm
        if y < 25*mm:
            c.showPage(); y = H - 25*mm
            c.setFont('Helvetica-Bold', 12); c.drawString(x, y, title); y -= 8*mm
    c.showPage(); c.save()

if __name__=='__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for src in SRC.glob('*.md'):
        render_pdf(src, OUT/(src.stem + '.pdf'))
    print('[print] wrote PDFs to', OUT)
```

> 의존성: `pip install reportlab`

---

## 2) QR Manifest Generator
`custody/tools/qr_manifest.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import json, os
from pathlib import Path
import qrcode

ROOT = Path(__file__).resolve().parents[2]
TRUST = ROOT/'controls'/'trust'
OUT = ROOT/'custody'/'prints'

if __name__=='__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    chain = json.loads((TRUST/'chain_manifest.json').read_text(encoding='utf-8'))
    payload = {
        'root_fp': chain['root_fingerprint_sha256'],
        'policy': chain.get('policy', {}),
        'crl': chain['policy'].get('crl',''),
        'ts': os.environ.get('CEREMONY_TS','')
    }
    img = qrcode.make(json.dumps(payload, ensure_ascii=False))
    out = OUT/'chain_manifest.qr.png'
    img.save(out)
    print('[qr] wrote', out)
```

> 의존성: `pip install qrcode[pil]`

---

## 3) Ceremony Packet Composer (PDF 표지 + QR 합본)
`custody/tools/compose_packet.py`
```python
#!/usr/bin/env python3
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from PIL import Image
from pathlib import Path
import datetime

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'custody'/'prints'

if __name__=='__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    W,H = A4
    pdf = canvas.Canvas(str(OUT/'ceremony_packet.pdf'), pagesize=A4)
    pdf.setFont('Helvetica-Bold', 18)
    pdf.drawString(20*mm, H-25*mm, 'Lumen Root Ceremony Packet')
    pdf.setFont('Helvetica', 10)
    pdf.drawString(20*mm, H-35*mm, 'Includes: Checklists, Chain Manifest (QR), Seal Log')

    # QR
    qr = Image.open(OUT/'chain_manifest.qr.png')
    qr_w = 50*mm
    qr_h = qr_w
    qr = qr.resize((int(qr_w), int(qr_h)))
    qr_path = OUT/'qr_temp.jpg'
    qr.save(qr_path)
    pdf.drawImage(str(qr_path), W-20*mm-qr_w, H-70*mm, qr_w, qr_h)

    pdf.drawString(20*mm, H-60*mm, f"Generated: {datetime.datetime.utcnow().isoformat()}Z")
    pdf.drawString(20*mm, H-70*mm, "Seal IDs: __________  /  Witnesses: __________, __________")

    pdf.showPage(); pdf.save()
    print('[packet] ceremony_packet.pdf ready')
```

> 의존성: `pip install pillow reportlab`

---

## 4) Auto-Archive Sync — 의식 산출물 정리
`custody/tools/auto_sync.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUST = ROOT/'custody'
PROV = ROOT/'controls'/'provenance'
TRUST = ROOT/'controls'/'trust'

TARGETS = [
    (CUST/'records', PROV/'manifests'/'custody'),
    (CUST/'prints',  TRUST/'custody_prints')
]

if __name__=='__main__':
    for src, dst in TARGETS:
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.rglob('*'):
            if f.is_file():
                shutil.copy2(f, dst/f.name)
    print('[sync] custody artifacts copied')
```

---

## 5) VS Code 태스크
`.vscode/tasks.json`에 추가:
```json
{
  "label": "lumen:custody:print-all",
  "type": "shell",
  "command": "python custody/tools/print_checklists.py && python custody/tools/qr_manifest.py && python custody/tools/compose_packet.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" }
},
{
  "label": "lumen:custody:sync",
  "type": "shell",
  "command": "python custody/tools/auto_sync.py",
  "options": { "env": { "PYTHONUTF8": "1" } }
}
```

---

## 6) Grafana — Custody Ledger 패널(요약)
`grafana/dashboards/custody_ledger.json` (발췌)
```json
{
  "title": "Lumen – Custody Ledger",
  "panels": [
    {"type":"table","title":"Ceremony Records","targets":[{"expr":"loki query to custody/records"}]},
    {"type":"stat","title":"Last Ceremony Age","targets":[{"expr":"time()-last_over_time(custody_ceremony_timestamp[365d])"}]}
  ]
}
```
> 운영 환경에 맞춰 Loki/Promtail로 `custody/records/*.json`을 수집하면 검색이 쉬워집니다.

---

## 7) 운영 루틴
1) 의식 전: `lumen:custody:print-all` 실행 → PDF/QR 패킷 준비  
2) 의식 중: 체크리스트 수기 기록, 봉인 ID·서명 기입  
3) 의식 후: 사진·기록 JSON을 `/custody/records`에 저장 → `lumen:custody:sync` 실행  
4) CI/대시보드에서 체인 지문·CRL·투명성 로그 일치 확인

---

## 8) 보안 메모
- 출력물의 디지털 사본은 **읽기 전용** 저장소에 보관, 접근 로깅 활성화
- QR 페이로드에는 **민감정보 금지**(지문/정책 경로만)
- `auto_sync.py`는 **덮어쓰기 주의**: 필요 시 날짜 접두사로 보강

루멘의 판단: 이제 의식은 **준비→실행→기록→동기화**가 한 흐름으로 닫혔고, 지문과 정책이 **눈으로 보고 손으로 확인**되는 형태로 남습니다. 다음 박자에는 **오프라인 Ceremony Simulator**(드릴/교육용)도 붙일 수 있어요.