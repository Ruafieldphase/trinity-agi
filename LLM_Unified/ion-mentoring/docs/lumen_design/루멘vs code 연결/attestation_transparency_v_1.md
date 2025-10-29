# Attestation & Transparency v1.0  
**(DSSE + In‑Toto Style + Read‑Only TLog Server)**

목적: 빌드/보고/아카이브 전 과정에 대해 **표준화된 증명(Attestation)**을 발행하고, **투명성 로그(TLog)**에 영구 기록하여 **검증 가능성**과 **공급망 신뢰**를 완성한다. Trust Chain·Root Custody·Signature 레이어와 연동된다.

---

## 0) 개념 요약
- **DSSE(Dead Simple Signing Envelope)**: payload(증명) + 서명자를 담는 경량 컨테이너
- **in‑toto 스타일 증명**: _subject(산출물), materials(입력), byproducts(메트릭/해시), builder(환경)_을 구조화
- **Transparency Log**: append‑only 머클 로그 + **Inclusion Proof** 제공 (Read‑Only API)

---

## 1) 파일 구조
```
.
├─ attest/
│  ├─ schema/
│  │  └─ intoto_attestation.v1.json
│  ├─ dsse_sign.py             # DSSE 서명기(Ed25519)
│  ├─ dsse_verify.py           # DSSE 검증기(체인+서명)
│  ├─ make_attestation.py      # in‑toto 스타일 증명 생성
│  ├─ attach_to_artifact.py    # 산출물 옆에 .att.json 저장
│  ├─ verify_attestation.py    # 산출물↔증명 상호검증
│  └─ tlog/
│     ├─ server.py             # Read‑only Transparency API (FastAPI)
│     ├─ merkle.py             # 머클 로그/증명 생성
│     ├─ db.jsonl              # append‑only 저장소
│     └─ proofs/               # 증명 스냅샷
└─ .vscode/tasks.json          # 빌드/서명/등록/검증 태스크
```

---

## 2) in‑toto 스타일 스키마 (요약)
`attest/schema/intoto_attestation.v1.json`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Intoto Attestation v1",
  "type": "object",
  "required": ["_type", "subject", "predicateType", "predicate"],
  "properties": {
    "_type": {"const": "https://in-toto.io/Statement/v1"},
    "subject": {"type":"array", "items":{"type":"object","required":["name","digest"],"properties":{"name":{"type":"string"},"digest":{"type":"object"}}}},
    "predicateType": {"type":"string"},
    "predicate": {
      "type": "object",
      "required": ["builder","buildType","invocation","metadata"],
      "properties": {
        "builder": {"type":"object","required":["id"],"properties":{"id":{"type":"string"}}},
        "buildType": {"type":"string"},
        "invocation": {"type":"object"},
        "materials": {"type":"array"},
        "byproducts": {"type":"object"},
        "metadata": {"type":"object","properties":{"buildStartedOn":{"type":"string"},"buildFinishedOn":{"type":"string"}}}
      }
    }
  }
}
```

---

## 3) DSSE 서명/검증
`attest/dsse_sign.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import json, base64, hashlib, os
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

TYPE = "application/vnd.in-toto+json"

ROOT = Path(__file__).resolve().parents[1]
PRIV = ROOT/'controls'/'keys'/'current'/'signer_priv.pem'
CERT = ROOT/'controls'/'keys'/'current'/'signer_cert.pem'
ROOT_CA = ROOT/'controls'/'keys'/'root'/'root_ca_cert.pem'

HEADER = {"payloadType": TYPE}


def b64(b: bytes) -> str:
    return base64.b64encode(b).decode()

if __name__=='__main__':
    import sys
    data = Path(sys.argv[1]).read_bytes()
    payload = b64(data)
    priv = serialization.load_pem_private_key(PRIV.read_bytes(), password=os.environ.get('LUMEN_SIGNER_PASS','').encode() or None)
    to_sign = ("DSSEv1".encode()+b" "+TYPE.encode()+b" "+str(len(data)).encode()+b"\n"+data)
    sig = priv.sign(hashlib.sha256(to_sign).digest())
    env = {
        "payloadType": TYPE,
        "payload": payload,
        "signatures": [{
            "keyid": hashlib.sha256(Path(CERT).read_bytes()).hexdigest(),
            "sig": b64(sig),
            "cert": CERT.read_text('utf-8')
        }]
    }
    out = Path(sys.argv[1]).with_suffix('.att.json')
    out.write_text(json.dumps(env, ensure_ascii=False, indent=2), encoding='utf-8')
    print('[dsse] wrote', out)
```

`attest/dsse_verify.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import json, base64, hashlib, sys
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import serialization

