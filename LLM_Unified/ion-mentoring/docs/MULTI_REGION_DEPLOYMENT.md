# Multi-Region 배포 가이드

## 📋 개요

**목표**: 글로벌 가용성 및 낮은 지연 시간
**구성**: Primary (us-central1) + Secondary (europe-west1, asia-northeast1)
**이점**: 가용성 99.99%, 지역별 최적화된 응답

---

## 🌍 멀티 지역 아키텍처

```
┌─────────────────────────────────────────┐
│ Global Load Balancer                    │
│ (Traffic routing based on geography)    │
└──────────────┬──────────────────────────┘
   ├─ 30% US → us-central1 (10ms)
   ├─ 50% EU → europe-west1 (50ms)
   └─ 20% ASIA → asia-northeast1 (80ms)
        ↓
┌──────────────────────────────────────────┐
│ Cloud SQL (Multi-region replication)    │
│ ├─ Primary: us-central1 (write)         │
│ └─ Replicas: eu, asia (read)            │
├─ Redis Cluster (distributed cache)      │
└─ BigQuery Datasets (multi-region)       │
```

---

## 🛠️ 배포 단계 (40시간)

### Phase 1: Infrastructure (2주)

```bash
# 1. eu-west1 리전에 리소스 생성
gcloud compute regions list
gcloud run deploy ion-api-eu --region europe-west1
gcloud sql instances create ion-db-eu --region europe-west1
gcloud redis instances create ion-redis-eu --region europe-west1

# 2. asia-northeast1 리전에 리소스 생성
gcloud run deploy ion-api-asia --region asia-northeast1
gcloud sql instances create ion-db-asia --region asia-northeast1
gcloud redis instances create ion-redis-asia --region asia-northeast1

# 3. Global Load Balancer 설정
gcloud compute backend-services create ion-global-backend --global
gcloud compute url-maps create ion-global-lb --default-service=ion-global-backend
gcloud compute target-https-proxies create ion-global-proxy \
  --url-map=ion-global-lb \
  --ssl-certificates=ion-cert
```

### Phase 2: Data Replication (1주)

```bash
# Cloud SQL 다중 지역 복제
gcloud sql instances create ion-db-eu --replica-of=ion-db

# Cloud Storage 다중 지역 복제
gsutil mb -b on -l US -c STANDARD gs://ion-backup-us/
gsutil mb -b on -l EU -c STANDARD gs://ion-backup-eu/

# Firestore (또는 Spanner) 다중 지역 설정
gcloud firestore databases create --type=firestore-native --region=eur3
```

### Phase 3: 장애 조치 설정 (1주)

```bash
# Health checks
gcloud compute health-checks create https ion-health-check \
  --request-path=/health \
  --check-interval=10s

# Traffic splitting (카나리)
gcloud run services update-traffic ion-api \
  --to-revisions ion-api-us=70,ion-api-eu=20,ion-api-asia=10
```

---

## 📊 예상 성능 개선

| 지역 | 응답시간 (기존) | 응답시간 (멀티) | 개선 |
|------|-----------------|-----------------|------|
| US | 1.8s | 0.9s | 50% ↓ |
| EU | 8.2s | 1.2s | 85% ↓ |
| ASIA | 12.5s | 1.5s | 88% ↓ |

---

## 🔄 재해 조치 (Failover)

```bash
# 자동 장애 조치 설정
gcloud run services update ion-api \
  --min-instances=3 \
  --max-instances=100 \
  --region=us-central1

# 모니터링 및 자동 복구
gcloud compute instance-templates create ion-template \
  --enable-display-device \
  --health-check=ion-health-check
```

---

## 📋 배포 체크리스트

- [ ] 3개 리전에 리소스 생성
- [ ] Data replication 설정
- [ ] Global Load Balancer 구성
- [ ] Health checks 활성화
- [ ] Traffic routing 검증
- [ ] Failover 테스트
- [ ] 성능 벤치마크 실행
- [ ] Disaster recovery 드릴

---

## ⏱️ 예상 소요 시간: 40시간 (4주)
