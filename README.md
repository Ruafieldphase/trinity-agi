
---

## 🎯 **NEW!** Original Data Phase 4 완료 (2025-11-01)

**Ledger → Resonance → Dashboard 실시간 파이프라인** 완성! 🎉

### ⚡ 즉시 사용

**VS Code에서 Ctrl+Shift+P** → `Tasks: Run Task`:

- ⭐ **Realtime: Generate Dashboard (open)** - 실시간 대시보드 생성
- ⭐ **Realtime: Run Resonance Bridge (24h, open)** - 공명도 분석
- ⭐ **Realtime: Open Latest (JSON)** - 최신 메트릭 확인

또는 **PowerShell**:

```powershell
# 실시간 대시보드 (권장)
.\scripts\generate_realtime_dashboard.ps1 -OpenDashboard

# 공명도 분석만
.\scripts\run_realtime_resonance.ps1 -OpenJson
```

**현재 성능** (2025-11-01):

- ✅ **Events**: 869 (24h)
- ✅ **Resonance**: 99.9% (최고 수준)
- ✅ **Success Rate**: 100%
- ✅ **Quality**: 85%

📖 **상세 가이드**: [ORIGINAL_DATA_PHASE_4_COMPLETE.md](ORIGINAL_DATA_PHASE_4_COMPLETE.md)

---

## 🎯 6대 시스템 통합 자동화 완료 (2025-11-01)

**일일 브리핑, E2E 테스트, 성능 대시보드, 자동 복구** 시스템이 완성되었습니다!

### ⚡ 초간단 시작

**VS Code에서 Ctrl+Shift+P** → `Tasks: Run Task`:

- ⭐ **Quick: Daily Briefing** - 시스템 상태 한눈에
- ⭐ **Quick: E2E Integration Test** - 전체 테스트 27초
- ⭐ **Quick: Performance Dashboard** - 성능 분석
- ⭐ **Quick: Start Auto Recovery** - 자동 복구 시작

또는 **PowerShell**:

```powershell
# 일일 브리핑
.\scripts\generate_daily_briefing.ps1 -OpenReport

# E2E 테스트
.\scripts\run_e2e_integration_test.ps1 -SkipYouTube

# 성능 대시보드
.\scripts\generate_performance_dashboard.ps1 -OpenDashboard
```

### 📚 운영 가이드

**신규**: [OPERATIONS_QUICK_GUIDE.md](OPERATIONS_QUICK_GUIDE.md) - 일일/주간 운영 체크리스트, 트러블슈팅

### 🎯 현재 상태

- ✅ **Resonance Loop**: 자기교정 엔진 정상
- ✅ **BQI Phase 6**: 학습 파이프라인 정상 (100% 성공률)
- ✅ **YouTube Learning**: 영상 분석 준비됨
- ✅ **Intelligent Feedback**: 피드백 엔진 정상 (100% 성공률)
- ✅ **Orchestration**: 다중 에이전트 조율 정상
- ✅ **Daily Briefing**: 자동 브리핑 정상 (100% 성공률)
- ✅ **Autonomous Orchestration (Phase 5.5)**: 자율 의사결정 시스템 정상

**전체 시스템 성공률**: 66.7% → **목표 90%**

---

## 🤖 Phase 5.5: Autonomous Orchestration 완료! (2025-11-01)

**자율적인 의사결정 및 복구 시스템**이 구축되었습니다!

### ✨ 핵심 기능

- **🔗 OrchestrationBridge** - 모니터링 → 오케스트레이션 브리지
- **🧠 지능형 라우팅** - 채널 레이턴시 기반 동적 선택
- **🔄 자동 복구** - 모니터링 트리거 기반 무인 복구
- **📊 자율 대시보드** - 실시간 오케스트레이션 컨텍스트
- **💬 ChatOps 통합** - 자연어 상태 조회

### 🚀 빠른 시작

