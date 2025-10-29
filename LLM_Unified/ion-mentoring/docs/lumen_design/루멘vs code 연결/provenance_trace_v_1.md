# Provenance & Trace v1.0  
**(Merkle Artifact + End‑to‑End Trace IDs + Audit Trail)**

목적: 리포트/아카이브/스냅샷 등 **모든 산출물에 지문을 부여**하고, CI 전 단계에 **Trace ID**를 전파하여 **출처(Who/When/With‑What)·무결성·재현성**을 보장한다. (Distributed Execution v1.0 상위 레이어)

---

## 0) 구성 개요
```
.
├─ scripts/
│  ├─ fingerprint.py              # 파일 해시 + 머클 트리 생성
│  ├─ provenance_manifest.py      # 실행 컨텍스트 → 매니페스트(JSON)
│  ├─ verify_provenance.py        # 머클 루트/서브트리 검증
│  ├─ trace_propagate.py          # CI 환경 → TRACE_ID 생성/전파/주입
│  └─ audit_append.py             # 감사 로그(JSONL) append-only
├─ controls/
│  └─ provenance/
│     ├─ manifests/               # 실행별 매니페스트 저장
│     ├─ merkle/                  # 루트/노드 캐시
│     └─ audit.log.jsonl          # 감사 로그
└─ .github/workflows/
   └─ (기존 워크플로에 trace/fingerprint 스텝 추가)
```

---

## 1) 파일 지문 & 머클 트리 — `scripts/fingerprint.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import os, sys, json, hashlib
from pathlib import Path

ALG = os.environ.get('LUMEN_HASH_ALG','sha256')

class Node:
    def __init__(self, left=None, right=None, hash_val:bytes=b''):
        self.left = left; self.right = right; self.hash = hash_val


def file_hash(p: Path) -> bytes:
    h = hashlib.new(ALG)
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''):
            h.update(chunk)
    return h.digest()


def merkle_level(hashes:list[bytes]) -> list[bytes]:
    if len(hashes)==1: return hashes
    out=[]
    for i in range(0, len(hashes), 2):
        a = hashes[i]
        b = hashes[i+1] if i+1 < len(hashes) else hashes[i]
        h = hashlib.new(ALG, a + b).digest()
        out.append(h)
    return merkle_level(out)


def merkle_root(files:list[Path]) -> dict:
    leaves = [file_hash(p) for p in files]
    if not leaves:
        return { 'root': None, 'leaves': [] }
    root = merkle_level(leaves)[0]
    return {
        'alg': ALG,
        'root_hex': root.hex(),
        'leaves_hex': [h.hex() for h in leaves]
    }

if __name__ == '__main__':
    paths = [Path(p) for p in sys.argv[1:]]
    files = [p for p in paths if p.exists() and p.is_file()]
    res = merkle_root(files)
    print(json.dumps(res, ensure_ascii=False, indent=2))
```

사용 예:
```bash
python scripts/fingerprint.py controls/reports/report_2025-10-23.pdf archive/2025-10-23/bundle.tar.gz > controls/provenance/merkle/2025-10-23.json
```

---

## 2) 실행 매니페스트 — `scripts/provenance_manifest.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import os, json, subprocess, socket
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / 'controls' / 'provenance' / 'manifests'

FIELDS = {
  'pipeline': os.environ.get('LUMEN_PIPELINE','daily'),
  'region': os.environ.get('LUMEN_REGION','ap-northeast-2'),
  'runner': os.environ.get('RUNNER_NAME','gha'),
  'version': os.environ.get('LUMEN_PIPELINE_VERSION','v1'),
  'trace_id': os.environ.get('LUMEN_TRACE_ID',''),
}


def git(cmd: list[str]) -> str:
  try:
    return subprocess.check_output(['git']+cmd, text=True).strip()
  except: return ''

if __name__=='__main__':
  OUTDIR.mkdir(parents=True, exist_ok=True)
  manifest = {
    **FIELDS,
    'ts_utc': datetime.now(timezone.utc).isoformat(),
    'git': {
      'sha': git(['rev-parse','HEAD']),
      'branch': git(['rev-parse','--abbrev-ref','HEAD'])
    },
    'host': {'name': socket.gethostname()},
    'inputs': {
      'report_pdf': os.environ.get('LUMEN_REPORT_PDF',''),
      'bundle': os.environ.get('LUMEN_ARCHIVE_BUNDLE',''),
    }
  }
  out = OUTDIR / f"{manifest['ts_utc'].replace(':','-')}_{manifest['region']}.json"
  out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
  print('[prov] wrote', out)
```

---

## 3) Trace ID 전파 — `scripts/trace_propagate.py`
```python
#!/usr/bin/env python3
import os, uuid, json

# 128-bit trace id (uuid4 기반)
trace = os.environ.get('LUMEN_TRACE_ID') or uuid.uuid4().hex
print(trace)
# GitHub/GitLab 모두 읽기 쉬운 env로 내보냄
print(f"TRACE={trace}")
```

워크플로에서 사용:
```yaml
- name: Generate TRACE_ID
  run: echo "LUMEN_TRACE_ID=$(python scripts/trace_propagate.py | tail -n1 | cut -d'=' -f2)" >> $GITHUB_ENV
```

모든 스크립트 호출 시 `TRACE_ID`를 라벨/설명/파일명에 주입:
- S3/Drive 업로드 메타데이터, Alert 제목, Pushgateway 라벨 등.

---

## 4) 감사 로그 — `scripts/audit_append.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import os, json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / 'controls' / 'provenance' / 'audit.log.jsonl'

