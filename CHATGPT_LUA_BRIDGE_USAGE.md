# ChatGPT-Lua Bridge 사용 가이드

## 🎯 개요

이 시스템은 **ChatGPT에서 Lua 스크립트로 요청**을 보내고, AGI 시스템이 **자동으로 처리 후 응답**을 생성하는 완전 자동화된 브릿지입니다.

---

## 🚀 빠른 시작

### 1️⃣ ChatGPT에서 요청 전송

ChatGPT에서 다음 형식으로 요청:

```json
{
  "request_id": "unique-id-123",
  "timestamp": "2025-11-13T10:30:00Z",
  "query": "AGI 시스템 상태 요약해줘",
  "context": {
    "user": "developer",
    "priority": "high"
  }
}
```

**Lua 스크립트로 저장 위치**: `C:\workspace\agi\outputs\lua_requests\request_*.json`

---

### 2️⃣ 자동 처리 (백그라운드 모니터)

모니터 모드 실행:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\workspace\agi\scripts\send_to_chatgpt_lua.ps1" -Monitor -MonitorIntervalSec 10
```

**동작**:

- 10초마다 `lua_requests/` 폴더 스캔
- 새 요청 발견 시 자동 처리
- 응답 생성 → `trinity_responses/response_*.json`
- 처리된 요청 → `lua_requests/processed/`로 이동

---

### 3️⃣ 응답 확인

**응답 파일 위치**: `C:\workspace\agi\outputs\trinity_responses\response_<request_id>.json`

```json
{
  "request_id": "unique-id-123",
  "timestamp": "2025-11-13T10:30:15Z",
  "status": "success",
  "response": {
    "summary": "AGI 시스템 정상 작동 중...",
    "rhythm_status": "EXCELLENT (92.5%)",
    "active_goals": 3
  },
  "artifacts": [
    "outputs/session_continuity_latest.md",
    "outputs/quick_status_latest.json"
  ]
}
```

ChatGPT는 이 JSON을 읽어 사용자에게 자연어로 응답합니다.

---

## 🔧 수동 실행 모드

### 한 번만 처리 (Process Once)

```powershell
.\send_to_chatgpt_lua.ps1 -ProcessOnce
```

현재 대기 중인 요청을 **1회만** 처리하고 종료합니다.

---

### 샘플 요청 생성

```powershell
.\send_to_chatgpt_lua.ps1 -GenerateSample
```

테스트용 샘플 요청 파일 생성 (`lua_requests/test_request_*.json`)

---

## 🛡️ 보안 (HMAC 검증)

### HMAC 키 설정

```powershell
$env:LUA_BRIDGE_HMAC_KEY = "your-secret-key-here"
```

**자동 검증**: 요청에 `hmac` 필드가 있으면 자동으로 검증합니다.

```json
{
  "request_id": "123",
  "query": "상태 요약",
  "hmac": "sha256-hash-here"
}
```

검증 실패 시 요청 거부 및 로그 기록.

---

## 📁 디렉토리 구조

```
outputs/
├── lua_requests/          # 입력: Lua에서 생성한 요청
│   ├── request_*.json
│   └── processed/         # 처리 완료된 요청 아카이브
├── trinity_responses/     # 출력: AGI 응답
│   └── response_*.json
└── chatgpt_bridge/        # 기타 브릿지 아티팩트
```

---

## 🔄 통합 플로우

```
[ChatGPT] 
    ↓ (Lua 스크립트)
[lua_requests/request_*.json]
    ↓ (모니터 감지)
[send_to_chatgpt_lua.ps1 -Monitor]
    ↓ (컨텍스트 수집)
[Rhythm + Goals + System 상태]
    ↓ (응답 생성)
[trinity_responses/response_*.json]
    ↓ (Lua 스크립트)
[ChatGPT]
    ↓ (자연어 응답)
[사용자]
```

---

## 🧪 테스트

### E2E 테스트

```powershell
# 1. 샘플 생성
.\send_to_chatgpt_lua.ps1 -GenerateSample

# 2. 처리 실행
.\send_to_chatgpt_lua.ps1 -ProcessOnce

# 3. 응답 확인
Get-Content "outputs\trinity_responses\response_*.json" -Raw | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## ⚙️ VS Code Task 통합

`.vscode/tasks.json`에 추가:

```json
{
  "label": "🌉 Lua Bridge: Start Monitor",
  "type": "shell",
  "command": "powershell",
  "args": [
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    "${workspaceFolder}/scripts/send_to_chatgpt_lua.ps1",
    "-Monitor",
    "-MonitorIntervalSec",
    "10"
  ],
  "isBackground": true,
  "group": "build"
}
```

---

## 🐛 트러블슈팅

### 응답이 생성되지 않음

1. 모니터가 실행 중인지 확인
2. `lua_requests/` 폴더에 요청 파일이 있는지 확인
3. 로그 확인: `outputs/lua_bridge_monitor.log`

### HMAC 검증 실패

1. 환경 변수 확인: `$env:LUA_BRIDGE_HMAC_KEY`
2. Lua 스크립트에서 동일한 키 사용 확인
3. 페이로드가 변조되지 않았는지 확인

---

## 📊 모니터링

### 로그 확인

```powershell
Get-Content "outputs\lua_bridge_monitor.log" -Tail 50
```

### 처리 통계

```powershell
Get-ChildItem "outputs\lua_requests\processed" | Measure-Object
Get-ChildItem "outputs\trinity_responses" | Measure-Object
```

---

## 🎉 완료

이제 ChatGPT에서 Lua 스크립트로 요청을 보내면:

1. ✅ 자동 감지 및 처리
2. ✅ 컨텍스트 수집 (리듬, 목표, 시스템 상태)
3. ✅ 응답 생성
4. ✅ ChatGPT로 자동 전달

**모든 작업이 완전 자동화되었습니다!** 🚀

---

## 📝 다음 단계

1. **프로덕션 배포**: 모니터를 Windows 서비스나 스케줄러로 등록
2. **로그 회전**: 로그 파일 자동 정리 구현
3. **대시보드**: 처리 통계를 시각화하는 웹 UI 추가

---

**작성일**: 2025-11-13  
**버전**: 1.0  
**상태**: ✅ 프로덕션 준비 완료
