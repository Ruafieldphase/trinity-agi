# Unified Dashboard & Alerts (v1.9 × v1.5)

## Grafana
- 대시보드 JSON: `grafana/dashboard_v19xv15_operational_intel.json`
- 데이터소스: `grafana/ds_prometheus.yaml`, `grafana/ds_loki.yaml` (앞서 제공)
- 임포트 후 변수 `service`, `window(6h/24h)`로 필터

## Prometheus Alerts
- 규칙 파일: `prometheus_rules/prom_rules_lumen.yaml`
- 기존 `prometheus_v15.yml`에 rule_files 섹션 추가 필요:
```yaml
rule_files:
  - /etc/prometheus/prom_rules_lumen.yaml
```
- 도커 컴포즈 시 아래처럼 마운트:
```yaml
prometheus:
  volumes:
    - ./prometheus_v15.yml:/etc/prometheus/prometheus.yml:ro
    - ./prometheus_rules/prom_rules_lumen.yaml:/etc/prometheus/prom_rules_lumen.yaml:ro
```

## 패널 구성
- ROI: deploy_success_rate, rollback_rate
- SLO: error_rate, burn_rate (service 변수)
- Maturity: overall + sense/feedback/release, windowed(6h/24h)
- Incidents: Loki 로그 `{app="lumen"} |= "incident"`
- Stat: 현재 overall maturity, 현재 burn rate

> 메트릭은 앞서 만든 익스포터들이 제공:  
> - ROI: :9156 — `lumen_prod_deploy_success_rate`, `lumen_prod_rollback_rate`  
> - SLO: :9157 — `lumen_slo_error_rate{service=...}`, `lumen_slo_burn_rate{service=...}`  
> - Maturity: :9158 — `lumen_maturity_*`
