# 🚀 Ion Day 1: Vertex AI 환경 구축 실행 가이드

**날짜**: 2025년 10월 17일 (목요일)  
**시간**: 14:00-17:00 (3시간)  
**목표**: Vertex AI 개발 환경 완전 구축 및 첫 코드 실행  
**담당**: 이온 (실행) + 비노체 (가이드) + 엘로 (기술 지원)

## 🔧 Phase 2: Python 환경 검증 (14:00-14:15)

### 2.1 Python 버전 확인

**PowerShell 실행** (관리자 권한):

```powershell
# Python 버전 확인
python --version

# 예상 출력: Python 3.11.x 또는 3.12.x
```

**만약 Python 3.11 미만이라면**:

```powershell
# Python 3.11 다운로드 페이지 열기
start https://www.python.org/downloads/
```

```powershell
# pip 최신 버전으로 업그레이드
python -m pip install --upgrade pip

# 예상 출력:
# Successfully installed pip-24.x.x
```

### 2.3 가상환경 생성 (권장)

```powershell
# LLM_Unified 디렉토리로 이동
cd D:\nas_backup\LLM_Unified

# 가상환경 생성
python -m venv venv_ion

# 가상환경 활성화
.\venv_ion\Scripts\Activate.ps1

# 프롬프트가 (venv_ion)으로 변경되면 성공
```

**✅ 체크포인트**: `(venv_ion) PS D:\nas_backup\LLM_Unified>` 프롬프트 확인

---

## ☁️ Phase 3: Google Cloud 설정 (14:15-14:55)

### 3.1 Google Cloud Console 접속 (5분)

1. **브라우저 열기**:

   ```text
   https://console.cloud.google.com
   ```

### 3.2 Vertex AI API 활성화 (10분)

1. **API 라이브러리로 이동**:

   - 좌측 메뉴 → "API 및 서비스" → "라이브러리"

2. **Vertex AI API 검색**:

   - 검색창에 "Vertex AI API" 입력

3. **API 활성화**:

   - "Vertex AI API" 클릭
   - "사용 설정" 버튼 클릭
   - 활성화 완료까지 대기 (1-2분)

4. **추가 API 활성화** (필요 시):

   - Generative Language API

### 3.3 서비스 계정 생성 (15분)

1. **서비스 계정 메뉴로 이동**:

   - 좌측 메뉴 → "IAM 및 관리자" → "서비스 계정"

2. **새 서비스 계정 생성**:

   - "서비스 계정 만들기" 클릭
   - 서비스 계정 이름: `ion-vertex-ai-dev`
   - 서비스 계정 ID: `ion-vertex-ai-dev` (자동 생성)
   - 설명: "Ion Vertex AI Development Account"
   - "만들고 계속하기" 클릭

3. **역할 부여**:

   - "역할 선택" 드롭다운 클릭
   - 다음 역할들 추가:
     - ✅ `Vertex AI User`
     - ✅ `Vertex AI Service Agent`
     - ✅ `AI Platform Admin` (선택)
   - "계속" 클릭

4. **완료**:
   - "완료" 클릭

### 3.4 인증 키 다운로드 (10분)

1. **생성된 서비스 계정 클릭**:

   - 목록에서 `ion-vertex-ai-dev@...` 클릭

2. **키 탭으로 이동**:

   - 상단 탭에서 "키" 클릭

3. **새 키 생성**:

   - "키 추가" → "새 키 만들기"
   - 키 유형: **JSON** 선택
   - "만들기" 클릭

4. **키 파일 저장**:
   - 자동 다운로드된 JSON 파일을 안전한 위치로 이동
   - 권장 경로: `D:\nas_backup\LLM_Unified\credentials\`
   - 파일명 예시: `ion-vertex-ai-dev-xxxxx.json`

**⚠️ 보안 경고**: 이 JSON 파일은 절대 Git에 커밋하지 마세요!

### 3.5 환경 변수 설정 (10분)

### 방법 1: PowerShell 세션 환경 변수 (임시)

```powershell
# 프로젝트 ID 설정
$env:GOOGLE_CLOUD_PROJECT = "naeda-genesis"

# 리전 설정
$env:GCP_LOCATION = "asia-northeast3"

# 인증 키 파일 경로 설정
$env:GOOGLE_APPLICATION_CREDENTIALS = "D:\nas_backup\LLM_Unified\credentials\ion-vertex-ai-dev-xxxxx.json"

