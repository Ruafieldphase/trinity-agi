# ChatGPT-Lua Bridge 사용 가이드 🌉

## 🚀 빠른 시작

### 1️⃣ 샘플 요청 생성 (테스트용)

```powershell
.\scripts\send_to_chatgpt_lua.ps1 -GenerateSample
```

**결과**: `outputs/chatgpt_bridge/lua_requests/sample_YYYYMMDD_HHMMSS.json` 생성

---

### 2️⃣ 요청 처리 (단일 실행)

```powershell
.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce
```

**동작**:

- `lua_requests/` 폴더의 `.json` 요청 처리
- HMAC 검증 (선택적)
- ChatGPT에 전송 및 응답 수신
- 응답 저장: `trinity_responses/` (MD + JSON)
- 처리된 요청 이동: `lua_requests/processed/`

---

### 3️⃣ 지속적 모니터링 (백그라운드)

```powershell
.\scripts\send_to_chatgpt_lua.ps1 -Monitor
```

**동작**:

- 5초마다 새 요청 확인
- 자동 처리 및 응답 저장
- Ctrl+C로 중지

---

## 📂 디렉터리 구조

```
outputs/chatgpt_bridge/
├── lua_requests/           # 처리 대기 중인 요청
│   ├── *.json             # 활성 요청
│   └── processed/         # 처리 완료된 요청
├── trinity_responses/      # ChatGPT 응답
│   ├── *.md              # Markdown 응답
│   └── *.json            # JSON 응답
└── lua_bridge_activity.jsonl  # 활동 로그
```

---

## 🔐 보안 (HMAC)

### HMAC 시크릿 설정 (선택)

```powershell
$env:LUA_BRIDGE_HMAC_SECRET = "your-secret-key"
```

### HMAC 포함 요청 생성

```powershell
.\scripts\send_to_chatgpt_lua.ps1 -GenerateSample
```

HMAC이 자동으로 계산되어 `hmac` 필드에 포함됩니다.

---

## 📋 요청 JSON 형식

```json
{
  "timestamp": "2025-11-12T22:57:26Z",
  "source": "lua_script",
  "query": "현재 작업 컨텍스트를 요약해줘",
  "context": {
    "current_task": "코딩",
    "focus_level": "high"
  },
  "hmac": "abc123..."
}
```

---

## 📊 응답 JSON 형식

```json
{
  "query": "현재 작업 컨텍스트를 요약해줘",
  "response": "ChatGPT 응답 내용...",
  "timestamp": "2025-11-12T22:57:27Z",
  "hmac_verified": true
}
```

---

## 🎯 다음 단계

### 1. **Lua 통합**

- 자율 목표 시스템에서 요청 생성
- Trinity Cycle에서 자동 호출

### 2. **워크플로우 개선**

- 응답 분석 및 자동 액션 트리거
- 리듬 상태 기반 요청 우선순위

### 3. **모니터링 강화**

- 대시보드에 bridge 활동 통합
- 성공/실패율 추적

---

## 🔧 트러블슈팅

### 문제: 요청이 처리되지 않음

**해결**: `lua_requests/` 폴더에 `.json` 파일이 있는지 확인

### 문제: HMAC 검증 실패

**해결**:

```powershell
$env:LUA_BRIDGE_HMAC_SECRET = "correct-secret"
```

### 문제: ChatGPT API 오류

**해결**: `OPENAI_API_KEY` 환경 변수 확인

---

## 📝 로그 확인

```powershell
Get-Content outputs/chatgpt_bridge/lua_bridge_activity.jsonl -Tail 10 | ConvertFrom-Json | Format-List
```

---

**완료! 🎉**

- ✅ Lua bridge 완전히 작동
- ✅ E2E 테스트 성공
- ✅ 통합 준비 완료
