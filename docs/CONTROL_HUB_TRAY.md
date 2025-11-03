# AGI Control Hub Tray

Windows 작업표시줄에 아이콘으로 상주하여, 자주 쓰는 운영/모니터링 작업을 한곳에서 실행할 수 있게 해주는 간단한 트레이 유틸리티입니다.

## 시작/중지

- VS Code 작업으로 실행/중지
  - Control Hub: Start (Tray)
  - Control Hub: Stop (Tray)
  - Control Hub: Restart (Tray)

시작하면 우측 하단 트레이에 "AGI Control Hub" 아이콘이 생깁니다. 아이콘을 우클릭하여 메뉴를 엽니다.

## 제공 메뉴

- 🟢 Unified Dashboard (24h, HTML): 24시간 리포트를 생성하고 최신 대시보드를 엽니다.
- 🚀 Enhanced Dashboard (GPU+Queue+LLM): 확장 대시보드를 브라우저로 엽니다.
- ❤️ AGI Quick Health (fast): 빠른 헬스 체크를 JSON only로 수행합니다.
- 🌅 Morning Kickoff (1h, open): 모닝 킥오프(1시간) 리포트를 생성/오픈합니다.
- 🗄️ End of Day Backup: 하루 마감 백업을 실행합니다.
- 📦 Queue: Ensure Server (8091): 로컬 큐 서버를 보장(없으면 기동)합니다.
- 👷 Queue: Ensure Worker: 워커 프로세스를 보장(없으면 기동)합니다.
- 🛡️ Watchdog: Start: 워치독(자가 복구 감시) 시작.
- 🛑 Watchdog: Stop: 워치독 종료.
- 📊 Open Latest Dashboard (HTML): 최신 HTML 대시보드 열기.
- 📄 Open Latest Report (MD): 최신 모니터링 리포트(MD) VS Code로 열기.
- ℹ️ About / ❎ Exit Control Hub: 정보/종료.

## 요구 사항

- OS: Windows
- Shell: Windows PowerShell 5.1 권장 (VS Code 기본 셸 환경에서 동작)
- 이 스크립트는 STA 모드와 단일 인스턴스를 자동 보장합니다. 하위 작업은 별도 프로세스로 `-ExecutionPolicy Bypass` 및 `Hidden` 창으로 실행됩니다.

## 위치

- 스크립트: `scripts/control_hub_tray.ps1`
- 산출물: `outputs/` 폴더 내 최신 리포트/대시보드 파일을 사용합니다.
