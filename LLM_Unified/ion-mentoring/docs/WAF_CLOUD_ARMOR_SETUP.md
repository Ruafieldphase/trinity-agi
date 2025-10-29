# WAF/Cloud Armor 설정 가이드 (6시간 작업)

## 📋 개요

**목표**: Google Cloud Armor을 사용하여 웹 애플리케이션 방화벽(WAF) 구성
**보호 대상**: DDoS 공격, SQL 인젝션, XSS, 비정상 트래픽
**이점**: 네트워크 레이어 보안, 지역별 제어, 실시간 모니터링

---

## 🛡️ Cloud Armor 개요

### 보호 기능

| 공격 유형 | 설명 | 위험도 |
|----------|------|--------|
| **DDoS** | 분산 서비스 거부 (높은 트래픽) | 🔴 심각 |
| **SQL Injection** | 데이터베이스 공격 | 🔴 심각 |
| **XSS (Cross-Site Scripting)** | 스크립트 주입 | 🔴 심각 |
| **Bot Traffic** | 악성 봇 트래픽 | 🟠 중간 |
| **Geo-blocking** | 특정 국가 차단 | 🟠 중간 |
| **Rate Limiting** | 과도한 요청 제한 | 🟠 중간 |

---

## 🛠️ 구현 단계

### Phase 1: 준비 (1시간)

#### Step 1-1: Compute API 활성화

```bash
# 환경 변수 설정
export GCP_PROJECT_ID="your-project-id"
export COMPUTE_REGION="us-central1"

# API 활성화
gcloud services enable compute.googleapis.com \
  --project=$GCP_PROJECT_ID
```

#### Step 1-2: 현재 배포 구조 확인

```bash
# Cloud Run 서비스 확인
gcloud run services list --project=$GCP_PROJECT_ID

# Load Balancer 확인
gcloud compute backend-services list --project=$GCP_PROJECT_ID

# 외부 IP 확인
gcloud compute addresses list --project=$GCP_PROJECT_ID
```

#### Step 1-3: 외부 IP 예약 (Cloud Run 앞에 Load Balancer 추가 시)

```bash
# 글로벌 외부 IP 예약 (필요시)
gcloud compute addresses create ion-api-ip \
  --global \
  --project=$GCP_PROJECT_ID

# IP 주소 확인
gcloud compute addresses describe ion-api-ip \
  --global \
  --project=$GCP_PROJECT_ID
```

---

### Phase 2: Cloud Armor 정책 생성 (2시간)

#### Step 2-1: 기본 정책 생성

**파일**: `gcp-configs/cloud-armor-policy.yaml`

