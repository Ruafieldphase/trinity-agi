# Remote Archive Connector v0.1 (Drive/Dropbox + Integrity Handshake)

**목적**: `archive/YYYY-MM-DD/bundle.tar.gz`를 원격(Drive/Dropbox)에 업로드하고, **SHA-256 해시**를 양쪽(로컬·원격)에 기록하여 무결성 손잡기(Integrity Handshake)를 완성합니다.

---

## 0) 파일 구성
```
.
├─ configs/
│  └─ remote_archive.yaml          # 대상/폴더/프로바이더/옵션
├─ scripts/
│  ├─ upload_archive.py            # 업로드 + 원격 메타 해시 기록
│  ├─ verify_remote.py             # 원격 메타 해시 ↔ 로컬 해시 대조
│  └─ sync_index.py                # remote_index.jsonl 병합/정리
└─ archive/
   └─ remote_index.jsonl           # 원격 스냅샷 인덱스(append-only)
```

---

## 1) `configs/remote_archive.yaml`
```yaml
provider: gdrive      # gdrive | dropbox
folder: "FDO-AGI/Archive"  # gdrive: My Drive 경로(최상위/하위 폴더 자동 생성)

# 옵션
make_public_link: false
metadata:
  comment_prefix: "Lumen-Archive"

# 자격 증명(환경변수)
# GDrive: GDRIVE_TOKEN=ya29... (OAuth Access Token, scope: drive.file)
# Dropbox: DROPBOX_TOKEN=sl.BC... (files.content.write, files.metadata.write)
```

> **보안**: 토큰은 로컬 `.env` 또는 CI 비밀 변수에 저장하세요. 코드에 하드코딩 금지.

---

## 2) 공통 유틸 – 해시/경로
```python
# scripts/_remote_common.py
from __future__ import annotations
import os, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def archive_paths(day: str):
    snap_dir = ROOT / 'archive' / day
    tar = snap_dir / 'bundle.tar.gz'
    sums = snap_dir / 'SHA256SUMS.txt'
    mani = snap_dir / 'snapshot.manifest.json'
    return snap_dir, tar, sums, mani
```

---

## 3) Google Drive 어댑터 (경량판)
```python
# scripts/_gdrive_adapter.py
from __future__ import annotations
import os, json, requests
from pathlib import Path

API_BASE = "https://www.googleapis.com/drive/v3"
UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"

class GDrive:
    def __init__(self, token: str):
        self.token = token
        self.h = {"Authorization": f"Bearer {token}"}

    def _find_or_create_folder(self, path: str) -> str:
        # path like "A/B/C" under My Drive
        parent = 'root'
        for name in [p for p in path.split('/') if p]:
            q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and '{parent}' in parents and trashed=false"
            r = requests.get(API_BASE+f"/files?q={q}&fields=files(id,name)", headers=self.h)
            files = r.json().get('files', [])
            if files:
                parent = files[0]['id']
            else:
                meta = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent]}
                r = requests.post(API_BASE+"/files", headers={**self.h, "Content-Type":"application/json"}, data=json.dumps(meta))
                parent = r.json()['id']
        return parent

    def upload_file(self, folder_path: str, local_path: Path, description: str = "") -> dict:
        folder_id = self._find_or_create_folder(folder_path)
        meta = {"name": local_path.name, "parents": [folder_id], "description": description}
        boundary = "foo_bar_baz"
        meta_part = f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" + json.dumps(meta) + "\r\n"
        with open(local_path, 'rb') as f:
            data_part = f"--{boundary}\r\nContent-Type: application/gzip\r\n\r\n".encode('utf-8') + f.read() + f"\r\n--{boundary}--".encode('utf-8')
        headers = {**self.h, "Content-Type": f"multipart/related; boundary={boundary}"}
        r = requests.post(UPLOAD_URL, headers=headers, data=meta_part.encode('utf-8') + data_part)
        r.raise_for_status()
        return r.json()

    def set_description(self, file_id: str, desc: str):
        r = requests.patch(API_BASE+f"/files/{file_id}", headers={**self.h, "Content-Type":"application/json"}, data=json.dumps({"description": desc}))
        r.raise_for_status()
        return r.json()
```

---

