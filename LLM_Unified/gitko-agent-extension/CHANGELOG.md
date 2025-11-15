# Changelog

All notable changes to the Gitko AI Agent Orchestrator extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.1] - 2025-11-14

### Added
- **Activity Tracker**: 사용자 활동 추적 및 시각화
- Activity 통계 대시보드
- 사용 패턴 분석 기능

### Changed
- Performance Viewer UI 개선
- 로깅 메시지 최적화

### Fixed
- Activity Tracker 메모리 누수 수정
- 로그 출력 인코딩 문제 해결

---

## [0.3.0] - 2025-11-14

### Added
- **Performance Viewer**: 성능 메트릭 실시간 모니터링
- HTTP Task Poller 성능 대시보드
- Computer Use 작업 통계 표시

### Changed
- Task Queue Monitor UI 재설계
- Resonance Ledger 필터링 개선

### Fixed
- HTTP Poller 안정성 향상
- OCR 백엔드 폴백 로직 수정

---

## [0.2.1] - 2025-11-02

### Added
- 자동 테스트 스크립트 (`test-extension.ps1`)
- 문제 해결 스크립트 (`troubleshoot.ps1`)
- 프로젝트 통계 스크립트 (`project-stats.ps1`)

### Changed
- README 문서 개선
- 설정 검증 로직 강화

### Fixed
- Python 경로 자동 탐지 개선
- UTF-8 인코딩 처리 수정
- 타임아웃 처리 안정성 향상

---

## [0.2.0] - 2025-11-02

### Added
- **Task Queue Monitor**: Task Queue Server 실시간 모니터링
  - Health Status 표시
  - Success Rate 그래프
  - 작업 통계 (Pending, In-Flight, Completed, Failed)
  - 자동 갱신 (2초 주기)
  
- **Resonance Ledger Viewer**: AGI 자기교정 시스템 시각화
  - 최근 100개 이벤트 타임라인
  - Agent별 필터링 (Sena, Lubit, Binoche)
  - 파일 변경 자동 감지
  - 이벤트 상세 정보 표시

### Changed
- Extension 아키텍처 모듈화
- 로거 시스템 개선
- 설정 검증기 추가

### Fixed
- WebView 메모리 관리 개선
- 에러 처리 강화

---

## [0.1.0] - 2025-10-29

### Added
- **GitHub Copilot Language Model Tools 통합**
  - Sian Agent (코드 개선)
  - Lubit Agent (코드 리뷰)
  - Gitko Orchestrator (멀티 에이전트)
  
- **Chat Participant (`@gitko`)**
  - `/review` - 코드 리뷰
  - `/improve` - 코드 개선
  - `/parallel` - 병렬 작업

- **Computer Use (RPA/OCR)**
  - 화면 스캔 (`scan`)
  - 텍스트 찾기 (`find`)
  - 클릭 자동화 (`click`)
  - 키보드 입력 (`type`)
  - Tesseract / RapidOCR 지원

- **HTTP Task Poller**
  - Task Queue Server 연동 (Port 8091)
  - 원격 Computer Use 작업 실행
  - 자동 폴링 (2초 주기)
  - 안전 장치 (killswitch, failsafe)

- **설정 시스템**
  - Python 경로 자동 탐지
  - 스크립트 경로 자동 탐지
  - `${workspaceFolder}` 템플릿 지원
  - 타임아웃 설정
  - 로깅 제어

### Technical
- TypeScript 기반 VS Code Extension
- Python 백엔드 (gitko_cli.py, computer_use.py)
- WebView 기반 UI
- Output Channel 통합 로깅

---

## [Unreleased]

### Planned
- 통합 대시보드 (모든 모니터링 한 화면에)
- AI Agent 성능 메트릭
- 커스텀 에이전트 지원
- Cloud 동기화

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 0.3.1 | 2025-11-14 | Activity Tracker |
| 0.3.0 | 2025-11-14 | Performance Viewer |
| 0.2.1 | 2025-11-02 | Stability & Testing |
| 0.2.0 | 2025-11-02 | Task Queue Monitor, Resonance Ledger |
| 0.1.0 | 2025-10-29 | Initial Release |

---

## Links

- [Latest Release Notes](../RELEASE_NOTES.md)
- [Project Structure](../PROJECT_STRUCTURE.md)
- [Quick Start Guide](../QUICKSTART.md)