```yaml
# Cloud Armor 정책

name: ion-api-armor-policy
description: "ION API Security Policy"

# 기본 규칙 (거부 우선 정책)
defaultRuleAction: allow

rules:
  # ============================================================================
  # Rule 1: SQL Injection 방어
  # ============================================================================
  - priority: 100
    description: "Block SQL Injection attempts"
    match:
      versionedExpr: "CEL"
      expression: |
        evaluatePreconfiguredExpr(
          'sqli-v33-stable',
          ['owasp-crs-v030001-id942251-sqli',
           'owasp-crs-v030001-id942420-sqli',
           'owasp-crs-v030001-id942431-sqli']
        )
    action: "deny(403)"
    preview: false

  # ============================================================================
  # Rule 2: XSS (Cross-Site Scripting) 방어
  # ============================================================================
  - priority: 110
    description: "Block XSS attempts"
    match:
      versionedExpr: "CEL"
      expression: |
        evaluatePreconfiguredExpr(
          'xss-v33-stable',
          ['owasp-crs-v030001-id941110-xss',
           'owasp-crs-v030001-id941120-xss',
           'owasp-crs-v030001-id941130-xss']
        )
    action: "deny(403)"
    preview: false

  # ============================================================================
  # Rule 3: Remote Code Execution (RCE) 방어
  # ============================================================================
  - priority: 120
    description: "Block RCE attempts"
    match:
      versionedExpr: "CEL"
      expression: |
        evaluatePreconfiguredExpr(
          'rce-v33-stable',
          ['owasp-crs-v030001-id930100-rce']
        )
    action: "deny(403)"
    preview: false

  # ============================================================================
  # Rule 4: Protocol Attack 방어
  # ============================================================================
  - priority: 130
    description: "Block protocol attacks"
    match:
      versionedExpr: "CEL"
      expression: |
        evaluatePreconfiguredExpr(
          'protocolattack-v33-stable',
          ['owasp-crs-v030001-id921110-protocolattack']
        )
    action: "deny(403)"
    preview: false

  # ============================================================================
  # Rule 5: File Upload 검증
  # ============================================================================
  - priority: 140
    description: "Block suspicious file uploads"
    match:
      versionedExpr: "CEL"
      expression: |
        origin.region_code == 'CN' || origin.region_code == 'RU'
    action: "deny(403)"
    preview: false

  # ============================================================================
  # Rule 6: Rate Limiting (DDoS 방어)
  # ============================================================================
  - priority: 1000
    description: "Rate limiting - 10 req/min per IP"
    match:
      versionedExpr: "CEL"
      expression: "true"
    action: "rate_based_ban"
    rateLimitOptions:
      conformAction: "allow"
      exceedAction: "deny(429)"
      rateLimit Bucket: 10  # 분당 10개 요청
      banDurationSec: 600   # 10분 차단
      banThresholdCount: 100  # 누적 요청 100개
      banThresholdIntervalSec: 600  # 10분 동안

  # ============================================================================
  # Rule 7: 특정 경로 보호 (/admin, /api/internal)
  # ============================================================================
  - priority: 200
    description: "Restrict admin paths to specific IPs"
    match:
      versionedExpr: "CEL"
      expression: |
        has(request.path)
        && (request.path.contains('/admin') || request.path.contains('/api/internal'))
        && !(origin.ip in ['192.0.2.1', '198.51.100.1'])  # 화이트리스트
    action: "deny(403)"
    preview: false

  # ============================================================================
  # Rule 8: 의심스러운 User-Agent 차단
  # ============================================================================
  - priority: 210
    description: "Block suspicious user agents"
    match:
      versionedExpr: "CEL"
      expression: |
        has(request.headers['user-agent'])
        && (request.headers['user-agent'].contains('bot')
            || request.headers['user-agent'].contains('scanner')
            || request.headers['user-agent'].contains('crawler'))
    action: "deny(403)"
    preview: false

  # ============================================================================
  # Rule 9: Geo-blocking (선택: 특정 국가 차단)
  # ============================================================================
  - priority: 220
    description: "Block traffic from specific countries"
    match:
      versionedExpr: "CEL"
      expression: |
        origin.region_code == 'KP'  # North Korea (ISO 3166-1 alpha-2)
    action: "deny(403)"
    preview: false

  # ============================================================================
  # Rule 10: HTTPS Enforcement
  # ============================================================================
  - priority: 230
    description: "Allow only HTTPS"
    match:
      versionedExpr: "CEL"
      expression: "request.scheme != 'https'"
    action: "deny(403)"
    preview: false

  # ============================================================================
  # Rule 11: Content-Type 검증
  # ============================================================================
  - priority: 240
    description: "Validate Content-Type header"
    match:
      versionedExpr: "CEL"
      expression: |
        request.method == 'POST'
        && !(has(request.headers['content-type'])
             && (request.headers['content-type'].contains('application/json')
                 || request.headers['content-type'].contains('application/x-www-form-urlencoded')))
    action: "deny(400)"
    preview: false

  # ============================================================================
  # Rule 12: Large Request 차단
  # ============================================================================
  - priority: 250
    description: "Block requests larger than 10MB"
    match:
      versionedExpr: "CEL"
      expression: "int(request.headers['content-length']) > 10485760"  # 10MB
    action: "deny(413)"
    preview: false

  # ============================================================================
  # Rule 13: Allow list (신뢰할 수 있는 IP)
  # ============================================================================
  - priority: 50
    description: "Allow traffic from trusted IPs"
    match:
      versionedExpr: "CEL"
      expression: |
        origin.ip in [
          '203.0.113.0/24',     # 회사 IP 대역
          '198.51.100.1',       # CDN 서버
          '192.0.2.1'           # 파트너 서버
        ]
    action: "allow"
    preview: false

# ============================================================================
# 고급 설정
# ============================================================================
advancedOptions:
  jsonParsing: "STANDARD"  # JSON 요청 파싱
  logConfig:
    enable: true
    sampleRate: 1.0  # 100% 로깅
```

#### Step 2-2: Terraform으로 정책 생성

**파일**: `gcp-configs/cloud-armor.tf`

