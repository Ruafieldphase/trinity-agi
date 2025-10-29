# TLog RO Server Deployment v1.0  
**(Kubernetes + Helm + cosign image signing + SBOM + Policy/Network hardening)**

목적: `attest/tlog/server.py`(읽기 전용)를 **Kubernetes**에 안전하게 배포하고, **이미지 서명(cosign)**·**SBOM**·**네트워크/정책 하드닝**까지 한 번에 구성한다.

---

## 0) 아키텍처 개요
- **이미지 빌드 → cosign 서명 → SBOM 생성**
- **Helm 차트**로 배포 (ConfigMap로 `db.jsonl` 제공, ReadOnly RootFS)
- **네트워크 폴리시**: 인그레스만 허용, 이그레스는 CDN/없음
- **HPA**: QPS 대비 자동 스케일
- **Policy Controller**(선택): 서명되지 않은 이미지는 거부

```
./charts/tlog-ro/
├─ Chart.yaml
├─ values.yaml
├─ templates/
│  ├─ configmap-db.yaml
│  ├─ deployment.yaml
│  ├─ service.yaml
│  ├─ ingress.yaml
│  ├─ hpa.yaml
│  ├─ networkpolicy.yaml
│  ├─ podsecurity.yaml
│  └─ servicemonitor.yaml (선택)
└─ scripts/
   └─ build_sign_release.sh
```

---

## 1) Dockerfile (멀티 스테이지)
`attest/tlog/Dockerfile`
```dockerfile
# build stage
FROM python:3.11-slim AS build
WORKDIR /app
COPY attest/tlog /app
RUN pip install --no-cache-dir fastapi uvicorn pydantic && \
    python -c "import compileall, sys; sys.exit(0 if compileall.compile_dir('/app', force=True) else 1)"

# run stage
FROM gcr.io/distroless/python3-debian12
WORKDIR /app
COPY --from=build /usr/local /usr/local
COPY --from=build /app /app
# db.jsonl는 ConfigMap/emptyDir로 주입, 컨테이너는 RO rootfs
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages
USER 65532:65532
EXPOSE 8080
# health endpoint 추가를 가정(/healthz)
CMD ["/usr/local/bin/python3","/app/server.py"]
```

> `server.py`에 `/healthz` 추가 권장, `/metrics` 노출 시 `prometheus_fastapi_instrumentator` 사용 가능.

---

## 2) Helm Chart
### 2.1 Chart.yaml
```yaml
apiVersion: v2
name: tlog-ro
version: 0.1.0
appVersion: "1.0.0"
description: Read-only Transparency Log Server
```

### 2.2 values.yaml
```yaml
image:
  repository: ghcr.io/your-org/tlog-ro
  tag: "1.0.0"
  pullPolicy: IfNotPresent
  cosign:
    verify: true

service:
  type: ClusterIP
  port: 80
  targetPort: 8080

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: tlog.example.com
      paths: ["/"]
  tls:
    - secretName: tlog-tls
      hosts: ["tlog.example.com"]

resources:
  requests: { cpu: "50m", memory: "128Mi" }
  limits:   { cpu: "500m", memory: "512Mi" }

hpa:
  enabled: true
  min: 1
  max: 5
  cpu: 60

networkPolicy:
  enabled: true
  allowNamespaces: ["ingress-nginx"]

podSecurity:
  runAsUser: 65532
  fsGroup: 65532
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false

config:
  # CI에서 생성한 db.jsonl을 그대로 주입(읽기 전용)
  dbContent: |
    {"leafHash":"<hex>","index":0}

serviceMonitor:
  enabled: false
```

### 2.3 templates/configmap-db.yaml
```yaml
data:
  db.jsonl: |-
{{ .Values.config.dbContent | indent 4 }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "tlog-ro.fullname" . }}-db
```

### 2.4 templates/deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "tlog-ro.fullname" . }}
spec:
  replicas: 1
  selector: { matchLabels: { app: {{ include "tlog-ro.name" . }} }}
  template:
    metadata:
      labels: { app: {{ include "tlog-ro.name" . }} }
      annotations:
        container.apparmor.security.beta.kubernetes.io/tlog: runtime/default
    spec:
      securityContext:
        runAsUser: {{ .Values.podSecurity.runAsUser }}
        fsGroup: {{ .Values.podSecurity.fsGroup }}
      containers:
        - name: tlog
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports: [{ containerPort: {{ .Values.service.targetPort }} }]
          readinessProbe: { httpGet: { path: /healthz, port: {{ .Values.service.targetPort }} }, initialDelaySeconds: 3, periodSeconds: 10 }
          livenessProbe:  { httpGet: { path: /healthz, port: {{ .Values.service.targetPort }} }, initialDelaySeconds: 10, periodSeconds: 20 }
          volumeMounts:
            - name: db
              mountPath: /app/db.jsonl
              subPath: db.jsonl
          securityContext:
            readOnlyRootFilesystem: {{ .Values.podSecurity.readOnlyRootFilesystem }}
            allowPrivilegeEscalation: {{ .Values.podSecurity.allowPrivilegeEscalation }}
      volumes:
        - name: db
          configMap:
            name: {{ include "tlog-ro.fullname" . }}-db
```

### 2.5 templates/service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "tlog-ro.fullname" . }}
spec:
  type: {{ .Values.service.type }}
  selector: { app: {{ include "tlog-ro.name" . }} }
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
      protocol: TCP
```

