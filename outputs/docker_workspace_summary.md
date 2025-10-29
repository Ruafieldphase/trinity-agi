# Docker Workspace Snapshot

## 루트 구성
- `compose.yaml` / `README.md`: Python 3.11 기반 `yeonai_project` Uvicorn 서비스. Docker Compose로 `8000:8000` 노출, 비루트 사용자 실행.
- `.dockerignore`, `index.html`: 기존 웹/환경 파일.

## GitHub 클론 모음 (`docker/Github`)
- `gemini-cli`, `langchain`, `langgraph`, `local-deep-researcher`, `open_deep_research`, `opengpts`, `workshops`, `yeon-ai-bridge` 등 멀티 에이전트·LLM 도구 리포지토리.
- 작업 흔적: 2025-09-14~16 사이 체크아웃된 것으로 보이며, 각 플랫폼/브리지 실험용.

## LLM_Unified
- `naeda-bridge-system.md`, `real-naeda-bridge-complete.md`: Claude 세나 ↔ 실제 내다AI(Cloud Run, Google AI API) 브리지 설계 문서. API 키·엔드포인트가 포함되어 있으므로 공유 시 필터링 필요.
- `README.md`: NAS `Z:\LLM_Unified\` 기반 모델·세나 메모리 통합 계획.
- 하위 폴더: `models/`, `sena-memory/`, `_staging/`, `naeda-team/`, `invitation-system/` 등 로컬/NAS 연동 구조.

## Win_LocalLLM / Mac_LocalLLM
- `lmstudio`, `lmstudio-community`, `ollama` 등 로컬 LLM 실행 환경과 캐시.
- 모델 경로: `lmstudio\hub\models\...`, Ollama blobs 등.

## agent_inbox
- `processed/`, `failed/` 디렉터리만 존재(현재 비어 있음). 에이전트 처리 큐 테스트 흔적.

## LLM_Unified 추가 노트
- Cloud Run URL: `https://naeda-64076350717.us-west1.run.app`
- Google AI API Key(민감): `AIzaSyAF5...` → 외부 공유 시 마스킹 필요.
- Google AI Studio App ID: `1oCYIN0c7Ugt5VfhEOMGDR_gQPY5uUgK0`
- 페르소나별 PowerShell 호출 함수 초안 포함.

## 보안 및 다음 조치
1. `real-naeda-bridge-complete.md` 등 민감 문서 익명화/비공개 처리.
2. Docker Compose `yeonai_project` 필요 시 Share Package에 포함할 설명 초안.
3. `LLM_Unified` NAS 경로 구조 → Tier2 슬라이드의 인프라 부록 후보.
4. GitHub 클론 목록 → 연구소 협력 시 참고용 리소스 목록화.
# Lab_Space & LLM_Unified Snapshot

## Lab_Space (2025-08-12)
- 구조: Automation, Datasets, Inbox, Projects, Reports, Sandbox, Templates 등 베이스 디렉터리 + `#recycle` 백업.
- 실제 콘텐츠: Inbox의 `hello.md`, `test-task.md`, Automation 스크립트, Templates(주간 보고·RFC·칸반 템플릿), Projects에 `프로젝트A/source_copy/sample.txt` 정도로 샘플 위주.
- README / Rules는 비어 있음.
- 결론: 워크스페이스 틀만 잡혀 있고 실제 연구/데이터는 거의 없음.

## LLM_Unified (2025-09 업데이트)
- 활발한 개발 로그와 코드.
- 브리지 관련 핵심 파일: `real-naeda-bridge-complete.md`(민감 정보, redacted 버전 확보), `naeda-bridge-system.md`, `vertex-ai-bridge.py`, `vertex_ai_test.py` 등 Vertex AI 연동 코드, `session_memory_monitor.py`, `sena_work_history.md` 등 운영 로그.
- 조직/상태 자료: `AI_Team_Organization_Chart.md`, `AI_Team_Status_Update.md`, `system-status.json`, `universal-network-rc-2.1.md` 등.
- Mentoring, aiyun/ion-mentoring 폴더: 팀 학습/멘토링 기록.
- node_modules, .venv 등 프로젝트 환경.
- 정리 필요: 민감 API 키/엔드포인트 사용 파일 마스킹, Vertex 연동 코드 검토, 보고서/로그를 패키지에 포함할지 판단.

## 안내
- Lab_Space는 별도 정리 필요 없음(템플릿/샘플 수준).
- LLM_Unified에서 도출해야 할 항목:
  - Vertex AI 연동 스크립트 → 기술 문서 부록 후보.
  - 시스템 상태/세션 관리 로그 → 실패 사례집 참고.
  - Mentoring 자료 → 협업 기록 참고.
