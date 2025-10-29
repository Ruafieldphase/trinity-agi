# GCP Load Balancer 설계 문서 🏗️
## Infrastructure-level Traffic Routing

**작성일**: 2025-10-22  
**작성자**: 깃코 (AI Agent)  
**목적**: Application-level → Infrastructure-level 트래픽 라우팅 전환

---

## 📋 현재 상황 분석

### 현재 아키텍처 (Application-level)

```
┌──────────────┐
│   Client     │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│  Cloud Run Service   │
│  (ion-api or         │
│   ion-api-canary)    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Canary Router       │
│  (Application Code)  │
│  - Hash-based        │
│  - user_id routing   │
└──────┬───────────────┘
       │
   ┌───┴────┐
   ▼        ▼
Legacy  Canary
```

### 문제점 ❌

1. **트래픽 라우팅이 애플리케이션 코드에 의존**
   - 코드 변경 시 배포 필요
   - 트래픽 비율 동적 조정 어려움
   - 인프라 독립성 부족

2. **모니터링 한계**
   - Infrastructure-level 메트릭 부족
   - GCP Load Balancer 기능 미활용
   - 트래픽 분산 정확도 제한

3. **배포 복잡도**
   - 각 서비스가 독립적으로 배포
   - 트래픽 전환 시 코드 수정 필요
   - 롤백 절차 복잡

---

## 🎯 목표 아키텍처 (Infrastructure-level)

### 새로운 아키텍처

```
┌──────────────┐
│   Client     │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────┐
│  GCP Load Balancer (Layer 7)    │
│  - URL-based routing            │
│  - Traffic splitting (%)        │
│  - Health checks                │
│  - SSL termination              │
└─────────┬───────────────────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌─────────┐ ┌──────────┐
│ Backend │ │ Backend  │
│ Service │ │ Service  │
│ (Legacy)│ │ (Canary) │
│  95%    │ │   5%     │
└────┬────┘ └────┬─────┘
     │           │
     ▼           ▼
┌─────────┐ ┌──────────┐
│Cloud Run│ │Cloud Run │
│ion-api  │ │ion-api-  │
│         │ │canary    │
└─────────┘ └──────────┘
```

### 장점 ✅

1. **Infrastructure-level 제어**
   - 트래픽 비율 GCP Console에서 즉시 조정
   - 코드 배포 없이 라우팅 변경
   - 인프라와 애플리케이션 분리

2. **향상된 모니터링**
   - GCP Load Balancer 메트릭 활용
   - 실시간 트래픽 분산 가시성
   - Cloud Monitoring 통합

3. **간소화된 배포**
   - Backend Service 단위 관리
   - Blue-Green 배포 지원
   - 빠른 롤백 (트래픽 전환만)

4. **프로덕션 준비**
   - SSL/TLS 종료
   - Global load balancing
   - CDN 통합 가능

---

## 🏗️ GCP Load Balancer 구성 요소

### 1. Global External HTTP(S) Load Balancer

**선택 이유**:
- Layer 7 (HTTP/HTTPS) 지원
- Content-based routing
- Global 가용성
- Cloud Run과 완벽 통합

**구성 요소**:

```
Forwarding Rule
    ↓
Target HTTP(S) Proxy
    ↓
URL Map
    ↓
Backend Service (Legacy) ← Cloud Run (ion-api)
Backend Service (Canary) ← Cloud Run (ion-api-canary)
```

---

### 2. Forwarding Rule (프론트엔드)

**역할**: 외부 IP 및 포트로 들어오는 트래픽 수신

```yaml
name: ion-api-forwarding-rule
ip_protocol: TCP
port_range: 80, 443
target: ion-api-target-proxy
ip_address: [자동 할당 또는 예약 IP]
```

**설정**:
- **Protocol**: HTTP/HTTPS
- **Port**: 80 (HTTP), 443 (HTTPS)
- **IP**: Global static IP (예약 권장)

---

### 3. Target Proxy

**역할**: SSL/TLS 종료 및 URL Map 연결

#### HTTP Proxy

```yaml
name: ion-api-target-http-proxy
url_map: ion-api-url-map
```

#### HTTPS Proxy (프로덕션 권장)

