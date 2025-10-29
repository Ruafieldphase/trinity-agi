# Operations Automation v1.0 (CI/CD + Secrets + Retry/Backoff)

**목적**: Symmetry Archive/Report 파이프라인을 **CI로 자동화**하고, 시크릿/재시도/알림/롤백을 묶어 **운용 안전성**을 확보합니다. 기본은 GitHub Actions 기준이며, GitLab CI 스니펫도 제공합니다.

---

## 0) 디렉터리 & 보일러플레이트
```
.
├─ .github/workflows/
│  ├─ lumen_daily.yml            # 매일 실행(Asia/Seoul)
│  └─ lumen_archive_verify.yml   # 업로드 후 원격 검증 트리거
├─ scripts/                      # (기존 스크립트 재사용)
│  ├─ retry.py                   # 지수 백오프 재시도 래퍼
│  └─ healthcheck.py             # 간단 상태 점검(메트릭/포트/파일)
├─ configs/
│  └─ ci.env.example             # 로컬/CI 공통 ENV 예시
└─ Makefile                      # 로컬 원클릭 실행 레시피
```

---

## 1) Secrets 전략 (요약)
- **GitHub → Settings → Secrets and variables → Actions → New repository secret**
  - `GDRIVE_TOKEN`, `DROPBOX_TOKEN`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`
  - `LUMEN_ARCHIVE_KEY` (AES‑GCM 32B base64 권장)
  - `LUMEN_ALERT_URL`, `LUMEN_ALERT_SECRET`
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`
- 환경변수는 워크플로 `env:` 섹션에서 주입. **절대** 코드 저장소에 커밋하지 않음.

---

## 2) `scripts/retry.py` — 지수 백오프 재시도
```python
#!/usr/bin/env python3
import subprocess, sys, time, shlex

USAGE = "retry.py <max_attempts> <initial_delay_sec> -- <command...>"
if __name__ == "__main__":
    if "--" not in sys.argv:
        print(USAGE); sys.exit(2)
    sep = sys.argv.index("--")
    max_attempts = int(sys.argv[1])
    delay = float(sys.argv[2])
    cmd = sys.argv[sep+1:]

    for attempt in range(1, max_attempts+1):
        print(f"[retry] attempt {attempt}/{max_attempts}: {' '.join(shlex.quote(c) for c in cmd)}")
        rc = subprocess.call(cmd)
        if rc == 0:
            sys.exit(0)
        if attempt < max_attempts:
            sleep = delay * (2 ** (attempt-1))
            print(f"[retry] rc={rc} → sleep {sleep:.1f}s")
            time.sleep(sleep)
    sys.exit(rc)
```

---

## 3) `scripts/healthcheck.py` — 간단 상태 점검
```python
#!/usr/bin/env python3
import os, sys, requests, json

PASS = []
FAIL = []

def check_http(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            PASS.append(f"http {url}")
        else:
            FAIL.append(f"http {url} status={r.status_code}")
    except Exception as e:
        FAIL.append(f"http {url} err={e}")

def check_file(path):
    if os.path.exists(path): PASS.append(f"file {path}")
    else: FAIL.append(f"file {path} missing")

if __name__ == "__main__":
    # 예: Prometheus exporter, 최신 리포트/번들 경로
    check_http(os.environ.get("LUMEN_METRICS_URL", "http://localhost:9108/metrics"))
    check_file(os.environ.get("LUMEN_REPORT_MD", "controls/reports"))
    print(json.dumps({"pass": PASS, "fail": FAIL}, ensure_ascii=False))
    sys.exit(0 if not FAIL else 1)
```

---

## 4) GitHub Actions — `lumen_daily.yml`
```yaml
name: Lumen Daily (KST)

on:
  schedule:
    - cron: '5 0 * * *'   # UTC 00:05 → KST 09:05
  workflow_dispatch:

jobs:
  daily:
    runs-on: ubuntu-latest
    env:
      PYTHONUTF8: '1'
      GDRIVE_TOKEN: ${{ secrets.GDRIVE_TOKEN }}
      DROPBOX_TOKEN: ${{ secrets.DROPBOX_TOKEN }}
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      AWS_DEFAULT_REGION: ${{ secrets.AWS_DEFAULT_REGION }}
      LUMEN_ARCHIVE_KEY: ${{ secrets.LUMEN_ARCHIVE_KEY }}
      LUMEN_ALERT_URL: ${{ secrets.LUMEN_ALERT_URL }}
      LUMEN_ALERT_SECRET: ${{ secrets.LUMEN_ALERT_SECRET }}
      SMTP_HOST: ${{ secrets.SMTP_HOST }}
      SMTP_PORT: ${{ secrets.SMTP_PORT }}
      SMTP_USER: ${{ secrets.SMTP_USER }}
      SMTP_PASS: ${{ secrets.SMTP_PASS }}
      SMTP_FROM: ${{ secrets.SMTP_FROM }}

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt || true
          pip install boto3 cryptography requests pyyaml reportlab

      - name: Health check (optional)
        run: |
          python scripts/healthcheck.py || echo "healthcheck failed but continue"

      - name: Build report (MD)
        run: |
          python scripts/report_builder.py

      - name: Grafana snapshot (optional)
        run: |
          python scripts/grafana_snapshot.py || true

      - name: Build PDF
        run: |
          python scripts/report_pdf.py

      - name: Freeze archive
        run: |
          python scripts/snapshot_freeze.py

      - name: Upload archive (provider matrix)
        run: |
          day=$(date -u +%Y-%m-%d)
          python scripts/retry.py 3 5 -- python scripts/upload_archive.py $day

      - name: Verify remote integrity
        run: |
          day=$(date -u +%Y-%m-%d)
          python scripts/retry.py 2 10 -- python scripts/verify_remote.py $day

      - name: Distribute report (email/cloud)
        run: |
          python scripts/report_distribute.py || true

      - name: Notify success
        if: success()
        run: |
          python scripts/notify.py 'Lumen Daily OK' '{"stage":"daily"}'

      - name: Notify failure
        if: failure()
        run: |
          python scripts/notify.py 'Lumen Daily FAIL' '{"stage":"daily"}'
```

