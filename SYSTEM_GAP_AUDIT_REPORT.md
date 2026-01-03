# Shion(Shion) AGI 시스템: 기능 갭(껍데기/Shell) 종합 감사 리포트

이 문서는 “현재 워크스페이스에서 실제로 동작하지 않거나(미구현/스텁), 실행이 시뮬레이션이거나, 수동 단계로 우회되는” 요소를 기능 영역별로 정리한 사실 기반 리포트입니다.

원칙:
- 네트워크/철학 해석 없이 “무엇이 실제로 비어 있는지”만 정리
- “가짜 성공(fake success)”을 성공으로 간주하지 않음

## 0. 최근 반영된 개선(2025-12-23 기준)
아래 항목들은 이 리포트 작성 과정에서/직후 실제 코드가 보강된 부분입니다.

- `services/model_selector.py`
  - Google AI Studio(GenAI) / Vertex 선택 로직이 존재하며, `GOOGLE_API_KEY` 또는 `GEMINI_API_KEY`를 인식합니다.
  - 초기화 단계에서 사람용 요약을 위해 **네트워크 호출 없이 상태 스냅샷**을 제공(`get_status_snapshot()`).
- `fdo_agi_repo/orchestrator/llm_client.py`
  - `provider=auto|model_selector` 경로로 `services/model_selector.py`를 통해 GenAI/Vertex를 사용 가능(실패 시 None 반환).
  - GenAI 직접 호출 경로는 `gemini-2.5-flash` 계열을 우선 시도 후 fallback.
- `scripts/execute_proposal.py`
  - 미구현을 성공으로 속이던 패턴을 줄이고, 미구현은 `NOT_IMPLEMENTED`로 실패 처리.
  - 일부 타입은 로컬에서 실제로 수행하거나(유지/요약 루틴 실행), 요청 파일(signal)로 물질화하도록 개선.
  - REFACTOR는 기본 차단(`AGI_ALLOW_CLOUD_REFACTOR=1`일 때만 허용).
- `scripts/meta_supervisor.py`
  - “자가치유(self-healing)” 결과가 콘솔 출력으로만 끝나지 않도록 파일 리포트로 고정:
    - `outputs/bridge/meta_supervisor_report_latest.txt`
    - `outputs/bridge/meta_supervisor_report_latest.json`
  - 안전/휴식/통증(pain) 기반 실행 게이트로 무거운 조치를 억제.
  - 일부 액션은 기대 출력 파일 mtime 갱신 여부로 성공 재검증(가짜 성공 완화).

## 1. 코어 로직 & Self-Acquisition (“생각은 있는데 실제 행동이 약함”)

- `agi_core/self_acquisition_loop.py`
  - 상태: 구조는 있으나 내부 액션이 다수 스텁/미구현일 가능성(예: `TODO: 실제 실험 로직`).
  - 갭: “경험이 들어와도 실제 환경 행동/툴 실행으로 이어지는 경로”가 얇음.

- `scripts/execute_proposal.py`
  - 상태: 부분 구현(정직 실행).
  - 남은 갭:
    - 행동 타입 표준화(어떤 타입이 어떤 파일을 갱신해야 ‘성공’인지)의 일관성이 아직 부족.
    - RPA/툴 실행과의 연결이 제한적(검색 요청은 signal로 남기지만 소비 루프가 필요).

## 2. LLM 상호작용 레이어 (“선택/연결은 있지만 일관된 클라이언트 레이어가 약함”)

- `services/model_selector.py`
  - 상태: GenAI/Vertex 백엔드 선택 + 모델 후보 선택은 구현됨.
  - 남은 갭:
    - 실제 호출 실패(404/Quota/권한 문제)가 발생했을 때, 어떤 모델이 실패했는지/얼마나 블랙리스트 됐는지의 관측 표준화는 추가 여지.

- `fdo_agi_repo/orchestrator/llm_client.py`
  - 상태: `auto/model_selector` 브릿지로 부분 구현.
  - 남은 갭:
    - OpenAI/Anthropic “직접 provider”는 아직 미구현(설계상 필요할 때만).

