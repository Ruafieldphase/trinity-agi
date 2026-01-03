# ChatOps: 자연어 스트리밍 제어 시스템

자연어로 OBS 스트리밍과 YouTube 자동응답 봇을 제어하는 통합 ChatOps 시스템입니다.

## 🚀 빠른 시작

### 1. 상태 확인

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/chatops_router.ps1 -Say "상태 보여줘"
```

### 2. 온보딩 (신규 사용자)

```powershell
# 1단계: 온보딩 가이드 확인
powershell -File scripts/chatops_router.ps1 -Say "온보딩 도와줘"

# 2단계: Client Secret 설치
powershell -File scripts/chatops_router.ps1 -Say "시크릿 등록해줘"

# 3단계: OAuth 인증
powershell -File scripts/chatops_router.ps1 -Say "oauth"
```

### 3. 방송 시작

```powershell
powershell -File scripts/chatops_router.ps1 -Say "방송 시작해줘"
```

## 📋 지원 명령어

### 방송 제어

| 자연어 | 동작 |
|--------|------|
| "방송 시작해줘" / "스트림 시작" | OBS 스트리밍 시작 (YouTube Studio 자동 오픈) |
| "방송 멈춰" / "스트림 정지" | 스트리밍 중지 |
| "씬 [이름] 로 바꿔줘" | 지정한 씬으로 전환 |

**예시**

```powershell
chatops_router.ps1 -Say "방송 시작해줘"
chatops_router.ps1 -Say "씬 Coding 바꿔줘"
chatops_router.ps1 -Say "방송 멈춰"
```

### 상태 확인

| 자연어 | 동작 |
|--------|------|
| "상태" / "상태 보여줘" / "status" | 안전 요약 대시보드 (항상 성공) |
| "퀵 상태" / "quick status" | 빠른 상태 확인 |
| "obs 상태" / "obs status" | OBS 상세 상태 |

**특징**: 모든 상태 조회는 환경 준비가 안 되어 있어도 실패하지 않습니다 (exit code 0).

### YouTube 봇 제어

| 자연어 | 동작 |
|--------|------|
| "봇 켜줘" / "자동응답 시작" | YouTube Live 자동응답 봇 시작 |
| "봇 꺼줘" / "자동응답 중지" | 봇 중지 |
| "드라이런" / "dry" | 테스트 모드 (실제 댓글 작성 안 함) |

### 온보딩 & 설정

| 자연어 | 동작 |
|--------|------|
| "온보딩 도와줘" / "onboarding" | 단계별 온보딩 가이드 표시 |
| "시크릿 등록해줘" | Client Secret 대화형 설치 |
| "프리플라이트" / "점검" | 의존성 확인 |
| "oauth" / "인증" | OAuth 대화형 인증 |

## 🏗️ 아키텍처

```
자연어 입력 (한글/영어)
    ↓
chatops_router.ps1
    ↓
chatops_intent.py (Python 의도 파서)
    ↓
ASCII 토큰 반환
    ↓
PowerShell 액션 함수 실행
    ↓
obs_ws_control.py / youtube_live_bot.py 등
```

**핵심 설계 결정**:

- Windows PowerShell 5.1의 UTF-8 정규식 문제를 회피하기 위해 Python으로 의도 파싱 위임
- 모든 상태 조회는 무조건 exit 0 반환 → CI/CD 파이프라인에서 안전
- 자연어 → ASCII 토큰 변환으로 인코딩 독립성 확보

## 📁 파일 구조

```
scripts/
├── chatops_router.ps1           # 메인 라우터 (자연어 → 액션)
├── chatops_intent.py            # Python 의도 파서
├── obs_ws_control.py            # OBS WebSocket 제어
├── youtube_live_bot.py          # YouTube 자동응답 봇
├── quick_stream_status.ps1      # 안전 상태 집계
├── start_ai_dev_stream.ps1      # 스트리밍 시작 오케스트레이터
└── install_youtube_client_secret.ps1  # Client Secret 설치
```

## 🔧 사전 요구사항

### OBS 설정

1. OBS Studio 설치
2. Tools → WebSocket Server Settings
3. "Enable WebSocket server" 체크
4. Port: 4455 (기본값)

### Python 환경

```powershell
# OBS 제어용
pip install obsws-python

# YouTube 봇용
pip install google-api-python-client google-auth-oauthlib python-dotenv backoff
```

### YouTube API 설정

1. Google Cloud Console에서 프로젝트 생성
2. YouTube Data API v3 활성화
3. OAuth 2.0 Client ID 생성 (Desktop app)
4. `client_secret.json` 다운로드
5. `credentials/client_secret.json` 경로에 배치

**팁**: "시크릿 등록해줘" 명령으로 대화형 설치 가능

## 🎯 VS Code 통합

`.vscode/tasks.json`에 정의된 태스크로 원클릭 실행:

- **Streaming: Quick Status (safe)** - 안전 상태 확인
- **ChatOps Test: Status** - ChatOps 상태 조회 테스트
- **YouTube: Quick Onboarding (guided)** - 전체 온보딩 프로세스

## 🐛 문제 해결

### OBS 연결 실패

```powershell
# 1. OBS가 실행 중인지 확인
# 2. WebSocket 설정 확인 (Port 4455)
chatops_router.ps1 -Say "obs 상태"
```

### YouTube 봇 인증 오류

```powershell
# 1. 의존성 설치 확인
chatops_router.ps1 -Say "프리플라이트"

# 2. Client Secret 재설치
chatops_router.ps1 -Say "시크릿 등록해줘"

# 3. OAuth 재인증
chatops_router.ps1 -Say "oauth"
```

### 한글 출력 깨짐

- **원인**: Windows PowerShell 5.1의 콘솔 인코딩 제한
- **영향**: 시각적 출력만, 모든 기능은 정상 동작
- **해결**: PowerShell 7+ 사용 또는 VS Code 통합 터미널 사용

## 📊 품질 보증

- ✅ **Zero-Fail Status**: 상태 조회는 절대 파이프라인을 중단하지 않음
- ✅ **인코딩 독립**: Python 파서로 UTF-8 정규식 문제 회피
- ✅ **사용자 친화**: 자연어 12개 이상의 의도 인식
- ✅ **자체 완결**: 온보딩 가이드가 시스템에 내재

## 🔐 보안 고려사항

- `client_secret.json`은 Git에 커밋하지 마세요 (`.gitignore`에 포함)
- OAuth 토큰은 `credentials/token.json`에 저장됨 (자동 생성)
- 환경변수 방식도 지원: `YOUTUBE_CLIENT_SECRET_JSON` 환경변수 설정

## 📝 라이선스

이 프로젝트는 내부 도구로 개발되었습니다.

## 🤝 기여

버그 제보 및 기능 제안은 이슈 트래커를 이용해주세요.

---

**마지막 업데이트**: 2025-10-27  
**버전**: 1.0.0  
**작성자**: Shion_Core
