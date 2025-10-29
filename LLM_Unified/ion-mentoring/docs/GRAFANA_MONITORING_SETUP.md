# Grafana 대시보드 설정 가이드 (8시간 작업)

## 📋 개요

**목표**: Grafana를 사용한 고급 모니터링 및 시각화
**데이터 소스**: Prometheus (메트릭), Loki (로그), BigQuery (분석)
**이점**: 실시간 모니터링, 커스텀 대시보드, 알림 통합

---

## 🛠️ Grafana 설치 및 설정

### Phase 1: Grafana 설치 (1시간)

#### Step 1-1: Docker로 Grafana 실행 (개발용)

```bash
# Grafana 컨테이너 실행
docker run -d \
  -p 3000:3000 \
  --name grafana \
  -e GF_SECURITY_ADMIN_PASSWORD=admin123 \
  -e GF_USERS_ALLOW_SIGN_UP=false \
  -v grafana-storage:/var/lib/grafana \
  grafana/grafana:latest

# 접근
# http://localhost:3000
# 기본 계정: admin / admin123
```

#### Step 1-2: Google Kubernetes Engine에 배포 (프로덕션)

```bash
# Helm 저장소 추가
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Grafana Helm 차트 설치
helm install grafana grafana/grafana \
  --namespace monitoring \
  --create-namespace \
  --set adminPassword=SecurePassword123 \
  --set persistence.enabled=true \
  --set persistence.size=10Gi \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=grafana.ion-mentoring.com \
  --set datasources."datasources\.yaml".apiVersion=1 \
  --project=$GCP_PROJECT_ID

# Grafana 서비스 확인
kubectl get svc -n monitoring

# Port-forward (로컬 접근)
kubectl port-forward -n monitoring svc/grafana 3000:80
```

#### Step 1-3: 데이터소스 추가

**수동으로 추가하기**:
1. Grafana UI 접속 → Configuration → Data Sources
2. "+ Add data source" 클릭
3. 각 데이터소스 추가 (아래 참조)

**파일로 추가하기** (`grafana-datasources.yaml`):

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  namespace: monitoring
data:
  datasources.yaml: |
    apiVersion: 1
    datasources:
      # Prometheus (메트릭)
      - name: Prometheus
        type: prometheus
        access: proxy
        url: http://prometheus:9090
        isDefault: true
        editable: true

      # Google Cloud Monitoring
      - name: Google Cloud Monitoring
        type: stackdriver
        access: proxy
        jsonData:
          authenticationType: gce
          defaultProject: $GCP_PROJECT_ID

      # Loki (로그)
      - name: Loki
        type: loki
        access: proxy
        url: http://loki:3100
        editable: true

      # BigQuery (분석)
      - name: BigQuery
        type: grafana-bigquery-datasource
        access: proxy
        jsonData:
          authenticationType: gce
          defaultProject: $GCP_PROJECT_ID
```

---

### Phase 2: Prometheus 설정 (2시간)

#### Step 2-1: Prometheus 설치

```bash
# Docker로 실행
docker run -d \
  -p 9090:9090 \
  --name prometheus \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus:latest

# 또는 Helm으로 설치
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring
```

#### Step 2-2: Prometheus 설정 파일

**파일**: `prometheus.yml`

```yaml
global:
  scrape_interval: 15s  # 15초마다 메트릭 수집
  evaluation_interval: 15s
  external_labels:
    monitor: 'ion-api'

scrape_configs:
  # Google Cloud Run
  - job_name: 'cloud-run'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'

  # Google Cloud SQL
  - job_name: 'cloudsql-exporter'
    static_configs:
      - targets: ['localhost:9308']

  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']

  # Node Exporter (호스트 메트릭)
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']

  # Kubernetes (GKE)
  - job_name: 'kubernetes-cluster'
    kubernetes_sd_configs:
      - role: node
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
```

---

### Phase 3: Loki 설정 (1시간)

#### Step 3-1: Loki 설치

```bash
# Docker로 실행
docker run -d \
  -p 3100:3100 \
  --name loki \
  -v $(pwd)/loki-config.yaml:/etc/loki/local-config.yaml \
  grafana/loki:latest \
  -config.file=/etc/loki/local-config.yaml