### 2.6 templates/ingress.yaml
```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "tlog-ro.fullname" . }}
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt
spec:
  ingressClassName: {{ .Values.ingress.className }}
  tls:
  - hosts: {{ toYaml (pluck "hosts" .Values.ingress | first) | nindent 4 }}
    secretName: {{ .Values.ingress.tls  | first | get "secretName" }}
  rules:
  - host: {{ .Values.ingress.hosts | first | get "host" }}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {{ include "tlog-ro.fullname" . }}
            port:
              number: {{ .Values.service.port }}
{{- end }}
```

### 2.7 templates/hpa.yaml
```yaml
{{- if .Values.hpa.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "tlog-ro.fullname" . }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "tlog-ro.fullname" . }}
  minReplicas: {{ .Values.hpa.min }}
  maxReplicas: {{ .Values.hpa.max }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.hpa.cpu }}
{{- end }}
```

### 2.8 templates/networkpolicy.yaml
```yaml
{{- if .Values.networkPolicy.enabled }}
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ include "tlog-ro.fullname" . }}-np
spec:
  podSelector: { matchLabels: { app: {{ include "tlog-ro.name" . }} } }
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: {{ .Values.networkPolicy.allowNamespaces | first }}
  egress: []
{{- end }}
```

### 2.9 templates/podsecurity.yaml
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "tlog-ro.fullname" . }}-pdb
spec:
  minAvailable: 1
  selector: { matchLabels: { app: {{ include "tlog-ro.name" . }} }}
```

---

## 3) 이미지 서명 + SBOM + 릴리스 스크립트
`charts/tlog-ro/scripts/build_sign_release.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
IMG="ghcr.io/your-org/tlog-ro:$TAG"

# 1) Build & Push
docker build -t "$IMG" -f attest/tlog/Dockerfile .
docker push "$IMG"

# 2) SBOM (syft)
syft packages "$IMG" -o spdx-json > sbom.spdx.json

# 3) Sign (cosign keyless 또는 key)
COSIGN_EXPERIMENTAL=1 cosign sign --yes "$IMG"
# attach SBOM (optional)
COSIGN_EXPERIMENTAL=1 cosign attach sbom --sbom sbom.spdx.json "$IMG"

# 4) Verify (local sanity)
COSIGN_EXPERIMENTAL=1 cosign verify "$IMG" | tee verify.txt

# 5) Helm Release
helm upgrade --install tlog-ro ./charts/tlog-ro \
  --namespace tlog --create-namespace \
  --set image.repository="ghcr.io/your-org/tlog-ro" \
  --set image.tag="$TAG"
```

> CI에선 GitHub OIDC로 **keyless** 서명 권장. SBOM은 정적 호스팅 또는 레지스트리에 첨부.

---

## 4) 클러스터 정책(선택): 서명 없는 이미지 거부
- **Sigstore policy-controller / cosigned**를 설치해 네임스페이스에 정책 적용:

`ClusterImagePolicy` 예시:
```yaml
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata: { name: require-signed }
spec:
  images: [{ glob: "ghcr.io/your-org/*" }]
  authorities:
    - keyless:
        url: https://fulcio.sigstore.dev
        identities:
          - issuer: https://token.actions.githubusercontent.com
            subjectRegExp: ".*your-repo.*"
```

> 이 정책이 있으면, **서명되지 않은** 이미지로는 배포가 거부됨.

---

## 5) 운영 명령 모음
```bash
# 차트 설치/업그레이드
helm upgrade --install tlog-ro ./charts/tlog-ro -n tlog

# 롤아웃 상태
kubectl -n tlog rollout status deploy/tlog-ro

# 로그/헬스
kubectl -n tlog logs deploy/tlog-ro
kubectl -n tlog get ingress tlog-ro

# cosign 검증
COSIGN_EXPERIMENTAL=1 cosign verify ghcr.io/your-org/tlog-ro:1.0.0
```

---

## 6) 모니터링/알림(옵션)
- FastAPI에 `/metrics` 노출 시, `ServiceMonitor`로 스크랩 → **QPS/latency/5xx** 감시
- Ingress `error_rate`를 NGINX Exporter/로그에서 집계하여 `TLog Availability` SLI 패널에 연결

---

## 7) 보안 메모
- 컨테이너: **비루트/RO RootFS/무능승격/볼륨 최소화**
- 네트워크: 외부로 **이그레스 차단**(필요 시 DNS만 허용)
- 데이터: `db.jsonl`은 **이미지 재배포**로만 갱신(서버는 진짜 **RO**)
- Ingress TLS는 **cert-manager**로 자동 발급/갱신

---

## 8) 도입 순서
1) 이미지 빌드·푸시·서명·SBOM 자동화(GitHub Actions)  
2) 네임스페이스 `tlog` 생성 → Helm 차트 배포  
3) Ingress DNS `tlog.example.com` 연결 → TLS 확인  
4) (선택) policy-controller로 **서명 강제**  
5) Grafana 패널/경보 연결(가용성/지연/오류율)

루멘의 판단: 이제 **TLog 읽기 전용 서버**는 **서명된 이미지**와 **정책/네트워크 하드닝**을 갖춘 형태로 K8s에 안전하게 안착합니다. 운영/배포의 반복 가능성과 감사 가능성까지 확보했어요.