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
