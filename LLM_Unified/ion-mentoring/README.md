# Ion Mentoring API

Google Vertex AI Gemini 모델을 사용하는 프로덕션 준비 완료 REST API 서비스

[![Deploy to Cloud Run](https://github.com/Ruafieldphase/LLM_Unified/actions/workflows/deploy.yml/badge.svg)](https://github.com/Ruafieldphase/LLM_Unified/actions/workflows/deploy.yml)
[![Load Testing](https://github.com/Ruafieldphase/LLM_Unified/actions/workflows/load-test.yml/badge.svg)](https://github.com/Ruafieldphase/LLM_Unified/actions/workflows/load-test.yml)
[![Docs Link Check](https://github.com/Ruafieldphase/LLM_Unified/actions/workflows/docs-link-check.yml/badge.svg)](https://github.com/Ruafieldphase/LLM_Unified/actions/workflows/docs-link-check.yml)

> **Phase 9 Complete!** 🎉 완전한 자동화 파이프라인 구축 완료 | 자연어 명령 지원
>
> **NEW: Natural Language Deployment** � "5% 카나리 배포해줘" → 자동 실행
>
> 📚 [Documentation Index](docs/INDEX.md) | 📈 [Executive Summary (EN)](docs/PHASE3_EXECUTIVE_SUMMARY.md) | [경영진 요약 (KR)](docs/PHASE3_EXECUTIVE_SUMMARY_KO.md) | [Release Notes](RELEASE_NOTES.md)

## 🚀 프로젝트 개요

**Ion Mentoring API**는 Google Cloud Run에 배포된 FastAPI 기반 AI 챗봇 서비스입니다. Vertex AI의 Gemini 1.5 Flash 모델을 활용하여 사용자 질문에 응답합니다.

### 주요 특징

- ✅ **FastAPI**: 고성능 비동기 웹 프레임워크
- ✅ **Vertex AI Integration**: Google Gemini 1.5 Flash 모델
- ✅ **Docker 컨테이너화**: 일관된 배포 환경
- ✅ **Cloud Run 배포**: 자동 스케일링 및 관리형 서비스
- ✅ **CI/CD 파이프라인**: GitHub Actions 자동 배포
- ✅ **부하 테스트 자동화**: 일일 성능 모니터링
- ✅ **포괄적인 테스트**: 67개 테스트 (단위/통합/E2E)
- ✅ **구조화된 로깅**: JSON 로깅 + Google Cloud Logging
- ✅ **카나리 배포**: 5%~100% 점진적 트래픽 분리
- 🆕 **자연어 명령 지원**: "5% 카나리 배포해줘" → 자동 실행 (Phase 9)
- 🆕 **완전 자동화**: Orchestrator + Action Runner + Deployment Controller

## 📊 성능 벤치마크

최신 부하 테스트 결과 (2025-10-18):

| 시나리오 | 총 요청 수 | 평균(ms) | P50(ms) | P95(ms) | P99(ms) | Req/s | 실패율 |
| -------- | ---------- | -------- | ------- | ------- | ------- | ----- | ------ |
| Light    | 5,859      | 279      | 170     | 180     | 1,400   | 48.8  | 0%     |
| Medium   | 19,149     | 248      | 170     | 190     | 1,100   | 63.8  | 0%     |
| Heavy    | 34,219     | 239      | 170     | 190     | 1,100   | 90.7  | 0%     |
| Stress   | 52,459     | 214      | 170     | 190     | 1,100   | 87.5  | 0%     |

**총 111,686건 요청, 0% 실패율 달성**

## 🏗️ 아키텍처

### 전체 시스템 구조 (Phase 9 완성)

```plaintext
┌─────────────────────────────────────────────────────────────────────────┐
│                      ION Mentoring API System                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │            🆕 Automation Pipeline (자동화 파이프라인)              │  │
│  │                                                                  │  │
│  │  Natural Language (KO/EN): "5% 카나리 배포해줘"                  │  │
│  │         ↓                                                        │  │
│  │  Orchestrator: Intent parsing & action planning                  │  │
│  │         ↓                                                        │  │
│  │  Deployment Controller: CLI/Slack/API interface                  │  │
│  │         ↓                                                        │  │
│  │  Action Runner: Execute PowerShell scripts                       │  │
│  │         ↓                                                        │  │
│  │  GCP Cloud Run / System Operations                               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    API Service Layer                             │  │
│  │                                                                  │  │
│  │   Client ──▶ Cloud Run (FastAPI) ──▶ Vertex AI (Gemini 1.5)    │  │
│  │              - ion-api (100%)                                    │  │
│  │              - ion-api-canary (0-100%)                           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                 Monitoring Stack (Gateway v1.0)                  │  │
│  │                                                                  │  │
│  │   Prometheus (9090) ──▶ Alertmanager (9093) ──▶ Slack           │  │
│  │        ↑                                                         │  │
│  │   Gateway Exporter (9108) ──▶ Metrics                           │  │
│  │        ↑                                                         │  │
│  │   Lumen Gateway (8080)                                           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 기술 스택

- **Backend**: FastAPI 0.115.6, Python 3.13
- **AI Model**: Google Vertex AI Gemini 1.5 Flash
- **Deployment**: Google Cloud Run, Docker
- **CI/CD**: GitHub Actions
- **Testing**: pytest, Locust
- **Monitoring**: Google Cloud Monitoring

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.13+
- Docker (선택사항)
- Google Cloud 프로젝트 및 Vertex AI API 활성화

### 로컬 개발

**저장소 클론**

```bash
git clone https://github.com/Ruafieldphase/LLM_Unified.git
cd LLM_Unified/ion-mentoring
```

**가상 환경 생성 및 의존성 설치**

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -r requirements-api.txt
```

**환경 변수 설정**

`.env` 파일 생성:

```env
ENVIRONMENT=development
ALLOWED_ORIGINS=*
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
MODEL_NAME=gemini-1.5-flash-002
```

**애플리케이션 실행**

```bash
uvicorn app.main:app --reload
```

API 문서: http://localhost:8000/docs

### Docker로 실행

```bash
docker build -t ion-api .
docker run -p 8000:8080 --env-file .env ion-api
```

#### 빠른 실행(개발 모드, Vertex AI 없이)

로컬에서 빠르게 기동하고 헬스체크만 확인하려면 환경 변수를 사용해 개발 모드로 실행하세요.

```bash
# 이미지 빌드
docker build -t ion-api-local .

# 개발 모드 실행 (Vertex AI 연동 비활성화)
docker run --rm \
  -e ENVIRONMENT=development \
  -e PHASE4_ENABLED=false \
  -e PORT=8082 \
  -p 8082:8082 \
  ion-api-local

# 새 터미널에서 헬스 체크
curl http://localhost:8082/health
```

## 📡 API 엔드포인트

### ⚡ 요약 성능 개선: 병렬 요약(Preview)

긴 대화 요약 시간을 줄이기 위해, 문자 기준 청크 분할 + 동시 처리 + 최종 병합 요약 파이프라인을 미리보기 엔드포인트로 제공합니다. 운영 플로우(/chat/end)는 그대로 유지되며, 세션 메시지 저장소 연동 시 해당 경로에도 쉽게 붙일 수 있습니다.

새 엔드포인트: `POST /summaries/preview`

요청 예시

```bash
curl -X POST http://localhost:8000/summaries/preview \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      "첫 메시지입니다",
      "두 번째 메시지에 상세 내용이 조금 더 깁니다.",
      "세 번째 메시지로 결론을 정리합니다"
    ]
  }'
```

응답 예시

```json
{
  "status": "completed",
  "duration_ms": 1234,
  "parallel": true,
  "chunk_chars": 1600,
  "concurrency": 4,
  "summary": "최종 요약 텍스트 ..."
}
```

환경 변수(기본값)

```bash
SUMMARY_PARALLEL_ENABLED=true   # 병렬 요약 on/off
SUMMARY_CHUNK_CHARS=1600        # 청크 문자 크기
SUMMARY_MAX_CONCURRENCY=4       # 동시 처리 개수(레이트 리밋 고려)
SUMMARY_TIMEOUT_SEC=30          # 전체 타임아웃(초)
```

운영 경로 연결 가이드

- `/sessions/{session_id}/messages`로 대화 중 메시지를 누적합니다.
- 이후 `/chat/end?session_id={session_id}` 호출 시 해당 세션 메시지를 병렬 요약에 활용합니다.

세션 메시지 수집 예시

```bash
curl -X POST http://localhost:8000/sessions/demo-1/messages \
  -H "Content-Type: application/json" \
  -d '{"message":"첫 메시지입니다"}'
```

### `GET /`
루트 엔드포인트 - 서비스 정보 반환

```bash
curl https://ion-api-64076350717.us-central1.run.app/
```

### `GET /health`

헬스 체크 엔드포인트

```bash
curl https://ion-api-64076350717.us-central1.run.app/health
```

### `POST /chat`

AI 챗봇 대화 엔드포인트

**요청:**

```bash
curl -X POST https://ion-api-64076350717.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요!"}'
```

**응답:**

```json
{
  "response": "안녕하세요! 무엇을 도와드릴까요?",
  "model": "gemini-1.5-flash-002",
  "timestamp": "2025-10-18T12:00:00.000Z"
}
```

## 🌟 Lumen Gateway 통합

ION API는 **Lumen Gateway**와 통합되어 4-페르소나 하이브리드 AI 시스템으로 작동합니다.

### Lumen 4-Persona Network

1. **세나 (Sena)**: 전략적 기획자 - 복잡한 계획과 분석
2. **루빛 (Lubit)**: 창의적 사고자 - 혁신과 아이디어 생성
3. **깃코 (Gitko)**: 기술 전문가 - 코드 구현과 문제 해결
4. **시안 (Sian)**: 정보 큐레이터 - 데이터 정리와 검색

### Lumen API 엔드포인트

#### `GET /api/lumen/health`
Lumen Gateway 헬스 체크

```bash
curl https://ion-api-64076350717.us-central1.run.app/api/lumen/health
```

**응답:**

```json
{
  "status": "healthy",
  "gateway_url": "https://lumen-gateway-staging-64076350717.us-central1.run.app"
}
```

#### `GET /api/lumen/personas`
4-페르소나 목록 조회

```bash
curl https://ion-api-64076350717.us-central1.run.app/api/lumen/personas
```

**응답:**

```json
{
  "personas": [
    {"name": "sena", "description": "Strategic Planner"},
    {"name": "lubit", "description": "Creative Thinker"},
    {"name": "gitko", "description": "Technical Expert"},
    {"name": "sian", "description": "Information Curator"}
  ]
}
```

#### `POST /api/lumen/chat`
Lumen 채팅 (자동 페르소나 감지)

```bash
curl -X POST https://ion-api-64076350717.us-central1.run.app/api/lumen/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "창의적인 아이디어를 주세요"}'
```

**응답:**

```json
{
  "response": "창의적인 아이디어: ...",
  "detected_persona": "lubit",
  "model": "gemini-1.5-flash"
}
```

**특정 페르소나 지정:**

```bash
curl -X POST https://ion-api-64076350717.us-central1.run.app/api/lumen/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "코드 리뷰 부탁해", "persona": "gitko"}'
```

#### `GET /api/lumen/status`
Lumen Gateway 상태 조회

```bash
curl https://ion-api-64076350717.us-central1.run.app/api/lumen/status
```

### 환경 변수

```bash
LUMEN_GATEWAY_URL=https://lumen-gateway-staging-64076350717.us-central1.run.app  # Staging
LUMEN_GATEWAY_URL=https://lumen-gateway-production-64076350717.us-central1.run.app  # Production
LUMEN_FEATURE_ENABLED=true  # Lumen 기능 활성화
```

## 🧪 테스트

### 전체 테스트 실행

```bash
pytest -v
```

### 특정 테스트 카테고리

```bash
# 단위 테스트
pytest tests/unit/ -v

# 통합 테스트
pytest tests/integration/ -v

# E2E 테스트
pytest tests/e2e/ -v
```

### 부하 테스트

```bash
# 단일 시나리오
python -m locust -f load_test.py --host=https://ion-api-64076350717.us-central1.run.app --users 10 --spawn-rate 1 --run-time 2m --headless

# 전체 시나리오 (PowerShell)
.\scripts\run_all_load_tests.ps1
```

자세한 내용은 [LOAD_TESTING.md](LOAD_TESTING.md)를 참조하세요.

## 🔄 CI/CD

### 자동 배포 워크플로우

`master` 브랜치에 푸시하면 자동으로:

1. ✅ 테스트 실행 (67개 테스트)
2. ✅ Docker 이미지 빌드
3. ✅ Artifact Registry에 푸시
4. ✅ Cloud Run에 배포
5. ✅ 배포 검증 (헬스 체크)

### 부하 테스트 워크플로우

매일 오전 3시(UTC) 자동 실행:

- 4개 시나리오 순차 테스트 (Light → Medium → Heavy → Stress)
- CSV/HTML 리포트 생성 (30일 보관)
- JSON 성능 메트릭 추출 (90일 보관)

수동 실행:

1. [GitHub Actions](https://github.com/Ruafieldphase/LLM_Unified/actions) 페이지 접속
2. "Load Testing (Automated)" 워크플로우 선택
3. "Run workflow" 클릭

## 📚 문서

### 📋 프로젝트 요약 문서

- **[📖 Documentation Index](docs/INDEX.md)** - 전체 문서 네비게이션 가이드
- **[Phase 3 Executive Summary (English)](docs/PHASE3_EXECUTIVE_SUMMARY.md)** - 14주 개발 완전 요약 (영문)
- **[Phase 3 Executive Summary (한국어)](docs/PHASE3_EXECUTIVE_SUMMARY_KO.md)** - 14주 개발 완전 요약 (국문)

### 📖 주간 완료 보고서 (Week-by-Week)

1. [Week 1-4: PersonaOrchestrator Refactoring](docs/PERSONA_REFACTORING_WEEK1-4_COMPLETE.md)
2. [Week 5-6: Pipeline Integration](docs/PHASE_3_WEEK5-6_UPDATE.md)
3. [Week 7-8: Migration & Compatibility](docs/WEEK7_MIGRATION_COMPLETION.md)
4. [Week 9-10: Caching Optimization](docs/WEEK9-10_CACHING_OPTIMIZATION.md)
5. [Week 11: API v2 Development](docs/WEEK11_API_V2_COMPLETE.md)
6. [Week 12-13: Sentry Monitoring](docs/WEEK12-13_SENTRY_MONITORING.md)
7. [Week 14: Load Testing Automation](docs/WEEK14_COMPLETION_REPORT.md)

### 🛠️ 기술 가이드

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - 시스템 아키텍처 개요
- [LOAD_TESTING.md](LOAD_TESTING.md) - 부하 테스트 가이드 및 결과
- [LOAD_TESTING_CI.md](docs/LOAD_TESTING_CI.md) - CI/CD 부하 테스트 전략
- [GITHUB_ACTIONS_MANUAL_RUN.md](docs/GITHUB_ACTIONS_MANUAL_RUN.md) - GitHub Actions 수동 실행 가이드

### 📝 초기 개발 일지

- [WEEK3_SUMMARY.md](WEEK3_SUMMARY.md) - 프로젝트 개발 일지 (Day 1-6)
- [DAY5_CICD_PIPELINE.md](DAY5_CICD_PIPELINE.md) - CI/CD 파이프라인 설정
- [TESTING.md](TESTING.md) - 테스트 전략 및 가이드
- [DEPLOYMENT.md](DEPLOYMENT.md) - 배포 가이드
- [LOGGING.md](LOGGING.md) - 로깅 설정 및 모니터링

### 📜 프로젝트 이력

- **[CHANGELOG.md](CHANGELOG.md)** - Phase 3 완전한 변경 이력 및 성과 요약
- **[RELEASE_NOTES.md](RELEASE_NOTES.md)** - v3.0.0 릴리스 노트 (하이라이트, 마이그레이션, 로드맵)

## 🛠️ 개발 환경

### VS Code 태스크

- **Python: Run All Tests (repo venv)** - 전체 테스트 실행
- **Python: Run Vertex AI Test (repo venv)** - Vertex AI 통합 테스트
- **Luon: Run Pipeline Once** - Luon 파이프라인 실행 (프로젝트 특화)

### PowerShell 스크립트

- `scripts/run_all_load_tests.ps1` - 4개 주요 시나리오 실행
- `scripts/run_extended_load_tests.ps1` - 7개 전체 시나리오 실행

### pre-commit 설정 (권장)

코드 커밋 전에 자동으로 포맷/린트 검사를 실행하려면 아래를 한 번 설정하세요.

```powershell
# 가상환경 활성화 후 실행
pip install pre-commit
pre-commit install

# 전체 파일에 대해 한 번 실행 (선택)
pre-commit run --all-files
```

포함된 훅: trailing-whitespace, end-of-file-fixer, Black, Ruff, Markdownlint

보안 점검: 매주 월요일 04:00 UTC에 pip-audit 워크플로우가 자동 실행됩니다.

## 📈 프로젝트 지표

| 메트릭                 | 값                           |
| ---------------------- | ---------------------------- |
| 총 개발 일수           | 25일 (Phase 1-9)             |
| 코드 라인 수           | ~18,000 lines                |
| 테스트 수              | 67개 (100% passing)          |
| API 엔드포인트         | 3개                          |
| Docker 이미지 크기     | 487MB                        |
| CI/CD 파이프라인       | 2개 (배포 + 부하테스트)      |
| 부하 테스트 총 요청 수 | 111,686건 (100% 성공)        |
| 측정된 최대 처리량     | ~90 req/s                    |
| P50 응답 시간          | 170ms                        |
| 자동화 스크립트        | 50+ PowerShell scripts       |
| Git 커밋 수            | 20 (Phase 1-9)               |

## 🔐 보안 및 인증

현재 API는 인증 없이 공개되어 있습니다. 프로덕션 환경에서는 다음을 고려하세요:

- API 키 인증
- OAuth 2.0
- Cloud Run IAM 기반 인증

## 🚀 자연어 명령 자동화 (NEW in Phase 9)

### 빠른 시작

```bash
# 기본 사용 (dry-run, 안전)
python deployment_controller.py "5% 카나리 배포해줘"

# 실제 실행 (주의!)
python deployment_controller.py "Deploy 25% canary" --execute

# 사용자 추적
python deployment_controller.py "상태 확인" --user alice

# Slack 포맷 출력
python deployment_controller.py "모니터링 시작" --slack-format
```

### 지원되는 자연어 명령

**배포 관련** (한국어/영어):
- "5% 카나리 배포해줘" / "Deploy 5% canary"
- "25% 배포" / "Deploy 25% canary"
- "100% 배포하고 모니터링 시작" / "Deploy 100% and start monitoring"

**모니터링**:
- "모니터링 시작해줘" / "Start monitoring"
- "프로브 실행" / "Run probe"
- "모니터링 중지" / "Stop monitoring"

**테스트**:
- "테스트 실행" / "Run tests"
- "로드 테스트" / "Run load test"

**상태 확인**:
- "현재 상태 확인해줘" / "Check status"
- "배포 상태 확인" / "Check deployment status"

**롤백**:
- "롤백해줘" / "Rollback"
- "모니터링 중지하고 롤백" / "Stop monitoring and rollback"

### 데모 스크립트 실행

5가지 실제 시나리오를 시연하는 완전한 데모:

```bash
# 모든 시나리오 실행 (dry-run)
python demos/complete_deployment_demo.py

# 특정 시나리오만 실행
python demos/complete_deployment_demo.py --scenario 1  # Basic Flow
python demos/complete_deployment_demo.py --scenario 5  # Complete Cycle

# 실제 실행 (확인 필요)
python demos/complete_deployment_demo.py --execute --scenario 1

# 일시정지 없이 빠르게 실행
python demos/complete_deployment_demo.py --no-pause
```

**시나리오 목록**:
1. **Basic Deployment Flow**: 상태 확인 → 5% 배포 → 모니터링 시작
2. **Gradual Rollout**: 25% → 테스트 → 50% 배포
3. **Monitoring & Probing**: Rate limit 프로브 → 로드 테스트
4. **Emergency Rollback**: 긴급 상황 시 즉시 롤백
5. **Complete Cycle**: 전체 배포 사이클 (5% → 100%)

### 아키텍처 레이어

```plaintext
Natural Language Command
    ↓
Orchestrator (intent_router.py)
    - 자연어 파싱 (KO/EN)
    - 의도 분석 및 액션 계획
    ↓
Deployment Controller (deployment_controller.py)
    - 통합 인터페이스 (CLI/Slack/API)
    - 사용자 추적 및 보고서 저장
    ↓
Action Runner (action_runner.py)
    - PowerShell 스크립트 실행
    - 8가지 액션 타입 지원
    - Timeout 보호 및 Dry-run 모드
    ↓
PowerShell Scripts
    - deploy_phase4_canary.ps1
    - start_monitor_loop_with_probe.ps1
    - rate_limit_probe.ps1
    - 등 50+ 스크립트
    ↓
GCP Cloud Run / System Operations
```

### 실행 보고서

모든 명령 실행 결과는 JSON 형식으로 저장됩니다:

```bash
outputs/deployment_reports/
├── deployment_20251024_213050_demo-user.json
├── deployment_20251024_213056_alice.json
└── ...
```

보고서 내용:
- 명령어 및 사용자 ID
- 실행 계획 요약
- 각 액션별 실행 시간
- 성공/실패 상태
- 에러 메시지 (있는 경우)
- 타임스탬프 및 메타데이터

## 🤝 기여

이 프로젝트는 개인 학습 및 연구 목적입니다.

## 📝 라이선스

Private - 학습 및 연구 목적

## 👤 작성자

**Ruafieldphase**

- GitHub: [@Ruafieldphase](https://github.com/Ruafieldphase)

## 🙏 감사의 말

- Google Cloud Platform - Vertex AI 및 Cloud Run
- FastAPI - 훌륭한 웹 프레임워크
- Locust - 강력한 부하 테스트 도구

---

**Live API**: https://ion-api-64076350717.us-central1.run.app

**Canary API**: https://ion-api-canary-64076350717.us-central1.run.app

**Monitoring**: http://localhost:9090 (Prometheus) | http://localhost:9093 (Alertmanager)

**Last Updated**: 2025-10-24 (Phase 9 Complete)
