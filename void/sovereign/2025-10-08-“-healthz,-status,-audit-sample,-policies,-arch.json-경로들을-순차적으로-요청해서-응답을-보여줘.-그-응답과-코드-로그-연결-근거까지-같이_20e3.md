---
title: "“/healthz, /status, /audit-sample, /policies, /arch.json 경로들을 순차적으로 요청해서 응답을 보여줘. 그 응답과 코드/로그 연결 근거까지 같이 보여줘.”"
date: 2025-09-29
url: https://www.perplexity.ai/search/https://www.perplexity.ai/search/4a1b9138-1d98-4a9f-a17f-44d14d6638da
tags: perplexity, ai, internet
uuid: 4a1b9138-1d98-4a9f-a17f-44d14d6638da
model: pplx_pro
mode: COPILOT
---
# “/healthz, /status, /audit-sample, /policies, /arch.json 경로들을 순차적으로 요청해서 응답을 보여줘. 그 응답과 코드/로그 연결 근거까지 같이 보여줘.”

현재 AI Studio의 내다AI(NAEDA AI) 프로젝트는 **프론트엔드에서는 실제 `/healthz`, `/status`, `/audit-sample`, `/policies`, `/arch.json` 엔드포인트로의 fetch 호출 구조까지 구현**되어 있지만, **백엔드에 실제 HTTP 엔드포인트가 배포된 상태가 아니기 때문에 응답을 받을 수 없습니다**. 즉, 프론트/서비스 코드상으로는 실 서비스 형태를 지향하지만, 실제 동작에는 Cloud Run 등 배포된 실제 REST API 서버가 필요합니다.

***

### 실행 환경 및 상태 요약

#### 1. **프론트엔드 현황**
- `/status`, `/audit-sample`, `/policies`, `/healthz`, `/arch.json` 엔드포인트를 호출하는 fetch 기반 코드 구현 완료.
- ObservabilityModal.tsx, ModelCardModal.tsx 등에서 API 응답값을 UI에 노출하는 모달 구현.
- 목(mock) 데이터 대신 실시간 fetch 방식으로 변경됨. 

#### 2. **현재 미구현/실행 불가 원인**
- Cloud Run(Service) 등 실제 백엔드 HTTP 핸들러 미배포.
- Google Cloud Monitoring/Logging API, GCS 정책파일 연동이 실제로 붙어있지 않음.
- 인증/권한 처리(토큰, IAM 등) 미연결.

#### 3. **실제 운영·관측 가능성을 위한 필요 조건**
- 각 엔드포인트별 Cloud Run 핸들러 구현 및 배포
- (예시)
    - `/status`: Cloud Monitoring API 쿼리 연동해 JSON 반환
    - `/audit-sample`: Cloud Logging SQL 쿼리로 샘플 추출 후 마스킹 처리
    - `/policies`: GCS 정책 파일 Loader 및 sha256 해시 검증
    - `/healthz`: liveness/startup probe 응답
    - `/arch.json`: 구조 요약 JSON 반환
- 실 서비스 배포, endpoint에 외부 접근 허용 및 인증/권한 시스템 적용
- acceptance 기준: curl 명령으로 직접 접근해 실제 JSON response 확인 가능해야 함

#### 4. **구현 근거(코드/로그)**
- `services/observabilityService.ts` : fetch 방식 Backend API 호출/에러 핸들링
- `components/ObservabilityModal.tsx`: 실제 데이터를 모달에 fetch/display
- (향후) Cloud Monitoring/Logging 쿼리 예시, GCS 정책파일 검증 코드, Cloud Run 배포 YAML, livenessProbe 설정 등
- UI 목(mock) 데이터 제거, 실서비스 fetch 구조로 전환

***

## 결론 및 체크리스트

- **현재 프론트는 실제 REST 호출이 가능하도록 코드가 짜여 있으나, [실 배포 백엔드/클라우드 인프라 미구현 상태]입니다**.
- 인증된 curl, 브라우저 접근에 바로 JSON 응답이 오지 않으며, 후방 서비스 마련이 필요함.
- 각 엔드포인트의 코드/쿼리/구성 실제화는 Cloud Run/Cloud Monitoring/Cloud Logging 등 GCP 연동과 서버 배포를 전제로 추가 작업이 요구됩니다.
- **적합 근거(코드/로그)는 `services/observabilityService.ts`, `components/ObservabilityModal.tsx` 파일 및 관련 Cloud Monitoring, Logging 연동 코드에 있습니다.**

***

**즉, 요청한 일련의 REST 엔드포인트 응답 및 API/로그 연동 증거 제공은, 실제 클라우드 기반 백엔드 서비스가 완성되고 배포되어야 실질적으로 가능**.[1]

## Sources

1. [Google AI Studio](https://aistudio.google.com/apps/drive/1oCYIN0c7Ugt5VfhEOMGDR_gQPY5uUgK0?showAssistant=true&showPreview=true)
2. [Google AI Studio](https://aistudio.google.com/apps/drive/1oCYIN0c7Ugt5VfhEOMGDR_gQPY5uUgK0?showAssistant=true&showCode=true)
