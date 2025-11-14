# ChatGPT ↔ VS Code Bridge 빠른 시작 가이드

## 📌 개요

Lua 스크립트에서 자연어 요청을 보내면 ChatGPT가 **실제 VS Code 태스크를 실행**하고 결과를 반환하는 브리지 시스템입니다.

---

## 🚀 빠른 시작 (3단계)

### 1️⃣ 모니터 시작

```powershell
cd C:\workspace\agi\scripts
.\send_to_chatgpt_lua.ps1 -Monitor
```

- 백그라운드에서 `outputs/chatgpt_bridge` 폴더의 `request_*.json` 파일 감시
- 새 요청 파일 발견 시 자동으로 ChatGPT에 전송 및 응답 처리

### 2️⃣ Lua에서 요청 보내기

```lua
-- Lua 스크립트 예시
local utils = require("agi_lua_utils")
local response = utils.send_to_chatgpt({
    action = "run_task",
    task_label = "Lumen: Quick Health Probe",
    context = "시스템 상태 확인 필요"
})

if response.success then
    print("Task completed: " .. response.output)
else
    print("Failed: " .. response.error)
end
```

### 3️⃣ 결과 확인

- **성공**: `outputs/chatgpt_bridge/response_<id>.json`
  - `success: true`
  - `output`: 태스크 실행 결과 (터미널 출력)
- **실패**: `error` 메시지 포함

---

## 🛠️ 주요 기능

### A. 모니터 모드 (권장)

```powershell
.\send_to_chatgpt_lua.ps1 -Monitor -IntervalSeconds 2
```

- 지속적으로 새 요청 감시 (기본 5초 간격)
- Ctrl+C로 종료

### B. 일회성 처리

```powershell
.\send_to_chatgpt_lua.ps1 -ProcessOnce
```

- 현재 대기 중인 요청 1개만 처리 후 종료

### C. 샘플 요청 생성

```powershell
.\send_to_chatgpt_lua.ps1 -GenerateSample -SampleAction "run_task"
```

- 테스트용 샘플 요청 파일 생성 (`sample_request_*.json`)
- Lua 개발 시 참고용

---

## 📋 요청 JSON 형식

```json
{
  "id": "req_20251113_123456",
  "timestamp": "2025-11-13T12:34:56Z",
  "action": "run_task",
  "task_label": "System: Health Check (Quick)",
  "context": "배포 전 시스템 상태 확인",
  "hmac": "sha256_signature_here"
}
```

### 필수 필드

- `id`: 고유 요청 ID (예: `req_20251113_123456`)
- `action`: 작업 유형 (현재 `run_task`만 지원)
- `task_label`: 실행할 VS Code 태스크 라벨
- `hmac`: 보안 서명 (HMAC-SHA256)

### 선택 필드

- `context`: 추가 컨텍스트 정보

---

## 🔐 보안 (HMAC 검증)

### 환경 변수 설정

```powershell
# 사용자 환경 변수 설정 (영구)
[Environment]::SetEnvironmentVariable("CHATGPT_BRIDGE_HMAC_KEY", "your-secret-key-here", "User")
```

### Lua에서 HMAC 생성

```lua
local crypto = require("crypto")
local json_str = '{"id":"req_123","action":"run_task",...}'
local hmac = crypto.hmac.digest("sha256", json_str, secret_key)
```

**중요**: HMAC 검증 실패 시 요청은 거부됩니다 (권한 없음).

---

## 📂 파일 구조

```
C:\workspace\agi\outputs\chatgpt_bridge\
├── request_20251113_123456.json      # Lua가 생성한 요청
├── response_20251113_123456.json     # PS1이 반환한 응답
├── sample_request_run_task.json      # 샘플 (테스트용)
└── processed_20251113_123456.json    # 처리 완료 (아카이브)
```

---

## 🔧 고급 옵션

### 커스텀 브리지 폴더

```powershell
.\send_to_chatgpt_lua.ps1 -Monitor -BridgeFolder "D:\custom\bridge"
```

### 디버그 모드

```powershell
.\send_to_chatgpt_lua.ps1 -Monitor -Verbose
```

- 상세 로그 출력 (요청/응답 JSON, HMAC 검증 과정)

### 타임아웃 설정

```powershell
.\send_to_chatgpt_lua.ps1 -ProcessOnce -TimeoutSeconds 60
```

- 태스크 실행 타임아웃 (기본 30초)

---

## 🐛 트러블슈팅

### 1. "HMAC verification failed"

- 환경 변수 `CHATGPT_BRIDGE_HMAC_KEY` 확인
- Lua와 PowerShell이 동일한 키 사용하는지 확인

### 2. "Task not found"

- VS Code `tasks.json`에 해당 라벨이 존재하는지 확인
- 대소문자 정확히 일치해야 함

### 3. 응답 파일이 생성되지 않음

- 모니터가 실행 중인지 확인 (`Get-Process -Name pwsh | Where {$_.CommandLine -like '*send_to_chatgpt*'}`)
- 로그 확인: `outputs/chatgpt_bridge/bridge_monitor.log`

### 4. 태스크 실행 중 에러

- VS Code에서 수동으로 해당 태스크 실행해보기
- 터미널 권한 문제 (일부 태스크는 관리자 권한 필요)

---

## 📖 예제 시나리오

### 시나리오 1: Lua 스크립트에서 시스템 상태 확인

```lua
local response = utils.send_to_chatgpt({
    action = "run_task",
    task_label = "System: Core Processes (JSON)"
})
if response.success then
    local status = json.decode(response.output)
    print("CPU: " .. status.cpu .. "%")
end
```

### 시나리오 2: 자동화된 건강 체크 루프

```lua
while true do
    local health = utils.send_to_chatgpt({
        action = "run_task",
        task_label = "Lumen: Quick Health Probe"
    })
    if not health.success then
        print("[ALERT] Health check failed!")
    end
    os.execute("sleep 300")  -- 5분 대기
end
```

### 시나리오 3: 조건부 태스크 실행

```lua
local queue_status = utils.send_to_chatgpt({
    action = "run_task",
    task_label = "Queue: Health Check"
})

if queue_status.success and queue_status.output:match("degraded") then
    -- 큐가 degraded 상태면 워커 재시작
    utils.send_to_chatgpt({
        action = "run_task",
        task_label = "Queue: Ensure Single Worker"
    })
end
```

---

## 🎯 다음 단계

1. **Lua 유틸리티 확장**: `agi_lua_utils.lua`에 더 많은 헬퍼 함수 추가
2. **응답 캐싱**: 동일 요청 반복 시 캐시 활용
3. **WebSocket 통신**: JSON 파일 대신 실시간 통신 고려
4. **권한 레벨**: 태스크별 실행 권한 세분화

---

## 📚 관련 문서

- [전체 시스템 가이드](./CHATGPT_VSCODE_BRIDGE_USAGE_GUIDE.md)
- [아키텍처 설계](./CHATGPT_VSCODE_BRIDGE_COMPLETE.md)
- [보안 가이드](./SECURITY_HMAC_GUIDE.md) *(작성 예정)*

---

**마지막 업데이트**: 2025-11-13  
**버전**: 1.0.0  
**상태**: ✅ Production Ready
