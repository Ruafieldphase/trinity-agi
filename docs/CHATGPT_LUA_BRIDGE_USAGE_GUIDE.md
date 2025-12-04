# ChatGPT ↔ Lua Bridge 사용 가이드

## 🎯 개요

이 시스템은 Neovim(Lua)에서 ChatGPT로 요청을 보내고 응답을 받는 비동기 브릿지입니다.

---

## 🚀 빠른 시작

### 1. 샘플 요청 생성 (테스트용)

```powershell
.\scripts\send_to_chatgpt_lua.ps1 -GenerateSample
```

→ `outputs\lua_requests\sample_[timestamp].json` 생성

### 2. 요청 처리 (한 번만)

```powershell
.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce
```

→ 대기 중인 요청 1개 처리
→ 응답: `outputs\trinity_responses\[timestamp].md` + `.json`
→ 처리된 요청: `outputs\lua_requests\processed\`로 이동

### 3. 모니터링 모드 (백그라운드)

```powershell
.\scripts\send_to_chatgpt_lua.ps1 -Monitor
```

→ 60초마다 새 요청 자동 처리

---

## 📁 디렉토리 구조

```
outputs/
├── lua_requests/           # Lua에서 생성한 요청
│   └── processed/          # 처리 완료된 요청
├── trinity_responses/      # ChatGPT 응답
└── chatgpt_bridge/         # 브릿지 상태 (활성화된 경우)
```

---

## 🔧 Neovim(Lua) 통합 (예정)

### 요청 생성 (Lua)

```lua
-- Neovim에서 요청 생성
local request = {
    query = "AGI 시스템 상태 요약해줘",
    context = {
        current_file = vim.fn.expand("%:p"),
        timestamp = os.time()
    }
}

local json = vim.json.encode(request)
local file = io.open(
    "C:/workspace/agi/outputs/lua_requests/request_" .. os.time() .. ".json",
    "w"
)
file:write(json)
file:close()
```

### 응답 읽기 (Lua)

```lua
-- 최신 응답 읽기
local response_dir = "C:/workspace/agi/outputs/trinity_responses/"
-- ... (파일 검색 로직)
local response = vim.json.decode(content)
print(response.answer)
```

---

## 🔒 보안

- **HMAC SHA256** 서명 검증
- Secret: `~/.agi_bridge_secret` (자동 생성)
- 요청 위조 방지

---

## 📊 응답 형식

**JSON**:

```json
{
    "rcl": null,
    "recommended_actions": [
        "리듬 상태 확인 및 조정",
        "활성 목표 진행 상황 점검"
    ],
    "goals": null,
    "file_references": [
        "C:\\workspace\\agi\\outputs\\session_continuity_latest.md"
    ],
    "timestamp": "2025-11-12T22:57:51+09:00"
}
```

**Markdown**: 읽기 쉬운 형식으로 동일한 내용

---

## 🎯 다음 단계

### Lua 통합 완성

1. Neovim 플러그인 생성
2. 키맵 설정 (예: `<leader>aa` = AGI 상태 확인)
3. 응답 파싱 및 버퍼 표시

### 자동화 확장

1. Monitor 모드를 Scheduled Task로 등록
2. RPA Worker와 통합
3. 자율 목표 시스템과 연결

---

## 🛠️ 문제 해결

### 요청이 처리되지 않음

```powershell
# 대기 중인 요청 확인
Get-ChildItem outputs\lua_requests -Filter "*.json" | Where-Object { $_.Directory.Name -ne "processed" }

# 수동 처리
.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce -Verbose
```

### 응답이 없음

```powershell
# 최근 응답 확인
Get-ChildItem outputs\trinity_responses | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

### HMAC 검증 실패

```powershell
# Secret 재생성
Remove-Item ~/.agi_bridge_secret -Force
.\scripts\send_to_chatgpt_lua.ps1 -GenerateSample  # 자동 재생성
```

---

## 📚 관련 문서

- **설계**: `docs/CHATGPT_VSCODE_BRIDGE_COMPLETE.md`
- **전체 가이드**: `docs/CHATGPT_VSCODE_BRIDGE_USAGE_GUIDE.md`
- **아키텍처**: `docs/ARCHITECTURE_OVERVIEW.md`

---

## ✅ 테스트 확인

```powershell
# E2E 테스트
.\scripts\send_to_chatgpt_lua.ps1 -GenerateSample
.\scripts\send_to_chatgpt_lua.ps1 -ProcessOnce

# 결과 확인
code outputs\trinity_responses\sample_[latest].md
```

**성공 시**: Markdown 응답이 생성되고, 요청이 `processed/`로 이동

---

**작성일**: 2025-11-12  
**버전**: 1.0  
**상태**: ✅ Production Ready
