# Helm/lumen‑v16 — Exporter & Proofd Services (루멘 판단)

> 목적: v1.6에서 필요한 **Exporter v16(메트릭)**, **Proofd v16(`/stats`)**를 Helm 차트에 포함해 일관된 배포/모니터링을 제공. Service/ServiceMonitor/Ingress(옵션), RBAC, 보안컨텍스트, 값(Values)까지 표준화.

---

## 0) 차트 구조 (추가/갱신)
```
helm/lumen-v16/
├─ values.yaml
├─ templates/
│  ├─ exporter-deployment.yaml
│  ├─ exporter-service.yaml
│  ├─ proofd-deployment.yaml
│  ├─ proofd-service.yaml
│  ├─ servicemonitor-exporter.yaml   # (옵션) Prometheus Operator
│  ├─ ingress-proofd.yaml            # (옵션)
│  └─ rbac-exporter.yaml             # (필요 시)
```

---

## 1) values.yaml (스니펫 추가)
`helm/lumen-v16/values.yaml`
```yaml
exporter:
  enabled: true
  image: {repository: ghcr.io/<org>/lumen-runner, tag: "16", pullPolicy: IfNotPresent}
  replicas: 1
  port: 9108
  path: /metrics
  resources: {limits: {cpu: "500m", memory: 256Mi}, requests: {cpu: 50m, memory: 64Mi}}
  securityContext: {runAsNonRoot: true, runAsUser: 10001, allowPrivilegeEscalation: false, readOnlyRootFilesystem: true, seccompProfile: {type: RuntimeDefault}}
  env: []
  envFrom: [] # [{secretRef: {name: lumen-runtime}}]
  serviceMonitor: {enabled: true, interval: 15s}

proofd:
  enabled: true
  image: {repository: ghcr.io/<org>/lumen-runner, tag: "16", pullPolicy: IfNotPresent}
  replicas: 1
  port: 8077
  path: /stats
  resources: {limits: {cpu: "500m", memory: 256Mi}, requests: {cpu: 50m, memory: 64Mi}}
  securityContext: {runAsNonRoot: true, runAsUser: 10001, allowPrivilegeEscalation: false, readOnlyRootFilesystem: true, seccompProfile: {type: RuntimeDefault}}
  env: []
  envFrom: []
  ingress:
    enabled: false
    className: ""
    host: proofd.local
    annotations: {}
    tls: []
```

---

## 2) Exporter — Deployment/Service
`helm/lumen-v16/templates/exporter-deployment.yaml`
```yaml
{{- if .Values.exporter.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "lumen.fullname" . }}-exporter
  labels: {{- include "lumen.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.exporter.replicas }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "lumen.fullname" . }}-exporter
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "lumen.fullname" . }}-exporter
        {{- include "lumen.labels" . | nindent 8 }}
    spec:
      securityContext: {runAsNonRoot: true}
      containers:
        - name: exporter
          image: "{{ .Values.exporter.image.repository }}:{{ .Values.exporter.image.tag }}"
          imagePullPolicy: {{ .Values.exporter.image.pullPolicy }}
          command: ["bash","-lc"]
          args: ["python lumen_v1_5_preview_assets/exporter.py || python scripts/serve_metrics_v16.py"]
          ports: [{name: metrics, containerPort: {{ .Values.exporter.port }}}]
          readinessProbe: {httpGet: {path: {{ .Values.exporter.path }}, port: metrics}, initialDelaySeconds: 5, periodSeconds: 10}
          livenessProbe:  {httpGet: {path: {{ .Values.exporter.path }}, port: metrics}, initialDelaySeconds: 15, periodSeconds: 20}
          securityContext: {{- toYaml .Values.exporter.securityContext | nindent 12 }}
          resources: {{- toYaml .Values.exporter.resources | nindent 12 }}
          env: {{- toYaml .Values.exporter.env | nindent 12 }}
          envFrom: {{- toYaml .Values.exporter.envFrom | nindent 12 }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ include "lumen.fullname" . }}-exporter
  labels: {{- include "lumen.labels" . | nindent 4 }}
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: {{ include "lumen.fullname" . }}-exporter
  ports:
    - name: metrics
      port: {{ .Values.exporter.port }}
      targetPort: metrics
{{- end }}
```