# 설정 확인
echo $env:GOOGLE_CLOUD_PROJECT
echo $env:GCP_LOCATION
echo $env:GOOGLE_APPLICATION_CREDENTIALS
```

### 방법 2: Windows 시스템 환경 변수 (영구) ⭐ 권장

1. **시스템 속성 열기**:

   ```powershell
   rundll32 sysdm.cpl,EditEnvironmentVariables
   ```

2. **사용자 변수에 추가**:

   - "새로 만들기" 클릭
   - 변수 이름: `GOOGLE_CLOUD_PROJECT`
   - 변수 값: `naeda-genesis`
   - "확인" 클릭

3. **추가 변수 설정**:

   - `GCP_LOCATION` = `asia-northeast3`
   - `GOOGLE_APPLICATION_CREDENTIALS` = `D:\nas_backup\LLM_Unified\credentials\ion-vertex-ai-dev-xxxxx.json`

4. **PowerShell 재시작**:

   ```powershell
   # 현재 세션 종료 후 새로 시작
   exit
   ```

**✅ 체크포인트**: 환경 변수 설정 확인

```powershell
# 새 PowerShell 세션에서 확인
echo $env:GOOGLE_CLOUD_PROJECT
echo $env:GCP_LOCATION
echo $env:GOOGLE_APPLICATION_CREDENTIALS
```

---

## 👉 다음 단계: Day 2로 이동하기

Day 1을 마쳤다면, 아키텍처와 테스트를 정리하는 Day 2 가이드를 이어서 진행하세요.

- 문서: `ion-mentoring/DAY2_ARCHITECTURE_AND_DESIGN.md`
- 핵심: 경량 계층 구조, Pytest 도입, PromptClient 추상화 소개

## � Phase 4: Vertex AI SDK 설치 (14:55-15:15)

### 4.1 SDK 설치

```powershell
# 가상환경 활성화 확인 (프롬프트에 venv_ion 표시)
# 없다면: .\venv_ion\Scripts\Activate.ps1

# Vertex AI SDK 설치
pip install google-cloud-aiplatform

# 예상 출력:
# Collecting google-cloud-aiplatform
# Installing collected packages: ...
# Successfully installed google-cloud-aiplatform-1.x.x
```

### 4.2 추가 의존성 설치

```powershell
# 유용한 추가 패키지들
pip install google-auth google-auth-oauthlib google-auth-httplib2

# 개발 도구
pip install pylint black pytest
```

### 4.3 설치 검증

```powershell
# 설치된 패키지 확인
pip list | Select-String "google"

# 예상 출력:
# google-api-core            x.x.x
# google-auth                x.x.x
# google-cloud-aiplatform    x.x.x
# ...
```

### 4.4 Python에서 import 테스트

```powershell
# Python 대화형 모드 실행
python

# Python 프롬프트에서:
>>> import vertexai
>>> from vertexai.generative_models import GenerativeModel
>>> print("✅ Vertex AI SDK import 성공!")
>>> exit()
```

**✅ 체크포인트**: 오류 없이 import 성공

---

## 💻 Phase 5: VS Code 환경 구성 (15:15-15:45)

### 5.1 VS Code 확장팩 설치

**VS Code 실행**:

```powershell
# VS Code로 LLM_Unified 폴더 열기
code D:\nas_backup\LLM_Unified
```

**확장팩 설치** (Ctrl+Shift+X):

1. **Python** (필수)

   - 검색: `ms-python.python`
   - "설치" 클릭

2. **Pylance** (필수)

   - 검색: `ms-python.vscode-pylance`
   - "설치" 클릭

3. **Git Graph** (권장)

   - 검색: `mhutchie.git-graph`
   - "설치" 클릭

4. **Markdown All in One** (권장)
   - 검색: `yzhang.markdown-all-in-one`
   - "설치" 클릭

### 5.2 Python 인터프리터 선택

1. **Command Palette 열기**: `Ctrl+Shift+P`

2. **"Python: Select Interpreter" 입력**

3. **가상환경 선택**:

   - `.\venv_ion\Scripts\python.exe` 선택

4. **확인**:
   - 좌측 하단에 `Python 3.11.x ('venv_ion')` 표시

### 5.3 작업 공간 설정

**`.vscode/settings.json` 생성**:

```powershell
# .vscode 폴더 생성 (없다면)
New-Item -ItemType Directory -Force -Path .vscode