TYPE = "application/vnd.in-toto+json"

if __name__=='__main__':
    f = Path(sys.argv[1])
    root = Path(sys.argv[2])
    env = json.loads(f.read_text('utf-8'))
    payload = base64.b64decode(env['payload'])
    sig = base64.b64decode(env['signatures'][0]['sig'])
    cert_pem = env['signatures'][0]['cert']
    signer = x509.load_pem_x509_certificate(cert_pem.encode('utf-8'))
    root_cert = x509.load_pem_x509_certificate(Path(root).read_bytes())
    # chain check
    root_cert.public_key().verify(signer.signature, signer.tbs_certificate_bytes)
    # dsse
    to_sign = ("DSSEv1".encode()+b" "+TYPE.encode()+b" "+str(len(payload)).encode()+b"\n"+payload)
    signer.public_key().verify(sig, hashlib.sha256(to_sign).digest())
    print(json.dumps({"ok": True, "subject": json.loads(payload).get('subject',[])}, indent=2))
```

---

## 4) in‑toto 증명 생성/부착/검증
`attest/make_attestation.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import json, os, hashlib
from pathlib import Path
from datetime import datetime, timezone

if __name__=='__main__':
    art = Path(os.environ.get('LUMEN_ARTIFACT', 'controls/reports/report.pdf'))
    subject = {"name": art.name, "digest": {"sha256": hashlib.sha256(art.read_bytes()).hexdigest()}}
    att = {
      "_type": "https://in-toto.io/Statement/v1",
      "subject": [subject],
      "predicateType": "https://slsa.dev/provenance/v1",
      "predicate": {
        "builder": {"id": os.environ.get('BUILDER_ID','lumen-ci')},
        "buildType": "lumen/daily-report@v1",
        "invocation": {"configSource": {"uri": os.environ.get('GIT_URL',''), "digest": {"git": os.environ.get('GIT_SHA','')}}},
        "materials": [{"uri": "grafana://dashboard", "digest": {"rev": os.environ.get('GRAFANA_REV','')}}],
        "byproducts": {"pdf_pages": int(os.environ.get('PDF_PAGES','0'))},
        "metadata": {"buildStartedOn": os.environ.get('BUILD_START',''), "buildFinishedOn": datetime.now(timezone.utc).isoformat()}
      }
    }
    out = art.with_suffix('.intoto.json')
    out.write_text(json.dumps(att, ensure_ascii=False, indent=2), encoding='utf-8')
    print('[att] wrote', out)
```

`attest/attach_to_artifact.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import shutil, sys

if __name__=='__main__':
    art = Path(sys.argv[1])
    att = art.with_suffix('.intoto.json')
    dsse = art.with_suffix('.att.json')
    dest_dir = art.parent
    for p in [att, dsse]:
        if p.exists(): shutil.copy2(p, dest_dir/p.name)
    print('[attach] ok ->', dest_dir)
```

`attest/verify_attestation.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib, sys
from pathlib import Path

if __name__=='__main__':
    art = Path(sys.argv[1])
    att = json.loads(art.with_suffix('.intoto.json').read_text('utf-8'))
    d = att['subject'][0]['digest']['sha256']
    ok = (hashlib.sha256(art.read_bytes()).hexdigest() == d)
    print(json.dumps({'ok': ok, 'subject': att['subject'][0]['name']}, indent=2))
    sys.exit(0 if ok else 1)
```

---

## 5) Transparency Log (머클 로그 + API)
`attest/tlog/merkle.py`
```python
from __future__ import annotations
import hashlib, json

class MerkleLog:
    def __init__(self):
        self.leaves = []  # list of hex digests

    def add(self, payload: bytes) -> dict:
        h = hashlib.sha256(payload).hexdigest()
        self.leaves.append(h)
        idx = len(self.leaves)-1
        root, proof = self._build_proof(idx)
        return { 'index': idx, 'leafHash': h, 'rootHash': root, 'proof': proof }

    def _build_proof(self, i:int):
        level = [bytes.fromhex(x) for x in self.leaves]
        proof = []
        idx = i
        while len(level) > 1:
            if len(level) % 2 == 1:
                level.append(level[-1])
            pair_idx = idx ^ 1
            proof.append(level[pair_idx].hex())
            nxt = []
            for a,b in zip(level[0::2], level[1::2]):
                nxt.append(hashlib.sha256(a+b).digest())
            level = nxt
            idx = idx // 2
        root = level[0].hex() if level else None
        return root, proof

    @staticmethod
    def verify(leaf_hex: str, proof: list[str], root_hex: str, index: int) -> bool:
        h = bytes.fromhex(leaf_hex)
        idx = index
        for sib_hex in proof:
            sib = bytes.fromhex(sib_hex)
            if idx % 2 == 0:
                h = hashlib.sha256(h + sib).digest()
            else:
                h = hashlib.sha256(sib + h).digest()
            idx //= 2
        return h.hex() == root_hex
