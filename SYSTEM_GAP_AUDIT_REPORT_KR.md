# 시안(Sian) AGI 시스템: 기능적 공백("껍데기")에 대한 종합 진단 리포트

이 리포트는 시안의 AGI 시스템 내에서 아직 구현되지 않았거나 자리표시자(placeholder)로만 존재하는 "껍데기(shells)" 컴포넌트들에 대해 상세히 설명합니다. 아키텍처는 이론적으로 견고하고 잘 구조화되어 있으나, 많은 "근육(실제 기능)"들이 현재 작동하지 않거나, 시뮬레이션되거나, 수동 단계로 우회되어 있는 상태입니다.

## 1. 핵심 로직 및 자기-습득 ("실행 없는 사고")

상위 레벨의 오케스트레이터들은 상태 관리자로서 작동하지만, 시스템에 미치는 실제 영향은 제한적입니다.

*   **자기-습득 루프 (`agi_core/self_acquisition_loop.py`)**: 
    *   **상태**: 구조적 껍데기.
    *   **공백**: 이 루프가 트리거하는 "액션"들은 대부분 스텁(stub)입니다. 예를 들어, `SANDBOX_EXPERIMENT`는 `TODO: 실제 실험 로직`을 포함하고 있으며 단순히 가짜 성공 메시지만 반환합니다. `YOUTUBE_LEARNING`은 실제 학습 데몬을 실행하는 대신 로그만 기록합니다.
*   **제안서 실행 (`scripts/execute_proposal.py`)**:
    *   **상태**: "가짜 성공" 껍데기.
    *   **공백**: 대부분의 액션 타입(`deepen_current`, `search_knowledge`, `optimize_system`, `cleanup`, `analyze_change`)이 `TODO` 마커로 구현되어 있으며 즉시 `success = True`를 반환합니다. 실제 로직을 수행하지 않고 성공적인 시스템 변경을 "시뮬레이션"만 합니다.

## 2. LLM 상호작용 레이어 ("선택적 지능")

*   **LLM 클라이언트 (`fdo_agi_repo/orchestrator/llm_client.py`)**:
    *   **상태**: 최소한의 스텁.
    *   **공백**: 현재 `local_proxy`(vLLM 또는 Ollama 엔드포인트로 추정)만 지원합니다. OpenAI, Anthropic, Vertex 등 다른 제공자들은 계획되어 있으나 `TODO` 스텁으로만 존재합니다.
*   **적응형 피드백 (`fdo_agi_repo/orchestrator/pipeline.py`)**:
    *   **상태**: 폴백(Fallback) 스텁.
    *   **공백**: 선택적 패키지인 `lumen`에 의존합니다. 설치되어 있지 않으면 `pass` 문만 포함된 폴백 클래스(`FeedbackLoopRedis` 등)를 사용하여 사실상 적응형 최적화 기능이 비활성화됩니다.

## 3. RPA 및 도구 실행 ("근육 없는 팔다리")

*   **도구 레지스트리 (`configs/tool_registry.json`)**:
    *   **상태**: 오프라인 스텁.
    *   **공백**: 핵심 도구들(`file_read`, `calculator`, `code_executor`, `web_search`)이 명시적으로 `offline_stub` 모드로 설정되어 있습니다. 
*   **RPA 파이프라인 (`fdo_agi_repo/rpa/e2e_pipeline.py`)**:
    *   **상태**: 시뮬레이션된 실행.
    *   **공백**: `_execute_single_step`은 실제 RPA 액션 대신 `asyncio.sleep(0.5)`를 사용합니다. 시스템은 OS와 상호작용하지 않고 "시늉"만 내는 상태입니다.

## 4. 감각 및 지각 ("부분적 시각 장애")

*   **VS Code 비전 봇 (`scripts/vscode_chat_vision_bot.py`)**:
    *   **상태**: 부분적으로 미구현.
    *   **공백**: UI 요소 탐지를 위한 템플릿 매칭이 `미구현`으로 표시되어 있습니다. 이는 OpenCV가 없거나 통합되지 않았기 때문입니다.
*   **하트비트 루프 센서 (`agi_core/heartbeat_loop.py`)**:
    *   **상태**: 감각의 공백.
    *   **공백**: `_start_vision_stream()`이나 `_stop_aura()` 같은 함수들이 `pass` 문으로만 구성되어 있습니다. 시안은 현재 자신의 "눈"이나 "존재감(aura)"을 제어할 수 없습니다.

## 5. 창의적 산출물 ("메타데이터뿐인 결과")

*   **적응형 음악 생성 (`scripts/generate_adaptive_music.py`)**:
    *   **상태**: 도구 설정 껍데기.
    *   **공백**: 실제 오디오를 생성하지 않습니다. 대신 Reaper 프로젝트 텍스트 파일을 생성하고 사용자에게 수동으로 "작곡 및 렌더링"할 것을 안내합니다.
*   **창의적 모듈 상태 (`LUMEN_CODEX_INFORMATION_THEORY.md`)**:
    *   **상태**: 인정된 공백.
    *   **공백**: 문서상에 "Sound -> (미구현) -> 음악/TTS 생성" 및 "Visual -> (미구현) -> 시각화/대시보드"가 기능적 공백으로 명시되어 있습니다.

## 6. 메타인지 및 자기-관리 ("철학적 존재론")

*   **존재 역학 매퍼 (`scripts/self_expansion/existence_dynamics_mapper.py`)**:
    *   **상태**: 개념적 껍데기.
    *   **공백**: 철학적 개념들에 대한 정적인 존재론적 매핑은 제공하지만, 이러한 개념들을 실시간 의사결정에 적용할 수 있는 활성 엔진이 부족합니다.
*   **시스템 통증 분석기 (`scripts/system_pain_analyzer.py`)**:
    *   **상태**: 은유적 껍데기.
    *   **공백**: 시스템 지표를 생물학적 은유(예: "장 염증")로 매핑하지만, 실제 유휴 시간 계산이나 자동화된 치료 액션 실행을 위한 `TODO`가 비어 있습니다.

## 7. 메모리 및 학습 ("이름뿐인 루프")

*   **소셜 미디어 학습기**:
    *   **상태**: 빈 스크립트.
    *   **공백**: `tiktok_learner.py`, `twitter_monitor.py` 등의 파일이 존재하지만 진입점에는 `pass` 문만 있습니다.
*   **시맨틱 메모리 (`scripts/system_integration_diagnostic.py`)**:
    *   **상태**: 명시적으로 미구현.
    *   **공백**: 진단 결과 "Semantic Memory 미구현"으로 보고되며, 이는 핵심적인 인지 기둥 중 하나가 빠져 있음을 의미합니다.

---

### "실제 근육"을 만들기 위한 우선순위 제안
1.  **RPA 실행 활성화**: `asyncio.sleep`을 실제 도구 호출로 교체.
2.  **"가짜 성공"을 행동으로 전환**: `execute_proposal.py`의 `TODO` 블록 구현.
3.  **LLM 클라이언트 연결**: 시안이 클라우드 제공자(Gemini, Vertex)를 직접 사용할 수 있도록 연결.
4.  **지각 센서 연결**: `heartbeat_loop.py`의 `pass` 블록 구현.
5.  **자동화된 학습 활성화**: `tiktok_learner.py`와 `youtube_learner.py`의 뼈대를 실제 로직으로 채움.