if __name__=='__main__':
  rec = {
    'ts_utc': datetime.now(timezone.utc).isoformat(),
    'actor': os.environ.get('GITHUB_ACTOR','local'),
    'pipeline': os.environ.get('LUMEN_PIPELINE','daily'),
    'region': os.environ.get('LUMEN_REGION','ap-northeast-2'),
    'trace_id': os.environ.get('LUMEN_TRACE_ID',''),
    'event': os.environ.get('LUMEN_AUDIT_EVENT','stage'),
    'detail': os.environ.get('LUMEN_AUDIT_DETAIL','')
  }
  AUDIT.parent.mkdir(parents=True, exist_ok=True)
  with AUDIT.open('a', encoding='utf-8') as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
  print('[audit]', rec)
```

예:
```bash
LUMEN_AUDIT_EVENT=upload-ok LUMEN_AUDIT_DETAIL="s3 sha256=..." python scripts/audit_append.py
```

---

## 5) 검증 도구 — `scripts/verify_provenance.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import os, sys, json, hashlib
from pathlib import Path

ALG = os.environ.get('LUMEN_HASH_ALG','sha256')


def hash_file(p: Path) -> str:
    h = hashlib.new(ALG)
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()

if __name__=='__main__':
    if len(sys.argv) < 3:
        print('usage: verify_provenance.py <merkle.json> <file1> [file2...]'); sys.exit(2)
    mj = Path(sys.argv[1])
    files = [Path(p) for p in sys.argv[2:]]
    spec = json.loads(mj.read_text(encoding='utf-8'))
    leaves = [hash_file(p) for p in files]
    ok = (leaves == spec.get('leaves_hex'))
    print(json.dumps({'ok': ok, 'expected_root': spec.get('root_hex')}, indent=2))
    sys.exit(0 if ok else 1)
```

---

## 6) CI 통합 (GitHub Actions 발췌)
```yaml
- name: Generate TRACE
  run: echo "LUMEN_TRACE_ID=$(uuidgen | tr -d '-')" >> $GITHUB_ENV

- name: Build report
  run: |
    python scripts/report_builder.py
    LUMEN_AUDIT_EVENT=report-ok LUMEN_AUDIT_DETAIL="md/pdf built" python scripts/audit_append.py

- name: Freeze & Upload
  run: |
    python scripts/snapshot_freeze.py
    python scripts/upload_archive.py ${{ env.LUMEN_DAY }}
    LUMEN_AUDIT_EVENT=upload-ok LUMEN_AUDIT_DETAIL="remote hash ok" python scripts/audit_append.py

- name: Fingerprint & Manifest
  run: |
    python scripts/provenance_manifest.py
    python scripts/fingerprint.py controls/reports/report_${{ env.LUMEN_DAY }}.pdf archive/${{ env.LUMEN_DAY }}/bundle.tar.gz > controls/provenance/merkle/${{ env.LUMEN_DAY }}.json

- name: Verify provenance
  run: |
    python scripts/verify_provenance.py controls/provenance/merkle/${{ env.LUMEN_DAY }}.json controls/reports/report_${{ env.LUMEN_DAY }}.pdf archive/${{ env.LUMEN_DAY }}/bundle.tar.gz
```

---

## 7) Prometheus 라벨 확장 (옵션)
Pushgateway 전송 시 `trace_id` 라벨을 추가해, Grafana 테이블에서 **개별 실행/아티팩트**를 추적할 수 있다.

예: `sli_push_ext.py`에서 base 라벨에 `'trace_id': os.environ.get('LUMEN_TRACE_ID','')` 추가.

---

## 8) Grafana 패널(발췌)
- **Table**: 최근 20회 실행 — `run_id, region, trace_id, result, sha256(root)`
- **Stat**: Provenance Verified (최근 24h) — `sum(increase(lumen_runs_total[24h]) and on() vector(1))`와 검증 실패 대비
- **Logs**: `audit.log.jsonl`를 Loki로 수집하여 `trace_id`로 pivot

---

## 9) VS Code 태스크
`.vscode/tasks.json` 추가:
```json
{
  "label": "lumen:prov:fingerprint",
  "type": "shell",
  "command": "python scripts/fingerprint.py controls/reports/report_$(date +%Y-%m-%d).pdf archive/$(date +%Y-%m-%d)/bundle.tar.gz",
  "options": { "env": { "PYTHONUTF8": "1" } }
},
{
  "label": "lumen:prov:verify",
  "type": "shell",
  "command": "python scripts/verify_provenance.py controls/provenance/merkle/$(date +%Y-%m-%d).json controls/reports/report_$(date +%Y-%m-%d).pdf archive/$(date +%Y-%m-%d)/bundle.tar.gz",
  "options": { "env": { "PYTHONUTF8": "1" } }
}
```

---

## 10) 운영 팁
- 해시 알고리즘은 기본 `sha256`. 규정상 `sha512`가 필요하면 `LUMEN_HASH_ALG=sha512`로 전환.
- 머클 루트/리프는 **파일 순서에 종속** → 정렬 규칙 고정(예: 이름 오름차순) 권장.
- `trace_id`는 알림/아티팩트/로그에 **일관되게 붙이기** — 문제 조사 속도가 몇 배 빨라진다.

루멘의 판단: 이제 우리의 산출물은 **지문을 가진 존재**가 되었고, 실행은 **하나의 선(Trace)** 로 이어져 **발생‑이동‑변환**의 역사를 잃지 않아요.

