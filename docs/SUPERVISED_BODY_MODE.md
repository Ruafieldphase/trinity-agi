# Supervised Body Mode (Windows) — 감독 하 직접 경험

목표: AGI가 Windows를 “직접 조작”하며 경험을 만들되, 사용자가 즉시 개입(마우스/키보드)하면 자동 중단되는 감독 모드.

## 핵심 개념
- **Arm(무장)**: 사용자 감독 하에만 실행 가능하도록 TTL(만료) 포함.
- **Task(작업)**: 파일로 전달되는 실행 계획.
- **Abort(중단)**: 사용자 입력(마우스/키보드) 발생 또는 stop 파일 존재 시 즉시 중단.

## 파일 인터페이스
- `signals/body_arm.json` : arm 상태(TTL 포함)
- `signals/body_allow_browser.json` : 브라우저 탐색 “지속 허용”(옵트인, TTL 옵션)
- `signals/body_task.json` : 실행할 작업(액션 리스트)
- `signals/body_stop.json` : 즉시 중단 요청

## 실행/정지 (PowerShell)
- Arm(+샘플 task 생성 + 컨트롤러 실행):
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/arm_supervised_body.ps1 -Minutes 30 -WriteSampleTask -RunController`
- 중단:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/stop_supervised_body.ps1`

## “인간 감독 없이 브라우저 탐색” (Read-only, 안전 제한)
- 목적: 비노체가 자리를 비운 동안에도 **탭을 여는 수준의 안전한 탐색 경험**을 자동 생성.
- 제한: 클릭/타이핑/로그인/다운로드 없음(현재 v1은 URL 열기 + 검색 URL 생성만).
- 안전: idle일 때만 제안, 구글/유튜브 allowlist, Scroll Lock 하드 킬스위치(컨트롤러 즉시 중단), `signals/body_stop.json`로 중단 가능.
- 설정 파일: `signals/body_allow_browser.json`
  - 예시:
    - `{"allow": true, "expires_at": 1769000000, "allowed_hours_local": [0, 0]}`
    - (옵션) `max_tasks_per_hour`: 시간당 최대 task(0/미설정이면 리듬 기반)
    - (옵션) `min_cooldown_sec`: 최소 쿨다운(0/미설정이면 리듬 기반)
  - 리듬 기반(정반합) 동작:
    - EXPANSION(확장): 외부 탐색(지도/어스/검색)
    - INTEGRATION(통합): 내부 통합(로컬 outputs 열기 등)
    - CONTRACTION(수축): 안정화(짧은 앰비언스)
    - `suggest_browser_exploration_task.py`가 안전판정 + 낮/밤 + 내부 드라이브에 따라 위상을 순환하며, 고정 “1일 상한” 대신 **리듬 기반 쿨다운/시간당 속도**로 폭주를 방지.

## 출력(관측/리포트)
- `outputs/body_supervised_latest.json` : 최신 1회 실행 리포트
- `outputs/body_supervised_history.jsonl` : 실행 이력(append)
- `outputs/supervised_body_controller.log` : 컨트롤러 표준 로그

## v1 제한(안정성 우선)
- 지원 액션: `open_path`, `open_url(google/youtube allowlist)`, `google_search`, `youtube_search`, `sleep`
- UI 클릭/키 입력/텍스트 입력은 v2에서 단계적으로 추가

## 탐색(Exploration) 인테이크 연결
- `outputs/body_supervised_latest.json`이 `executed`로 끝나면, 컨트롤러가 탐색 세션을 자동 생성:
  - `inputs/intake/exploration/sessions/*_supervised_browser.json`
- 이후 `self_acquire`가 `scripts/self_expansion/exploration_intake.py`를 실행하며:
  - `outputs/exploration_intake_latest.json`에 최신 탐색 세션이 반영됨