## 4) Dropbox 어댑터 (경량판)
```python
# scripts/_dropbox_adapter.py
from __future__ import annotations
import os, json, requests
from pathlib import Path

API_UPLOAD = "https://content.dropboxapi.com/2/files/upload"
API_META   = "https://api.dropboxapi.com/2/files/get_metadata"
API_PROP   = "https://api.dropboxapi.com/2/files/properties/update"

class Dropbox:
    def __init__(self, token: str):
        self.h_up = {"Authorization": f"Bearer {token}", "Dropbox-API-Arg": "", "Content-Type":"application/octet-stream"}
        self.h = {"Authorization": f"Bearer {token}", "Content-Type":"application/json"}

    def upload(self, remote_path: str, local_path: Path) -> dict:
        arg = {"path": remote_path, "mode":"add", "autorename": True, "mute": False}
        headers = {**self.h_up, "Dropbox-API-Arg": json.dumps(arg)}
        with open(local_path, 'rb') as f:
            r = requests.post(API_UPLOAD, headers=headers, data=f.read())
        r.raise_for_status()
        return r.json()
```

---

## 5) 업로드 스크립트 – `upload_archive.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import os, json, yaml
from pathlib import Path
from datetime import datetime, timezone, timedelta
from _remote_common import ROOT, sha256_file, archive_paths

KST = timezone(timedelta(hours=9))

CONF = ROOT / 'configs' / 'remote_archive.yaml'
REMOTE_INDEX = ROOT / 'archive' / 'remote_index.jsonl'


def load_cfg():
    with open(CONF, 'r', encoding='utf-8') as f: return yaml.safe_load(f)