```

`attest/tlog/server.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
from .merkle import MerkleLog

app = FastAPI(title='Lumen TLog (read-only)')
DB = Path(__file__).resolve().parent/'db.jsonl'
LOG = MerkleLog()

class Entry(BaseModel):
    payload: str  # base64 or json string

# 초기화: 파일에서 로드 (append-only)
if DB.exists():
    for line in DB.read_text('utf-8').splitlines():
        obj = json.loads(line)
        LOG.leaves.append(obj['leafHash'])

@app.get('/v1/log/root')
async def root():
    root = LOG._build_proof(len(LOG.leaves)-1)[0] if LOG.leaves else None
    return { 'size': len(LOG.leaves), 'rootHash': root }

@app.get('/v1/log/entry/{index}')
async def entry(index: int):
    if index < 0 or index >= len(LOG.leaves):
        raise HTTPException(404)
    leaf = LOG.leaves[index]
    root, proof = LOG._build_proof(index)
    return { 'index': index, 'leafHash': leaf, 'rootHash': root, 'proof': proof }

# 등록은 CI에서만: 파일에 append → 서버는 재기동 시 로드(읽기 전용 배포)
```

> 운영 배포는 **읽기 전용(RO)** 서버만 노출하고, 등록은 CI에서 `db.jsonl`에 append로 수행 → 이미지 재배포.

---

## 6) CI 통합 (발췌)
```yaml
- name: Make attestation (in-toto)
  run: |
    export LUMEN_ARTIFACT=controls/reports/report_${{ env.LUMEN_DAY }}.pdf
    python attest/make_attestation.py

- name: DSSE sign attestation
  run: |
    python attest/dsse_sign.py controls/reports/report_${{ env.LUMEN_DAY }}.intoto.json

- name: Verify attestation (dsse + chain)
  run: |
    python attest/dsse_verify.py controls/reports/report_${{ env.LUMEN_DAY }}.att.json controls/keys/root/root_ca_cert.pem

- name: Attach sidecars
  run: |
    python attest/attach_to_artifact.py controls/reports/report_${{ env.LUMEN_DAY }}.pdf

- name: Append to TLog (CI only)
  run: |
    jq -c '{leafHash: (.["signatures"][0].sig)}' controls/reports/report_${{ env.LUMEN_DAY }}.att.json >> attest/tlog/db.jsonl
```

---

## 7) VS Code 태스크
`.vscode/tasks.json` 추가:
```json
{
  "label": "lumen:attest:make+sign",
  "type": "shell",
  "command": "export LUMEN_ARTIFACT=controls/reports/report_$(date +%Y-%m-%d).pdf && python attest/make_attestation.py && python attest/dsse_sign.py controls/reports/report_$(date +%Y-%m-%d).intoto.json",
  "options": { "env": { "PYTHONUTF8": "1" } }
},
{
  "label": "lumen:attest:verify",
  "type": "shell",
  "command": "python attest/dsse_verify.py controls/reports/report_$(date +%Y-%m-%d).att.json controls/keys/root/root_ca_cert.pem && python attest/verify_attestation.py controls/reports/report_$(date +%Y-%m-%d).pdf",
  "options": { "env": { "PYTHONUTF8": "1" } }
}
```

---

## 8) 대시보드/알림 연계
- **SLI 대시보드**에 “Attestation Verified” 패널 추가: 최근 30일 검증 비율
- **알림**: DSSE 검증 실패/체인 실패/머클 포함증명 실패 시 `severity: page`

---

## 9) 보안 메모
- 증명에는 **민감정보 금지**(경로/해시/버전만) — 개인 데이터 포함 금지
- DSSE 서명키는 기존 **Signer Cert**와 동일 계층 사용(회전/CRL 정책 상속)
- TLog는 **공개 읽기 전용**, 쓰기는 **CI 이미지 빌드 타임**에만 수행

---

## 10) 롤링 도입 계획
1) 보고서 PDF → 증명/DSSE 상용 운용부터 시작
2) 스냅샷 번들/지표 산출물로 확장, 재현데이터(materials) 점진 추가
3) 외부 검증자에게 TLog API RO 엔드포인트 공개

루멘의 판단: 이제 산출물은 **증명(Attestation)**과 **투명성 로그**까지 갖추어, 출처와 진위를 **누구나 재현 가능**한 방식으로 보증할 수 있다.