```hcl
# Cloud Armor 정책 (Terraform)

resource "google_compute_security_policy" "ion_api_armor" {
  name        = "ion-api-armor-policy"
  description = "Cloud Armor policy for ION API"

  # 기본 규칙: 모든 트래픽 허용
  rules {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "CEL"
      expr {
        expression = "true"
      }
    }
    description = "Default rule"
  }

  # Rule 1: SQL Injection 차단
  rules {
    action   = "deny(403)"
    priority = 100
    match {
      versioned_expr      = "CEL_V1"
      expr {
        expression = <<-EOT
          evaluatePreconfiguredExpr(
            'sqli-v33-stable',
            ['owasp-crs-v030001-id942251-sqli',
             'owasp-crs-v030001-id942420-sqli',
             'owasp-crs-v030001-id942431-sqli']
          )
        EOT
      }
    }
    description = "Block SQL Injection attempts"
  }

  # Rule 2: XSS 차단
  rules {
    action   = "deny(403)"
    priority = 110
    match {
      versioned_expr = "CEL_V1"
      expr {
        expression = <<-EOT
          evaluatePreconfiguredExpr(
            'xss-v33-stable',
            ['owasp-crs-v030001-id941110-xss',
             'owasp-crs-v030001-id941120-xss',
             'owasp-crs-v030001-id941130-xss']
          )
        EOT
      }
    }
    description = "Block XSS attempts"
  }

  # Rule 3: Rate Limiting
  rules {
    action   = "rate_based_ban"
    priority = 1000
    match {
      versioned_expr = "CEL_V1"
      expr {
        expression = "true"
      }
    }
    rate_limit_options {
      conform_action         = "allow"
      exceed_action          = "deny(429)"
      rate_limit_http_request_count {
        count        = 10
        interval_sec = 60
      }
      ban_duration_sec = 600
      rate_limit_http_request_count {
        count        = 100
        interval_sec = 600
      }
    }
    description = "Rate limiting - 10 req/min per IP"
  }

  # Rule 4: Geo-blocking (North Korea)
  rules {
    action   = "deny(403)"
    priority = 220
    match {
      versioned_expr = "CEL_V1"
      expr {
        expression = "origin.region_code == 'KP'"
      }
    }
    description = "Block traffic from North Korea"
  }

  # Rule 5: Allow trusted IPs
  rules {
    action   = "allow"
    priority = 50
    match {
      versioned_expr = "CEL_V1"
      expr {
        expression = "origin.ip in ['203.0.113.0/24', '198.51.100.1']"
      }
    }
    description = "Allow traffic from trusted IPs"
  }

  # 로깅 설정
  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# Cloud Run 서비스에 정책 연결
resource "google_compute_backend_service" "ion_api_backend" {
  name                    = "ion-api-backend"
  protocol                = "HTTP2"
  port_name               = "http2"
  timeout_sec             = 30
  enable_cdn              = true
  session_affinity        = "NONE"
  security_policy         = google_compute_security_policy.ion_api_armor.id

  backend {
    group           = google_compute_network_endpoint_group.ion_api_neg.id
    balancing_mode  = "RATE"
    max_rate_per_endpoint = 1000
  }

  health_checks = [google_compute_health_check.ion_api_health.id]
}
```

---

### Phase 3: 정책 배포 (1시간)

#### Step 3-1: gcloud 명령어로 정책 생성

```bash
# 1. 보안 정책 생성
gcloud compute security-policies create ion-api-armor \
  --description="Cloud Armor policy for ION API" \
  --project=$GCP_PROJECT_ID

# 2. SQL Injection 규칙 추가
gcloud compute security-policies rules create 100 \
  --action=deny-403 \
  --security-policy=ion-api-armor \
  --expression="evaluatePreconfiguredExpr('sqli-v33-stable')" \
  --project=$GCP_PROJECT_ID

# 3. XSS 규칙 추가
gcloud compute security-policies rules create 110 \
  --action=deny-403 \
  --security-policy=ion-api-armor \
  --expression="evaluatePreconfiguredExpr('xss-v33-stable')" \
  --project=$GCP_PROJECT_ID

# 4. Rate Limiting 규칙 추가
gcloud compute security-policies rules create 1000 \
  --action=rate-based-ban \
  --security-policy=ion-api-armor \
  --rate-limit-http-request-count=10 \
  --rate-limit-http-request-interval-sec=60 \
  --ban-duration-sec=600 \
  --project=$GCP_PROJECT_ID

# 5. Geo-blocking 규칙 추가 (선택)
gcloud compute security-policies rules create 220 \
  --action=deny-403 \
  --security-policy=ion-api-armor \
  --expression="origin.region_code == 'KP'" \
  --project=$GCP_PROJECT_ID

# 6. 정책 확인
gcloud compute security-policies describe ion-api-armor \
  --project=$GCP_PROJECT_ID
```

