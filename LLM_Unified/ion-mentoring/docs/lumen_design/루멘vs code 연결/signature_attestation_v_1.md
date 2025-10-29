# Signature & Attestation v1.0  
**(Ed25519 + Rotation + Remote Metadata)**

목적: 아카이브/리포트 번들을 **Ed25519 전자서명**으로 보호하고, 원격 메타데이터에 **서명·키 지시자**를 기록하여 **부인방지(Non‑repudiation)**와 **재현 검증**을 완성합니다. (Provenance & Trace v1.0 상위 레이어)

---

## 0) 의존성
```bash
pip install cryptography pyyaml requests boto3
```

---

## 1) 키 관리 (파일 레이아웃)
```
controls/keys/
├─ current/
│  ├─ ed25519_priv.pem      # PKCS#8, 암호화 보관 권장
│  └─ ed25519_pub.pem
└─ archive/
   └─ ed25519_pub_<date>.pem
```

- 기본은 **파일 키**. 가능하면 HSM/YubiKey로 대체(추후 확장 지점 표시).
- 개인키 보호: OS 권한 600, 또는 암호화 PEM(암호는 CI 시크릿에서 주입).

---

## 2) 키 생성 — `scripts/keygen_ed25519.py`
```python
#!/usr/bin/env python3
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from datetime import datetime
from pathlib import Path
import os, getpass

ROOT = Path(__file__).resolve().parent.parent
KEYS = ROOT / 'controls' / 'keys' / 'current'

if __name__=='__main__':
    KEYS.mkdir(parents=True, exist_ok=True)
    sk = ed25519.Ed25519PrivateKey.generate()
    pw = os.environ.get('LUMEN_KEY_PASS','').encode() or None
    enc = serialization.BestAvailableEncryption(pw) if pw else serialization.NoEncryption()
    pem_priv = sk.private_bytes(encoding=serialization.Encoding.PEM,
                                format=serialization.PrivateFormat.PKCS8,
                                encryption_algorithm=enc)
    pem_pub = sk.public_key().public_bytes(encoding=serialization.Encoding.PEM,
                                           format=serialization.PublicFormat.SubjectPublicKeyInfo)
    (KEYS/'ed25519_priv.pem').write_bytes(pem_priv)
    (KEYS/'ed25519_pub.pem').write_bytes(pem_pub)
    print('[keygen] wrote', KEYS)
```

---

## 3) 서명 — `scripts/sign_file.py` (detached .sig)
```python
#!/usr/bin/env python3
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from pathlib import Path
import os, sys, base64, json, hashlib

ROOT = Path(__file__).resolve().parent.parent
KEY = ROOT / 'controls' / 'keys' / 'current' / 'ed25519_priv.pem'

ALG = os.environ.get('LUMEN_HASH_ALG','sha256')

if __name__=='__main__':
    if len(sys.argv) < 2:
        print('usage: sign_file.py <file>'); sys.exit(2)
    target = Path(sys.argv[1])
    priv = serialization.load_pem_private_key(KEY.read_bytes(), password=os.environ.get('LUMEN_KEY_PASS','').encode() or None)
    data = target.read_bytes()
    # (선택) 해시 후 서명 — 큰 파일의 일관성 유지
    h = hashlib.new(ALG, data).digest()
    sig = priv.sign(h)
    out = target.with_suffix(target.suffix + '.sig')
    meta = {
        'alg': ALG,
        'hash_hex': hashlib.new(ALG, data).hexdigest(),
        'sig_b64': base64.b64encode(sig).decode(),
    }
    out.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    print('[sign] wrote', out)
```

---

## 4) 검증 — `scripts/verify_sig.py`
```python
#!/usr/bin/env python3
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from pathlib import Path
import json, sys, hashlib, base64

if __name__=='__main__':
    if len(sys.argv) < 3:
        print('usage: verify_sig.py <file> <pubkey_pem> [sig_json]'); sys.exit(2)
    f = Path(sys.argv[1]); pub = Path(sys.argv[2])
    s = Path(sys.argv[3]) if len(sys.argv)>3 else f.with_suffix(f.suffix+'.sig')
    meta = json.loads(s.read_text(encoding='utf-8'))
    h = hashlib.new(meta['alg'], f.read_bytes()).digest()
    pk = serialization.load_pem_public_key(pub.read_bytes())
    try:
        pk.verify(base64.b64decode(meta['sig_b64']), h)
        print(json.dumps({'ok': True, 'hash_hex': meta['hash_hex']}, indent=2))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({'ok': False, 'error': str(e)}, indent=2)); sys.exit(1)
```

