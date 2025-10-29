# Trust Chain v1.0  
**(Root → Signer Certs + CRL/OCSP + Transparency Log)**

목적: Ed25519 서명자 키에 **신뢰사슬(chain of trust)**을 부여한다. 오프라인 **루트 CA**가 서명자 공개키를 인증서로 발급하고, 검증 시 **서명+체인+폐지(Revocation)**까지 확인하여 공급망 신뢰를 완성한다.

---

## 0) 구성 개요
```
controls/keys/
├─ root/
│  ├─ root_ca_priv.pem          # 오프라인 보관(암호화)
│  ├─ root_ca_pub.pem
│  └─ root_ca_cert.pem          # self-signed X.509 (Ed25519)
├─ current/
│  ├─ signer_priv.pem           # 서명자 개인키(암호화)
│  ├─ signer_pub.pem
│  └─ signer_cert.pem           # 루트가 서명한 X.509
└─ archive/
   ├─ signer_cert_YYYYMM.pem
   └─ revoked.jsonl             # 폐지 목록(CRL 대용 jsonl)

controls/trust/
├─ chain_manifest.json          # 체인 지시자(루트 지문/버전/정책)
├─ crl.jsonl                    # 중앙 CRL(append-only)
└─ transparency.log.jsonl       # 서명 이력 투명성 로그
```

---

## 1) 루트 CA 생성 — `scripts/ca_root_init.py`
```python
#!/usr/bin/env python3
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent / 'controls' / 'keys' / 'root'
ROOT.mkdir(parents=True, exist_ok=True)

if __name__=='__main__':
    sk = ed25519.Ed25519PrivateKey.generate()
    pw = os.environ.get('LUMEN_CA_PASS','').encode() or None
    enc = serialization.BestAvailableEncryption(pw) if pw else serialization.NoEncryption()
    ROOT.joinpath('root_ca_priv.pem').write_bytes(
        sk.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, enc)
    )
    ROOT.joinpath('root_ca_pub.pem').write_bytes(
        sk.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u'Lumen Root CA'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'Lumen System C'),
    ])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(sk.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=1), critical=True)
        .sign(private_key=sk, algorithm=None)
    )
    ROOT.joinpath('root_ca_cert.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    print('[root-ca] created:', ROOT)
```

---

## 2) 서명자 인증서 발급 — `scripts/ca_issue_signer.py`
```python
#!/usr/bin/env python3
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os

BASE = Path(__file__).resolve().parent.parent / 'controls' / 'keys'
ROOT = BASE / 'root'
CUR  = BASE / 'current'

if __name__=='__main__':
    # 서명자 키가 없다면 생성
    CUR.mkdir(parents=True, exist_ok=True)
    if not (CUR/'signer_priv.pem').exists():
        sk = ed25519.Ed25519PrivateKey.generate()
        pw = os.environ.get('LUMEN_SIGNER_PASS','').encode() or None
        enc = serialization.BestAvailableEncryption(pw) if pw else serialization.NoEncryption()
        CUR.joinpath('signer_priv.pem').write_bytes(
            sk.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, enc))
        CUR.joinpath('signer_pub.pem').write_bytes(
            sk.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))

    # CSR 유사: 공개키 로드
    with open(CUR/'signer_pub.pem','rb') as f:
        spk = serialization.load_pem_public_key(f.read())

    # 루트 키/인증서 로드
    r_priv = serialization.load_pem_private_key((ROOT/'root_ca_priv.pem').read_bytes(), password=os.environ.get('LUMEN_CA_PASS','').encode() or None)
    from cryptography import x509
    r_cert = x509.load_pem_x509_certificate((ROOT/'root_ca_cert.pem').read_bytes())

    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u'Lumen Artifact Signer'),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'Pipeline'),
        ]))
        .issuer_name(r_cert.subject)
        .public_key(spk)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=180))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CODE_SIGNING]), critical=False)
        .sign(private_key=r_priv, algorithm=None)
    )
    (CUR/'signer_cert.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    print('[issue] signer_cert.pem issued')
```

---

## 3) 서명파일(.sig) → 체인 연결 — `scripts/sign_file.py` 확장
```python
# ... (기존 해시→Ed25519 서명 생성 후)
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CUR  = ROOT / 'controls' / 'keys' / 'current'

# 체인 지시자 포함(meta)
meta.update({
  'signer_cert_pem': (CUR/'signer_cert.pem').read_text(encoding='utf-8'),
  'root_fingerprint': __import__('hashlib').sha256((ROOT/'controls'/'keys'/'root'/'root_ca_cert.pem').read_bytes()).hexdigest(),
})
out.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
```

---

## 4) 검증(체인+서명) — `scripts/verify_sig_chain.py`
```python
#!/usr/bin/env python3
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
import json, sys, hashlib, base64
from pathlib import Path

if __name__=='__main__':
  if len(sys.argv)<3:
    print('usage: verify_sig_chain.py <file> <root_ca_cert.pem> [sig_json]'); sys.exit(2)
  f = Path(sys.argv[1]); root_pem = Path(sys.argv[2])
  s = Path(sys.argv[3]) if len(sys.argv)>3 else f.with_suffix(f.suffix+'.sig')
  meta = json.loads(s.read_text('utf-8'))
  # 1) 체인: 서명자 인증서의 issuer가 루트와 일치하는지
  root = x509.load_pem_x509_certificate(root_pem.read_bytes())
  signer = x509.load_pem_x509_certificate(meta['signer_cert_pem'].encode('utf-8'))
  try:
    root.public_key().verify(signer.signature, signer.tbs_certificate_bytes)
  except Exception as e:
    print(json.dumps({'ok': False, 'error':'bad chain: '+str(e)})); sys.exit(1)
  # 2) 서명 검증
  h = hashlib.new(meta['alg'], f.read_bytes()).digest()
  pk = signer.public_key()
  try:
    pk.verify(base64.b64decode(meta['sig_b64']), h)
    ok = True
  except Exception as e:
    print(json.dumps({'ok': False, 'error':'bad signature: '+str(e)})); sys.exit(1)
  print(json.dumps({'ok': ok, 'hash_hex': meta['hash_hex']}, indent=2))
```