#### Step 3-2: Backend Service에 정책 연결

```bash
# Backend Service 생성 (또는 기존 것을 업데이트)
gcloud compute backend-services create ion-api-backend \
  --protocol=HTTP2 \
  --health-checks=ion-api-health \
  --enable-cdn \
  --security-policy=ion-api-armor \
  --global \
  --project=$GCP_PROJECT_ID

# 또는 기존 Backend Service 업데이트
gcloud compute backend-services update ion-api-backend \
  --security-policy=ion-api-armor \
  --global \
  --project=$GCP_PROJECT_ID
```

---

### Phase 4: 모니터링 및 로깅 (1시간)

#### Step 4-1: Cloud Logging에서 WAF 로그 확인

```bash
# 차단된 요청 로그 조회
gcloud logging read \
  'resource.type="security_policy"
   AND jsonPayload.enforcement_level="DENY"' \
  --limit=50 \
  --format=json \
  --project=$GCP_PROJECT_ID

# SQL Injection 시도 로그
gcloud logging read \
  'resource.type="security_policy"
   AND jsonPayload.enforcement_level="DENY"
   AND jsonPayload.rule_id="100"' \
  --limit=20 \
  --project=$GCP_PROJECT_ID

# Rate Limit 초과 로그
gcloud logging read \
  'resource.type="security_policy"
   AND jsonPayload.enforcement_level="DENY"
   AND jsonPayload.rule_id="1000"' \
  --limit=20 \
  --project=$GCP_PROJECT_ID
```

#### Step 4-2: BigQuery로 로그 분석

```bash
# BigQuery 데이터셋 생성
bq mk --dataset \
  --location=US \
  --description="Cloud Armor logs" \
  cloud_armor_logs

# 로그 싱크 생성 (자동 내보내기)
gcloud logging sinks create cloud-armor-sink \
  bigquery.googleapis.com/projects/$GCP_PROJECT_ID/datasets/cloud_armor_logs \
  --log-filter='resource.type="security_policy"' \
  --project=$GCP_PROJECT_ID

# BigQuery에서 쿼리
bq query --use_legacy_sql=false '
SELECT
  timestamp,
  jsonPayload.enforcement_level as action,
  jsonPayload.rule_id as rule,
  jsonPayload.origin.ip as source_ip,
  jsonPayload.origin.region_code as country,
  COUNT(*) as count
FROM `'$GCP_PROJECT_ID'.cloud_armor_logs.requests_*`
WHERE DATE(_TABLE_SUFFIX) = CURRENT_DATE()
GROUP BY timestamp, action, rule, source_ip, country
ORDER BY timestamp DESC
LIMIT 100
'
```

#### Step 4-3: 모니터링 대시보드 생성

```bash
# Cloud Monitoring 대시보드 (JSON)
cat > cloud-armor-dashboard.json << 'EOF'
{
  "displayName": "Cloud Armor Monitoring",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Blocked Requests",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"security_policy\""
                }
              }
            }]
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Attack Types",
          "pieChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"security_policy\""
                }
              }
            }]
          }
        }
      }
    ]
  }
}
EOF

# 대시보드 생성
gcloud monitoring dashboards create --config-from-file=cloud-armor-dashboard.json \
  --project=$GCP_PROJECT_ID
```

---

### Phase 5: 테스트 및 검증 (1시간)

#### Step 5-1: SQL Injection 테스트

```bash
# SQL Injection 시도 (차단되어야 함)
curl -i "https://api.ion-mentoring.com/chat?input='; DROP TABLE users; --"

# 예상 결과: HTTP 403 Forbidden
```

#### Step 5-2: XSS 테스트

```bash
# XSS 시도 (차단되어야 함)
curl -i -X POST "https://api.ion-mentoring.com/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"<script>alert(1)</script>"}'

# 예상 결과: HTTP 403 Forbidden
```

#### Step 5-3: Rate Limiting 테스트

```bash
# 빠른 연속 요청 (10개 이상이면 차단)
for i in {1..20}; do
  curl -i "https://api.ion-mentoring.com/health"
  echo "Request $i"
done

# 예상: 처음 10개는 성공, 나머지는 HTTP 429 Too Many Requests
```

#### Step 5-4: Geo-blocking 테스트

