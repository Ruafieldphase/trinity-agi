# 📁 Gitko Agent Extension - 프로젝트 구조

**정리 완료일**: 2025년 11월 15일  
**버전**: v0.3.1

---

## 디렉토리 구조

```
gitko-agent-extension/
├── .vscode/                    # VS Code 설정
│   ├── launch.json            # 디버그 설정
│   └── tasks.json             # Task 정의
│
├── docs/                       # 📚 문서 (NEW!)
│   ├── archive/               # 구버전 보고서 보관
│   │   ├── COMPLETION_REPORT_v0.2.0.md
│   │   ├── COMPLETION_REPORT_v0.2.1.md
│   │   ├── COMPLETION_REPORT_v0.3.0.md
│   │   ├── FINAL_SUMMARY.md
│   │   └── FINAL_ENHANCEMENTS.md
│   │
│   ├── releases/              # 릴리스 노트 아카이브
│   │   ├── RELEASE_NOTES_v0.2.0.md
│   │   ├── RELEASE_NOTES_v0.2.1.md
│   │   └── RELEASE_NOTES_v0.3.0.md
│   │
│   ├── AUTOMATIC_AGENT_GUIDE.md   # Agent 자동 호출 가이드
│   ├── CHEATSHEET.md              # 빠른 참조
│   ├── DEPLOYMENT_CHECKLIST.md    # 배포 체크리스트
│   ├── RELEASE_CHECKLIST.md       # 릴리스 체크리스트
│   ├── SETUP_GUIDE.md             # 상세 설정 가이드
│   └── USAGE_EXAMPLES.md          # 실전 사용 예제
│
├── scripts/                    # ⚙️ 스크립트 (NEW!)
│   ├── setup/                 # 설치 관련 스크립트
│   │   ├── install_tesseract.ps1
│   │   ├── install_tesseract_admin.ps1
│   │   ├── install_tesseract_choco.ps1
│   │   ├── install_tesseract_manual.ps1
│   │   ├── install_tesseract_winget.ps1
│   │   └── configure_tesseract.ps1
│   │
│   ├── auto_resume_session.py     # 세션 자동 복원
│   ├── reload_vscode_with_ocr.py  # OCR 재로드
│   ├── troubleshoot.ps1           # 자동 진단 & 수정
│   └── project-stats.ps1          # 프로젝트 통계
│
├── src/                        # 💻 소스 코드
│   ├── extension.ts           # 메인 진입점
│   ├── computerUse.ts         # Computer Use 기능
│   ├── httpTaskPoller.ts      # HTTP Task Poller
│   ├── taskQueueMonitor.ts    # Task Queue 모니터
│   ├── resonanceLedgerViewer.ts # Resonance Ledger 뷰어
│   ├── performanceViewer.ts   # 성능 모니터
│   ├── activityTracker.ts     # 활동 추적기
│   ├── configValidator.ts     # 설정 검증기
│   ├── logger.ts              # 로거
│   ├── integrationTest.ts     # 통합 테스트
│   └── devUtils.ts            # 개발 유틸리티
│
├── tests/                      # 🧪 테스트 (NEW!)
│   ├── test-extension.ps1     # 확장 기능 테스트
│   ├── test_integration.ps1   # PowerShell 통합 테스트
│   └── test_integration_simple.py # Python 통합 테스트
│
├── resources/                  # 🎨 리소스
│   └── icon.png               # 확장 아이콘
│
├── out/                        # 📦 빌드 출력 (자동 생성)
│   └── *.js                   # 컴파일된 JavaScript
│
├── node_modules/               # 📦 의존성 (자동 생성)
│
├── .gitignore                  # Git 무시 파일
├── .vscodeignore              # VSIX 패키징 무시 파일
├── package.json               # 패키지 정의
├── package-lock.json          # 의존성 잠금
├── tsconfig.json              # TypeScript 설정
├── requirements.txt           # Python 의존성 (NEW!)
│
├── README.md                  # 📖 메인 문서
├── QUICKSTART.md              # 🚀 빠른 시작 가이드
├── COMPLETION_REPORT.md       # 📊 최신 완료 보고서
├── RELEASE_NOTES.md           # 📝 최신 릴리스 노트
├── PROJECT_COMPLETION.md      # 🎉 프로젝트 완성 요약
├── 실행방법.md                 # 한글 실행 가이드
│
└── organize_workspace.ps1     # 🔧 워크스페이스 정리 스크립트
```

---