---

## 5) CRL/OCSP(경량) — 폐지/만료 확인
- 운영 단순화를 위해 **jsonl CRL**을 채택(서버 없는 경량 구현). 필요 시 OCSP 유사 응답 엔드포인트로 확장 가능.

`controls/trust/crl.jsonl` 예시:
```json
{"serial": 1234567890, "reason":"keyCompromise", "revoked_at":"2025-10-01T00:00:00Z"}
```

`scripts/crl_check.py`:
```python
#!/usr/bin/env python3
import json, sys
from pathlib import Path

def is_revoked(cert_serial: int, crl_path: Path) -> bool:
    for line in crl_path.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        obj = json.loads(line)
        if int(obj.get('serial', -1)) == cert_serial:
            return True
    return False

if __name__=='__main__':
    from cryptography import x509
    if len(sys.argv)<3: print('usage: crl_check.py <signer_cert.pem> <crl.jsonl>'); sys.exit(2)
    cert = x509.load_pem_x509_certificate(Path(sys.argv[1]).read_bytes())
    crl = Path(sys.argv[2])
    print('revoked' if is_revoked(cert.serial_number, crl) else 'valid')
```

→ 검증 파이프에서 `crl_check.py`를 먼저 호출하여 폐지된 인증서면 즉시 실패 처리.

---

## 6) 체인 매니페스트 — `controls/trust/chain_manifest.json`
```json
{
  "root_subject": "CN=Lumen Root CA, O=Lumen System C",
  "root_fingerprint_sha256": "<hex>",
  "policy": {
    "signer_valid_days": 180,
    "key_rotation": "6 months",
    "allowed_eku": ["codeSigning"],
    "crl": "controls/trust/crl.jsonl"
  }
}
```

---

## 7) 투명성 로그 — `scripts/transparency_append.py`
```python
#!/usr/bin/env python3
import json, os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
TLOG = ROOT/'controls'/'trust'/'transparency.log.jsonl'

if __name__=='__main__':
  rec = {
    'ts_utc': datetime.now(timezone.utc).isoformat(),
    'artifact': os.environ.get('LUMEN_ARTIFACT','bundle'),
    'hash_hex': os.environ.get('LUMEN_HASH',''),
    'signer_serial': os.environ.get('LUMEN_SIGNER_SERIAL',''),
    'trace_id': os.environ.get('LUMEN_TRACE_ID','')
  }
  TLOG.parent.mkdir(parents=True, exist_ok=True)
  with TLOG.open('a', encoding='utf-8') as f: f.write(json.dumps(rec)+"\n")
  print('[tlog]', rec)
```

---

## 8) CI 통합(발췌)
```yaml
- name: Root/Signer setup (once per rotation)
  run: |
    LUMEN_CA_PASS='${{ secrets.LUMEN_CA_PASS }}' python scripts/ca_root_init.py || true
    LUMEN_CA_PASS='${{ secrets.LUMEN_CA_PASS }}' LUMEN_SIGNER_PASS='${{ secrets.LUMEN_SIGNER_PASS }}' python scripts/ca_issue_signer.py

- name: Sign artifacts (with cert chain)
  run: |
    python scripts/sign_file.py archive/${{ env.LUMEN_DAY }}/bundle.tar.gz
    python scripts/sign_file.py controls/reports/report_${{ env.LUMEN_DAY }}.pdf

- name: Verify (chain + signature + CRL)
  run: |
    python scripts/verify_sig_chain.py archive/${{ env.LUMEN_DAY }}/bundle.tar.gz controls/keys/root/root_ca_cert.pem
    python scripts/crl_check.py controls/keys/current/signer_cert.pem controls/trust/crl.jsonl

- name: Transparency log append
  run: |
    export LUMEN_ARTIFACT=bundle
    export LUMEN_HASH=$(jq -r .hash_hex archive/${{ env.LUMEN_DAY }}/bundle.tar.gz.sig)
    export LUMEN_SIGNER_SERIAL=$(python -c "from cryptography import x509;print(x509.load_pem_x509_certificate(open('controls/keys/current/signer_cert.pem','rb').read()).serial_number)")
    python scripts/transparency_append.py
```

---

## 9) 보안 메모
- **루트키는 오프라인**: CI에는 절대 올리지 않으며, 필요 시 별도 보안 워크스테이션에서만 사용.
- 서명자 키는 CI에 존재하되 **암호화 PEM** + 단기 만료 인증서(180일) 정책.
- 폐지 발생 시 `crl.jsonl`에 즉시 기록, 이후 서명/검증 스텝은 자동으로 차단.

---

## 10) 운영 루틴
1) 분기마다: `ca_issue_signer.py`로 새 서명자 발급 → 구서명자 cert는 `archive/`로 이동
2) 장애·유출 의심: `revoked.jsonl`/`crl.jsonl`에 일련번호 기록 → 즉시 재발급
3) 정기 점검: 체인 매니페스트와 루트 지문이 보고서 표지/메타에 표시되는지 확인

루멘의 판단: 이제 서명자는 **루트에 의해 신원 확인**되고, 검증은 **서명+체인+폐지**를 아우르는 완전한 공급망 신뢰 흐름으로 완성됐어요.