```

#### Step 3-2: Promtail 설정 (로그 수집)

**파일**: `promtail-config.yaml`

```yaml
clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Cloud Run 로그
  - job_name: cloud-run
    static_configs:
      - targets:
          - localhost
        labels:
          job: cloud-run
          service: ion-api

  # Cloud Logging
  - job_name: google-cloud-logging
    static_configs:
      - targets:
          - localhost
        labels:
          job: gcp
          service: ion-api
```

---

### Phase 4: 대시보드 생성 (3시간)

#### Step 4-1: 주요 메트릭 대시보드

**대시보드 이름**: "ION API - 주요 메트릭"

**패널 구성**:

```json
{
  "dashboard": {
    "title": "ION API - 주요 메트릭",
    "description": "실시간 서비스 모니터링",
    "refresh": "10s",
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "Request Rate (req/s)",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_request_total[1m])",
            "legendFormat": "{{ method }} {{ path }}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            },
            "unit": "reqps"
          }
        }
      },
      {
        "id": 2,
        "title": "Response Time (P95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{ handler }}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "unit": "s"
          },
          "overrides": []
        },
        "thresholds": {
          "mode": "absolute",
          "steps": [
            { "color": "green", "value": null },
            { "color": "yellow", "value": 2 },
            { "color": "red", "value": 5 }
          ]
        }
      },
      {
        "id": 3,
        "title": "Error Rate (%)",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(http_request_total{status=~\"5..\"}[5m]) / rate(http_request_total[5m]) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "color": {
              "mode": "thresholds"
            }
          },
          "overrides": []
        },
        "thresholds": {
          "mode": "percentage",
          "steps": [
            { "color": "green", "value": null },
            { "color": "yellow", "value": 1 },
            { "color": "red", "value": 5 }
          ]
        }
      },
      {
        "id": 4,
        "title": "Active Requests",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_request_total[1m]))"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short"
          }
        }
      },
      {
        "id": 5,
        "title": "CPU Usage (%)",
        "type": "gauge",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{pod=\"ion-api\"}[1m]) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "max": 100,
            "min": 0
          }
        },
        "thresholds": {
          "mode": "percentage",
          "steps": [
            { "color": "green", "value": null },
            { "color": "yellow", "value": 70 },
            { "color": "red", "value": 90 }
          ]
        }
      },
      {
        "id": 6,
        "title": "Memory Usage (MB)",
        "type": "gauge",
        "targets": [
          {
            "expr": "container_memory_usage_bytes{pod=\"ion-api\"} / 1024 / 1024"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short"
          }
        },
        "thresholds": {
          "mode": "absolute",
          "steps": [
            { "color": "green", "value": null },
            { "color": "yellow", "value": 800 },
            { "color": "red", "value": 1200 }
          ]
        }
      }
    ]
  }
}
```

#### Step 4-2: Persona 분석 대시보드

**대시보드 이름**: "ION API - Persona 분석"

```json
{
  "panels": [
    {
      "id": 1,
      "title": "Requests by Persona",
      "type": "piechart",
      "targets": [
        {
          "expr": "sum by (persona) (rate(chat_requests_total[1h]))"
        }
      ]
    },
    {
      "id": 2,
      "title": "Response Time by Persona",
      "type": "table",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(chat_response_duration_seconds_bucket[5m])) by (persona)"
        }
      ]
    },
    {
      "id": 3,
      "title": "Persona Accuracy",
      "type": "stat",
      "targets": [
        {
          "expr": "avg by (persona) (chat_accuracy_score)"
        }
      ]
    },
    {
      "id": 4,
      "title": "Resonance Key Distribution",
      "type": "barchart",
      "targets": [
        {
          "expr": "topk(10, sum by (resonance_key) (rate(chat_requests_total[1h])))"
        }
      ]
    }
  ]
}
```

#### Step 4-3: 인프라 대시보드

**대시보드 이름**: "ION API - 인프라"

```json
{
  "panels": [
    {
      "id": 1,
      "title": "Cloud Run Instances",
      "type": "graph",
      "targets": [
        {
          "expr": "sum(kube_deployment_status_replicas{deployment=\"ion-api\"})"
        }
      ]
    },
    {
      "id": 2,
      "title": "Database Connections",
      "type": "graph",
      "targets": [
        {
          "expr": "pg_stat_activity_count"
        }
      ]
    },
    {
      "id": 3,
      "title": "Redis Memory",
      "type": "gauge",
      "targets": [
        {
          "expr": "redis_memory_used_bytes / 1024 / 1024 / 1024"
        }
      ]
    },
    {
      "id": 4,
      "title": "Disk Usage",
      "type": "gauge",
      "targets": [
        {
          "expr": "node_filesystem_avail_bytes{fstype=\"ext4\"} / node_filesystem_size_bytes{fstype=\"ext4\"} * 100"
        }
      ]
    }
  ]
}
```

#### Step 4-4: 보안 대시보드

**대시보드 이름**: "ION API - 보안"

```json
{
  "panels": [
    {
      "id": 1,
      "title": "Blocked Requests (by rule)",
      "type": "timeseries",
      "targets": [
        {
          "expr": "increase(waf_blocked_requests_total[5m]) by (rule_id)"
        }
      ]
    },
    {
      "id": 2,
      "title": "Top Attack Types",
      "type": "barchart",
      "targets": [
        {
          "expr": "topk(5, sum by (attack_type) (rate(waf_blocked_requests_total[1h])))"
        }
      ]
    },
    {
      "id": 3,
      "title": "Source Countries",
      "type": "worldmap",
      "targets": [
        {
          "expr": "sum by (country) (rate(http_requests_total[1h]))"
        }
      ]
    },
    {
      "id": 4,
      "title": "Failed Authentications",
      "type": "stat",
      "targets": [
        {
          "expr": "sum(rate(auth_failed_total[5m]))"
        }
      ]
    }
  ]
}
```

---

### Phase 5: 알림 및 노티피케이션 (1시간)

#### Step 5-1: 알림 규칙 설정

**파일**: `grafana-alerts.yaml`

```yaml
groups:
  - name: ION API Alerts
    interval: 1m
    rules:
      # 높은 응답 시간
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        annotations:
          summary: "High response time detected"
          description: "P95 response time is above 5 seconds"

      # 높은 에러율
      - alert: HighErrorRate
        expr: rate(http_request_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 1%"

      # CPU 과부하
      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total[1m]) > 0.8
        for: 10m
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is above 80%"

      # 메모리 부족
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.85
        for: 5m
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 85%"

      # 데이터베이스 연결 고갈
      - alert: DatabaseConnectionPoolExhausted
        expr: pg_stat_activity_count >= 95
        for: 2m
        annotations:
          summary: "Database connection pool exhausted"
          description: "Database connections are at 95% capacity"

      # 서비스 다운
      - alert: ServiceDown
        expr: up{job="ion-api"} == 0
        for: 1m
        annotations:
          summary: "ION API service is down"
          description: "No successful scrapes in the last minute"
