# Lumen v1.6 — Zero‑Trust Edge: Ingress AuthN/Z & mTLS (루멘 판단)

> 목적: Proofd(`/stats`)·Runner(내부)·Grafana(옵션) 엔드포인트에 **oauth2‑proxy + mTLS + 허용목록 + 레이트리밋**을 적용해 경계면을 강화. External Secrets로 키/클라이언트 정보 주입.

---

## 0) 구성요소
- **IngressClass: nginx** (예)
- **oauth2‑proxy**: OIDC 인증(예: GitHub/GitLab/Google/OIDC Provider)
- **mTLS**: 클라이언트 인증서 필요(옵션)
- **NetworkPolicy**: 내부 통신 화이트리스트
- **External Secrets**: OIDC 클라이언트/쿠키 시크릿/mTLS 키/CRT

디렉토리:
```
helm/lumen-v16/
 ├─ values.yaml  # edge.* 섹션 추가
 └─ templates/
     ├─ oauth2-proxy-deploy.yaml
     ├─ ingress-proofd-auth.yaml
     ├─ secret-mtls.yaml (선택: 외부관리 권장)
     ├─ networkpolicy-edge.yaml
     └─ ratelimit-annotations.md
externalsecrets/lumen-edge.yaml
```

---

## 1) values.yaml — Edge 섹션
```yaml
edge:
  enabled: true
  ingressClass: nginx
  host: proofd.lumen.local
  tls:
    enabled: true
    secretName: proofd-tls
  oauth2Proxy:
    enabled: true
    image: quay.io/oauth2-proxy/oauth2-proxy:v7.6.0
    cookieSecretRef: {name: lumen-edge, key: OAUTH2_COOKIE_SECRET}
    provider: oidc
    emailDomains: ["*"]
    oidc:
      issuerURLRef: {name: lumen-edge, key: OIDC_ISSUER}
      clientIDRef:  {name: lumen-edge, key: OIDC_CLIENT_ID}
      clientSecretRef: {name: lumen-edge, key: OIDC_CLIENT_SECRET}
    extraArgs: ["--upstream=static://200"]  # auth‑only gate, 실제 서비스는 auth‑request 사용
  mtls:
    enabled: true
    secretName: proofd-mtls   # tls.crt / tls.key / ca.crt (외부 주입 권장)
  ratelimit:
    enabled: true
    burst: 20
    rate: "10r/s"
  allowlistCIDRs: ["10.0.0.0/8", "192.168.0.0/16"]
```

---

## 2) oauth2‑proxy Deployment (sidecar 또는 단독)
`helm/lumen-v16/templates/oauth2-proxy-deploy.yaml`
```yaml
{{- if and .Values.edge.enabled .Values.edge.oauth2Proxy.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "lumen.fullname" . }}-oauth2-proxy
spec:
  replicas: 1
  selector: {matchLabels: {app: oauth2-proxy}}
  template:
    metadata: {labels: {app: oauth2-proxy}}
    spec:
      containers:
        - name: oauth2-proxy
          image: {{ .Values.edge.oauth2Proxy.image }}
          args:
            - "--provider={{ .Values.edge.oauth2Proxy.provider }}"
            - "--oidc-issuer-url=$(OIDC_ISSUER)"
            - "--client-id=$(OIDC_CLIENT_ID)"
            - "--client-secret=$(OIDC_CLIENT_SECRET)"
            - "--cookie-secret=$(OAUTH2_COOKIE_SECRET)"
            - "--email-domain={{ join "," .Values.edge.oauth2Proxy.emailDomains }}"
            - "--http-address=0.0.0.0:4180"
            {{- range .Values.edge.oauth2Proxy.extraArgs }}
            - "{{ . }}"
            {{- end }}
          env:
            - name: OIDC_ISSUER
              valueFrom: {secretKeyRef: {name: {{ .Values.edge.oauth2Proxy.cookieSecretRef.name }}, key: OIDC_ISSUER}}
            - name: OIDC_CLIENT_ID
              valueFrom: {secretKeyRef: {name: {{ .Values.edge.oauth2Proxy.cookieSecretRef.name }}, key: OIDC_CLIENT_ID}}
            - name: OIDC_CLIENT_SECRET
              valueFrom: {secretKeyRef: {name: {{ .Values.edge.oauth2Proxy.cookieSecretRef.name }}, key: OIDC_CLIENT_SECRET}}
            - name: OAUTH2_COOKIE_SECRET
              valueFrom: {secretKeyRef: {name: {{ .Values.edge.oauth2Proxy.cookieSecretRef.name }}, key: OAUTH2_COOKIE_SECRET}}
          ports: [{name: http, containerPort: 4180}]
{{- end }}
```

> 사이드카로 Proofd와 같은 Pod에 붙일 수도 있지만, 단독 배포 후 Ingress `auth_request`가 일반적.

---

