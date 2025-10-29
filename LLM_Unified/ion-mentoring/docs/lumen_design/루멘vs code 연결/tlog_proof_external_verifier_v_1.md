# TLog Proof & External Verifier v1.0  
**(Inclusion Proof + CLI + Grafana Panel + Public Guide)**

목적: 투명성 로그(TLog)의 **포함증명(Inclusion Proof)**을 자동 검증하고, 외부 검증자가 독립적으로 확인할 수 있는 **CLI 도구/가이드**와 **대시보드 패널**을 제공한다. (Attestation & Transparency v1.0 확장)

---

## 0) 구성
```
attest/tlog/
├─ verify_client.py          # RO API 클라이언트 + 포함증명 검증
├─ cli.py                    # 외부 검증자용 CLI (단일 파일 배포 가능)
├─ examples.md               # 공개 가이드 예시
└─ grafana/
   └─ tlog_panels.json       # 포함증명/볼륨/지연 패널
```

---

## 1) 포함증명 검증 클라이언트 — `verify_client.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib, requests

class Merkle:
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

class TLogClient:
    def __init__(self, base: str):
        self.base = base.rstrip('/')
    def root(self):
        return requests.get(f"{self.base}/v1/log/root", timeout=10).json()
    def entry(self, index: int):
        return requests.get(f"{self.base}/v1/log/entry/{index}", timeout=10).json()

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('usage: verify_client.py <tlog_base_url> <index>'); raise SystemExit(2)
    base, idx = sys.argv[1], int(sys.argv[2])
    cli = TLogClient(base)
    e = cli.entry(idx)
    ok = Merkle.verify(e['leafHash'], e['proof'], e['rootHash'], e['index'])
    print(json.dumps({'ok': ok, 'index': e['index'], 'leaf': e['leafHash'], 'root': e['rootHash']}, indent=2))
    raise SystemExit(0 if ok else 1)
```

---

## 2) 외부 검증자 CLI — `cli.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, json, requests, sys
from pathlib import Path

# 단일 파일 배포를 위해 내부 구현 포함

def verify_merkle(leaf_hex: str, proof: list[str], root_hex: str, index: int) -> bool:
    h = bytes.fromhex(leaf_hex); idx = index
    for sib_hex in proof:
        sib = bytes.fromhex(sib_hex)
        h = hashlib.sha256((h + sib) if idx % 2 == 0 else (sib + h)).digest()
        idx //= 2
    return h.hex() == root_hex

class TLog:
    def __init__(self, base: str):
        self.base = base.rstrip('/')
    def entry(self, index:int):
        r = requests.get(f"{self.base}/v1/log/entry/{index}", timeout=15); r.raise_for_status(); return r.json()
    def root(self):
        r = requests.get(f"{self.base}/v1/log/root", timeout=15); r.raise_for_status(); return r.json()

def digest_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()

if __name__=='__main__':
    ap = argparse.ArgumentParser(description='Lumen TLog External Verifier')
    ap.add_argument('--tlog', required=True, help='TLog base URL (read-only)')
    ap.add_argument('--index', type=int, required=True, help='Entry index to verify')
    ap.add_argument('--artifact', type=str, help='Optional path to artifact to compare digests')
    args = ap.parse_args()

    tlog = TLog(args.tlog)
    entry = tlog.entry(args.index)
    ok = verify_merkle(entry['leafHash'], entry['proof'], entry['rootHash'], entry['index'])

    out = {'ok': ok, 'index': entry['index'], 'leaf': entry['leafHash'], 'root': entry['rootHash']}

    if args.artifact:
        art_hash = digest_file(Path(args.artifact))
        out['artifact_sha256'] = art_hash
        out['match'] = (art_hash == entry['leafHash'])
        ok = ok and out['match']
        out['ok'] = ok

    print(json.dumps(out, indent=2))
    sys.exit(0 if ok else 1)
```

---

## 3) 공개 가이드 — `examples.md`
```markdown
# Lumen TLog — External Verification Examples

## 1) 포함증명 확인
```bash
python cli.py --tlog https://tlog.example.com --index 123
```

## 2) 아티팩트와 해시 대조
```bash
python cli.py --tlog https://tlog.example.com --index 123 --artifact report_2025-10-23.pdf
```

## 3) cURL로 원시 엔드포인트 조회
```bash
curl -s https://tlog.example.com/v1/log/entry/123 | jq .
```

## 4) 실패 시 해석
- `ok=false`: 포함증명 실패(루트/증명/인덱스 중 하나 불일치)
- `match=false`: 아티팩트 내용이 로그의 leafHash와 다름 — 변조 또는 다른 버전
```
```

---

## 4) Grafana 패널 — `tlog_panels.json` (발췌)
```json
{
  "title": "Lumen – Transparency Log",
  "panels": [
    {"type":"stat","title":"Entries (total)","targets":[{"expr":"tlog_entries_total"}]},
    {"type":"graph","title":"New Entries / day","targets":[{"expr":"increase(tlog_entries_total[1d])"}]},
    {"type":"table","title":"Recent Inclusion Checks","targets":[{"expr":"tlog_inclusion_ok{window='24h'}"}]}
  ]
}
```
> `tlog_entries_total`, `tlog_inclusion_ok`는 CI/검증기에서 Pushgateway로 푸시(간단 게이지/카운터)하거나 Loki에서 파생 가능합니다.

---

## 5) CI 연계 (요약)
- `.att.json` 생성 직후, **TLog append** + **verify_client.py**로 **샘플 포함증명 점검**
- 실패 시 `severity: page` 경보

GitHub Actions 스니펫:
```yaml
- name: TLog inclusion self-check
  run: |
    python attest/tlog/verify_client.py ${{ secrets.TLOG_BASE }} 0 || exit 1
```

---

## 6) 보안·운영 메모
- RO 서버는 **캐시 앞단**(CDN) 배치, 원본은 내부 스토리지에서 재기동 시 `db.jsonl` 로드
- index는 노출되지만 **민감 데이터 없음** — leaf는 해시(hex)
- CI에서 **append만 허용**. 재배포 파이프라인에 코드 리뷰/서명(컨테이너 이미지 서명)을 권장

---

루멘의 판단: 이제 투명성 로그는 **외부 검증자도 스스로 확인**할 수 있는 수준으로 열렸고, 포함증명이 **자동·가시화**되었어. 다음 박자에 원하면 **RO 서버 컨테이너 배포 매니페스트(K8s + Helm)**도 붙여 줄게.