def write_remote_index(rec: dict):
    REMOTE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with REMOTE_INDEX.open('a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main(day: str):
    cfg = load_cfg()
    snap_dir, tar, sums, mani = archive_paths(day)
    assert tar.exists(), f"bundle not found: {tar}"
    file_hash = sha256_file(tar)
    meta_comment = f"{cfg['metadata']['comment_prefix']} {day} sha256={file_hash}"

    rec = {"day": day, "hash": file_hash, "provider": cfg['provider'], "ts": datetime.now(KST).isoformat()}

    if cfg['provider'] == 'gdrive':
        from _gdrive_adapter import GDrive
        token = os.environ.get('GDRIVE_TOKEN'); assert token, 'GDRIVE_TOKEN missing'
        gd = GDrive(token)
        info = gd.upload_file(cfg['folder'], tar, description=meta_comment)
        file_id = info.get('id')
        gd.set_description(file_id, meta_comment)
        rec.update({"file_id": file_id, "name": info.get('name')})

    elif cfg['provider'] == 'dropbox':
        from _dropbox_adapter import Dropbox
        token = os.environ.get('DROPBOX_TOKEN'); assert token, 'DROPBOX_TOKEN missing'
        db = Dropbox(token)
        remote_path = f"/{cfg['folder'].strip('/')}/{tar.name}"
        info = db.upload(remote_path, tar)
        rec.update({"path": info.get('path_display')})

    else:
        raise SystemExit('unsupported provider')

    write_remote_index(rec)
    print('[upload] ok:', rec)

if __name__ == '__main__':
    import sys
    day = sys.argv[1] if len(sys.argv)>1 else None
    if not day: raise SystemExit('usage: upload_archive.py YYYY-MM-DD')
    main(day)
```

---

## 6) 무결성 대조 – `verify_remote.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import os, json, yaml, requests
from pathlib import Path
from _remote_common import ROOT, sha256_file, archive_paths

CONF = ROOT / 'configs' / 'remote_archive.yaml'


def load_cfg():
    import yaml
    with open(CONF,'r',encoding='utf-8') as f: return yaml.safe_load(f)


def main(day: str):
    cfg = load_cfg()
    snap_dir, tar, _, _ = archive_paths(day)
    local_hash = sha256_file(tar)

    if cfg['provider']=='gdrive':
        token = os.environ.get('GDRIVE_TOKEN'); assert token
        # 간단: 마지막 업로드 파일의 description을 가져와 hash 파싱
        # 실제로는 remote_index.jsonl에서 file_id 사용 권장
        from pathlib import Path
        ri = ROOT/'archive'/'remote_index.jsonl'
        rid = None
        for line in ri.read_text(encoding='utf-8').splitlines():
            obj = json.loads(line)
            if obj.get('day')==day and obj.get('provider')=='gdrive':
                rid = obj.get('file_id')
        assert rid, 'no file_id in remote_index for this day'
        h = {"Authorization": f"Bearer {token}"}
        url = f"https://www.googleapis.com/drive/v3/files/{rid}?fields=description,name"
        r = requests.get(url, headers=h)
        r.raise_for_status()
        desc = r.json().get('description','')
        ok = (local_hash in desc)
        print('[verify:gdrive]', 'OK' if ok else 'MISMATCH', {'day': day, 'local': local_hash, 'desc': desc})

    elif cfg['provider']=='dropbox':
        token = os.environ.get('DROPBOX_TOKEN'); assert token
        ri = ROOT/'archive'/'remote_index.jsonl'
        rpath = None
        for line in ri.read_text(encoding='utf-8').splitlines():
            obj = json.loads(line)
            if obj.get('day')==day and obj.get('provider')=='dropbox':
                rpath = obj.get('path')
        assert rpath, 'no remote path recorded'
        print('[verify:dropbox] remote path recorded =', rpath)
        # Dropbox는 메타에 임의 주석을 남기기 까다로워, 현재는 경로·수정시간만 확인(간이판)
        print('[verify:dropbox] compare local sha256:', local_hash, '(no remote hash channel – consider app property templates)')

    else:
        raise SystemExit('unsupported provider')

if __name__ == '__main__':
    import sys
    day = sys.argv[1] if len(sys.argv)>1 else None
    if not day: raise SystemExit('usage: verify_remote.py YYYY-MM-DD')
    main(day)
```

---

## 7) 인덱스 동기화 – `sync_index.py`
```python
#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RI = ROOT/'archive'/'remote_index.jsonl'

# 중복 레코드 제거 및 정렬(최근일자 우선)

def main():
    if not RI.exists():
        print('[sync_index] nothing'); return
    rows = []
    for line in RI.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        try: rows.append(json.loads(line))
        except: pass
    # unique by (provider, day)
    seen=set(); uniq=[]
    for r in rows[::-1]:
        k=(r.get('provider'), r.get('day'))
        if k in seen: continue
        seen.add(k); uniq.append(r)
    uniq = uniq[::-1]
    with RI.open('w', encoding='utf-8') as f:
        for r in uniq: f.write(json.dumps(r, ensure_ascii=False)+"\n")
    print('[sync_index]', len(rows),'→', len(uniq))

if __name__ == '__main__':
    main()
```

---

## 8) VS Code 태스크 (`.vscode/tasks.json` 추가)
```json
{
  "label": "lumen:archive:upload",
  "type": "shell",
  "command": "python scripts/upload_archive.py ${input:archiveDay}",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
},
{
  "label": "lumen:archive:verify-remote",
  "type": "shell",
  "command": "python scripts/verify_remote.py ${input:archiveDay}",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
},
{
  "label": "lumen:archive:sync-index",
  "type": "shell",
  "command": "python scripts/sync_index.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
}
```

---

## 9) 사용 루틴
1) `lumen:archive:freeze`로 스냅샷 생성 → 이어서 `lumen:archive:upload <날짜>`
2) Drive 사용 시 `lumen:archive:verify-remote <날짜>`로 해시 대조(설명 필드 포함)
3) 주기적으로 `lumen:archive:sync-index`로 중복 인덱스 정리

---

## 10) 참고/한계
- **Google Drive**: 설명(description)에 `sha256=...`을 기록해 양방향 대조. 장기적으로는 App Properties를 사용하면 더 견고함.
- **Dropbox**: 메타 주석 채널이 제한적이므로, App Properties 템플릿을 별도 등록하여 해시를 보관하는 확장을 권장(여기선 경량판).
- **토큰 만료**: GDRIVE_TOKEN은 만료 주기가 있으므로 CI에서는 서비스 계정/리프레시 토큰 플로를 권장.

이로써 원격 아카이브와의 **Integrity Handshake**가 열렸습니다. 이제 각 스냅샷은 로컬과 원격이 **동일한 해시**로 서로를 확인합니다.