`helm/lumen-v16/templates/servicemonitor-exporter.yaml`
```yaml
{{- if and .Values.exporter.enabled .Values.exporter.serviceMonitor.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ include "lumen.fullname" . }}-exporter
  labels: {{- include "lumen.labels" . | nindent 4 }}
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "lumen.fullname" . }}-exporter
  endpoints:
    - port: metrics
      path: {{ .Values.exporter.path }}
      interval: {{ .Values.exporter.serviceMonitor.interval }}
{{- end }}
```

---

## 3) Proofd — Deployment/Service/Ingress(옵션)
`helm/lumen-v16/templates/proofd-deployment.yaml`
```yaml
{{- if .Values.proofd.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "lumen.fullname" . }}-proofd
  labels: {{- include "lumen.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.proofd.replicas }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "lumen.fullname" . }}-proofd
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "lumen.fullname" . }}-proofd
        {{- include "lumen.labels" . | nindent 8 }}
    spec:
      securityContext: {runAsNonRoot: true}
      containers:
        - name: proofd
          image: "{{ .Values.proofd.image.repository }}:{{ .Values.proofd.image.tag }}"
          imagePullPolicy: {{ .Values.proofd.image.pullPolicy }}
          command: ["bash","-lc"]
          args: ["python scripts/proofd_stats_v16.py"]
          ports: [{name: http, containerPort: {{ .Values.proofd.port }}}]
          readinessProbe: {httpGet: {path: {{ .Values.proofd.path }}, port: http}, initialDelaySeconds: 5, periodSeconds: 10}
          livenessProbe:  {httpGet: {path: {{ .Values.proofd.path }}, port: http}, initialDelaySeconds: 15, periodSeconds: 20}
          securityContext: {{- toYaml .Values.proofd.securityContext | nindent 12 }}
          resources: {{- toYaml .Values.proofd.resources | nindent 12 }}
          env: {{- toYaml .Values.proofd.env | nindent 12 }}
          envFrom: {{- toYaml .Values.proofd.envFrom | nindent 12 }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ include "lumen.fullname" . }}-proofd
  labels: {{- include "lumen.labels" . | nindent 4 }}
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: {{ include "lumen.fullname" . }}-proofd
  ports:
    - name: http
      port: {{ .Values.proofd.port }}
      targetPort: http
{{- end }}
```

`helm/lumen-v16/templates/ingress-proofd.yaml`
```yaml
{{- if and .Values.proofd.enabled .Values.proofd.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "lumen.fullname" . }}-proofd
  labels: {{- include "lumen.labels" . | nindent 4 }}
  annotations: {{- toYaml .Values.proofd.ingress.annotations | nindent 4 }}
spec:
  ingressClassName: {{ .Values.proofd.ingress.className | quote }}
  rules:
    - host: {{ .Values.proofd.ingress.host }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "lumen.fullname" . }}-proofd
                port: {number: {{ .Values.proofd.port }}}
  tls: {{- toYaml .Values.proofd.ingress.tls | nindent 4 }}
{{- end }}
```

---

## 4) RBAC (필요 시 최소권한)
Exporter/Proofd 모두 클러스터 리소스 접근이 필요 없다면 SA/RBAC 생략 가능. 로그/컨피그맵 접근이 필요하면 `rbac-exporter.yaml`로 Role/RoleBinding 최소권한 부여.

---

## 5) 배포/검증 (루멘 판단)
```bash
# 1) values.yaml 의 <org> 교체
helm upgrade --install lumen-v16 helm/lumen-v16 -n lumen-v16 --create-namespace

# 2) 상태 확인
kubectl -n lumen-v16 get deploy,svc
kubectl -n lumen-v16 port-forward svc/<release>-lumen-v16-exporter 9108:9108 &
curl -sf localhost:9108/metrics | head

kubectl -n lumen-v16 port-forward svc/<release>-lumen-v16-proofd 8077:8077 &
curl -sf localhost:8077/stats | jq
```

---

## 6) Grafana/Prometheus 연동 체크리스트
- ServiceMonitor가 `metrics` 포트를 정상 스크랩하는지 확인
- 대시보드 v16에서 루프/위상/창의/엔트로피/보안 타일이 실데이터로 채워지는지 확인
- Proofd `/stats`를 하이퍼링크(패널 링크)로 연결

---

## 7) Next
- Runner Job과 조합해 `v16.smoke → v16.integrated`를 Kubernetes 상에서 주기 실행(CronWorkflow와 연동)
- Ingress 활성화 시, 인증/허용목록(Whitelisting) 추가(예: oauth2-proxy, mTLS)