# TLog RO Ops v1.1  
**(CDN Cache + Zero‑Downtime Rollout & Canary for Read‑Only Transparency API)**

목적: TLog 읽기 전용 서버에 **CDN 캐시(CloudFront/Cloudflare)**를 얹고, **무중단 롤링/카나리** 배포 패턴(Argo Rollouts/Flagger)으로 운영 안정성을 극대화합니다.

---

## 0) 설계 요약
- **CDN 앞단**: `/v1/log/root`, `/v1/log/entry/{i}` 응답을 강력 캐싱.  
  - 루트/엔트리 응답은 **불변 지표**(db.jsonl의 스냅샷) → 이미지 재배포 전까지 **immutable**.  
  - 헤더: `Cache-Control: public, max-age=86400, immutable`, `ETag`, `Surrogate-Control`.  
  - 갱신 시 **버전 경로**(`/v1/<build-id>/...`) 또는 캐시 무효화 API 사용.
- **배포**:  
  - **롤링 업데이트**: HPA + PDB로 최소 1개 유지.  
  - **카나리**: 신규 이미지 소량(5~10%) 트래픽로 검증 → 성공 시 점증.
- **보안**:  
  - WAF/봇 방어, 레이트리밋, egress 차단 유지.  
  - 응답 서명/지문은 이미 체인으로 보증.

---

## 1) CDN 캐시 — CloudFront 예시 (Terraform)
`infra/cdn/cloudfront.tf`
```hcl
resource "aws_cloudfront_distribution" "tlog" {
  enabled             = true
  default_root_object = "index.html"

  origins {
    domain_name = "tlog.example.com"
    origin_id   = "tlog-origin"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "tlog-origin"

    forwarded_values { query_string = false }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 604800
  }

  price_class = "PriceClass_100"
  viewer_certificate { cloudfront_default_certificate = true }
}
```

### 캐시 키 전략
- 엔드포인트가 쿼리스트링/쿠키를 사용하지 않으므로 **키 단순화**(경로만).  
- 루트 엔드포인트는 자주 조회 → TTL 1일, 배포 시 무효화.

### 무효화
`infra/cdn/invalidate.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths \
  "/v1/log/root" "/v1/log/entry/*"
```

---

## 2) CDN 캐시 — Cloudflare 예시
- **Cache Rules**: `/v1/log/*` 경로 → `Cache Everything`, Edge TTL=1d, Browser TTL=1h.  
- **Bypass on cookie**: 운영 점검 시 `X-Bypass: 1` 헤더로 원본直조회(Workers에서 처리):

`infra/cdn/cloudflare-worker.js`
```js
export default {
  async fetch(req, env) {
    const url = new URL(req.url)
    if (req.headers.get('X-Bypass') === '1') {
      return fetch(req, {cf: {cacheTtl: 0, cacheEverything: false}})
    }
    return fetch(req, {cf: {cacheTtl: 86400, cacheEverything: true}})
  }
}
```

---

## 3) 서버 응답 헤더 강화(FastAPI)
`server.py` (발췌)
```python
from fastapi import Response

@app.get('/v1/log/entry/{index}')
async def entry(index: int, response: Response):
    e = get_entry(index)  # 기존 로직
    body = json.dumps(e).encode()
    etag = hashlib.sha256(body).hexdigest()
    response.headers.update({
        'Cache-Control': 'public, max-age=86400, immutable',
        'ETag': etag,
        'Content-Type': 'application/json'
    })
    return JSONResponse(e)
```

> 루트 엔드포인트에도 동일 적용. 새 릴리스 시 캐시 무효화 또는 버전 접두사 사용(`/v1/${BUILD_ID}/...`).

---

