# 깃코(Gitco) - 자연스러운 대화형 Slack Bot

## 🎯 특징

**완전히 자연스러운 대화:**

```
❌ 명령어 방식 (이전):
User: "상태"
Bot: "현재 카나리 50% 배포 중"

✅ 대화 방식 (현재):
User: "지금 어떻게 돼?"
Bot: "🔍 현재 카나리 50% 배포 중이에요! 모니터링하고 있으며 45분 후 다음 단계로 넘어갈 예정입니다."

User: "괜찮아?"
Bot: "네, 모든 헬스 체크가 정상이에요! ✅ 에러율 0%, 레이턴시도 안정적입니다."

User: "그럼 100% 올려도 될까?"
Bot: "네, 100% 배포 진행하셔도 될 것 같아요. 실행할까요?"

User: "응, 해줘"
Bot: "알겠습니다! 100% 배포를 시작할게요. 2-3분 소요되고 이후 2시간 모니터링이 진행됩니다. 🚀"
```

## 🚀 빠른 시작

### 1. 패키지 설치

```powershell
cd D:\nas_backup\LLM_Unified
.\.venv\Scripts\Activate.ps1
pip install -r ion-mentoring\slack_bot_requirements.txt
```

### 2. 환경 변수 설정

```powershell
# Slack Bot Token
[Environment]::SetEnvironmentVariable("SLACK_BOT_TOKEN", "xoxb-your-token", "User")

# GCP 인증 (이미 설정되어 있으면 생략)
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\service-account-key.json"
```

### 3. Bot 시작

```powershell
# 자동 시작 스크립트 사용
.\LLM_Unified\ion-mentoring\scripts\start_slack_bot.ps1 -KillExisting

# 또는 직접 실행
cd LLM_Unified\ion-mentoring
python slack_bot_conversational.py
```

## 💬 대화 예시

### 상태 확인

```
You: "배포 상황 알려줘"
Gitco: "🔍 현재 카나리 50% 배포 중이고, 100-monitoring 단계에요. 
       모니터링이 1시간 12분 남았습니다!"

You: "문제 없어?"
Gitco: "네, 모든 시스템이 정상이에요! 헬스 체크도 통과했습니다. ✅"
```

### 배포 실행

```
You: "100% 올려도 될까?"
Gitco: "네, 현재 상태가 안정적이어서 100% 배포 진행하셔도 좋을 것 같아요. 
       바로 시작할까요?"

You: "응"
Gitco: "알겠습니다! 🚀 100% 배포를 시작할게요..."
[배포 실행 중]
Gitco: "✅ 100% 배포가 완료되었습니다! 
       2시간 모니터링이 시작됐고, 14:30에 종료될 예정이에요."
```

### 테스트 실행

```
You: "테스트 좀 돌려봐"
Gitco: "🔍 헬스 프로브를 실행할게요. 잠시만 기다려주세요..."
[실행 완료]
Gitco: "✅ 프로브 완료! 
       Canary: 10/10 성공 (100%)
       Legacy: 10/10 성공 (100%)
       모두 정상이에요!"
```

### 로그 확인

```
You: "최근 로그 보여줘"
Gitco: "📋 최근 1시간 로그를 확인했어요.
       에러 없이 모든 요청이 정상 처리됐습니다.
       평균 레이턴시: 120ms"
```

### 긴급 상황

```
You: "에러가 너무 많아! 롤백해야 할 것 같아"
Gitco: "알겠습니다. 긴급 롤백을 실행할게요. 카나리를 0%로 되돌립니다. ⚠️"
[롤백 실행]
Gitco: "✅ 롤백이 완료됐습니다. 모든 트래픽이 안정된 레거시 버전으로 전환됐어요."
```

## 🧠 AI 기능

### 문맥 이해
- 이전 대화 내용을 기억하고 참조
- 모호한 표현도 문맥으로 파악 ("그거", "그럼", "응" 등)

### 의도 파악
- 명령어 없이 자연어로 의도 파악
- 질문, 요청, 확인 등을 구분하여 적절히 대응

### 상황 판단
- 현재 배포 상태를 고려한 응답
- 위험한 작업은 확인 후 실행

## 📋 Slack App 설정

상세한 설정은 `SLACK_BOT_SETUP.md` 참고

**간단 요약:**
1. https://api.slack.com/apps 에서 앱 생성
2. **Bot Token Scopes** 추가:
   - `chat:write`
   - `channels:history`
   - `im:history`
3. **Event Subscriptions** 설정:
   - URL: `http://your-ngrok-url/slack/events`
   - Subscribe: `message.channels`, `message.im`
4. 워크스페이스에 설치하고 Token 복사

## 🔧 고급 설정

### ngrok으로 로컬 테스트

```powershell
# ngrok 설치 후
ngrok http 8080
```

생성된 URL을 Slack Event Subscriptions에 설정

### 백그라운드 실행

```powershell
.\start_slack_bot.ps1 -KillExisting
```

### Windows 서비스 등록

```powershell
# NSSM 사용
nssm install GitcoBot "D:\nas_backup\LLM_Unified\.venv\Scripts\python.exe"
nssm set GitcoBot AppParameters "D:\nas_backup\LLM_Unified\ion-mentoring\slack_bot_conversational.py"
nssm set GitcoBot AppDirectory "D:\nas_backup\LLM_Unified\ion-mentoring"
nssm start GitcoBot
```

## 🎨 커스터마이징

### 성격 변경
`slack_bot_conversational.py`의 `SYSTEM_INSTRUCTION` 수정:

```python
SYSTEM_INSTRUCTION = """당신은 "깃코(Gitco)"입니다. 
[원하는 성격과 스타일 설명]
"""
```

### 새 기능 추가
`_create_tools()` 메서드에 새 Function Declaration 추가:

```python
FunctionDeclaration(
    name="your_function",
    description="설명",
    parameters={...}
)
```

## 🐛 트러블슈팅

### Bot이 응답하지 않음

```powershell
# 1. 토큰 확인
$env:SLACK_BOT_TOKEN

# 2. 서버 상태 확인
Invoke-RestMethod http://localhost:8080/health

# 3. GCP 인증 확인
gcloud auth application-default login
```

### 대화가 부자연스러움
- 시스템 프롬프트 조정
- Temperature 값 변경 (현재 기본값 사용)
- 대화 히스토리 제한 조정 (현재 10회)

### 함수 실행 실패
- PowerShell 스크립트 경로 확인
- GCP 프로젝트 권한 확인
- 로그 파일 확인

## 📊 모니터링

### 서버 로그

```powershell
# Bot 실행 중인 터미널에서 실시간 로그 확인
```

### Slack 대화 히스토리
- 채널별로 최근 20개 메시지 저장
- 서버 재시작 시 초기화 (영구 저장 필요 시 DB 연동)

## 🔐 보안

- **Token 보호**: 환경 변수로만 관리, 코드에 하드코딩 금지
- **GCP 인증**: Service Account Key 파일 권한 최소화
- **Rate Limiting**: Slack API 제한 준수
- **함수 실행**: 위험한 작업(롤백)은 명확한 사용자 의도 확인 후 실행

---

**문의:** Slack에서 `@Gitco 도움말` 또는 직접 대화로 질문하세요!