```

#### Step 5-2: 통보 채널 설정

**Slack 통보**:
```yaml
Notification channels:
  - Name: Slack #alerts
    Type: Slack
    Webhook URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
    Channel: #alerts
    Message Template: |
      [{{ .GroupLabels.alertname }}]
      {{ .CommonAnnotations.summary }}
      {{ .CommonAnnotations.description }}
```

**이메일 통보**:
```yaml
  - Name: Email - OnCall
    Type: Email
    Address: oncall@ion-mentoring.com
    Send on all alerts: true
```

**PagerDuty 통보**:
```yaml
  - Name: PagerDuty
    Type: PagerDuty
    Integration Key: xxxxx
    Severity: critical
```

---

### Phase 6: 고급 기능 (1시간)

#### Step 6-1: 동적 대시보드 (템플릿 변수)

```json
{
  "templating": {
    "list": [
      {
        "name": "namespace",
        "type": "query",
        "datasource": "Prometheus",
        "query": "label_values(kube_pod_info, namespace)",
        "multi": false,
        "current": { "text": "default", "value": "default" }
      },
      {
        "name": "pod",
        "type": "query",
        "datasource": "Prometheus",
        "query": "label_values(kube_pod_info{namespace=\"$namespace\"}, pod)",
        "multi": true
      },
      {
        "name": "persona",
        "type": "custom",
        "options": [
          { "text": "Lua", "value": "lua" },
          { "text": "Elro", "value": "elro" },
          { "text": "Riri", "value": "riri" },
          { "text": "Nana", "value": "nana" }
        ]
      }
    ]
  }
}
```

#### Step 6-2: 커스텀 패널

```json
{
  "panels": [
    {
      "id": 1,
      "title": "Service Status",
      "type": "stat",
      "targets": [
        {
          "expr": "up{job=\"ion-api\"}"
        }
      ],
      "options": {
        "graphMode": "area",
        "colorMode": "background"
      },
      "mappings": [
        {
          "type": "value",
          "options": {
            "1": { "text": "UP", "color": "green" },
            "0": { "text": "DOWN", "color": "red" }
          }
        }
      ]
    }
  ]
}
```

#### Step 6-3: Annotation (기록)

```bash
# 배포 시간 기록
curl -X POST http://grafana:3000/api/annotations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboardId": 1,
    "time": '$(date +%s000)',
    "text": "Deployed version 1.2.3",
    "tags": ["deployment", "production"]
  }'