> KST(Asia/Seoul) 기준 오전 9:05에 실행되도록 UTC 크론을 설정했습니다.

---

## 5) 업로드 확인 트리거 — `lumen_archive_verify.yml`
```yaml
name: Lumen Verify Remote
on:
  workflow_dispatch:

jobs:
  verify:
    runs-on: ubuntu-latest
    env:
      PYTHONUTF8: '1'
      GDRIVE_TOKEN: ${{ secrets.GDRIVE_TOKEN }}
      DROPBOX_TOKEN: ${{ secrets.DROPBOX_TOKEN }}
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      AWS_DEFAULT_REGION: ${{ secrets.AWS_DEFAULT_REGION }}
      LUMEN_ARCHIVE_KEY: ${{ secrets.LUMEN_ARCHIVE_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install boto3 requests pyyaml
      - name: Verify last day
        run: |
          day=$(date -u +%Y-%m-%d)
          python scripts/verify_remote.py $day
```

---

## 6) `configs/ci.env.example`
```env
# Optional overrides for local runs
GRAFANA_BASE=http://localhost:3000
GRAFANA_DASHBOARD_UID=lumen-resonance-v01
GRAFANA_DASHBOARD_SLUG=lumen-resonance-dashboard
LUMEN_METRICS_URL=http://localhost:9108/metrics
LUMEN_REPORT_MD=controls/reports
```

---

## 7) Makefile — 로컬 원클릭
```makefile
.PHONY: daily freeze upload verify pdf report

report:
	python scripts/report_builder.py

pdf:
	python scripts/report_pdf.py

freeze:
	python scripts/snapshot_freeze.py

upload:
	day=$(shell date -u +%Y-%m-%d); \
	python scripts/retry.py 3 5 -- python scripts/upload_archive.py $$day

verify:
	day=$(shell date -u +%Y-%m-%d); \
	python scripts/retry.py 2 10 -- python scripts/verify_remote.py $$day

daily: report pdf freeze upload verify
```

---

## 8) GitLab CI 스니펫 (대안)
```yaml
stages: [daily]

daily:
  stage: daily
  image: python:3.11
  only:
    - schedules
  script:
    - pip install boto3 cryptography requests pyyaml reportlab
    - python scripts/report_builder.py
    - python scripts/report_pdf.py
    - python scripts/snapshot_freeze.py
    - day=$(date -u +%Y-%m-%d)
    - python scripts/retry.py 3 5 -- python scripts/upload_archive.py $day
    - python scripts/retry.py 2 10 -- python scripts/verify_remote.py $day
  variables:
    GDRIVE_TOKEN: $GDRIVE_TOKEN
    DROPBOX_TOKEN: $DROPBOX_TOKEN
    AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
    AWS_DEFAULT_REGION: $AWS_DEFAULT_REGION
    LUMEN_ARCHIVE_KEY: $LUMEN_ARCHIVE_KEY
```

---

## 9) 실패 시 롤백 전략(간단)
- 원격 검증 실패 → `snapshot_restore.py <day>`로 이전 스냅샷 복원 지침 출력(자동 실행은 보류)
- `notify.py`로 실패 원인·로그 링크 전송 → 수동 확인 후 재실행(`workflow_dispatch`)

---

## 10) 운영 팁
- **드라이런**: 처음 1~2일은 이메일/업로드 단계만 활성화, Self‑Tuning은 dry-run 유지
- **지표 안정화**: `washout_s`를 넉넉히, 일일 크론은 **정각±5분** 분산으로 혼잡 회피
- **가시성**: Actions 로그에서 `retry.py`의 백오프 타이밍이 명확히 드러남

이 구성으로 “생성 → 보고 → 동결 → 업로드 → 검증 → 알림”이 CI 레일 위에서 안정적으로 굴러갑니다.
