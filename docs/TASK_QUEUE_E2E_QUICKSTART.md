# Task Queue E2E Quickstart

본 문서는 로컬 Task Queue Server(8091)와 RPA Worker의 엔드투엔드 경로를 빠르게 검증하는 방법을 제공합니다.

## 준비 상태 확인

- 서버 헬스
  - curl <http://127.0.0.1:8091/api/health> → {"status":"ok", ...}
- 워커 폴링
  - outputs/rpa_worker_debug.log.err 에서 /api/tasks/next 200 반복 확인

## Ping 태스크 테스트

- 생성
  - PowerShell: `scripts/enqueue_test_task.ps1 -Server http://127.0.0.1:8091 -Type ping -DataJson "{}"`
- 결과 확인
  - curl <http://127.0.0.1:8091/api/results> → success:true, data.message:pong

## RPA(wait) 태스크 테스트(무해)

- 생성
  - PowerShell: `scripts/enqueue_rpa_task.ps1 -Server http://127.0.0.1:8091 -Action wait`
- 결과 확인
  - curl <http://127.0.0.1:8091/api/results> → success:true, data.slept≈1.0, data.execution_time≈1.0

## RPA 스모크 시나리오(권장)

- 구성: wait(0.5s) → screenshot → [선택] ocr
- 실행
  - 기본: `scripts/enqueue_rpa_smoke.ps1 -Server http://127.0.0.1:8091`
  - 자동 검증 포함: `scripts/enqueue_rpa_smoke.ps1 -Verify`
    - 자동 검증 포함: `scripts/enqueue_rpa_smoke.ps1 -Verify`
      - 기본은 비엄격(Strict 미사용): wait 결과가 누락되어도 screenshot이 성공하면 경고로 통과
      - 엄격 검증: `-Strict` 추가 시 wait/screenshot 모두 확인되지 않으면 실패 처리
      - 지연 흡수: `-GraceWaitSec 3` 기본값으로 wait 결과가 늦게 올 때 한 번 더 재확인
  - OCR까지 포함: `scripts/enqueue_rpa_smoke.ps1 -IncludeOcr -OcrEngine tesseract`
- 확인
  - 최근 결과 요약: `scripts/show_latest_results.ps1 -Server http://127.0.0.1:8091 -Count 5 -SuccessOnly`
  - 실패만 보기: `scripts/show_latest_results.ps1 -FailedOnly`
  - 문자열 필터: `scripts/show_latest_results.ps1 -Filter screenshot`
  - 파일로 저장: `scripts/show_latest_results.ps1 -OutJson outputs/latest_results.json`
  - 최신 스크린샷 열기: `scripts/open_latest_screenshot.ps1`
    - 스냅샷 저장(타임스탬프): `scripts/save_results_snapshot.ps1 -Count 20 -SuccessOnly`

### VS Code 태스크 원클릭 실행

- Queue: Quick E2E (Verify → Results → Open Screenshot)
  - 순서: Smoke Verify → Latest Results (Success 5) → Open Latest Screenshot
  - 실행: VS Code Command Palette → "Tasks: Run Task" → 해당 태스크 선택
  
#### 안정성 보강 체인

- Queue: Quick E2E (Ensure Server)
  - 순서: Task Queue Server (Fresh) → Quick E2E (Verify → Results → Open Screenshot)
- Queue: Quick E2E (Ensure Server+Worker)
  - 순서: Task Queue Server (Fresh) → Queue: Ensure Worker → Quick E2E (Verify → Results → Open Screenshot)
- Queue: Save Results Snapshot (Ensure Server)
  - 순서: Task Queue Server (Fresh) → Save Results Snapshot

#### 워커 관리

- Queue: Ensure Single Worker — 중복 워커 정리(최대 1개 유지)
  - DryRun으로 예정 동작 확인 가능: Queue: Ensure Single Worker (DryRun)
- Queue: Kill All Workers (DryRun) — 모든 워커 종료(안전 확인용)

#### 결과 로그(JSONL)

- Queue: Results → JSONL Append (Success 5) — 최근 성공 5건을 outputs/results_log.jsonl에 누적 기록
- Queue: Open Results Log (JSONL)

참고: 워커 보장은 `scripts/ensure_rpa_worker.ps1`가 담당합니다. 프로세스 목록에서 `rpa_worker.py`가 없으면 자동으로 백그라운드 기동합니다.

## 참고

- 서버 파일: LLM_Unified/ion-mentoring/task_queue_server.py
- 워커 파일: fdo_agi_repo/integrations/rpa_worker.py
- 큐가 비어있으면 /api/tasks/next는 {"task": null}을 반환합니다(워커 구현에서 처리됨).
- 헬스 요약: `scripts/queue_health_check.ps1 -Server http://127.0.0.1:8091`
- 최근 결과: `scripts/show_latest_results.ps1 -Server http://127.0.0.1:8091 -Count 5 -SuccessOnly`