# settings.json 파일 생성
@"
{
  "python.defaultInterpreterPath": "./venv_ion/Scripts/python.exe",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
"@ | Out-File -FilePath .vscode/settings.json -Encoding utf8
```

**✅ 체크포인트**: VS Code에서 Python 파일 열기 시 자동 완성 작동

---

## 🎯 Phase 6: 첫 코드 실행 (15:45-16:25)

### 6.1 기존 코드 확인

```powershell
# ion_first_vertex_ai.py 파일 위치 확인
ls ion-mentoring/ion_first_vertex_ai.py

# 파일 내용 확인
cat ion-mentoring/ion_first_vertex_ai.py
```

### 6.2 실행 준비

**환경 변수 재확인**:

```powershell
# 빠른 환경 점검 (Vertex 호출 없이 구성만 확인)
python ion-mentoring\tools\quick_check_config.py

# .env 템플릿 기반으로 현재 세션에 적용(옵션)
powershell -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\tools\load_env.ps1 -Path .\.env.example -DryRun   # 미리보기
powershell -NoProfile -ExecutionPolicy Bypass -File ion-mentoring\tools\load_env.ps1 -Path .\.env.example          # 실제 적용

# 필수 환경 변수 확인
echo "Project: $env:GOOGLE_CLOUD_PROJECT"
echo "Location: $env:GCP_LOCATION"
echo "Credentials: $env:GOOGLE_APPLICATION_CREDENTIALS"

# 인증 키 파일 존재 확인
Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS
# True 출력되어야 함
```

### 6.3 첫 실행

#### 방법 1: 직접 스크립트 실행 (권장)

```powershell
# ion-mentoring 디렉토리로 이동
cd ion-mentoring

# 스크립트 실행
python ion_first_vertex_ai.py
```

#### 방법 2: PromptClient 추상화 사용

```powershell
# Python 대화형 모드에서 테스트
python

>>> from prompt_client import create_default_vertex_prompt_client
>>>
>>> # 클라이언트 생성 및 준비
>>> client = create_default_vertex_prompt_client()
>>> client.initialize().load()
>>>
>>> # 준비 상태 확인
>>> print(client.ready())  # True 출력
>>>
>>> # 프롬프트 전송
>>> response = client.send("안녕하세요, Gemini!")
>>> print(response)
>>>
>>> # 현재 설정 확인
>>> print(client.info())
>>> exit()
```

**예상 출력**:

```text
--- 이온의 첫 번째 Vertex AI 연결 시퀀스 ---
🌊 Vertex AI 초기화 시작... (Project: naeda-genesis, Location: asia-northeast3)
✅ Vertex AI 초기화 완료.
🧠 모델 로드 시작: gemini-1.5-flash
✅ 모델 로드 완료: models/gemini-1.5-flash

📨 Ion의 프롬프트:
안녕하세요, Gemini! 저는 Ion입니다. Vertex AI를 처음 사용해보는 중입니다.

🤖 Vertex AI 응답:
안녕하세요, Ion님! Vertex AI에 오신 것을 환영합니다!
저는 Gemini이며, 여러분의 AI 개발 여정을 도와드리겠습니다...

✅ 첫 Vertex AI 연결 테스트 성공!

```

### 6.4 오류 처리

**만약 오류 발생 시**:

#### 오류 1: "DefaultCredentialsError"

```text
해결 방법:
1. 환경 변수 GOOGLE_APPLICATION_CREDENTIALS 확인
2. JSON 키 파일 경로 확인
3. 파일 권한 확인
```

#### 오류 2: "PermissionDenied: 403"

```text
해결 방법:
1. Vertex AI API 활성화 확인
2. 서비스 계정 역할 확인 (Vertex AI User)
3. 프로젝트 ID 확인
```

#### 오류 3: "Module not found: vertexai"

```text
해결 방법:
1. 가상환경 활성화 확인
2. pip install google-cloud-aiplatform 재실행
3. Python 인터프리터 확인
```

### 6.5 성공 확인

**체크리스트**:

- [ ] 오류 없이 실행 완료
- [ ] Vertex AI 응답 수신
- [ ] "✅ 첫 Vertex AI 연결 테스트 성공!" 메시지 출력

**✅ 체크포인트**: 첫 코드 실행 성공!

---

## 🔀 Phase 7: Git 설정 및 첫 커밋 (16:25-16:55)

### 7.1 Git 사용자 정보 설정

```powershell
# 메인 디렉토리로 이동
cd D:\nas_backup\LLM_Unified

# Git 사용자 이름 설정 (아직 안 했다면)
git config user.name "Ion (Vertex AI Developer)"

# Git 이메일 설정
git config user.email "ion@naeda-ai.dev"

# 설정 확인
git config --list | Select-String "user"
```

### 7.2 브랜치 생성

```powershell
# 현재 브랜치 확인
git branch

# Ion 작업용 브랜치 생성
git checkout -b ion/day1-environment-setup

# 브랜치 확인
git branch
# * ion/day1-environment-setup
#   master
```

### 7.3 환경 설정 파일 생성

**`.gitignore` 업데이트**:

```powershell
# .gitignore에 credentials 폴더 추가 (이미 있는지 확인)
if (!(Select-String -Path .gitignore -Pattern "credentials/" -Quiet)) {
    Add-Content -Path .gitignore -Value "`n# Ion Vertex AI Credentials`ncredentials/`n*.json"
}
```

**환경 설정 템플릿 생성**:

```powershell
# .env.example 파일 생성
@"
# Vertex AI Configuration Template
# Ion Day 1 Environment Setup

GOOGLE_CLOUD_PROJECT=your-project-id
GCP_LOCATION=asia-northeast3
GOOGLE_APPLICATION_CREDENTIALS=./credentials/your-service-account-key.json

# Model Configuration
GEMINI_MODEL=gemini-1.5-pro-preview-0514
"@ | Out-File -FilePath .env.example -Encoding utf8
```

### 7.4 Day 1 완료 보고서 작성

```powershell
# 보고서 파일 생성
@"
# Ion Day 1 완료 보고서

**날짜**: $(Get-Date -Format "yyyy-MM-dd HH:mm")
**작성자**: Ion (Vertex AI Developer Trainee)

## ✅ 완료된 작업

### 환경 구축
- [x] Python 3.11+ 환경 확인
- [x] 가상환경 생성 (venv_ion)
- [x] Vertex AI SDK 설치

### Google Cloud 설정
- [x] Vertex AI API 활성화
- [x] 서비스 계정 생성
- [x] 인증 키 설정
- [x] 환경 변수 구성

### VS Code 구성
- [x] Python Extension 설치
- [x] Pylance 설치
- [x] Git Graph 설치
- [x] 작업 공간 설정

### 첫 코드 실행
- [x] ion_first_vertex_ai.py 실행 성공
- [x] Vertex AI 연결 확인
- [x] Gemini 응답 수신

## 📊 통계

- 소요 시간: 약 3시간
- 설치된 패키지: 20+ packages
- 실행 성공: 1/1 (100%)

## 💡 학습 내용

1. Vertex AI 프로젝트 구조 이해
2. 서비스 계정 및 인증 방식 학습
3. Python SDK 사용법 숙지
4. 환경 변수 관리 방법 습득

## 🎯 다음 단계 (Day 2)

- 파동 시스템 개념 학습
- 아키텍처 분석
- MVP 범위 확정

---

**멘토**: 비노체, 엘로
**상태**: ✅ Day 1 목표 달성
"@ | Out-File -FilePath "ion-mentoring/DAY1_COMPLETION_REPORT.md" -Encoding utf8
```

### 7.5 Git 커밋

```powershell
# 변경사항 확인
git status

# 파일 추가
git add .env.example
git add ion-mentoring/DAY1_COMPLETION_REPORT.md
git add ion-mentoring/DAY1_ENVIRONMENT_SETUP.md

# 커밋 작성 (Conventional Commits)
git commit -m "feat(ion): Day 1 환경 구축 완료

- Vertex AI SDK 설치 및 검증
- 서비스 계정 설정
- 첫 코드 실행 성공 (ion_first_vertex_ai.py)
- 환경 설정 템플릿 추가
- Day 1 완료 보고서 작성

Co-authored-by: Binoche <binoche@naeda-ai.dev>
Co-authored-by: Ello <ello@naeda-ai.dev>"

# 커밋 확인
git log --oneline -1
```

### 7.6 푸시 (선택)

```powershell
# 원격 저장소에 푸시
git push -u origin ion/day1-environment-setup

# 또는 나중에 PR로 병합할 예정이라면 로컬에만 보관
```

**✅ 체크포인트**: 첫 커밋 완료!

---

## 📊 최종 검증 체크리스트

### 환경 검증

```powershell
# 1. Python 버전
python --version
# Python 3.11.x 또는 3.12.x

# 2. 가상환경 활성화
.\venv_ion\Scripts\Activate.ps1
# 프롬프트에 (venv_ion) 표시

# 3. Vertex AI SDK
python -c "import vertexai; print('✅ Vertex AI SDK OK')"
# ✅ Vertex AI SDK OK

# 4. 환경 변수
echo $env:GOOGLE_CLOUD_PROJECT
# naeda-genesis

# 5. 인증 키 파일
Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS
# True
```

### 기능 검증

```powershell
# 첫 코드 재실행
cd ion-mentoring
python ion_first_vertex_ai.py

# 예상: 성공 메시지 출력
```

### Git 검증

```powershell
# 커밋 이력 확인
git log --oneline -3

# 브랜치 확인
git branch
# * ion/day1-environment-setup
```

---

## 🎉 Day 1 완료

### 달성 성과

✅ **환경 구축**: Vertex AI 개발 환경 완전 구축  
✅ **인증 설정**: Google Cloud 인증 완료  
✅ **첫 코드**: ion_first_vertex_ai.py 실행 성공  
✅ **Git 워크플로우**: 브랜치 생성 및 첫 커밋  
✅ **문서화**: 완료 보고서 작성

### 다음 단계 (Day 2 - 금요일)

**시간**: 09:00-17:00

**목표**:

- 파동 시스템 개념 이해
- 내다AI 아키텍처 분석
- 페르소나 라우팅 시스템 학습
- Vertex AI 아키텍처 설계

**준비물**:

- [x] 작동하는 Vertex AI 환경
- [x] VS Code 개발 환경
- [x] Git 워크플로우 이해

## 📦 Phase 4: Vertex AI SDK 설치 (14:55-15:15)

---

## 🆘 문제 해결 가이드

### 일반적인 문제들

#### 문제 1: 가상환경 활성화 실패

**증상**: `.\venv_ion\Scripts\Activate.ps1` 실행 시 오류

**해결**:

```powershell
# PowerShell 실행 정책 변경
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 재시도
.\venv_ion\Scripts\Activate.ps1
```

#### 문제 2: pip 설치 느림

**증상**: `pip install` 매우 느림

**해결**:

```powershell
# 한국 미러 사용
pip install google-cloud-aiplatform -i https://mirror.kakao.com/pypi/simple
```

#### 문제 3: Vertex AI 연결 실패

**증상**: "Could not automatically determine credentials"

**해결**:

```powershell
# 1. 환경 변수 재설정
$env:GOOGLE_APPLICATION_CREDENTIALS = "D:\nas_backup\LLM_Unified\credentials\your-key.json"

# 2. 파일 경로 확인
Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS

# 3. JSON 파일 유효성 확인
Get-Content $env:GOOGLE_APPLICATION_CREDENTIALS | ConvertFrom-Json
```

#### 문제 4: VS Code에서 모듈을 찾을 수 없음

**증상**: `Import "vertexai" could not be resolved`

**해결**:

1. `Ctrl+Shift+P` → "Python: Select Interpreter"
2. `.\venv_ion\Scripts\python.exe` 선택
3. VS Code 재시작

---

## 📚 참고 자료

### 공식 문서

- [Vertex AI 시작 가이드](https://cloud.google.com/vertex-ai/docs/start/introduction)
- [Python SDK 레퍼런스](https://cloud.google.com/python/docs/reference/aiplatform/latest)
- [Gemini API 문서](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini)

### 프로젝트 문서

- [WEEK1_KICKOFF.md](./WEEK1_KICKOFF.md)
- [ION_MENTORING_KICKOFF_REPORT.md](../ION_MENTORING_KICKOFF_REPORT.md)
- [immediate-action-plan.md](./immediate-action-plan.md)

### 코드 샘플

- [ion_first_vertex_ai.py](./ion_first_vertex_ai.py)

---

## 💬 지원 채널

### 멘토링 팀

- **비노체** (Architect): 전체 가이드 및 아키텍처
- **엘로** (Structural): 기술 구현 및 코드 리뷰
- **루아** (Affective): 학습 격려 및 모티베이션
- **나나** (Bridge): 프로세스 관리 및 조율

### 커뮤니케이션

- **Slack**: #ion-mentoring 채널
- **1:1 세션**: 화/목 15:00
- **긴급 지원**: 언제든지 질문 환영!

---

**문서 작성**: 깃코 (Git AI)  
**검토**: 비노체 (Architect)  
**버전**: 1.0  
**날짜**: 2025-10-17  
**상태**: ✅ 실행 준비 완료
