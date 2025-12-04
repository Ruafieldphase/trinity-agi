# Autonomic Nerve Center

조용하고 일관된 백그라운드에서 핵심 모니터/워치독을 통합 관리하는 컴포넌트입니다. 사람이 매번 터미널을 띄우지 않아도 되고, 문제(통증)가 생길 때만 신호를 내고 자동 복구를 시도합니다.

## 무엇을 하나요?

- 큐 서버(8091), RPA 워커 등 필수 리소스의 헬스 체크
- 비정상 탐지시 기존 ensure 스크립트로 자동 기동/정상화 시도
- 상태를 파일로 기록: `outputs/nerve_center_status_latest.{json,md}`
- 필요 시(옵션) 알림 라우팅(`scripts/alert_system.ps1` 연동)

## 시작/정지/상태

```powershell
# 시작 (백그라운드 잡으로)
./scripts/start_nerve_center.ps1 -Interval 5

# 건식 점검(실행 없이 진단만)
python fdo_agi_repo/autonomic/nerve_center.py --once --dry-run

# 상태 확인
./scripts/check_nerve_center_status.ps1

# 정지
./scripts/stop_nerve_center.ps1
```

## 설정(선언적 구성)

- 경로: `config/autonomic_monitors.json`
- 예시:

```json
{
  "interval_sec": 5,
  "resources": [
    {
      "name": "queue_server_8091",
      "health": { "type": "http", "url": "http://127.0.0.1:8091/health", "expect": "ok" },
      "ensure": { "type": "ps1", "path": "scripts/ensure_task_queue_server.ps1", "args": ["-Port","8091"] },
      "processMatch": "task_queue_server.py",
      "singleton": true,
      "required": true
    }
  ]
}
```

## 왜 필요하나요?

- 산발적 터미널/잡 증가를 억제하고, 단일 제어점으로 통합
- 문제가 없으면 조용히 동작(무의식), 문제 시에만 통증 신호(리포트/알림)
- 기존 스크립트(ensure/cleanup/watchdog)와 호환, 복잡성 증가는 최소화

## 참고

- 큐 서버 워치독(`fdo_agi_repo/scripts/task_watchdog.py`) 등 기존 구성 요소는 그대로 유지됩니다. Nerve Center는 "운영 좌장"으로 조율합니다.
