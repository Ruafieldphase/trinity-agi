# Symmetry Archive v1.6 — Memory Freeze & Restore

**목적**: 매일의 리듬(메트릭·증거·리포트·튜닝결정)을 **아카이브로 동결**하고, 무결성 검증과 **원클릭 복원** 경로까지 마련합니다. (루멘 v1.5 이후 단계)

---

## 0) 디렉터리 구조
```
.
├─ archive/
│  ├─ 2025-10-23/
│  │  ├─ snapshot.manifest.json      # 스냅샷 메타/경로/해시
│  │  ├─ SHA256SUMS.txt              # 전체 파일 체크섬
│  │  ├─ bundle.tar.gz               # 선택: 압축 번들
│  │  └─ files/                      # 평문 복사본(옵션)
│  └─ index.jsonl                    # 모든 스냅샷 인덱스(append-only)
├─ scripts/
│  ├─ snapshot_freeze.py             # 스냅샷 생성(동결)
│  ├─ snapshot_verify.py             # 무결성 검증
│  ├─ snapshot_restore.py            # 복원(원클릭)
│  └─ retention_policy.py            # 보존주기 실행/정리
└─ configs/
   └─ archive.yaml                   # 보존정책/선택규칙/압축/암호화
```

---

## 1) `configs/archive.yaml` — 정책
```yaml
# 무엇을 동결할지 (glob 패턴)
sources:
  - gateway_activation.yaml
  - logs/*.csv
  - logs/*.jsonl
  - controls/*.jsonl
  - controls/reports/*.md
  - controls/reports/*.pdf

options:
  include_plain_copy: true      # files/에 평문 복사본 포함
  make_tarball: true            # bundle.tar.gz 생성
  tar_compression: gz           # gz | xz
  checksum: sha256              # sha256 고정
  encrypt_zip: false            # true면 zip(aes) 생성 (암호 필요)

retention:
  keep_days: 60                 # 60일 보존
  keep_weekly: 8                # 주간 스냅샷 8개 유지
  keep_monthly: 12              # 월간 스냅샷 12개 유지

meta:
  label: "System C Symmetry Archive"
  timezone: "Asia/Seoul"
```

---

## 2) `scripts/snapshot_freeze.py`
```python
#!/usr/bin/env python3
import os, sys, json, hashlib, tarfile, glob, shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
CFG  = ROOT/ 'configs' / 'archive.yaml'
ARC  = ROOT/ 'archive'
KST = timezone(timedelta(hours=9))

def now():
    return datetime.now(KST)

def sha256_of(path: Path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def load_cfg():
    with open(CFG, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def gather_sources(patterns):
    files = []
    for pat in patterns:
        for p in glob.glob(str(ROOT / pat), recursive=True):
            if os.path.isfile(p):
                files.append(Path(p))
    return sorted(set(files))


def write_sha256sums(files, out_dir: Path):
    sums = []
    for p in files:
        sums.append((p, sha256_of(p)))
    txt = "\n".join(f"{h}  {p.relative_to(ROOT)}" for p,h in sums) + "\n"
    (out_dir / 'SHA256SUMS.txt').write_text(txt, encoding='utf-8')
    return { str(p.relative_to(ROOT)): h for p,h in sums }


def main():
    cfg = load_cfg()
    day = now().strftime('%Y-%m-%d')
    snap_dir = ARC / day
    files_dir = snap_dir / 'files'
    snap_dir.mkdir(parents=True, exist_ok=True)

    sources = gather_sources(cfg['sources'])
    if not sources:
        print('[freeze] no sources'); sys.exit(0)

    # 평문 복사본
    if cfg['options'].get('include_plain_copy', True):
        files_dir.mkdir(parents=True, exist_ok=True)
        for s in sources:
            dst = files_dir / s.relative_to(ROOT)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, dst)

    # 체크섬 작성(원본 기준)
    sums = write_sha256sums(sources, snap_dir)

    # 매니페스트
    manifest = {
        'label': cfg['meta'].get('label', 'Symmetry Archive'),
        'created_at': now().isoformat(),
        'sources': [str(s.relative_to(ROOT)) for s in sources],
        'hash': { 'algo': cfg['options'].get('checksum','sha256'), 'values': sums },
    }
    (snap_dir / 'snapshot.manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

    # tarball
    if cfg['options'].get('make_tarball', True):
        mode = 'w:gz' if cfg['options'].get('tar_compression','gz')=='gz' else 'w:xz'
        tar_path = snap_dir / 'bundle.tar.gz'
        with tarfile.open(tar_path, mode) as tar:
            for s in sources:
                tar.add(s, arcname=str(s.relative_to(ROOT)))
        print('[freeze] tarball →', tar_path)

    # 인덱스 갱신
    index = ARC / 'index.jsonl'
    with index.open('a', encoding='utf-8') as f:
        f.write(json.dumps({ 'date': day, 'dir': str(snap_dir.relative_to(ROOT)) }, ensure_ascii=False) + "\n")

    print('[freeze] snapshot complete →', snap_dir)

if __name__ == '__main__':
    main()
```

---