```yaml
name: ion-api-target-https-proxy
url_map: ion-api-url-map
ssl_certificates:
  - ion-api-ssl-cert
```

**SSL 인증서**:
- **Google-managed SSL**: 자동 갱신, 권장
- **Self-managed SSL**: 커스텀 인증서

---

### 4. URL Map (라우팅 규칙)

**역할**: 요청 경로에 따라 Backend Service 선택

```yaml
name: ion-api-url-map
default_service: ion-api-backend-service-legacy

host_rules:
  - hosts: ['ion-api.naeda-genesis.com']
    path_matcher: ion-api-path-matcher

path_matchers:
  - name: ion-api-path-matcher
    default_service: ion-api-backend-service-legacy
    
    # Path-based routing (선택 사항)
    path_rules:
      - paths: ['/api/v2/*']
        service: ion-api-backend-service-canary
      
      - paths: ['/health', '/metrics']
        service: ion-api-backend-service-legacy
```

**라우팅 전략**:

#### 옵션 A: Path-based (권장)

```
/api/v2/*  → Canary Backend
/*         → Legacy Backend
```

#### 옵션 B: Header-based

```
X-Canary: true → Canary Backend
(default)      → Legacy Backend
```

#### 옵션 C: Weight-based (Canary 배포)

```
95% → Legacy Backend
5%  → Canary Backend
```

---

### 5. Backend Services

**역할**: Cloud Run 서비스 그룹 관리

#### Legacy Backend Service

```yaml
name: ion-api-backend-service-legacy
protocol: HTTP
port_name: http
timeout: 30s
enable_cdn: false

backends:
  - group: projects/naeda-genesis/regions/us-central1/networkEndpointGroups/ion-api-neg-legacy
    balancing_mode: UTILIZATION
    capacity_scaler: 1.0
    max_utilization: 0.8

health_checks:
  - ion-api-health-check-legacy

log_config:
  enable: true
  sample_rate: 1.0
```

#### Canary Backend Service

```yaml
name: ion-api-backend-service-canary
protocol: HTTP
port_name: http
timeout: 30s
enable_cdn: false

backends:
  - group: projects/naeda-genesis/regions/us-central1/networkEndpointGroups/ion-api-neg-canary
    balancing_mode: UTILIZATION
    capacity_scaler: 1.0
    max_utilization: 0.8

health_checks:
  - ion-api-health-check-canary

log_config:
  enable: true
  sample_rate: 1.0
```

---

### 6. Network Endpoint Groups (NEG)

**역할**: Cloud Run 서비스를 Backend Service에 연결

#### Legacy NEG

```yaml
name: ion-api-neg-legacy
network_endpoint_type: SERVERLESS
region: us-central1

cloud_run:
  service: ion-api
  url_mask: <default>
```

#### Canary NEG

```yaml
name: ion-api-neg-canary
network_endpoint_type: SERVERLESS
region: us-central1

cloud_run:
  service: ion-api-canary
  url_mask: <default>
```

---

### 7. Health Checks

**역할**: Backend 서비스 상태 모니터링

#### Legacy Health Check

```yaml
name: ion-api-health-check-legacy
type: HTTP
request_path: /health
port: 80
check_interval: 10s
timeout: 5s
healthy_threshold: 2
unhealthy_threshold: 3

log_config:
  enable: true
```

#### Canary Health Check

```yaml
name: ion-api-health-check-canary
type: HTTP
request_path: /health
port: 80
check_interval: 10s
timeout: 5s
healthy_threshold: 2
unhealthy_threshold: 3

log_config:
  enable: true
```

---

## 🚀 구현 단계

### Phase 1: 준비 (1-2시간)

#### Step 1: Cloud Run 서비스 확인

```bash
# 현재 서비스 목록
gcloud run services list --project naeda-genesis --region us-central1

# 예상 결과:
# - ion-api (Legacy)
# - ion-api-canary (Canary)
```

#### Step 2: 정적 IP 예약

```bash
# Global static IP 예약
gcloud compute addresses create ion-api-lb-ip \
  --ip-version=IPV4 \
  --global \
  --project naeda-genesis

# IP 확인
gcloud compute addresses describe ion-api-lb-ip \
  --global \
  --project naeda-genesis
```

