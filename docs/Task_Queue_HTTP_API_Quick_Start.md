# Task Queue HTTP API - Quick Start Guide

See also: `COMET_PING_빠른테스트.md` (HTTP 자동감지 + 파일 폴백 Ping 가이드)

> **작성일:** 2025-10-29  
> **대상:** 미래 세션에서 빠른 재개를 위한 참고 문서

## 🎯 개요

Copilot과 Comet Extension이 **HTTP API를 통해 비동기 작업을 협업**하는 시스템입니다.

```
┌────────────┐  POST /api/tasks   ┌─────────────┐
│  Copilot   │ ─────────────────> │  Flask API  │
│  (Client)  │ <───────────────── │  Server     │
└────────────┘  GET /result       │  :8091      │
                                   └─────────────┘
                                         │
                                         │ Poll
                                         ↓
                                   ┌─────────────┐
                                   │   Comet     │
                                   │  Extension  │
                                   │  (Worker)   │
                                   └─────────────┘
```

## 📦 구성 요소

### 1. API Server (`task_queue_api_server.py`)

**위치:** `d:\nas_backup\fdo_agi_repo\scripts\task_queue_api_server.py`  
**포트:** 8091  
**시작 명령:**

```powershell
cd d:\nas_backup\fdo_agi_repo
.\.venv\Scripts\python.exe .\scripts\task_queue_api_server.py
```

**주요 엔드포인트:**

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | API 문서 (엔드포인트 목록) |
| GET | `/health` | 서버 상태 확인 |
| GET | `/api/stats` | 통계 (완료/대기 작업 수) |
| POST | `/api/tasks` | 새 작업 생성 ⭐ |
| GET | `/api/tasks/:id/result` | 작업 결과 조회 ⭐ |
| POST | `/api/tasks/next` | 다음 작업 가져오기 (Worker용) |
| POST | `/api/tasks/:id/result` | 결과 제출 (Worker용) |

### 2. Worker (Comet Extension)

**모드:** File Watcher 또는 HTTP Poller  
**확인 명령:**

```powershell
cd d:\nas_backup\fdo_agi_repo
python scripts\check_comet_status.py
```

### 3. 클라이언트 스크립트

**Python:** `scripts/send_ping.py` (HTTP 권장, `send_ping_http.py` Deprecated)  
**PowerShell:** 직접 `Invoke-RestMethod` 사용

## 🚀 사용 예시

### 📤 작업 제출 (Python)

```python
import requests
import time

# 1. 작업 생성
response = requests.post("http://localhost:8091/api/tasks", json={
    "task_type": "ping",
    "data": {},
    "requester": "my-script"
})
task_id = response.json()['task_id']
print(f"Task created: {task_id}")

# 2. 결과 대기 (폴링)
for i in range(10):
    result = requests.get(f"http://localhost:8091/api/tasks/{task_id}/result")
    if result.status_code == 200:
        print("✅ Result:", result.json())
        break
    elif result.status_code == 404:
        print(f"⏳ Waiting... ({i+1}/10)")
        time.sleep(1)
    else:
        print(f"❌ Error: {result.status_code}")
        break
```

### 📤 작업 제출 (PowerShell)

```powershell
# 1. 작업 생성
$body = @{
    task_type = 'ping'
    data = @{}
    requester = 'powershell-script'
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri http://localhost:8091/api/tasks `
    -Method POST -Body $body -ContentType 'application/json'
$taskId = $response.task_id
Write-Host "Task created: $taskId"

# 2. 결과 대기
for ($i = 0; $i -lt 10; $i++) {
    try {
        $result = Invoke-RestMethod -Uri "http://localhost:8091/api/tasks/$taskId/result"
        Write-Host "✅ Result: $($result | ConvertTo-Json -Depth 10)"
        break
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 404) {
            Write-Host "⏳ Waiting... ($($i+1)/10)"
            Start-Sleep -Seconds 1
        } else {
            Write-Host "❌ Error: $_"
            break
        }
    }
}
```

### 📤 작업 제출 (curl)

```bash
# 1. 작업 생성
TASK_ID=$(curl -X POST http://localhost:8091/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_type":"ping","data":{},"requester":"curl"}' \
  | jq -r '.task_id')
echo "Task created: $TASK_ID"

