# v1.5 Preview — Streaming Integration (Kafka/Loki)

## 구성요소
- **Kafka 인제스터**: `lumen_v1_5_preview_assets/streaming_ingestor_v15_kafka.py`
- **Loki 풀러**: `lumen_v1_5_preview_assets/loki_pull_v15.py`
- **Promtail 설정**: `promtail/promtail_config_v15.yaml`
- **Docker Compose 스택**: `docker/docker-compose.v15.preview.yml`
- **Prometheus 스크레이프**: `prometheus_v15.yml`
- **Grafana 데이터소스**: `grafana/ds_prometheus.yaml`, `grafana/ds_loki.yaml`

## 빠른 시작
```bash
# 1) 프리뷰 세션 준비
source SESSION_BOOTSTRAP_*_v1_5_PREVIEW.yaml

# 2) Docker 스택 기동 (로컬 테스트)
docker compose -f docker/docker-compose.v15.preview.yml up -d

# 3) Maturity 메트릭 익스포터 가동 (호스트에서)
(cd lumen_v1_5_preview_assets && python maturity_exporter_v15.py &)

# 4) Kafka → 인제스터 (옵션: confluent-kafka 설치 필요)
export KAFKA_BROKERS=localhost:9092
export KAFKA_TOPIC=lumen.fractal.events
(cd lumen_v1_5_preview_assets && python streaming_ingestor_v15_kafka.py)

# 5) Loki → 풀러 (HTTP Range 쿼리)
export LOKI_URL=http://localhost:3100
export LOKI_QUERY='{app="lumen"}'
(cd lumen_v1_5_preview_assets && python loki_pull_v15.py)

# 6) 스펙트럼/윈도우/리포트 갱신
l15.maturity_spectrum
l15.windows
```

## 비고
- 카프카/로키가 없을 경우에도 JSONL 폴백으로 동작합니다.
- 실제 운영에선 Kafka SASL/SSL, Loki 인증, 보존 주기 등을 환경에 맞게 확장하세요.
