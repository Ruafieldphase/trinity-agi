# Windows 비정상 재부팅 대비: 자동 복구(Resume) 구조 가이드

이 워크스페이스는 비정상 재부팅 이후에도 작업을 자동으로 복원하고 이어갈 수 있도록 다음 구성요소로 설계되어 있습니다.

## 구성 요소

- Master Orchestrator (`scripts/master_orchestrator.ps1`)
  - 부팅/로그온 직후 핵심 프로세스 일괄 보장: Task Queue Server(8091), RPA Worker, Monitoring Daemon, Watchdog, 상태 대시보드 생성 등
  - VS Code Task: "?? Master: Register Auto-Start (Boot)"
- Auto Resume (`scripts/auto_resume_on_startup.ps1`, `scripts/register_auto_resume.ps1`)
  - 사용자 로그인 시 세션 연속성 복원, 최소 작업 재개 지원
  - VS Code Task: "?뵩 AGI: Register Auto Resume (Permanent)"
- Session Continuity Restore (`scripts/session_continuity_restore.ps1`)
  - 최근 세션 스냅샷/리듬 리포트/Goal Tracker 로드, Copilot 컨텍스트 요약 생성
  - VS Code Task: "📖 Session: Restore + Open Report" 또는 폴더 오픈 시 자동 실행
- Post-Reboot Verify (`scripts/post_reboot_verify.ps1`)
  - 재부팅 직후 자가 점검 + 자동 복구 체인 실행 (Queue/Worker/Watchdog/대시보드)
  - 결과 요약: `outputs/post_reboot_verify_summary.json`, `outputs/session_continuity_latest.md`
- Watchdog (`fdo_agi_repo/scripts/task_watchdog.py`)
  - 핵심 서비스 헬스 체크 및 자동 재구동

## 권장 설정 (1회)

1. 마스터 오케스트레이터 자동 시작 등록
   - VS Code Task: "?? Master: Register Auto-Start (Boot)"
2. 자동 재개(Auto Resume) 등록
   - VS Code Task: "?뵩 AGI: Register Auto Resume (Permanent)"
3. (선택) 모니터링 유지 보수/스냅샷 회전 등 보조 작업 스케줄 등록
   - 예: Monitoring Collector, Snapshot Rotation, Daily Maintenance

모든 등록이 실패할 경우 스크립트는 사용자 범위(HKCU) Run 키로 폴백해 다음 로그인 시점에 자동 시작합니다.

## 재부팅 후 확인 절차

- VS Code 없이도 가능: PowerShell
  - `scripts/post_reboot_verify.ps1 -AutoFix -StartWatchdog -OpenReport`
  - 주요 산출물
    - `outputs/post_reboot_verify_summary.json`
    - `outputs/quick_status_latest.json`
    - `outputs/session_continuity_latest.md`

- VS Code 내 손쉬운 확인(태스크)
  - "Queue: Health Check"
  - "Monitoring: Unified Dashboard (AGI + Lumen)"
  - "Watchdog: Check Task Watchdog Status"

## 신규: Resilient Reboot Recovery (one-shot)

재부팅 직후 단일 커맨드로 안전한 복구 체인을 실행하려면 아래 스크립트를 사용할 수 있습니다.

- 스크립트: `scripts/resilient_reboot_recovery.ps1`
- 기본 흐름: (안정화 대기) → Queue 보장(8091) → 단일 Worker 보장 → 세션 복원 → 통합 검증(Post-Reboot Verify)
- 출력: `outputs/resilient_reboot_recovery_summary.json`

예시:

- 드라이런(무해 테스트)
  - `scripts/resilient_reboot_recovery.ps1 -DryRun -Verbose`
- 안정화 대기 90초 + 리포트 자동 오픈 + AutoFix/Watchdog 보장
  - `scripts/resilient_reboot_recovery.ps1 -DelaySeconds 90 -OpenReport -AutoFix -StartWatchdog`

참고: 본 스크립트는 기존 자동화(오케스트레이터/오토-리줌/포스트-리부트 검증)를 재사용하여 실행 순서를 보장합니다. 여러 번 실행해도 안전하도록 재진입성을 고려해 설계되었습니다.

## 문제 발생 시

- `outputs/session_continuity_latest.md`와 `outputs/post_reboot_verify_summary.json`의 오류 메시지를 우선 확인하세요.
- Queue/Worker 이슈 → `scripts/ensure_task_queue_server.ps1`, `scripts/ensure_rpa_worker.ps1`
- Watchdog 미동작 → "Watchdog: Start Task Watchdog (Background)"
- 대시보드 미갱신 → `scripts/quick_status.ps1 -OutJson outputs/quick_status_latest.json`

## 설계 원칙

- 사용자 영역에서 안전하게 동작(관리자 권한 불필요), 실패 시 폴백 경로 제공
- 재진입 안전(idempotent), 비정상 종료/재부팅 후에도 상태 수복
- 모든 산출물과 로그는 `outputs/`에 기록되어 트러블슈팅 용이
