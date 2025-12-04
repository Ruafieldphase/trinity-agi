# ChatGPT Lua Bridge 사용 가이드

## 🎯 개요

**ChatGPT Lua Bridge**는 Lua 스크립트에서 VS Code의 Copilot Chat으로 자동화된 요청을 전송하고 응답을 받을 수 있는 시스템입니다.

---

## 📦 구성 요소

| 파일 | 위치 | 역할 |
|------|------|------|
| `send_to_chatgpt_lua.ps1` | `scripts/` | 메인 브리지 스크립트 |
| 요청 파일 | `outputs/chatgpt_bridge/lua_requests/` | Lua에서 생성한 JSON 요청 |
| 응답 파일 | `outputs/chatgpt_bridge/trinity_responses/` | 처리된 응답 (MD + JSON) |
| 처리 완료 | `outputs/chatgpt_bridge/lua_requests/processed/` | 처리된 요청 보관 |
| 로그 | `outputs/chatgpt_bridge/trinity_logs/` | 처리 로그 |

---

## 🚀 사용법

### 1️⃣ **Lua 스크립트에서 요청 생성**

```lua
local json = require("dkjson")

-- 요청 생성
local request = {
    id = "my_request_001",
    message = "Explain the concept of adaptive rhythm",
    context = {
        source = "Reaper",
        timestamp = os.time()
    }
}

-- JSON 파일 저장
local file = io.open("C:/workspace/agi/outputs/chatgpt_bridge/lua_requests/my_request_001.json", "w")
file:write(json.encode(request, { indent = true }))
file:close()

reaper.ShowConsoleMsg("Request sent to ChatGPT bridge\n")
```

### 2️⃣ **Bridge 실행 (3가지 모드)**

#### A. **ProcessOnce 모드** (단일 실행, 추천)

```powershell
.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce
```

#### B. **Monitor 모드** (지속 감시)

```powershell
.\scripts\send_to_chatgpt_lua.ps1 -Monitor -IntervalSeconds 10
```

#### C. **샘플 생성 모드** (테스트용)

```powershell
.\scripts\send_to_chatgpt_lua.ps1 -GenerateSample
```

### 3️⃣ **응답 파일 확인**

```lua
-- Lua에서 응답 읽기
local file = io.open("C:/workspace/agi/outputs/chatgpt_bridge/trinity_responses/my_request_001.json", "r")
if file then
    local content = file:read("*a")
    file:close()
    
    local response = json.decode(content)
    reaper.ShowConsoleMsg("Response: " .. response.answer .. "\n")
end
```

---

## 🔐 보안 (HMAC 검증)

모든 요청은 HMAC-SHA256으로 검증됩니다:

```json
{
    "id": "request_001",
    "message": "Your question",
    "signature": "abc123...",
    "timestamp": 1731421046
}
```

- **서명 생성**: 공유 시크릿 키 기반
- **타임스탬프 검증**: 5분 이내 요청만 허용
- **무결성 보장**: 변조된 요청 자동 거부

---

## 📊 응답 형식

### Markdown (`.md`)

```markdown
# ChatGPT Response

**Request ID**: request_001
**Timestamp**: 2025-11-12 22:57:26

---

## Answer

Your answer here...

---

**Metadata**:
- Source: Lua Bridge
- Processed: 2025-11-12 22:57:30
```

### JSON (`.json`)

```json
{
    "request_id": "request_001",
    "answer": "Your answer here...",
    "timestamp": "2025-11-12T22:57:30",
    "metadata": {
        "source": "Lua Bridge",
        "processed_at": "2025-11-12T22:57:30"
    }
}
```

---

## 🎮 VS Code Task 통합

```json
{
    "label": "ChatGPT: Process Lua Requests (Once)",
    "type": "shell",
    "command": "powershell",
    "args": [
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "${workspaceFolder}/scripts/send_to_chatgpt_lua.ps1",
        "-ProcessOnce"
    ],
    "group": "test"
}
```

---

## 🔄 자동화 시나리오

### 1. **Reaper에서 리듬 분석 요청**

```lua
-- Reaper: 현재 프로젝트 BPM 분석
local bpm = reaper.Master_GetTempo()
local request = {
    id = "rhythm_" .. os.time(),
    message = "Analyze rhythm pattern for BPM: " .. bpm,
    context = { bpm = bpm, source = "Reaper" }
}
-- JSON 저장 후 Bridge 실행
```

### 2. **주기적 모니터링**

```powershell
# 10초마다 새 요청 확인
.\scripts\send_to_chatgpt_lua.ps1 -Monitor -IntervalSeconds 10
```

### 3. **Scheduled Task 등록**

```powershell
# 매 5분마다 자동 실행
.\scripts\register_chatgpt_lua_bridge_task.ps1 -Register -IntervalMinutes 5
```

---

## 🧪 테스트

### 빠른 테스트

```powershell
# 1. 샘플 생성
.\scripts\send_to_chatgpt_lua.ps1 -GenerateSample

# 2. 처리
.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce

# 3. 결과 확인
code .\outputs\chatgpt_bridge\trinity_responses\sample_*.md
```

### E2E 테스트

```powershell
.\scripts\test_chatgpt_lua_bridge_e2e.ps1
```

---

## 📈 다음 단계

1. ✅ **완료**: 기본 브리지 시스템 구축
2. 🎯 **현재**: Lua 스크립트 통합
3. 🔜 **다음**:
   - Reaper에서 실시간 요청/응답
   - 응답 기반 자동 액션 (예: BPM 조정, 트랙 추가)
   - 멀티모달 응답 (이미지, 오디오)

---

## 🛠️ 트러블슈팅

| 문제 | 해결 방법 |
|------|----------|
| 응답 파일 없음 | Bridge 실행 여부 확인: `-ProcessOnce` |
| 서명 오류 | 타임스탬프 확인 (5분 이내) |
| JSON 파싱 실패 | 요청 형식 확인 (`id`, `message` 필수) |
| 권한 오류 | PowerShell 실행 정책: `Set-ExecutionPolicy Bypass` |

---

## 📚 관련 문서

- [CHATGPT_VSCODE_BRIDGE_COMPLETE.md](../CHATGPT_VSCODE_BRIDGE_COMPLETE.md)
- [TRINITY_AUTOPOIETIC_INTEGRATION.md](../TRINITY_AUTOPOIETIC_INTEGRATION.md)
- [AUTONOMOUS_GOAL_SYSTEM_OPERATIONAL.md](../AUTONOMOUS_GOAL_SYSTEM_OPERATIONAL.md)

---

**최종 업데이트**: 2025-11-12  
**버전**: 1.0.0  
**상태**: ✅ Production Ready