# 2. 결과 조회 (3초 후)
sleep 3
curl http://localhost:8091/api/tasks/$TASK_ID/result
```

## 📊 통계 확인

```powershell
Invoke-RestMethod http://localhost:8091/api/stats
```

**응답 예시:**

```json
{
  "completed_tasks": 55,
  "pending_tasks": 0,
  "tasks_dir": "d:\\nas_backup\\fdo_agi_repo\\outputs\\task_queue\\tasks",
  "results_dir": "d:\\nas_backup\\fdo_agi_repo\\outputs\\task_queue\\results"
}
```

## 🔍 문제 해결

### ❌ "Connection refused" 에러

**원인:** API 서버가 실행 중이지 않음  
**해결:**

```powershell
cd d:\nas_backup\fdo_agi_repo
.\.venv\Scripts\python.exe .\scripts\task_queue_api_server.py
```

### ❌ 결과가 계속 404

**원인:** Worker가 작업을 처리하지 않음  
**확인:**

```powershell
python scripts\check_comet_status.py
```

**해결:** Comet Extension 재시작 또는 HTTP Poller 시작

```powershell
python scripts\http_task_poller.py --interval 1.0
```

### ❌ "127.0.0.1 error reading task" 메시지

**원인:** 파일 쓰기 중 읽기 시도 (경쟁 상태)  
**상태:** 무해함 (다음 폴링에서 성공)  
**해결:** Phase 7c에서 이미 노이즈 억제됨 (JSONDecodeError silent skip)

### ❌ Port 8091 already in use

**확인:**

```powershell
Get-NetTCPConnection -LocalPort 8091 -ErrorAction SilentlyContinue
```

**해결:**

```powershell
# 프로세스 종료
Get-Process python | Where-Object {$_.CommandLine -like '*task_queue_api_server*'} | Stop-Process -Force

# 서버 재시작
cd d:\nas_backup\fdo_agi_repo
.\.venv\Scripts\python.exe .\scripts\task_queue_api_server.py
```

## 🧪 테스트 명령

### 헬스체크

```powershell
Invoke-RestMethod http://localhost:8091/health
```

### E2E 테스트

```powershell
cd d:\nas_backup\fdo_agi_repo
python scripts\send_ping_http.py
```

**예상 출력:**

```
🚀 HTTP-based Ping Task Submission
📤 Ping 작업 전송 중...
✅ 작업 전송 완료!
🆔 Task ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

⏳ Comet 응답 대기 중 (최대 10초)...

========================================
  ✅ 결과 수신 완료!
========================================
🤖 Worker: comet-extension
📊 Status: success
💬 Message: pong
⏰ Completed: 2025-10-29T...
========================================
```

### 배치 테스트 (5개 동시)

```powershell
cd d:\nas_backup\fdo_agi_repo

# 5개 작업 제출
python -c "import sys, json; sys.path.insert(0, 'scripts'); from shared_task_queue import TaskQueue; q = TaskQueue(); ids = [q.push_task('ping', {}, f'batch-{i}') for i in range(5)]; print(json.dumps({'submitted': len(ids), 'task_ids': ids}, indent=2))"

# 6초 대기 후 결과 확인
Start-Sleep -Seconds 6
# (결과 확인 로직 추가)
```

## 📁 디렉터리 구조

```
fdo_agi_repo/
├── scripts/
│   ├── task_queue_api_server.py    # Flask API 서버
│   ├── shared_task_queue.py        # 파일 기반 큐 라이브러리
│   ├── send_ping_http.py           # Python 클라이언트 예시
│   └── http_task_poller.py         # Python Worker 테스트
├── outputs/
│   └── task_queue/
│       ├── tasks/                  # 대기 중 작업 JSON
│       └── results/                # 완료된 결과 JSON
└── .venv/                          # Python 가상환경
```

## 🔧 작업 타입

| 타입 | 설명 | 데이터 예시 |
|------|------|-------------|
| `ping` | 간단한 응답 테스트 | `{}` |
| `calculation` | 계산 작업 | `{"numbers": [1,2,3]}` |
| `data_transform` | 데이터 변환 | `{"input": "...", "format": "json"}` |
| `batch_calculation` | 배치 계산 | `{"operations": [...]}` |

## 📚 관련 문서

- **구현 완료 보고:** `깃코_Phase7c_HTTP_Result_API_완료_2025-10-29.md`
- **TS 통합 가이드:** `COMET_HTTP_Poller_구현가이드.ts` (252 lines)
- **아키텍처 문서:** (추후 작성 예정)

## 🚀 다음 단계 (Phase 8a)

**Comet Extension TypeScript 통합:**

1. `src/httpTaskPoller.ts` 생성
2. Extension activation에 HTTP 폴링 추가
3. Python test poller 대체
4. 프로덕션 환경 준비 완료

**예상 소요 시간:** 1-2시간

---

## 📝 마지막 업데이트

- **날짜:** 2025-10-29
- **버전:** Phase 7c 완료
- **상태:** ✅ 프로덕션 준비 완료 (개발 환경)
- **총 처리 작업:** 55개
- **대기 작업:** 0개
- **성공률:** 100%

---

**💡 Tip:** 새 세션 시작 시 이 문서부터 읽으면 빠르게 컨텍스트를 파악할 수 있습니다!