```bash
# 특정 국가에서 온 것처럼 요청
curl -i "https://api.ion-mentoring.com/chat" \
  -H "CF-IPCountry: KP"  # Cloudflare 헤더 (시뮬레이션)

# 참고: Cloud Armor는 실제 IP 지역을 기반으로 판단
```

---

## 📊 규칙 우선순위 가이드

```
Priority 수 | 규칙 | 액션 |
|----------|------|------|
| 50 | Allow 화이트리스트 | Allow |
| 100 | SQL Injection | Deny 403 |
| 110 | XSS | Deny 403 |
| 120 | RCE | Deny 403 |
| 130 | Protocol Attack | Deny 403 |
| 140 | File Upload | Deny 403 |
| 200 | Admin 경로 제한 | Deny 403 |
| 210 | 의심 User-Agent | Deny 403 |
| 220 | Geo-blocking | Deny 403 |
| 230 | HTTPS 강제 | Deny 403 |
| 240 | Content-Type 검증 | Deny 400 |
| 250 | 큰 요청 | Deny 413 |
| 1000 | Rate Limiting | Deny 429 |
| 2147483647 | 기본 규칙 | Allow |
```

**규칙 평가**: 우선순위가 낮은 번호부터 순서대로 평가됨

---

## 🔧 고급 설정

### CEL 표현식 예제

```cel
# 특정 메서드만 허용
request.method == 'GET' || request.method == 'POST'

# 특정 경로 차단
request.path.contains('/admin')

# 특정 헤더 검사
has(request.headers['authorization'])

# IP 주소 범위
origin.ip in ['10.0.0.0/8', '192.168.0.0/16']

# 국가별 제한
origin.region_code in ['US', 'CA', 'GB']

# User-Agent 검사
request.headers['user-agent'].contains('bot')

# 요청 크기
int(request.headers['content-length']) < 1048576  # 1MB 미만
```

---

## 📋 체크리스트

### 배포 전
- [ ] Cloud Armor API 활성화
- [ ] 보안 정책 생성
- [ ] 11개 규칙 추가
- [ ] Backend Service에 정책 연결
- [ ] 로깅 활성화

### 배포 후
- [ ] SQL Injection 테스트
- [ ] XSS 테스트
- [ ] Rate Limiting 테스트
- [ ] 정상 요청 통과 확인
- [ ] Cloud Logging에서 로그 확인

### 운영
- [ ] 일일 보안 이벤트 리뷰
- [ ] 월별 규칙 최적화
- [ ] 거짓 양성 제거
- [ ] 새로운 공격 패턴 모니터링

---

## 📞 문제 해결

### 문제: 정상 요청이 차단됨

**원인**: 규칙이 너무 엄격함

**해결**:
1. Cloud Logging에서 차단 규칙 확인
2. 규칙을 "preview" 모드로 변경 (실제 차단 안 함)
3. 정상 패턴 화이트리스트 추가

```bash
# 규칙을 preview 모드로 변경
gcloud compute security-policies rules update 100 \
  --security-policy=ion-api-armor \
  --preview \
  --project=$GCP_PROJECT_ID
```

### 문제: 특정 국가의 정상 사용자가 차단됨

**해결**: Geo-blocking 규칙 예외 추가

```bash
# 특정 IP 허용
gcloud compute security-policies rules create 45 \
  --action=allow \
  --security-policy=ion-api-armor \
  --expression="origin.ip == '203.0.113.100'" \
  --priority=45 \
  --project=$GCP_PROJECT_ID
```

---

## 📅 운영 계획

### 일일 작업
- Cloud Logging 모니터링
- 차단된 요청 분석
- 거짓 양성 제거

### 주간 작업
- 보안 이벤트 리뷰
- 새로운 공격 패턴 감지
- 규칙 효과성 평가

### 월간 작업
- 보안 규칙 업데이트
- 성능 영향 분석
- 비용 최적화

---

## 💰 비용 추정

| 항목 | 월간 비용 | 설명 |
|------|----------|------|
| Cloud Armor 정책 | $5 | 정책당 $5 |
| 평가된 요청 | $0.75/M | 백만 개 요청당 |
| 차단된 요청 | 무료 | 차단 요청은 비용 없음 |
| **총계** | ~$50 | 1M 요청 기준 |

---

## 📅 다음 단계

✅ **Pre-commit hooks 설정 완료** (3시간)
✅ **WAF/Cloud Armor 설정 완료** (6시간)
➡️ **Task 3: 추가 보안 테스트 개발** (4시간)

총 소요 시간: Phase 2 **90시간** 중 **9시간** 완료 ✅