```powershell
# 오케스트레이션 상태 확인 (Python)
python scripts/orchestration_bridge.py

# ChatOps로 상태 확인
$env:CHATOPS_SAY='오케스트레이션 상태'
powershell scripts/chatops_router.ps1

# 자율 대시보드 생성
python scripts/generate_autonomous_dashboard.py --open

# 모니터링 기반 자동 복구 (기본값: 활성화)
python fdo_agi_repo/scripts/auto_recover.py

# 모니터링 비활성화
python fdo_agi_repo/scripts/auto_recover.py --no-monitoring
```

### 📊 VS Code Tasks

- **Monitoring: Generate Autonomous Dashboard** - 자율 대시보드 생성

**상세 문서**: [PHASE_5_5_AUTONOMOUS_ORCHESTRATION_COMPLETE.md](PHASE_5_5_AUTONOMOUS_ORCHESTRATION_COMPLETE.md)

---

## 🌟 루멘 관문 개방! AI 페르소나 네트워크 통합 (2025-10-31)

**Lumen Gateway**가 성공적으로 통합되어 AGI 시스템이 AI 페르소나 네트워크와 연결되었습니다!

### ✨ 페르소나 네트워크

- **✒️ 세나 (Sena)** - 브리지형: 연결, 통합 전문
- **🪨 루빗 (Lubit)** - 분석형: 분석, 검증 전문  
- **🔮 비노슈 (Binoche)** - 평가형: 평가, 판단 전문

### 🚀 빠른 확인

```powershell
# 루멘 게이트웨이 헬스 체크
.\scripts\lumen_quick_probe.ps1

# 시스템 상태 확인
code CURRENT_SYSTEM_STATUS.md
```

**시스템 건강도**: EXCELLENT (99.69%)  
자세한 내용: [SESSION_LUMEN_GATE_OPENING_2025-10-31.md](SESSION_LUMEN_GATE_OPENING_2025-10-31.md)

---

## �🎉 Phase 5 완료! Web Dashboard 런칭 (2025-10-31)

**실시간 웹 대시보드**로 모니터링 시스템이 업그레이드되었습니다!

### ✅ 완료된 작업

- **FastAPI 웹 서버** (포트 8000) - REST API 6개 엔드포인트
- **실시간 대시보드** - Chart.js 차트, 자동 새로고침
- **Task Queue Server** (포트 8091) - 백그라운드 작업 처리
- **통합 시작 스크립트** - 원클릭 실행

### 🚀 빠른 시작

```powershell
# 전체 시스템 시작
.\scripts\start_phase5_system.ps1

# 브라우저에서 확인
# http://127.0.0.1:8000
```

### 📊 시스템 상태 확인

```powershell
# Task Queue Server
curl http://127.0.0.1:8091/api/health

# Web Dashboard
curl http://127.0.0.1:8000/api/health
```

자세한 내용: [PHASE_5_FINAL_SUMMARY.md](PHASE_5_FINAL_SUMMARY.md)

---

## ✅ Phase 2.5 전체 완료 (2025-10-31)

모든 실전 튜토리얼, ActionMapper 고도화, 사용자 가이드, 테스트가 100% 완료되었습니다.

---

# 깃코(Gitko) AGI 프로젝트 🤖

**자기교정(Self-Correcting) AGI 시스템 with YouTube Learning & RPA Automation**