- `fdo_agi_repo/orchestrator/pipeline.py` (Adaptive Feedback)
  - 상태: `Core` 패키지 의존 및 fallback class가 `pass`인 경우가 있어 실질적 최적화가 비활성일 수 있음.

## 3. RPA & Tool Execution (“도구/사지가 실동작으로 연결되지 않음”)

- `configs/tool_registry.json`
  - 상태: 핵심 툴이 `offline_stub`로 고정되어 있을 수 있음.
  - 갭: “읽기/계산/웹/코드 실행” 같은 핵심 도구가 시스템 내에서 실제 실행기로 연결되지 않으면, 상위 정책이 있어도 현실 행동이 불가능.

- `fdo_agi_repo/rpa/e2e_pipeline.py`
  - 상태: `_execute_single_step`에서 `asyncio.sleep(...)` 형태의 시뮬레이션 흔적이 존재할 수 있음.
  - 갭: OS/브라우저/파일 조작 같은 실제 RPA 실행 루틴(혹은 supervised body 루프)과의 통일된 연결이 필요.

## 4. 감각/지각 레이어 (“부분적 감지/제어 공백”)

- `scripts/vscode_chat_vision_bot.py`
  - 상태: 템플릿 매칭(OpenCV 의존) 등이 미구현일 수 있음.

- `agi_core/heartbeat_loop.py`
  - 상태: 일부 감각 제어 함수가 `pass`로 남아있을 수 있음(“센서 공백”).

## 5. 창작 출력 (“메타/설정은 있으나 자동 생성이 약함”)

- `scripts/generate_adaptive_music.py`
  - 상태: 오디오 생성이 아니라 프로젝트/설정 텍스트 생성(수동 렌더링 전제)일 수 있음.

- 문서(`CORE_CODEX_INFORMATION_THEORY.md` 등)
  - 상태: Sound/Visual 쪽 “미구현” 명시가 존재.

## 6. 메타인지/자가관리 (“진단은 있는데 자동 치료가 얇음”)

- `scripts/self_expansion/existence_dynamics_mapper.py`
  - 상태: 개념 매핑 중심(정적).
  - 갭: 실시간 정책/행동 변화로 이어지는 엔진은 별도 필요.

- `scripts/system_pain_analyzer.py`
  - 상태: 생물학 은유 기반 진단 중심인 경우가 있음.
  - 갭: “통증(pain)=라우팅 신호”를 실제 정책 편향으로 연결하는 자동 치료 루프가 일관되게 통합되어 있는지는 추가 확인 필요.

## 7. 메모리/학습 (“파일은 있지만 엔트리포인트가 빈 경우”)

- Social learners (예: `tiktok_learner.py`, `twitter_monitor.py` 등)
  - 상태: 엔트리포인트가 `pass`로 비어 있을 수 있음.

- `scripts/system_integration_diagnostic.py`의 “Semantic Memory 미구현” 표기
  - 상태: 코어 인지 축 중 하나가 명시적으로 비어 있을 수 있음.

---

## “실근육(Real Muscle)” 우선순위(낮은 위험 → 높은 효과)

1) **RPA/툴 실행의 최소 단위 1개를 실제로 연결**
   - “1개 도구가 끝까지 실제로 수행되는 경로”를 만들고, 관측 파일로 성공을 고정.
2) **가짜 성공 제거(계속)**
   - `execute_proposal` 외에도 “성공=True”를 반환하지만 출력이 갱신되지 않는 루프를 찾아 동일한 방식으로 교정.
3) **LLM 클라이언트 통일**
   - `services/model_selector.py`를 표준 입구로 두고, 다른 스크립트의 제각각 키/모델/라이브러리 사용을 수렴.
4) **센서/지각 공백 최소 구현**
   - `pass`로 남은 시작/중지 함수들을 “관측/상태 파일 업데이트” 수준이라도 채워서 ‘빈 기능’이 되지 않게.
5) **학습 데몬/러너의 엔트리포인트 정리**
   - “파일은 있는데 실행 루프가 없음”을 우선 정리(실행 가능한 최소 루프 제공).