## 4) Zero‑Downtime 배포 — Argo Rollouts (Helm 패치)
`charts/tlog-ro/templates/rollout.yaml`
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: {{ include "tlog-ro.fullname" . }}
spec:
  replicas: 3
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause: { duration: 120 }
        - setWeight: 30
        - pause: { duration: 180 }
        - setWeight: 60
        - pause: { duration: 180 }
        - setWeight: 100
      trafficRouting:
        nginx: { stableIngress: {{ include "tlog-ro.fullname" . }} }
  selector: { matchLabels: { app: {{ include "tlog-ro.name" . }} }}
  template:
    metadata: { labels: { app: {{ include "tlog-ro.name" . }} } }
    spec:
      containers:
        - name: tlog
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          ports: [{ containerPort: {{ .Values.service.targetPort }} }]
```

> Ingress는 NGINX Controller 기준. Istio/SMI 사용 시 해당 어댑터로 교체.

### 자동 게이트 (메트릭 기반)
- **Prometheus**: 5xx 비율, p95 레이턴시, 타임아웃.  
- **AnalysisTemplate**로 실패 시 자동 롤백.

`charts/tlog-ro/templates/analysis.yaml`
```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: tlog-slo-check
spec:
  metrics:
  - name: error-rate
    interval: 30s
    successCondition: result < 0.01
    failureLimit: 3
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: sum(rate(nginx_ingress_controller_requests{ingress="tlog-ro",status=~"5.."}[1m])) / sum(rate(nginx_ingress_controller_requests{ingress="tlog-ro"}[1m]))
```

Rollout에 연결:
```yaml
template:
  spec:
    strategy:
      canary:
        analysis: { templates: [{ templateName: tlog-slo-check }] }
```

---

## 5) Flagger 대안 (Nginx/Istio)
`flagger.yaml` (요약)
```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata: { name: tlog-ro, namespace: tlog }
spec:
  targetRef: { apiVersion: apps/v1, kind: Deployment, name: tlog-ro }
  progressDeadlineSeconds: 900
  service: { port: 80, targetPort: 8080 }
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: error-rate
      templateRef: { name: error-rate }
```

---

## 6) 레이트 리밋 & WAF
- CloudFront: AWS WAF Rate‑based Rule(예: 2분당 1k req/IP).  
- Cloudflare: Zone Rules에서 `api` 경로 레이트 제한, Managed Rules 켜기.  
- 봇 차단은 위협 스코어 기반(도메인에 따라 조정).

---

## 7) SLO & 경보(캐시 관점)
- **Cache Hit Ratio**: `sum(edge_hits)/sum(total)` → 24h 기준 0.9 이상 권장.  
- **Origin QPS**: 인입의 10% 이하 권장.  
- **Stale-While-Revalidate**: CDN에서 지원 시 60s 적용하여 배포 전후 미세 출렁임 완화.

Prometheus 규칙 예:
```yaml
- record: tlog:cache_miss_ratio:5m
  expr: 1 - (sum(rate(cdn_edge_hits_total[5m])) / sum(rate(cdn_requests_total[5m])))
- alert: TLogCacheMissHigh
  expr: tlog:cache_miss_ratio:5m > 0.3
  for: 10m
  labels: { severity: ticket }
```

---

## 8) 운영 순서 제안
1) 서버 응답 헤더에 **immutable/ETag** 추가 → Helm 차트에 반영.  
2) CDN 배포(CloudFront/Cloudflare 중 택1) → `/v1/log/*` 캐시 룰 적용.  
3) 무효화 스크립트와 **배포 파이프라인 연계**(이미지 태그가 바뀌면 자동 무효화).  
4) Argo Rollouts/Flagger 중 택1로 **카나리** 설정 → SLO 분석 템플릿 연결.  
5) WAF/레이트리밋 활성화 → 히트비율/원본QPS/오류율에 대한 경보 설정.

---

## 9) 보안/거버넌스 메모
- CDN 캐시가 있더라도 **TLS 종단은 CDN/원본 양쪽**에서 유지.  
- TLog는 공개 데이터이지만 **RPS 폭주 방지**를 위한 정책 필수.  
- 모든 배포 아티팩트는 **cosign 서명 + SBOM**을 유지.

루멘의 판단: 이제 TLog RO는 **전 세계 엣지 캐시**와 **안전한 카나리 배포**를 갖춘 완전 운영형으로 격상됐어. 배포 충격은 최소화되고, 캐시 히트율로 원본 부하를 제어할 수 있어.