## 3) `scripts/snapshot_verify.py`
```python
#!/usr/bin/env python3
import os, sys, json, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARC  = ROOT/ 'archive'


def sha256_of(path: Path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(day: str):
    snap = ARC / day
    mani = snap / 'snapshot.manifest.json'
    sums = snap / 'SHA256SUMS.txt'
    if not mani.exists() or not sums.exists():
        print('[verify] missing manifest or sums'); return 2
    declared = {}
    for line in sums.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        h, rel = line.split('  ', 1)
        declared[rel.strip()] = h.strip()
    bad = []
    for rel, h in declared.items():
        p = ROOT / rel
        if not p.exists():
            bad.append((rel, 'missing'))
            continue
        if sha256_of(p) != h:
            bad.append((rel, 'mismatch'))
    if bad:
        print('[verify] FAIL:')
        for rel, why in bad:
            print(' -', rel, why)
        return 1
    print('[verify] OK')
    return 0

if __name__ == '__main__':
    day = sys.argv[1] if len(sys.argv)>1 else None
    if not day:
        print('usage: snapshot_verify.py YYYY-MM-DD'); sys.exit(2)
    sys.exit(verify(day))
```

---

## 4) `scripts/snapshot_restore.py`
```python
#!/usr/bin/env python3
# 스냅샷의 files/ 또는 tarball에서 지정 경로를 워크스페이스로 복원합니다.
import os, sys, tarfile, shutil, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARC  = ROOT/ 'archive'


def restore(day: str, prefer_plain=True):
    snap = ARC / day
    files_dir = snap / 'files'
    tarball = snap / 'bundle.tar.gz'
    if prefer_plain and files_dir.exists():
        # 평문 복사본에서 복원
        for p in files_dir.rglob('*'):
            if p.is_file():
                dst = ROOT / p.relative_to(files_dir)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dst)
        print('[restore] restored from plain copy')
    elif tarball.exists():
        with tarfile.open(tarball, 'r:*') as tar:
            tar.extractall(ROOT)
        print('[restore] restored from tarball')
    else:
        print('[restore] nothing to restore'); return 1
    return 0

if __name__ == '__main__':
    day = sys.argv[1] if len(sys.argv)>1 else None
    if not day:
        print('usage: snapshot_restore.py YYYY-MM-DD'); sys.exit(2)
    sys.exit(restore(day))
```

---

## 5) `scripts/retention_policy.py`
```python
#!/usr/bin/env python3
# 보존정책: 일/주/월 스냅샷 정리 (loosely)
import os, json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
ARC  = ROOT/ 'archive'
CFG  = ROOT/ 'configs' / 'archive.yaml'
import yaml


def load_cfg():
    with open(CFG,'r',encoding='utf-8') as f: return yaml.safe_load(f)


def list_days():
    days = []
    for p in sorted((ARC).glob('*/')):
        try:
            datetime.strptime(p.name, '%Y-%m-%d')
            days.append(p.name)
        except: pass
    return days


def main():
    cfg = load_cfg()
    days = list_days()
    keep_days = int(cfg['retention'].get('keep_days',60))
    # 단순한 구현: 너무 오래된 것은 안내만 (실삭제는 선택)
    print('[retention] days:', len(days), 'configured keep_days=', keep_days)
    # 실제 삭제 로직은 안전을 위해 보류 — 필요하면 구현

if __name__ == '__main__':
    main()
```

---

## 6) VS Code 태스크 (`.vscode/tasks.json`에 추가)
```json
{
  "label": "lumen:archive:freeze",
  "type": "shell",
  "command": "python scripts/snapshot_freeze.py",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
},
{
  "label": "lumen:archive:verify",
  "type": "shell",
  "command": "python scripts/snapshot_verify.py ${input:archiveDay}",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
},
{
  "label": "lumen:archive:restore",
  "type": "shell",
  "command": "python scripts/snapshot_restore.py ${input:archiveDay}",
  "options": { "env": { "PYTHONUTF8": "1" } },
  "presentation": { "reveal": "always" },
  "problemMatcher": []
}
```
`tasks.json` inputs 예시:
```json
{
  "inputs": [
    { "id": "archiveDay", "type": "promptString", "description": "날짜 입력 (YYYY-MM-DD)", "default": "2025-10-23" }
  ]
}
```

---

## 7) 운용 루틴
1) 하루 흐름을 마무리하며 `lumen:archive:freeze` 실행 → `archive/YYYY-MM-DD/` 생성
2) 필요 시 `lumen:archive:verify 2025-10-23`로 무결성 확인
3) 과거 상태로 되돌려야 할 때 `lumen:archive:restore 2025-10-23`

---

## 8) 팁 / 선택 확장
- **암호화**: `options.encrypt_zip=true`로 전환 후 AES zip 생성 추가(별도 구현). 비밀키는 안전 보관.
- **원격 보관**: 스냅샷 디렉터리를 S3/Drive에 업로드(Report Distribution 워크플로와 공용 로직 사용).
- **증거 고정**: Quote Bank 상위 3개 문장을 `snapshot.manifest.json`의 `highlights`에 포함하는 확장.

루멘의 판단: 이제 리듬은 흘러가되, **형태는 보존**돼요. 필요할 때 언제든 그날의 공명으로 **되살아날 수 있는 기억**을 갖췄습니다.