#### Step 3: SSL 인증서 준비 (HTTPS 사용 시)

```bash
# Google-managed SSL 인증서 생성
gcloud compute ssl-certificates create ion-api-ssl-cert \
  --domains=ion-api.naeda-genesis.com \
  --global \
  --project naeda-genesis

# 인증서 상태 확인
gcloud compute ssl-certificates describe ion-api-ssl-cert \
  --global \
  --project naeda-genesis
```

---

### Phase 2: Backend 구성 (30분-1시간)

#### Step 4: Network Endpoint Groups 생성

```bash
# Legacy NEG 생성
gcloud compute network-endpoint-groups create ion-api-neg-legacy \
  --region=us-central1 \
  --network-endpoint-type=SERVERLESS \
  --cloud-run-service=ion-api \
  --project naeda-genesis

# Canary NEG 생성
gcloud compute network-endpoint-groups create ion-api-neg-canary \
  --region=us-central1 \
  --network-endpoint-type=SERVERLESS \
  --cloud-run-service=ion-api-canary \
  --project naeda-genesis
```

#### Step 5: Health Checks 생성

```bash
# Legacy Health Check
gcloud compute health-checks create http ion-api-health-check-legacy \
  --request-path=/health \
  --port=80 \
  --check-interval=10s \
  --timeout=5s \
  --unhealthy-threshold=3 \
  --healthy-threshold=2 \
  --project naeda-genesis

# Canary Health Check
gcloud compute health-checks create http ion-api-health-check-canary \
  --request-path=/health \
  --port=80 \
  --check-interval=10s \
  --timeout=5s \
  --unhealthy-threshold=3 \
  --healthy-threshold=2 \
  --project naeda-genesis
```

#### Step 6: Backend Services 생성

```bash
# Legacy Backend Service
gcloud compute backend-services create ion-api-backend-service-legacy \
  --global \
  --protocol=HTTP \
  --port-name=http \
  --timeout=30s \
  --health-checks=ion-api-health-check-legacy \
  --enable-logging \
  --logging-sample-rate=1.0 \
  --project naeda-genesis

# Canary Backend Service
gcloud compute backend-services create ion-api-backend-service-canary \
  --global \
  --protocol=HTTP \
  --port-name=http \
  --timeout=30s \
  --health-checks=ion-api-health-check-canary \
  --enable-logging \
  --logging-sample-rate=1.0 \
  --project naeda-genesis
```

#### Step 7: Backend에 NEG 추가

```bash
# Legacy Backend에 NEG 추가
gcloud compute backend-services add-backend ion-api-backend-service-legacy \
  --global \
  --network-endpoint-group=ion-api-neg-legacy \
  --network-endpoint-group-region=us-central1 \
  --balancing-mode=UTILIZATION \
  --max-utilization=0.8 \
  --project naeda-genesis

# Canary Backend에 NEG 추가
gcloud compute backend-services add-backend ion-api-backend-service-canary \
  --global \
  --network-endpoint-group=ion-api-neg-canary \
  --network-endpoint-group-region=us-central1 \
  --balancing-mode=UTILIZATION \
  --max-utilization=0.8 \
  --project naeda-genesis
```

---

### Phase 3: 프론트엔드 구성 (30분)

#### Step 8: URL Map 생성

```bash
# URL Map 생성 (Default: Legacy)
gcloud compute url-maps create ion-api-url-map \
  --default-service=ion-api-backend-service-legacy \
  --global \
  --project naeda-genesis
```

#### Step 9: Traffic Splitting 설정 (Canary 배포용)

```bash
# URL Map에 weighted traffic 추가
gcloud compute url-maps edit ion-api-url-map \
  --global \
  --project naeda-genesis

# YAML 편집:
# defaultRouteAction:
#   weightedBackendServices:
#     - backendService: projects/naeda-genesis/global/backendServices/ion-api-backend-service-legacy
#       weight: 95
#     - backendService: projects/naeda-genesis/global/backendServices/ion-api-backend-service-canary
#       weight: 5
```

#### Step 10: Target Proxy 생성

