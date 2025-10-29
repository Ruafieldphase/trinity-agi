# Remote Archive Connector v0.3
**(Dropbox App Properties + S3 SSE‑KMS + Lifecycle + Alerts)**

v0.2를 확장하여 **Dropbox App Properties 해시 저장/검증**, **S3 서버사이드 암호화(KMS)**, **S3 Lifecycle 정책 예시**, 그리고 **알림(웹훅/이메일)**을 추가합니다.

---

## 0) 의존성
```bash
pip install boto3 cryptography requests pyyaml
```

---

## 1) 설정 — `configs/remote_archive.yaml` (추가 필드)
```yaml
provider: s3  # s3 | gdrive | dropbox
folder: "FDO-AGI/Archive"

s3:
  bucket: "lumen-archive-bucket"
  prefix: "SystemC/snapshots"
  region: "ap-northeast-2"
  sse:
    enable: true
    mode: "aws:kms"           # aws:kms | AES256
    kms_key_id: "arn:aws:kms:ap-northeast-2:123456789012:key/abcd-..."  # mode=aws:kms일 때
  lifecycle:
    suggest_policy: true       # true면 정책 샘플 JSON 출력(수동 적용 안내)

crypto:
  enable: true
  algo: "AES-GCM"
  env_key: "LUMEN_ARCHIVE_KEY"

metadata:
  comment_prefix: "Lumen-Archive"
  app_props:
    hash_key: "sha256"

alerts:
  webhook:
    enable: true
    url: "https://hooks.example.com/lumen-archive"
    secret: "${LUMEN_ALERT_SECRET}"  # 선택
  email:
    enable: false
    to: ["ops@example.com"]

# Dropbox 전용(속성 템플릿)
dropbox:
  path_prefix: "/FDO-AGI/Archive"
  template_id: "ptid:1a5n2..."       # Dropbox properties template ID
  field_key: "sha256"                # 템플릿 내 필드 키
```

---

## 2) Dropbox App Properties 어댑터 — `scripts/_dropbox_adapter.py` (확장)
```python
from __future__ import annotations
import os, json, requests
from pathlib import Path

API_UPLOAD = "https://content.dropboxapi.com/2/files/upload"
API_PROP_UPSERT = "https://api.dropboxapi.com/2/files/properties/update"

class Dropbox:
    def __init__(self, token: str):
        self.token = token
        self.h_up = {"Authorization": f"Bearer {token}", "Dropbox-API-Arg": "", "Content-Type":"application/octet-stream"}
        self.h = {"Authorization": f"Bearer {token}", "Content-Type":"application/json"}

    def upload(self, remote_path: str, local_path: Path) -> dict:
        arg = {"path": remote_path, "mode":"add", "autorename": True, "mute": False}
        headers = {**self.h_up, "Dropbox-API-Arg": json.dumps(arg)}
        with open(local_path, 'rb') as f:
            r = requests.post(API_UPLOAD, headers=headers, data=f.read())
        r.raise_for_status()
        return r.json()

    def upsert_property(self, path: str, template_id: str, key: str, value: str):
        body = {
            "path": path,
            "update_property_groups": [{
                "template_id": template_id,
                "add_or_update_fields": [{"name": key, "value": value}]
            }]
        }
        r = requests.post(API_PROP_UPSERT, headers=self.h, data=json.dumps(body))
        r.raise_for_status()
        return r.json()
```

---

## 3) S3 어댑터 — `scripts/_s3_adapter.py` (SSE‑KMS 지원)
```python
from __future__ import annotations
import boto3

class S3Client:
    def __init__(self, bucket: str, region: str, sse: dict | None = None):
        self.bucket = bucket
        self.client = boto3.client('s3', region_name=region)
        self.sse = sse or {"enable": False}

    def upload(self, local_path, key: str, metadata: dict = None, public: bool = False):
        extra = {'Metadata': metadata or {}}
        if public:
            extra['ACL'] = 'public-read'
        if self.sse.get('enable'):
            mode = self.sse.get('mode', 'AES256')
            if mode == 'AES256':
                extra['ServerSideEncryption'] = 'AES256'
            elif mode == 'aws:kms':
                extra['ServerSideEncryption'] = 'aws:kms'
                if self.sse.get('kms_key_id'):
                    extra['SSEKMSKeyId'] = self.sse['kms_key_id']
        self.client.upload_file(str(local_path), self.bucket, key, ExtraArgs=extra)
        return { 'bucket': self.bucket, 'key': key, 'url': f"s3://{self.bucket}/{key}" }
```

---

## 4) 업로드 — `scripts/upload_archive.py` (v0.3 발췌: S3/Dropbox 경로)
```python
# ... (공통 로직은 v0.2와 동일)
if cfg['provider'] == 's3':
    from _s3_adapter import S3Client
    s3 = S3Client(cfg['s3']['bucket'], cfg['s3']['region'], cfg['s3'].get('sse'))
    key = f"{cfg['s3']['prefix'].strip('/')}/{upload_path.name}"
    meta = {"sha256": file_hash}
    if enc_meta:
        meta.update({"enc": enc_meta['algo'], "salt_b64": enc_meta['salt_b64'], "nonce_b64": enc_meta['nonce_b64']})
    info = s3.upload(upload_path, key, metadata=meta, public=cfg.get('options',{}).get('make_public_link', False))
    rec.update({"s3": info})

elif cfg['provider'] == 'dropbox':
    from _dropbox_adapter import Dropbox
    db = Dropbox(os.environ['DROPBOX_TOKEN'])
    remote_path = f"/{cfg['dropbox']['path_prefix'].strip('/')}/{upload_path.name}"
    info = db.upload(remote_path, upload_path)
    # App Properties에 sha256 저장
    db.upsert_property(info['path_lower'], cfg['dropbox']['template_id'], cfg['dropbox']['field_key'], file_hash)
    rec.update({"path": info.get('path_display')})
```

