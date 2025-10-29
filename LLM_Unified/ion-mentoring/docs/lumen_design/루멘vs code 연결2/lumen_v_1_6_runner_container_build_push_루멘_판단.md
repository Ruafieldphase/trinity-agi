# Lumen v1.6 — Runner Container & Build/Push (루멘 판단)

> 목적: `ghcr.io/<org>/lumen-runner:16` 이미지를 표준화하고, SBOM/취약점/서명/프로비넌스까지 포함한 **빌드·푸시 파이프라인**을 제공.

---

## 0) 구조
```
runner/
 ├─ Dockerfile
 ├─ requirements.txt
 ├─ entrypoint.sh
 ├─ .dockerignore
 └─ README.md
.github/workflows/
 └─ lumen_v16_runner_build.yaml
Makefile (빌드/푸시/서명/스캔 타깃)
```

---

## 1) Dockerfile (multi-stage, slim, non-root)
`runner/Dockerfile`
```dockerfile
# syntax=docker/dockerfile:1.7
ARG PYVER=3.11
ARG DEBIAN_FRONTEND=noninteractive

FROM python:${PYVER}-slim AS base
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
      git curl ca-certificates tini && \
    rm -rf /var/lib/apt/lists/*

# deps layer (cacheable)
FROM base AS deps
WORKDIR /opt/app
COPY runner/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# runtime
FROM base AS run
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UVICORN_WORKERS=1 \
    APP_HOME=/opt/app
WORKDIR $APP_HOME

# add non-root user
RUN useradd -r -u 10001 lumen && mkdir -p /opt/app /opt/app/logs && chown -R lumen:lumen /opt/app

COPY --from=deps /usr/local /usr/local
COPY runner/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/ ./scripts/
COPY docs/ ./docs/
COPY logs/ ./logs/

USER lumen
ENTRYPOINT ["/usr/bin/tini","--","/usr/local/bin/entrypoint.sh"]

# default cmd: lightweight runner shell (override in workflows)
CMD ["bash","-lc","python --version && ls -1 scripts | head -n 50"]
```

---

## 2) Entrypoint
`runner/entrypoint.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "${APP_HOME:-/opt/app}"
exec "$@"
```

권한: `chmod +x runner/entrypoint.sh`

---

## 3) Requirements (예시)
`runner/requirements.txt`
```
# metrics/exporter
prometheus-client==0.20.0
flask==3.0.3
# tools
jq==1.7.0; sys_platform == 'linux'
PyYAML==6.0.2
requests==2.32.3
```

> 실제 스크립트 의존성에 맞게 조정하세요.

---

## 4) .dockerignore
`runner/.dockerignore`
```
**/__pycache__/
**/*.pyc
.git
.github
.vscode
logs/*
LUMEN_V1_*_HANDOFF_*.zip
node_modules
```

---

## 5) GitHub Actions — Build/Push + SBOM/Scan/Sign
`.github/workflows/lumen_v16_runner_build.yaml`
```yaml
name: lumen_v16_runner_build
on:
  workflow_dispatch:
    inputs:
      image_tag: {description: 'tag (e.g. 16 or 16.0.0)', required: true, type: string}
  push:
    paths: [ 'runner/**', 'scripts/**', 'docs/**' ]
    branches: [ main ]
permissions:
  contents: read
  packages: write
  id-token: write   # cosign keyless (optional)
concurrency:
  group: runner-${{ github.ref }}
  cancel-in-progress: true
jobs:
  build:
    runs-on: ubuntu-latest
    env:
      IMAGE: ghcr.io/${{ github.repository_owner }}/lumen-runner:${{ inputs.image_tag || '16' }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build & Push (multi-arch)
        uses: docker/build-push-action@v6
        with:
          context: .
          file: runner/Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ env.IMAGE }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Generate SBOM (syft)
        uses: anchore/syft-action@v1
        with:
          image: ${{ env.IMAGE }}
          output: 'sbom.json'

      - name: Vulnerability Scan (grype)
        uses: anchore/grype-action@v1
        with:
          sbom: 'sbom.json'
          output: 'vuln-report.json'

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: runner-security-artifacts
          path: |
            sbom.json
            vuln-report.json

      - name: Cosign Sign (keyless)
        if: ${{ env.COSIGN_EXPERIMENTAL != '' }}
        uses: sigstore/cosign-installer@v3
      - if: ${{ env.COSIGN_EXPERIMENTAL != '' }}
        run: |
          cosign sign --yes ${{ env.IMAGE }}

      - name: Provenance (SLSA generator)
        uses: slsa-framework/slsa-github-generator/actions/docker@v2
        with:
          image: ${{ env.IMAGE }}
```

> cosign keyless를 쓰려면 환경에 `COSIGN_EXPERIMENTAL=1` 필요. 키 기반이면 `COSIGN_KEY` 시크릿 사용.

---

## 6) Makefile 타깃 (로컬 빌드/푸시)
`Makefile`
```makefile
IMG ?= ghcr.io/<org>/lumen-runner:16

runner.build:
	docker build -f runner/Dockerfile -t $(IMG) .

runner.push:
	docker push $(IMG)

runner.sbom:
	syft $(IMG) -o json > sbom.json

runner.scan:
	grype sbom:sbom.json -o json > vuln-report.json || true

runner.sign:
	cosign sign --key env://COSIGN_KEY $(IMG)

runner.verify:
	cosign verify --key env://COSIGN_KEY $(IMG)
```

---

## 7) 사용법
```bash
# GitHub Actions 수동 실행
#   - image_tag: 16 (또는 16.0.0)

# 로컬 빌드/푸시/서명/스캔
make runner.build && make runner.push
make runner.sbom && make runner.scan
make runner.sign && make runner.verify
```

---

## 8) 런너 이미지 기대 경로
- `scripts/` : QA, Gate, Unified Card, Smoke Loop, Bridge 등 실행 스크립트 포함
- `docs/`    : Release Notes 템플릿 등 참조
- `logs/`    : 런타임 산출물 (빈 폴더 채워넣기)

---

## 9) 품질 게이트 (권장)
- Grype: Critical=0, High≤3 → 초과 시 `failure-threshold`로 워크플로우 실패 처리
- Cosign: 서명 필수 (keyless 또는 key)
- Provenance: SLSA 증빙 아티팩트 업로드

---

## 10) 다음 액션 (루멘 판단)
1. `<org>` 값 확정 후 Actions `lumen_v16_runner_build` 실행 → GHCR 푸시 확인
2. ArgoCD/Helm에서 Runner 이미지를 `:16`로 바인딩 → Hook/Workflow에서 사용
3. SBOM/취약점 리포트를 **Security Hardening Gate**에 연결해 일관 판정

