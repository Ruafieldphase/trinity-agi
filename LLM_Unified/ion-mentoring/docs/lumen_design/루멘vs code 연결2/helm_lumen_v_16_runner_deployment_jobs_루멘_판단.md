# Helm/lumen‑v16 — Runner Deployment & Jobs (루멘 판단)

> 목적: `ghcr.io/<org>/lumen-runner:16` 이미지를 배포하기 위한 **Helm 차트 스캐폴드**를 추가하고, 런너 Deployment/Job 템플릿, 값(Values), 보안/관찰성 설정을 표준화.

---

## 0) 차트 구조 (추가/갱신)
```
helm/lumen-v16/
├─ Chart.yaml
├─ values.yaml
├─ templates/
│  ├─ _helpers.tpl
│  ├─ runner-deployment.yaml
│  ├─ runner-job.yaml                # ad‑hoc 실행용 Job 템플릿 (선택)
│  ├─ servicemonitor.yaml            # (옵션) Prometheus Operator
│  ├─ networkpolicy.yaml             # (옵션) 수집 포트 화이트리스트
│  ├─ rbac-runner.yaml               # SA/Role/RoleBinding (최소권한)
│  └─ NOTES.txt
└─ files/
   └─ scripts/                       # (옵션) 소량 스크립트 번들 시 사용
```

---

## 1) values.yaml (스니펫)
`helm/lumen-v16/values.yaml`
```yaml
runner:
  enabled: true
  image:
    repository: ghcr.io/<org>/lumen-runner
    tag: "16"
    pullPolicy: IfNotPresent
  replicas: 1
  command: ["bash","-lc"]
  args: ["python --version && ls -1 scripts | head -n 50"]
  env: []
  envFrom: [] # [{secretRef: {name: lumen-runtime}}]
  serviceAccount:
    create: true
    name: ""
  resources:
    limits: {cpu: "1", memory: 512Mi}
    requests: {cpu: 100m, memory: 128Mi}
  nodeSelector: {}
  tolerations: []
  affinity: {}
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true
    seccompProfile: {type: RuntimeDefault}
  podSecurityContext:
    fsGroup: 10001
  ports:
    exporter: 9108
    proofd: 8077
  service:
    enabled: true
    type: ClusterIP
  serviceMonitor:
    enabled: true
    endpoints:
      - {port: exporter, path: /metrics, interval: 15s}
  extraVolumeMounts: []
  extraVolumes: []
```

---

## 2) _helpers.tpl
`helm/lumen-v16/templates/_helpers.tpl`
```tpl
{{- define "lumen.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{ .Values.fullnameOverride }}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "lumen.labels" -}}
app.kubernetes.io/name: {{ include "lumen.fullname" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | default .Chart.Version }}
app.kubernetes.io/part-of: lumen
{{- end -}}
```

---

## 3) Runner Deployment
`helm/lumen-v16/templates/runner-deployment.yaml`
```yaml
{{- if .Values.runner.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "lumen.fullname" . }}-runner
  labels: {{- include "lumen.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.runner.replicas }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "lumen.fullname" . }}-runner
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "lumen.fullname" . }}-runner
        {{- include "lumen.labels" . | nindent 8 }}
    spec:
      serviceAccountName: {{ include "lumen.runner.serviceAccountName" . }}
      securityContext: {{- toYaml .Values.runner.podSecurityContext | nindent 8 }}
      containers:
        - name: runner
          image: "{{ .Values.runner.image.repository }}:{{ .Values.runner.image.tag }}"
          imagePullPolicy: {{ .Values.runner.image.pullPolicy }}
          command: {{- toYaml .Values.runner.command | nindent 12 }}
          args: {{- toYaml .Values.runner.args | nindent 12 }}
          env: {{- toYaml .Values.runner.env | nindent 12 }}
          envFrom: {{- toYaml .Values.runner.envFrom | nindent 12 }}
          securityContext: {{- toYaml .Values.runner.securityContext | nindent 12 }}
          ports:
            - name: exporter
              containerPort: {{ .Values.runner.ports.exporter }}
            - name: proofd
              containerPort: {{ .Values.runner.ports.proofd }}
          readinessProbe:
            httpGet: {path: /metrics, port: exporter}
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet: {path: /metrics, port: exporter}
            initialDelaySeconds: 15
            periodSeconds: 20
          resources: {{- toYaml .Values.runner.resources | nindent 12 }}
          volumeMounts: {{- toYaml .Values.runner.extraVolumeMounts | nindent 12 }}
      volumes: {{- toYaml .Values.runner.extraVolumes | nindent 8 }}
      nodeSelector: {{- toYaml .Values.runner.nodeSelector | nindent 8 }}
      tolerations: {{- toYaml .Values.runner.tolerations | nindent 8 }}
      affinity: {{- toYaml .Values.runner.affinity | nindent 8 }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ include "lumen.fullname" . }}-runner
  labels: {{- include "lumen.labels" . | nindent 4 }}
spec:
  type: {{ .Values.runner.service.type }}
  selector:
    app.kubernetes.io/name: {{ include "lumen.fullname" . }}-runner
  ports:
    - name: exporter
      port: {{ .Values.runner.ports.exporter }}
      targetPort: exporter
    - name: proofd
      port: {{ .Values.runner.ports.proofd }}
      targetPort: proofd
{{- end }}
```

