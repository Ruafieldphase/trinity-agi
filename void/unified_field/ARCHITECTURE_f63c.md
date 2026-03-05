# 시스템 아키텍처 개요

본 문서는 ion-mentoring 프로젝트의 고수준 아키텍처를 요약합니다. 이후 심화 문서는 필요 시 확장 예정입니다.

## 구성요소

- API (FastAPI v2): 인증(JWT), CORS, 속도 제한
- 캐싱: L1 LRU, L2 Redis
- 모니터링: Sentry, Prometheus/Grafana
- 배포: Cloud Run

## 요청 흐름

1. 클라이언트 → API Gateway/Cloud Run
2. FastAPI 라우터 → Persona Router → Pipeline
3. 캐시 조회(L1 → L2)
4. 백엔드/모델 호출 후 응답 조립
5. 로깅/지표 전송(Sentry/Prometheus)

## 문서 링크

- [OpenAPI 스펙](../api/v2/openapi.yaml)
- [배포 가이드](../DEPLOYMENT.md)
- [문제 해결 가이드](TROUBLESHOOTING_GUIDE.md)