---

## 5) 원격 검증 — `scripts/verify_remote.py` (v0.3 발췌)
```python
if prov=='s3':
    import boto3
    s3 = boto3.client('s3', region_name=cfg['s3']['region'])
    key = rec['s3']['key']
    head = s3.head_object(Bucket=rec['s3']['bucket'], Key=key)
    remote_hash = (head.get('Metadata') or {}).get('sha256')
    ok = (remote_hash == local_hash)
    print('[verify:s3]', 'OK' if ok else 'MISMATCH', {'day': day, 'local': local_hash, 'remote': remote_hash})

elif prov=='dropbox':
    import requests, os
    token = os.environ['DROPBOX_TOKEN']
    # 파일 메타 속성 조회 (properties/get)
    r = requests.post('https://api.dropboxapi.com/2/files/properties/get',
                      headers={'Authorization': f'Bearer {token}', 'Content-Type':'application/json'},
                      json={'path': rec['path'], 'template_id': cfg['dropbox']['template_id']})
    if r.status_code==200:
        fields = {f['name']: f['value'] for f in r.json()['property_groups'][0]['fields']}
        remote_hash = fields.get(cfg['dropbox']['field_key'])
        print('[verify:dropbox]', 'OK' if remote_hash==local_hash else 'MISMATCH', {'day': day})
    else:
        print('[verify:dropbox] failed to read properties', r.text[:200])
```

---

## 6) S3 Lifecycle 정책 샘플 출력 — `scripts/s3_lifecycle_sample.py`
```python
#!/usr/bin/env python3
import json, os, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT/'configs'/'remote_archive.yaml'

policy = {
  "Rules": [
    {"ID":"lumen-archive-std-to-inf-30d","Status":"Enabled","Filter":{"Prefix":"SystemC/snapshots/"},
     "Transitions":[{"Days":30,"StorageClass":"STANDARD_IA"}],
     "NoncurrentVersionTransitions":[{"NoncurrentDays":30,"StorageClass":"STANDARD_IA"}],
     "Expiration":{"Days":365}}
  ]
}

if __name__=='__main__':
  print(json.dumps(policy, indent=2))
  print("\n# aws s3api put-bucket-lifecycle-configuration --bucket <bucket> --lifecycle-configuration file://policy.json")
```

---

## 7) 알림 — `scripts/notify.py`
```python
#!/usr/bin/env python3
import os, json, hmac, hashlib, requests

WEBHOOK_URL = os.environ.get('LUMEN_ALERT_URL')
WEBHOOK_SECRET = os.environ.get('LUMEN_ALERT_SECRET','')

def sign(body: str):
    if not WEBHOOK_SECRET: return ''
    return hmac.new(WEBHOOK_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()

def notify(title: str, payload: dict):
    if not WEBHOOK_URL: return
    body = json.dumps({"title": title, "payload": payload}, ensure_ascii=False)
    headers = {"Content-Type":"application/json", "X-Lumen-Signature": sign(body)}
    r = requests.post(WEBHOOK_URL, headers=headers, data=body)
    print('[notify]', r.status_code)

if __name__=='__main__':
    import sys, json
    title = sys.argv[1]
    payload = json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
    notify(title, payload)
```

업로드/검증 스크립트에서 성공/실패 시 `notify()`를 호출하도록 간단히 연결하세요.

---

## 8) VS Code 태스크 (추가)
```json
{
  "label": "lumen:s3:lifecycle:sample",
  "type": "shell",
  "command": "python scripts/s3_lifecycle_sample.py",
  "presentation": { "reveal": "always" }
},
{
  "label": "lumen:alert:test",
  "type": "shell",
  "command": "python scripts/notify.py 'Archive Upload Test' '{""event"": ""test""}'",
  "presentation": { "reveal": "always" }
}
```

---

## 9) 운영 루틴 요약
1) `lumen:archive:freeze` → 스냅샷
2) `lumen:archive:upload <날짜>` → S3(KMS)/Dropbox(App Props)/Drive(App Props) 업로드
3) `lumen:archive:verify-remote <날짜>` → 원격 해시 대조
4) (선택) `lumen:s3:lifecycle:sample` 정책을 검토·적용
5) 실패/성공은 `notify.py` 웹훅으로 알림

---

## 10) 보안 메모
- KMS 키는 최소 권한 정책으로 범위 제한(특정 버킷/프리픽스만 허용)
- Dropbox 템플릿/필드 권한은 앱 스코프로 최소화
- 알림 웹훅은 서명 검증(`X-Lumen-Signature`)을 서버에서 수행할 것

이로써 **원격 보관**은 암호화/수명/무결성/알림까지 한 사이클로 닫힙니다.