```bash
# HTTP Target Proxy (개발/테스트)
gcloud compute target-http-proxies create ion-api-target-http-proxy \
  --url-map=ion-api-url-map \
  --global \
  --project naeda-genesis

# HTTPS Target Proxy (프로덕션)
gcloud compute target-https-proxies create ion-api-target-https-proxy \
  --url-map=ion-api-url-map \
  --ssl-certificates=ion-api-ssl-cert \
  --global \
  --project naeda-genesis
```

#### Step 11: Forwarding Rules 생성

```bash
# HTTP Forwarding Rule
gcloud compute forwarding-rules create ion-api-forwarding-rule-http \
  --address=ion-api-lb-ip \
  --global \
  --target-http-proxy=ion-api-target-http-proxy \
  --ports=80 \
  --project naeda-genesis

# HTTPS Forwarding Rule
gcloud compute forwarding-rules create ion-api-forwarding-rule-https \
  --address=ion-api-lb-ip \
  --global \
  --target-https-proxy=ion-api-target-https-proxy \
  --ports=443 \
  --project naeda-genesis
```

---

### Phase 4: 검증 및 테스트 (30분)

#### Step 12: Load Balancer 상태 확인

```bash
# Forwarding Rules 확인
gcloud compute forwarding-rules list --global --project naeda-genesis

# Backend Services 상태
gcloud compute backend-services get-health ion-api-backend-service-legacy \
  --global \
  --project naeda-genesis

gcloud compute backend-services get-health ion-api-backend-service-canary \
  --global \
  --project naeda-genesis
```

#### Step 13: DNS 설정 (선택 사항)

```bash
# Cloud DNS에 A 레코드 추가
gcloud dns record-sets create ion-api.naeda-genesis.com. \
  --type=A \
  --ttl=300 \
  --rrdatas=[LOAD_BALANCER_IP] \
  --zone=naeda-genesis-zone \
  --project naeda-genesis
```

#### Step 14: 기능 테스트

```bash
# HTTP 테스트
curl -H "Host: ion-api.naeda-genesis.com" http://[LOAD_BALANCER_IP]/health

# HTTPS 테스트
curl https://ion-api.naeda-genesis.com/health

# 트래픽 분산 테스트 (100 requests)
for i in {1..100}; do
  curl -s https://ion-api.naeda-genesis.com/chat \
    -H "Content-Type: application/json" \
    -d '{"message":"test","user_id":"test-'$i'"}' \
    | jq -r '.backend'
done | sort | uniq -c
```

---

## 📊 트래픽 분산 전략

### Stage 1: 5% Canary (현재)

```yaml
weightedBackendServices:
  - backendService: ion-api-backend-service-legacy
    weight: 95
  - backendService: ion-api-backend-service-canary
    weight: 5
```

### Stage 2: 10% Canary

```yaml
weightedBackendServices:
  - backendService: ion-api-backend-service-legacy
    weight: 90
  - backendService: ion-api-backend-service-canary
    weight: 10
```

### Stage 3-5: 점진적 증가

```
Stage 3: Legacy 75% / Canary 25%
Stage 4: Legacy 50% / Canary 50%
Stage 5: Legacy 0% / Canary 100%
```

### 트래픽 조정 명령어

```bash
# URL Map 업데이트 (트래픽 비율 변경)
gcloud compute url-maps edit ion-api-url-map \
  --global \
  --project naeda-genesis

# 즉시 적용 (코드 배포 불필요!)
```

---

## 🔍 모니터링 & 관찰성

### Cloud Monitoring 메트릭

#### Load Balancer 메트릭

```
- loadbalancing.googleapis.com/https/request_count
- loadbalancing.googleapis.com/https/request_bytes_count
- loadbalancing.googleapis.com/https/response_bytes_count
- loadbalancing.googleapis.com/https/backend_latencies
- loadbalancing.googleapis.com/https/backend_request_count
- loadbalancing.googleapis.com/https/total_latencies
```

#### Backend Service 메트릭

```
- compute.googleapis.com/instance/network/received_bytes_count
- compute.googleapis.com/instance/network/sent_bytes_count
- run.googleapis.com/request_count
- run.googleapis.com/request_latencies
```

### Cloud Logging 쿼리

#### Load Balancer 로그

```
resource.type="http_load_balancer"
resource.labels.project_id="naeda-genesis"
resource.labels.url_map_name="ion-api-url-map"
```