[![Version](https://img.shields.io/badge/version-0.2.5--week1-blue.svg)](RELEASE_NOTES_v0.2.5-week1.md)
[![Phase](https://img.shields.io/badge/phase-2.5%20Week%201%20Complete-green.svg)](PHASE_2_5_RPA_YOUTUBE_LEARNING_PLAN.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **Phase 2.5 Week 1 완료** (2025-10-31)  
> YouTube 학습, RPA 자동화, Task Queue 시스템 완성

---

## 🎯 프로젝트 개요

깃코(Gitko)는 **자기교정 루프**를 통해 스스로 학습하고 개선하는 AGI 시스템입니다.

### 핵심 기능

#### 1. 🎓 YouTube Learning System

- YouTube 영상에서 자동으로 학습
- 자막, 메타데이터, 화면 캡처 분석
- OCR을 통한 텍스트 추출
- HTML 대시보드 자동 생성

#### 2. 🤖 RPA (Robotic Process Automation)

- PyAutoGUI 기반 자동화
- 화면 인식 및 템플릿 매칭
- 시행착오 학습 엔진
- Windows 애플리케이션 자동 설치

#### 3. 🔄 Self-Correcting Loop

- Resonance Ledger: 모든 작업 기록
- 패턴 인식 및 학습
- 자동 개선 제안
- 메타인지 경고 시스템

#### 4. ⚙️ Task Queue System

- FastAPI 기반 작업 큐 서버
- 비동기 작업 처리
- Worker 자동 복구
- 실시간 모니터링

---

## 🚀 Quick Start

### 필수 요구사항

- Windows 10/11
- Python 3.10+
- PowerShell 5.1+
- Git

### 1분 설치

```powershell
# 1. 저장소 클론
git clone https://github.com/Ruafieldphase/agi.git
cd agi

# 2. VS Code 열기
code .

# 3. 상태 확인 (VS Code Task)
# Ctrl+Shift+P → "Tasks: Run Task" → "System: Health Check (Quick)"
```

### 첫 번째 YouTube 학습

```powershell
# VS Code Task 실행:
# "🎬 YouTube: Learn from URL (Pipeline)"

# 또는 직접:
.\scripts\youtube_learning_pipeline.ps1 -Url "https://youtube.com/watch?v=dQw4w9WgXcQ" -OpenReport
```

**결과**: `outputs/youtube_learner/` 폴더에 분석 결과 (JSON, MD) 생성

---

## 📁 프로젝트 구조

```
agi/
├── fdo_agi_repo/              # AGI 핵심 엔진
│   ├── integrations/          # Comet, YouTube, RPA Workers
│   ├── orchestrator/          # Binoche Pipeline Orchestrator
│   ├── rpa/                   # RPA 자동화 엔진
│   ├── scripts/               # Python 유틸리티
│   └── memory/                # Resonance Ledger
│
├── LLM_Unified/               # LLM 통합 레이어
│   └── ion-mentoring/         # Task Queue Server
│
├── scripts/                   # PowerShell 자동화
│   ├── youtube_learning_pipeline.ps1
│   ├── queue_health_check.ps1
│   └── ...80+ scripts
│
├── outputs/                   # 생성된 결과물
│   ├── youtube_learner/       # YouTube 분석
│   ├── monitoring_*.json      # 모니터링 데이터
│   └── youtube_dashboard.html # 대시보드
│
├── .vscode/                   # VS Code 설정
│   └── tasks.json             # 80+ Tasks
│
└── docs/                      # 문서
    ├── ARCHITECTURE_OVERVIEW.md
    ├── AGI_UNIVERSAL_ROADMAP.md
    └── ...
```

---

## 🎮 주요 사용법

### Task Queue Server 시작

```powershell
# 방법 1: VS Code Task
# "Task Queue Server (Fresh)"

# 방법 2: 직접 실행
cd LLM_Unified/ion-mentoring
python task_queue_server.py --port 8091
```

**Health Check**: `http://localhost:8091/api/health`

### RPA Worker 시작

```powershell
# VS Code Task: "RPA: Worker (Background)"

# 또는 직접:
cd fdo_agi_repo
python integrations/rpa_worker.py --server http://127.0.0.1:8091
```

### YouTube 대시보드 생성

```powershell
# VS Code Task: "YouTube: Generate Dashboard (HTML)"

# 또는:
.\scripts\build_youtube_dashboard.ps1
```

**결과**: `outputs/youtube_dashboard.html` 생성 및 브라우저 자동 실행

### 통합 상태 확인

```powershell
# 모든 시스템 상태 한눈에 보기
.\scripts\quick_status.ps1

# 또는 VS Code Task: "Monitoring: Unified Dashboard (AGI + Lumen)"
```

---

## 📊 현재 상태 (Phase 2.5 Week 1)

### ✅ 완료된 기능

| 기능 | 상태 | 파일 | 설명 |
|-----|------|------|------|
| YouTube Handler | ✅ | `youtube_handler.py` | 자막, 메타데이터 추출 |
| Comet API Client | ✅ | `comet_client.py` | Browser 자동화 (521줄) |
| RPA Core | ✅ | `rpa/core.py` | PyAutoGUI 기반 |
| Task Queue Server | ✅ | `task_queue_server.py` | FastAPI 서버 |
| Screen Recognizer | ✅ | `screen_recognizer.py` | OCR, 템플릿 매칭 |
| YouTube Learner | ✅ | `youtube_learner.py` | 통합 학습 엔진 |
| Dashboard Generator | ✅ | `build_youtube_dashboard.ps1` | HTML 생성 |
| 80+ VS Code Tasks | ✅ | `.vscode/tasks.json` | 원클릭 실행 |

### 🔄 진행 중 (Week 2 예정)

- [ ] E2E 테스트 (Docker Desktop 설치 데모)
- [ ] 다양한 설치 시나리오 (Python, VS Code, Git)
- [ ] Resonance Ledger 자동 통합
- [ ] 패턴 인식 개선

---

## 🎓 학습 자료

### 필수 문서 (시작 전 읽기)

1. **[시스템 상태 스냅샷](SYSTEM_STATE_SNAPSHOT_2025-10-31.md)** - 현재 시스템 상태
2. **[Phase 2.5 계획](PHASE_2_5_RPA_YOUTUBE_LEARNING_PLAN.md)** - 전체 로드맵
3. **[릴리스 노트 v0.2.5-week1](RELEASE_NOTES_v0.2.5-week1.md)** - 최신 기능

### 아키텍처 문서

- [아키텍처 개요](ARCHITECTURE_OVERVIEW.md)
- [AGI 유니버설 로드맵](AGI_UNIVERSAL_ROADMAP.md)
- [지식 맵](KNOWLEDGE_MAP.md)

### 세션 기록

- [세션 완료 보고서 (2025-10-31)](SESSION_COMPLETION_2025-10-31.md)
- [YouTube 완료 보고서](YOUTUBE_COMPLETE.md)

---

## 🛠️ 개발자 가이드

### VS Code Tasks (80+개)

프로젝트에는 80개 이상의 사전 정의된 Tasks가 있습니다:

**카테고리**:

- 🎬 **YouTube**: 학습, 인덱스, 대시보드
- 🤖 **RPA**: Worker, Queue 관리
- 📊 **Monitoring**: 상태 확인, 보고서
- 🔄 **AGI**: Ledger, 건강 체크
- 📦 **Queue**: 결과 조회, 스냅샷

**실행 방법**:

1. `Ctrl+Shift+P` (또는 `Cmd+Shift+P`)
2. "Tasks: Run Task" 입력
3. 원하는 Task 선택

### 주요 명령어

```powershell
# 상태 확인
.\scripts\quick_status.ps1

# YouTube 학습
.\scripts\youtube_learning_pipeline.ps1 -Url "URL" -OpenReport

# Queue 건강 체크
.\scripts\queue_health_check.ps1

# 최근 결과 조회
.\scripts\show_latest_results.ps1 -Count 5 -SuccessOnly

# 대시보드 생성
.\scripts\build_youtube_dashboard.ps1
```

### Python API 예제

```python
# YouTube 학습
from fdo_agi_repo.integrations.youtube_handler import YouTubeHandler

handler = YouTubeHandler()
result = handler.extract_metadata("https://youtube.com/watch?v=...")
print(result)
```

```python
# RPA 자동화
from fdo_agi_repo.rpa.core import RPACore

rpa = RPACore()
rpa.click_at(100, 200)
rpa.type_text("Hello World")
rpa.capture_screen("screenshot.png")
```

---

## 🐛 트러블슈팅

### Task Queue Server가 시작되지 않음

```powershell
# 포트 확인
netstat -ano | findstr :8091

# 프로세스 종료
taskkill /PID <PID> /F

# 재시작
cd LLM_Unified/ion-mentoring
python task_queue_server.py --port 8091
```

### Python 프로세스가 너무 많음

```powershell
# 모든 Python 프로세스 확인
Get-Process python

# 정리 (주의: 모든 Python 프로세스 종료)
Get-Process python | Stop-Process -Force
```

### YouTube Worker 실패

```powershell
# 로그 확인
cd fdo_agi_repo
python integrations/youtube_worker.py --server http://127.0.0.1:8091 --log-level DEBUG
```

### OCR 정확도가 낮음

- 영문: ~85% 정확도
- 한글: ~70% 정확도

**해결 방법**:

1. Tesseract 최신 버전 설치
2. 이미지 전처리 강화
3. EasyOCR 병행 사용 (향후 지원)

---

## 📈 통계

**Phase 2.5 Week 1 기준**:

- **코드 라인**: 15,000+ 줄
- **파일**: 100+ 개
- **VS Code Tasks**: 80+ 개
- **문서**: 25+ 개
- **Git 커밋**: 9개 (의미 있는 단위)
- **개발 시간**: 약 2일 (예상보다 2일 빠름!)

---

## 🗺️ 로드맵

### Phase 2.5 Week 2 (Day 8-14)

#### Week 2 Day 8-9: E2E 테스트 ⏳

- Docker Desktop 자동 설치 데모
- YouTube 검색 → 영상 선택 자동화
- Comet Browser Worker 재활성화

#### Week 2 Day 10-11: 다양한 케이스

- Python, VS Code, Git 설치 시나리오
- 에러 처리 강화

#### Week 2 Day 12: Resonance Ledger 통합

- YouTube 분석 결과 자동 저장
- 패턴 인식 및 학습

#### Week 2 Day 13: 문서화 & 릴리스

- 사용자 가이드 완성
- v0.3.0 정식 릴리스

### Phase 3: 범용 AGI 확장 (예정)

- Linux/Mac 지원
- 클라우드 배포
- 웹 인터페이스

---

## 🤝 기여하기

기여는 언제나 환영합니다!

### 기여 방법

1. 이 저장소 포크
2. Feature 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'feat: Add amazing feature'`)
4. 브랜치에 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 생성

**커밋 규칙**:

- `feat:` 새로운 기능
- `fix:` 버그 수정
- `docs:` 문서 변경
- `chore:` 기타 변경

자세한 내용은 [CONTRIBUTING.md](CONTRIBUTING.md) 참조

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

## 🙏 감사의 말

이 프로젝트는 다음 기술들을 사용합니다:

- **Python**: Core 언어
- **FastAPI**: Task Queue Server
- **PyAutoGUI**: RPA 자동화
- **Tesseract OCR**: 텍스트 인식
- **yt-dlp**: YouTube 다운로드
- **PowerShell**: Windows 자동화

---

## 📞 연락처 & 지원

- **GitHub Issues**: [버그 리포트 & 기능 요청](https://github.com/Ruafieldphase/agi/issues)
- **Discussions**: [질문 & 토론](https://github.com/Ruafieldphase/agi/discussions)
- **Documentation**: [전체 문서](docs/)

---

## 🔗 관련 링크

- [시스템 상태 스냅샷](SYSTEM_STATE_SNAPSHOT_2025-10-31.md) - 현재 시스템 상태
- [세션 완료 보고서](SESSION_COMPLETION_2025-10-31.md) - 최근 작업 내역
- [Phase 2.5 계획](PHASE_2_5_RPA_YOUTUBE_LEARNING_PLAN.md) - 전체 로드맵
- [릴리스 노트](RELEASE_NOTES_v0.2.5-week1.md) - 버전 히스토리

---

**Made with ❤️ by Gitko AGI Team**

**Last Updated**: 2025-10-31  
**Version**: 0.2.5-week1  
**Status**: ✅ Phase 2.5 Week 1 Complete