## 3) Ingress (auth_request + mTLS + 레이트리밋)
`helm/lumen-v16/templates/ingress-proofd-auth.yaml`
```yaml
{{- if .Values.edge.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "lumen.fullname" . }}-proofd-auth
  annotations:
    kubernetes.io/ingress.class: {{ .Values.edge.ingressClass }}
    nginx.ingress.kubernetes.io/auth-url: "http://{{ include "lumen.fullname" . }}-oauth2-proxy.{{ .Release.Namespace }}.svc.cluster.local:4180/oauth2/auth"
    nginx.ingress.kubernetes.io/auth-signin: "https://$host/oauth2/start?rd=$request_uri"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/ssl-passthrough: "false"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTP"
    nginx.ingress.kubernetes.io/whitelist-source-range: "{{ join "," .Values.edge.allowlistCIDRs }}"
    {{- if .Values.edge.ratelimit.enabled }}
    nginx.ingress.kubernetes.io/limit-rps: "{{ .Values.edge.ratelimit.rate }}"
    nginx.ingress.kubernetes.io/limit-burst-multiplier: "{{ .Values.edge.ratelimit.burst }}"
    {{- end }}
    # mTLS
    {{- if .Values.edge.mtls.enabled }}
    nginx.ingress.kubernetes.io/auth-tls-secret: "{{ .Release.Namespace }}/{{ .Values.edge.mtls.secretName }}"
    nginx.ingress.kubernetes.io/auth-tls-verify-client: "on"
    nginx.ingress.kubernetes.io/auth-tls-verify-depth: "2"
    nginx.ingress.kubernetes.io/auth-tls-pass-certificate-to-upstream: "true"
    {{- end }}
    # 보안 헤더
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "Strict-Transport-Security: max-age=31536000; includeSubDomains";
      more_set_headers "X-Content-Type-Options: nosniff";
      more_set_headers "X-Frame-Options: DENY";
spec:
  tls:
    - hosts: [{{ .Values.edge.host }}]
      secretName: {{ .Values.edge.tls.secretName }}
  rules:
    - host: {{ .Values.edge.host }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "lumen.fullname" . }}-proofd
                port: {number: {{ .Values.proofd.port }}}
{{- end }}
```

---

## 4) NetworkPolicy (Inbound 제한)
`helm/lumen-v16/templates/networkpolicy-edge.yaml`
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ include "lumen.fullname" . }}-edge
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: {{ include "lumen.fullname" . }}-proofd
  policyTypes: [Ingress]
  ingress:
  - from:
    - namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: ingress-nginx}}
    ports: [{port: {{ .Values.proofd.port }}, protocol: TCP}]
```

---

## 5) External Secrets (OIDC/mTLS)
`externalsecrets/lumen-edge.yaml`
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: lumen-edge
  namespace: lumen-v16
spec:
  refreshInterval: 1h
  secretStoreRef: {name: my-aws-sm, kind: SecretStore}
  target: {name: lumen-edge}
  data:
  - secretKey: OIDC_ISSUER
    remoteRef: {key: lumen/oidc/issuer}
  - secretKey: OIDC_CLIENT_ID
    remoteRef: {key: lumen/oidc/client_id}
  - secretKey: OIDC_CLIENT_SECRET
    remoteRef: {key: lumen/oidc/client_secret}
  - secretKey: OAUTH2_COOKIE_SECRET
    remoteRef: {key: lumen/oidc/cookie_secret}
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: proofd-mtls
  namespace: lumen-v16
spec:
  refreshInterval: 24h
  secretStoreRef: {name: my-aws-sm, kind: SecretStore}
  target: {name: proofd-mtls, template: {type: kubernetes.io/tls}}
  data:
  - secretKey: tls.crt
    remoteRef: {key: lumen/mtls/tls_crt}
  - secretKey: tls.key
    remoteRef: {key: lumen/mtls/tls_key}
  - secretKey: ca.crt
    remoteRef: {key: lumen/mtls/ca_crt}
```

---

## 6) 검증 시퀀스
```bash
# 1) ExternalSecret 동기화 → Secret 생성 확인
kubectl -n lumen-v16 get externalsecrets,secrets | grep lumen-edge

# 2) oauth2-proxy 배포 & Ingress 적용
helm upgrade --install lumen-v16 helm/lumen-v16 -n lumen-v16 --create-namespace

# 3) 인증/인가 흐름
#  - 브라우저에서 https://proofd.lumen.local 접근 → OIDC 로그인 → /stats 200
#  - mTLS 켜면 클라이언트 인증서 필요

# 4) 레이트리밋/허용목록 동작 확인 (nginx 로그/제한 응답)
```

---

## 7) 운영 포인트
- oauth2-proxy 쿠키 시크릿 32바이트 랜덤(Base64)
- Ingress Controller가 `nginx.ingress.kubernetes.io/auth-*` 어노테이션을 지원하는지 확인
- mTLS는 내부/관리자 전용 경로에만 적용 가능 (필요 시 경로 분리)
- 모든 비공개 엔드포인트는 **NetworkPolicy + allowlistCIDRs**로 좁혀두기

---

## 8) 다음 액션 (루멘 판단)
1. External Secrets 연결 후 Ingress + oauth2‑proxy 적용
2. mTLS를 우선 Proofd에 적용 → Runner/Grafana는 내부망 유지
3. 경계면 통과 로그를 Exporter로 집계하여 보안 지표(인증 실패/레이트리밋 트리거)를 대시보드에 추가