## 주요 파일 설명

### 핵심 문서

| 파일 | 용도 |
|------|------|
| `README.md` | 프로젝트 메인 문서 (전체 개요) |
| `QUICKSTART.md` | 5분 빠른 시작 가이드 |
| `COMPLETION_REPORT.md` | 최신 완료 보고서 (v0.3.0) |
| `RELEASE_NOTES.md` | 최신 릴리스 노트 (v0.3.1) |
| `PROJECT_COMPLETION.md` | 프로젝트 완성 요약 |

### 소스 코드

| 파일 | 역할 |
|------|------|
| `src/extension.ts` | VS Code Extension 메인 진입점 |
| `src/computerUse.ts` | Computer Use (OCR, 클릭, 타이핑) |
| `src/taskQueueMonitor.ts` | Task Queue 실시간 모니터링 |
| `src/resonanceLedgerViewer.ts` | Resonance Ledger 시각화 |
| `src/performanceViewer.ts` | 성능 메트릭 대시보드 |
| `src/activityTracker.ts` | 사용자 활동 추적 |

### 설정 파일

| 파일 | 용도 |
|------|------|
| `package.json` | NPM 패키지 정의 & VS Code 확장 설정 |
| `tsconfig.json` | TypeScript 컴파일러 설정 |
| `requirements.txt` | Python 의존성 정의 |
| `.gitignore` | Git 무시 파일 목록 |

---

## 빌드 & 실행

### 개발 모드

```powershell
# 1. 의존성 설치
npm install

# 2. TypeScript 컴파일
npm run compile
# 또는 watch 모드
npm run watch

# 3. Extension Development Host 실행
# F5 키 누르기
```

### 테스트

```powershell
# 자동 테스트
.\tests\test-extension.ps1

# 통합 테스트
.\tests\test_integration.ps1
```

### 패키징

```powershell
# VSIX 패키지 생성
npm install -g @vscode/vsce
vsce package

# 생성물: gitko-agent-extension-0.3.1.vsix
```

---

## 의존성

### TypeScript/JavaScript

```json
{
  "vscode": "^1.90.0",
  "axios": "^1.6.0"
}
```

### Python (선택적)

```
requests>=2.31.0
python-dotenv>=1.0.0
pytest>=7.4.0
```

---

## 문서 탐색 가이드

### 처음 시작하는 경우
1. `README.md` - 전체 개요 확인
2. `QUICKSTART.md` - 5분 설치 & 실행
3. `docs/USAGE_EXAMPLES.md` - 실전 사용법

### 개발하는 경우
1. `docs/SETUP_GUIDE.md` - 개발 환경 설정
2. `src/extension.ts` - 코드 구조 이해
3. `tests/` - 테스트 작성 & 실행

### 배포하는 경우
1. `docs/DEPLOYMENT_CHECKLIST.md` - 배포 전 체크리스트
2. `docs/RELEASE_CHECKLIST.md` - 릴리스 절차
3. `vsce package` - VSIX 생성

### 문제 해결
1. `scripts/troubleshoot.ps1` - 자동 진단
2. `README.md` - FAQ 섹션
3. GitHub Issues

---

## 변경 이력

### 2025-11-15: 워크스페이스 대규모 정리 ✨

**문제점**:
- 루트에 30+ 파일 혼재
- 구버전 문서와 최신 문서 혼재
- 테스트/스크립트 파일 분산

**개선 사항**:
- ✅ `docs/` 폴더 생성 (문서 중앙화)
- ✅ `docs/archive/` 생성 (구버전 보관)
- ✅ `docs/releases/` 생성 (릴리스 노트 아카이브)
- ✅ `tests/` 폴더 생성 (테스트 중앙화)
- ✅ `scripts/` 폴더 생성 (스크립트 정리)
- ✅ `requirements.txt` 생성 (Python 의존성 명시)
- ✅ `.gitignore` 개선
- ✅ README 링크 업데이트

**결과**:
- 루트 파일 30+ → 10개로 축소 (67% 감소)
- 문서 접근성 향상
- 프로젝트 구조 명확화

---

## 참고

이 구조는 **외부 검토 (2025-11-15)** 피드백을 반영하여 재설계되었습니다.

주요 개선 원칙:
- 📁 **명확한 디렉토리 구조**
- 📚 **문서 중앙화 및 버전 관리**
- 🧪 **테스트 코드 분리**
- ⚙️ **스크립트 조직화**
- 📦 **의존성 명시화**
