# ChatGPT Lua Bridge - Quick Start Guide

## 🎯 개요

Lua 스크립트에서 ChatGPT API를 호출하고 응답을 받을 수 있는 브릿지 시스템입니다.

## 🚀 빠른 시작

### 1. 기본 사용법 (PowerShell)

```powershell
# 단일 요청 처리 (테스트용)
.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce

# 백그라운드 모니터링 시작 (프로덕션)
.\scripts\send_to_chatgpt_lua.ps1 -Monitor -IntervalSeconds 5

# 샘플 요청 생성 (테스트용)
.\scripts\send_to_chatgpt_lua.ps1 -GenerateSample
```

### 2. Lua 스크립트에서 사용

```lua
local request = {
    prompt = "Tell me a joke about programming",
    timestamp = os.time(),
    request_id = "lua_request_" .. os.time()
}

local json = require("cjson")
local file = io.open("C:/workspace/agi/outputs/lua_requests/request_" .. os.time() .. ".json", "w")
file:write(json.encode(request))
file:close()

os.execute("sleep 2")

local response_file = io.open("C:/workspace/agi/outputs/trinity_responses/response_" .. request.request_id .. ".json", "r")
if response_file then
    local response = json.decode(response_file:read("*all"))
    print("Response: " .. response.response)
    response_file:close()
end
```

## 📂 디렉토리 구조

## Optional: HMAC signing

outputs/chatgpt_bridge/
├── pending/          # Lua가 요청을 여기에 생성
├── processed/        # 처리된 요청 (아카이브)
├── responses/        # ChatGPT 응답 (Lua가 여기서 읽음)
└── errors/           # 실패한 요청 (디버깅용)

```

## 🔐 보안

### HMAC 검증 활성화

```powershell
# 비밀키 설정 (환경변수)
$env:CHATGPT_BRIDGE_SECRET = "your-secret-key-here"

# HMAC 검증 활성화로 실행
.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce -RequireHmac
```

### Lua에서 HMAC 서명 생성

```lua
local crypto = require("crypto")
local secret = "your-secret-key-here"
local message = json.encode(request)
request.hmac = crypto.hmac.digest("sha256", message, secret, true)
```

## 📊 모니터링

### VS Code 태스크로 시작

```json
// .vscode/tasks.json에 추가
{
    "label": "ChatGPT Bridge: Start Monitor",
    "type": "shell",
    "command": "powershell",
    "args": ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
             "${workspaceFolder}/scripts/send_to_chatgpt_lua.ps1",
             "-Monitor", "-IntervalSeconds", "5"],
    "isBackground": true,
    "group": "build"
}
```

### 상태 확인

```powershell
# 최근 처리된 요청 확인
Get-ChildItem "C:\workspace\agi\outputs\chatgpt_bridge\processed" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 5

# 에러 로그 확인
Get-ChildItem "C:\workspace\agi\outputs\chatgpt_bridge\errors" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1 | 
    Get-Content
```

## 🛠️ 고급 사용법

### 타임아웃 설정

```powershell
# 30초 타임아웃으로 실행
.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce -TimeoutSeconds 30
```

### 커스텀 디렉토리

```powershell
# 다른 브릿지 디렉토리 사용
.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce -BridgeDir "C:\custom\path"
```

### 상세 로깅

# Verbose 모드로 실행

.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce -Verbose

```

## 🧪 테스트

### End-to-End 테스트

```powershell
# 1. 샘플 요청 생성
.\scripts\send_to_chatgpt_lua.ps1 -GenerateSample

# 2. 요청 처리
.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce

# 3. 결과 확인
$response = Get-Content "C:\workspace\agi\outputs\chatgpt_bridge\responses\*.json" -Raw | ConvertFrom-Json
Write-Host "Response: $($response.response)"
```

### 성능 테스트

```powershell
# 10개 요청 동시 처리
1..10 | ForEach-Object {
    .\scripts\send_to_chatgpt_lua.ps1 -GenerateSample
}
.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce
```

### 요청이 처리되지 않을 때

1. **pending 디렉토리 확인**

   ```powershell
   Get-ChildItem "C:\workspace\agi\outputs\chatgpt_bridge\pending"
   ```

2. **에러 로그 확인**

   ```powershell
   Get-Content "C:\workspace\agi\outputs\chatgpt_bridge\errors\*.json" -Raw
   ```

3. **브릿지 스크립트 수동 실행**

   ```powershell

### HMAC 검증 실패

- 비밀키가 Lua와 PowerShell에서 동일한지 확인
- 메시지 인코딩(UTF-8)이 일치하는지 확인
- 타임스탬프가 너무 오래되지 않았는지 확인 (기본 300초)

### 응답이 느릴 때

- ChatGPT API 상태 확인
- 타임아웃 설정 증가: `-TimeoutSeconds 60`
- 네트워크 연결 확인

## 📈 성능 최적화

### 백그라운드 모니터 설정

```powershell
# 낮은 CPU 사용률로 실행
.\scripts\send_to_chatgpt_lua.ps1 -Monitor -IntervalSeconds 10

# 빠른 응답이 필요할 때
.\scripts\send_to_chatgpt_lua.ps1 -Monitor -IntervalSeconds 2
```

### 파일 정리

```powershell
# 오래된 처리된 요청 정리 (7일 이상)
Get-ChildItem "C:\workspace\agi\outputs\chatgpt_bridge\processed" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } |
    Remove-Item -Force
```

## 🔗 통합 예제

### Reaper Lua 스크립트와 통합

```lua
-- reaper_chatgpt_helper.lua
local bridge_dir = "C:/workspace/agi/outputs/chatgpt_bridge"

function send_to_chatgpt(prompt)
    local request = {
        prompt = prompt,
        timestamp = os.time(),
        request_id = "reaper_" .. reaper.time_precise()
    }
    
    local json = require("cjson")
    local filename = bridge_dir .. "/pending/request_" .. request.request_id .. ".json"
    local file = io.open(filename, "w")
    file:write(json.encode(request))
    file:close()
    
    return request.request_id
end

function get_response(request_id)
    local filename = bridge_dir .. "/responses/response_" .. request_id .. ".json"
    local file = io.open(filename, "r")
    if file then
        local json = require("cjson")
        local response = json.decode(file:read("*all"))
        file:close()
        return response.response
    end
    return nil
end

-- 사용 예
local req_id = send_to_chatgpt("Generate a chord progression in C major")
reaper.defer(function()
    local response = get_response(req_id)
    if response then
        reaper.ShowConsoleMsg("ChatGPT: " .. response .. "\n")
    end
end)
```

## 🎓 다음 단계

1. **Reaper 통합**: `reaper_chatgpt_bridge.lua` 스크립트 생성
2. **캐싱 추가**: 동일 요청에 대한 캐시 레이어 구현
3. **웹훅 지원**: HTTP 엔드포인트 추가로 외부 연동
4. **배치 처리**: 여러 요청을 한 번에 처리하는 최적화

## 📞 문의 및 지원

- 이슈 리포트: GitHub Issues
- 문서: `docs/CHATGPT_BRIDGE_ARCHITECTURE.md`
- 예제: `examples/chatgpt_bridge/`

---

**마지막 업데이트**: 2025-11-13
**버전**: 1.0.0
**작성자**: AGI System
