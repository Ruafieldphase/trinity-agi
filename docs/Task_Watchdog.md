# Task Watchdog

자동으로 Task Queue 서버 상태를 점검하고, 무한 루프/소비 중단/서버 다운 상황을 감지합니다. 옵션에 따라 ping 작업을 주입(Self-test)하고 간단한 자동 복구를 시도할 수 있습니다.

## 무엇을 감지하나요?

- server_down: 서버에 응답이 없거나 Health 체크가 일정 시간 이상 실패
- queue_stuck: 큐에 작업이 남아있는데 결과가 증가하지 않음(워커 미소비)
- consumers_not_consuming: Self-test ping을 주입했는데 일정 시간 내 처리되지 않음

## 출력

- `fdo_agi_repo/outputs/watchdog_status_latest.json|md` 최신 상태 리포트
- 타임스탬프 버전의 JSON 스냅샷
- 내부 상태: `fdo_agi_repo/outputs/watchdog_state.json`

## 실행 예시

### 단발(진단 1회)

```powershell
# fdo_agi_repo 가상환경 권장
cd .\fdo_agi_repo
.\.venv\Scripts\python.exe scripts\task_watchdog.py --server http://127.0.0.1:8091 --once --out outputs
```

### 모니터링 루프(5초 주기, Self-test 포함)

```powershell
cd .\fdo_agi_repo
.\.venv\Scripts\python.exe scripts\task_watchdog.py --server http://127.0.0.1:8091 --interval 5 --self-test --out outputs
```

### 자동 복구 시도(서버 다운 시)

```powershell
cd .\fdo_agi_repo
.\.venv\Scripts\python.exe scripts\task_watchdog.py --server http://127.0.0.1:8091 --interval 5 --auto-recover --server-script ..\\..\\LLM_Unified\\ion-mentoring\\task_queue_server.py
```

> 주의: 자동 복구는 베스트에포트로 서버 스크립트를 기동합니다. 운영 환경에서는 VS Code Task("Comet-Gitko: Start Task Queue Server (Background)")와 함께 사용하는 것을 추천합니다.

## 권장 운영 팁

- 모니터링 간격: 5~10초
- queue_stuck 임계값: 30~60초부터 시작, 환경에 맞춰 조정
- Self-test는 문제 발생 시점에만 주입되도록 간격을 길게 설정하거나 필요 시 수동으로 사용
- 상태 파일(JSON/MD)을 대시보드에서 집계하여 경보로 연결할 수 있음

## StallGuard (정보이론 기반 루프/정지 감지)

StallGuard는 최근 활동의 정보량(Shannon entropy)과 압축 가능성, 파일 갱신 신호를 결합하여 시스템이 의미 있는 진전을 내고 있는지 판단합니다. 다음 자산을 기본으로 모니터링합니다:

- `outputs/results_log.jsonl` 실행 결과 로그(있을 경우)
- `fdo_agi_repo/memory/resonance_ledger.jsonl` 레저
- `fdo_agi_repo/outputs/online_learning_log.jsonl` 온라인 러너 로그(있을 경우)
- 헬스 URL: `http://127.0.0.1:8091/api/health`

통합:

- PowerShell 워치독(`scripts/self_healing_watchdog.ps1`) 루프에서 주기적으로 `fdo_agi_repo/monitoring/stall_guard.py`를 호출하여 스톨 여부를 판정하고, 스톨 시 워커 재기동을 우선 시도합니다.

수동 실행:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stall_guard.ps1 -OpenReport
```

판정 기준(기본값):

- 최근 5분(window=300s) 내 파일 갱신 없음(stale)이고, 꼬리(tail) 샘플이 충분(>=64B)이며 저엔트로피/고압축성(low-information)이면 스톨로 분류
- 헬스 URL이 비정상이어도 스톨로 분류

출력:

- `outputs/stall_guard_report.json` JSON 리포트와 표준출력

튜닝 포인트:

- `--window-seconds`, `--min-entropy`, `--min-compression-ratio` 파라미터로 환경별 민감도 조정