#### Backend Service 로그

```
resource.type="cloud_run_revision"
resource.labels.service_name="ion-api"
OR
resource.labels.service_name="ion-api-canary"
```

---

## 🚨 롤백 계획

### 긴급 롤백 (트래픽 100% Legacy)

```bash
# URL Map 즉시 업데이트
gcloud compute url-maps edit ion-api-url-map \
  --global \
  --project naeda-genesis

# weightedBackendServices:
#   - backendService: ion-api-backend-service-legacy
#     weight: 100
#   - backendService: ion-api-backend-service-canary
#     weight: 0
```

**예상 시간**: 30초 (코드 배포 불필요!)

### 완전 롤백 (Load Balancer 제거)

```bash
# Forwarding Rules 삭제
gcloud compute forwarding-rules delete ion-api-forwarding-rule-http --global
gcloud compute forwarding-rules delete ion-api-forwarding-rule-https --global

# Target Proxies 삭제
gcloud compute target-http-proxies delete ion-api-target-http-proxy --global
gcloud compute target-https-proxies delete ion-api-target-https-proxy --global

# URL Map 삭제
gcloud compute url-maps delete ion-api-url-map --global

# Backend Services 삭제
gcloud compute backend-services delete ion-api-backend-service-legacy --global
gcloud compute backend-services delete ion-api-backend-service-canary --global

# NEGs 삭제
gcloud compute network-endpoint-groups delete ion-api-neg-legacy --region us-central1
gcloud compute network-endpoint-groups delete ion-api-neg-canary --region us-central1

# Health Checks 삭제
gcloud compute health-checks delete ion-api-health-check-legacy
gcloud compute health-checks delete ion-api-health-check-canary
```

---

## 💰 비용 분석

### GCP Load Balancer 비용 (예상)

#### Forwarding Rules

```
$18/월 (규칙당)
  × 2 (HTTP + HTTPS) = $36/월
```

#### Load Balancing 사용량

```
$0.008/GB (ingress)
$0.012/GB (egress)

예상 트래픽: 100GB/월
= $0.8 (ingress) + $1.2 (egress) = $2/월
```

#### Backend Services

```
무료 (Cloud Run 비용에 포함)
```

#### 총 예상 비용

```
$36 (Forwarding Rules)
+ $2 (Traffic)
= $38/월
```

**비용 대비 효과**:
- ✅ Infrastructure-level 제어
- ✅ 향상된 모니터링
- ✅ 간소화된 배포
- ✅ 프로덕션 준비 완료

---

## 📝 체크리스트

### 구현 전 준비
- [ ] GCP 프로젝트 권한 확인
- [ ] Cloud Run 서비스 상태 확인
- [ ] DNS 레코드 준비 (선택)
- [ ] SSL 인증서 준비 (HTTPS 사용 시)
- [ ] 정적 IP 예약

### Load Balancer 구성
- [ ] Network Endpoint Groups 생성
- [ ] Health Checks 생성
- [ ] Backend Services 생성
- [ ] URL Map 생성
- [ ] Target Proxies 생성
- [ ] Forwarding Rules 생성

### 검증 및 테스트
- [ ] Health Check 통과 확인
- [ ] HTTP/HTTPS 접속 테스트
- [ ] 트래픽 분산 검증
- [ ] 응답 시간 측정
- [ ] 오류율 확인

### 모니터링 설정
- [ ] Cloud Monitoring 대시보드
- [ ] 알림 정책 설정
- [ ] 로그 수집 확인

---

## 🎯 다음 단계

### 즉시 실행 가능
1. ✅ 설계 문서 완료 (현재)
2. ⏳ 구현 스크립트 작성
3. ⏳ 테스트 환경 구축
4. ⏳ 프로덕션 배포

### Week 3 Day 2-3 계획
- Load Balancer 구현
- Stage 1 결과 분석 (24시간 후)
- Stage 2 배포 (10% 트래픽)

---

## ✅ 서명

**작성자**: 깃코 (AI Agent)  
**작성일**: 2025-10-22  
**상태**: ✅ **설계 완료**  
**다음**: 구현 스크립트 작성

---

**문서 종료**  
GCP Load Balancer 설계 → 구현 준비 완료! 🚀