Helper: SA 이름
`helm/lumen-v16/templates/rbac-runner.yaml`
```yaml
{{- define "lumen.runner.serviceAccountName" -}}
{{- if .Values.runner.serviceAccount.create -}}
{{- default (printf "%s-runner" (include "lumen.fullname" .)) .Values.runner.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.runner.serviceAccount.name -}}
{{- end -}}
{{- end -}}
---
{{- if .Values.runner.serviceAccount.create }}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "lumen.runner.serviceAccountName" . }}
  labels: {{- include "lumen.labels" . | nindent 4 }}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ include "lumen.fullname" . }}-runner
rules:
- apiGroups: [""]
  resources: [pods, pods/log, configmaps]
  verbs: [get, list, create, watch]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{ include "lumen.fullname" . }}-runner
roleRef:
  kind: Role
  name: {{ include "lumen.fullname" . }}-runner
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: {{ include "lumen.runner.serviceAccountName" . }}
{{- end }}
```

---

## 4) Runner Job (ad‑hoc)
`helm/lumen-v16/templates/runner-job.yaml`
```yaml
{{- if .Values.runnerJob.enabled }}
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "lumen.fullname" . }}-runner-job
  labels: {{- include "lumen.labels" . | nindent 4 }}
spec:
  backoffLimit: 0
  template:
    spec:
      serviceAccountName: {{ include "lumen.runner.serviceAccountName" . }}
      restartPolicy: Never
      containers:
        - name: job
          image: "{{ .Values.runner.image.repository }}:{{ .Values.runner.image.tag }}"
          imagePullPolicy: {{ .Values.runner.image.pullPolicy }}
          command: ["bash","-lc"]
          args:
            - |
              make v16.smoke && make v16.integrated || true
          envFrom: {{- toYaml .Values.runner.envFrom | nindent 12 }}
          securityContext: {{- toYaml .Values.runner.securityContext | nindent 12 }}
          resources: {{- toYaml .Values.runner.resources | nindent 12 }}
{{- end }}
```

Values 확장:
```yaml
runnerJob:
  enabled: false
```

---

## 5) ServiceMonitor (옵션)
`helm/lumen-v16/templates/servicemonitor.yaml`
```yaml
{{- if and .Values.runner.service.enabled .Values.runner.serviceMonitor.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ include "lumen.fullname" . }}-runner
  labels: {{- include "lumen.labels" . | nindent 4 }}
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "lumen.fullname" . }}-runner
  endpoints:
  {{- toYaml .Values.runner.serviceMonitor.endpoints | nindent 2 }}
{{- end }}
```

---

## 6) NetworkPolicy (옵션)
`helm/lumen-v16/templates/networkpolicy.yaml`
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ include "lumen.fullname" . }}-runner-allow-scrape
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: {{ include "lumen.fullname" . }}-runner
  policyTypes: [Ingress]
  ingress:
  - from:
    - namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: monitoring}}
    ports:
    - {port: {{ .Values.runner.ports.exporter }}, protocol: TCP}
    - {port: {{ .Values.runner.ports.proofd }}, protocol: TCP}
```

---

## 7) NOTES.txt
`helm/lumen-v16/templates/NOTES.txt`
```
Runner deployed: {{ include "lumen.fullname" . }}-runner

Exporter metrics:  kubectl port-forward svc/{{ include "lumen.fullname" . }}-runner 9108:{{ .Values.runner.ports.exporter }} -n {{ .Release.Namespace }}
Proofd stats:      kubectl port-forward svc/{{ include "lumen.fullname" . }}-runner 8077:{{ .Values.runner.ports.proofd }} -n {{ .Release.Namespace }}

Job (optional):
  helm upgrade --install {{ .Release.Name }} {{ .Chart.Name }} \
    --set runnerJob.enabled=true
```

---

## 8) 배포/검증 (루멘 판단)
```bash
# values.yaml 내 <org> 치환 후
helm upgrade --install lumen-v16 helm/lumen-v16 -n lumen-v16 --create-namespace

# 메트릭/상태 확인
kubectl -n lumen-v16 get deploy,svc,pods
kubectl -n lumen-v16 logs deploy/lumen-v16-lumen-v16-runner -f

# (옵션) ServiceMonitor/NetworkPolicy 사용 시 CRD/네임스페이스 준비 필요
```

---

## 9) 연결 고리
- Runner 이미지: **Runner Container & Build/Push** 워크플로우 산출물 `:16`
- ArgoCD: **App‑of‑Apps & CronWorkflow** Application에서 이 차트 경로 지정
- Grafana v2/Exporter v16: 포트/메트릭 스키마 일치 확인

---

## 10) 다음 액션
1. `<org>` 확정 후 values.yaml 적용 → `helm upgrade --install` 수행
2. Exporter/proofd 포트가 대시보드 & 알림과 매칭되는지 검증
3. (옵션) runnerJob 활성화로 한 번에 `v16.smoke → v16.integrated` 드라이런