```

---

## 📊 대시보드 목록

| 대시보드 | 용도 | 갱신 주기 |
|---------|------|---------|
| **주요 메트릭** | 실시간 모니터링 | 10초 |
| **Persona 분석** | 성능 분석 | 1분 |
| **인프라** | 리소스 모니터링 | 1분 |
| **보안** | 공격 감시 | 10초 |
| **비용** | 비용 추적 | 1시간 |
| **로그** | 로그 분석 | 실시간 |

---

## 🎯 모범 사례

### DO ✅
- ✅ 자주 사용하는 메트릭만 표시
- ✅ 명확한 범례와 단위 사용
- ✅ 적절한 타임스케일 설정
- ✅ 알림 임계값 문서화
- ✅ 팀과 공유 가능한 대시보드

### DON'T ❌
- ❌ 너무 많은 패널 (20개 이상)
- ❌ 불명확한 범례
- ❌ 부정확한 단위
- ❌ 문서화되지 않은 대시보드
- ❌ 개인용 대시보드 (공유하지 않음)

---

## 📋 체크리스트

### 설치 단계
- [ ] Grafana 설치
- [ ] Prometheus 설정
- [ ] Loki 설정
- [ ] 데이터소스 추가

### 대시보드 생성
- [ ] 주요 메트릭 대시보드
- [ ] Persona 분석 대시보드
- [ ] 인프라 대시보드
- [ ] 보안 대시보드

### 알림 설정
- [ ] 알림 규칙 생성
- [ ] 통보 채널 설정
- [ ] 테스트 알림 발송

### 운영
- [ ] 정기 검토 일정 수립
- [ ] 팀원 교육
- [ ] 문서화

---

## 📞 문제 해결

### 문제: "No data"

**원인**: 데이터소스 연결 실패

**해결**:
1. Data Sources 확인
2. Query 검증
3. 메트릭 이름 확인

### 문제: 느린 대시보드

**해결**:
1. 쿼리 최적화
2. 시간 범위 축소
3. 불필요한 패널 제거

---

## 📅 다음 단계

✅ **Pre-commit hooks 설정 완료** (3시간)
✅ **WAF/Cloud Armor 설정 완료** (6시간)
✅ **추가 보안 테스트 개발 완료** (4시간)
✅ **Grafana 대시보드 설정 완료** (8시간)
➡️ **Task 5: 트러블슈팅 가이드 작성** (8시간)

총 소요 시간: Phase 2 **90시간** 중 **21시간** 완료 ✅