---

## 5) 회전 — `scripts/rotate_keys.py`
```python
#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parent.parent
CUR = ROOT/'controls'/'keys'/'current'
ARC = ROOT/'controls'/'keys'/'archive'

if __name__=='__main__':
    ARC.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    # 공개키만 아카이브(검증에 필요)
    shutil.copy2(CUR/'ed25519_pub.pem', ARC/f'ed25519_pub_{ts}.pem')
    print('[rotate] archived pubkey →', ARC)
```

- 정책 권장: **분기/월 단위 회전**, 구키는 `archive/`에 보관해 과거 서명 검증 유지.

---

## 6) 원격 메타데이터(지시자) — 업로드 연동 포인트
- **S3**: 객체 메타에 `sig_b64` 대신 **서명 파일 별도 업로드** 권장 → 메타에는 `sig_ref=s3://bucket/key.sig.json`, `pubkey_ref=s3://bucket/keys/ed25519_pub_<date>.pem`
- **Drive**: `appProperties`에 `sig_ref`, `pubkey_ref` 기록
- **Dropbox**: Properties 템플릿에 동일 키 기록

`scripts/upload_archive.py`(개념 발췌):
```python
# after encrypt/upload
sig_json = tar.with_suffix(tar.suffix+'.sig')
# Drive 예: appProperties 업데이트
app_props.update({'sig_ref': sig_json.name, 'pubkey_ref': 'ed25519_pub.pem'})
```

> 실제 구현에서는 `.sig` 파일을 같은 원격 경로에 함께 업로드하고, 인덱스(`remote_index.jsonl`)에 `sig_ref`를 추가합니다.

---

## 7) CI 통합 (발췌)
```yaml
- name: Generate keys (first time only)
  if: ${{ !hashFiles('controls/keys/current/ed25519_priv.pem') }}
  run: LUMEN_KEY_PASS='${{ secrets.LUMEN_KEY_PASS }}' python scripts/keygen_ed25519.py

- name: Sign bundle & report
  run: |
    day=$(date -u +%Y-%m-%d)
    python scripts/sign_file.py archive/$day/bundle.tar.gz
    python scripts/sign_file.py controls/reports/report_${day}.pdf

- name: Verify signatures
  run: |
    python scripts/verify_sig.py archive/$(date -u +%Y-%m-%d)/bundle.tar.gz controls/keys/current/ed25519_pub.pem
    python scripts/verify_sig.py controls/reports/report_$(date -u +%Y-%m-%d).pdf controls/keys/current/ed25519_pub.pem

- name: Upload .sig files with artifacts
  run: |
    # 기존 upload 스크립트 확장: .sig도 함께 업로드하고 appProperties/메타에 참조 기록
    python scripts/upload_archive.py $(date -u +%Y-%m-%d)
```

---

## 8) 현장 검증 루틴
1) 로컬: `python scripts/sign_file.py archive/2025-10-23/bundle.tar.gz` → `.sig` 생성  
2) 다른 머신: `python scripts/verify_sig.py ... ed25519_pub.pem` → `ok: true` 기대  
3) 원격: 메타의 `sig_ref/pubkey_ref`를 따라 내려받아 동일 검증 수행

---

## 9) HSM/보안키 확장 노트
- YubiKey(Ed25519) 또는 클라우드 KMS(Cloud KMS/HSM)로 **서명 연산 위임** 가능
- 이 경우 `sign_file.py`를 **외부 서명자 인터페이스**(stdin→digest, stdout→sig)로 추상화

---

## 10) 운영 팁
- 개인키 백업은 **오프라인** 매체(암호화 저장)로 이중화
- 키 교체 시점엔 **구키 공개키를 인덱스에 첨부**해 과거 검증 경로를 보존
- 알림: `verify_sig` 실패는 즉시 온콜(page) 레벨로 라우팅

루멘의 판단: 이제 산출물은 **전자서명**이라는 인장을 갖습니다. 해시(무결성)·머클(집합 보증)·서명(부인방지)이 합쳐져, 기록은 **증명 가능한 역사**가 되었어요.