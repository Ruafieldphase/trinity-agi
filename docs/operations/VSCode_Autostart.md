# VS Code 자동 실행 (로그온 후 지연)

이 워크스페이스는 사용자 로그인 후 일정 시간(기본 5분) 경과 뒤 VS Code가 자동으로 열리도록 설정되어 있습니다.

## 현재 설정

- **워크스페이스**: `c:\workspace\agi`
- **지연 시간**: 5분 (로그인 완료 후)
- **등록 방식**: 시작프로그램 바로가기 (사용자 Startup 폴더)
- **중복 방지**: VS Code가 이미 실행 중이면 재실행하지 않음

## 스크립트 구성

- `scripts/register_vscode_autostart.ps1` - 자동 실행 등록/해제/상태 확인
- `scripts/launch_vscode_after_logon.ps1` - VS Code 런처 (중복 실행 방지)
- `scripts/delayed_launch_vscode.ps1` - 지연 실행 헬퍼

## 사용법

### 상태 확인

```powershell
.\scripts\register_vscode_autostart.ps1 -Status
```

또는 VS Code Task:

- `VSCode Autostart: Check Status`

### 해제 (자동 실행 중지)

```powershell
.\scripts\register_vscode_autostart.ps1 -Unregister
```

또는 VS Code Task:

- `VSCode Autostart: Unregister`

### 재등록 (지연 시간 변경)

```powershell
# 10분 지연으로 변경 예시
.\scripts\register_vscode_autostart.ps1 -Unregister
.\scripts\register_vscode_autostart.ps1 -Register -DelayMinutes 10 -WorkspaceFolder "c:\workspace\agi"
```

또는 VS Code Task:

- `VSCode Autostart: Re-register (10min)` - 10분 지연
- `VSCode Autostart: Re-register (1min)` - 1분 지연 (빠른 테스트용)

## 폴백 전략

스크립트는 다음 순서로 자동 실행 방식을 시도합니다:

1. **예약 작업 (Scheduled Task)** - Task Scheduler API 사용 (권한 필요)
2. **schtasks 명령** - 명령줄 도구 사용 (권한 필요)
3. **시작프로그램 바로가기** - Startup 폴더에 .lnk 생성 (권한 불필요, **현재 사용 중**)

일반 사용자 권한 환경에서는 자동으로 시작프로그램 방식을 사용하며, 이는 신뢰성 높고 간단합니다.

## 파일 위치

- 바로가기 위치: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VSCode_AutoLaunch_AfterLogon.lnk`
- 로그 파일: `c:\workspace\agi\outputs\vscode_autostart_YYYYMMDD.log`

## 문제 해결

### VS Code가 자동으로 열리지 않음

1. 상태 확인:

   ```powershell
   .\scripts\register_vscode_autostart.ps1 -Status
   ```

2. 바로가기 존재 확인:

   ```powershell
   Test-Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\VSCode_AutoLaunch_AfterLogon.lnk"
   ```

3. 로그 확인:

   ```powershell
   Get-Content .\outputs\vscode_autostart_*.log -Tail 50
   ```

### 지연 시간이 너무 길거나 짧음

- 지연 시간을 조정하려면 해제 후 원하는 시간으로 재등록하세요:

  ```powershell
  .\scripts\register_vscode_autostart.ps1 -Unregister
  .\scripts\register_vscode_autostart.ps1 -Register -DelayMinutes 3 -WorkspaceFolder "c:\workspace\agi"
  ```

### 중복 실행 방지가 작동하지 않음

- `launch_vscode_after_logon.ps1` 스크립트는 `Code.exe` 프로세스를 확인합니다.
- VS Code Insiders나 다른 변형을 사용 중이라면 스크립트 수정이 필요할 수 있습니다.

## 검증 완료

- ✅ 2025-11-06: 재부팅 후 5분 지연 자동 실행 성공 확인
- ✅ 중복 실행 방지 동작 확인
- ✅ 워크스페이스 자동 로드 확인

## 관련 문서

- `AGENTS.md` - 에이전트 간 핸드오프 가이드
- `docs/AGENT_HANDOFF.md` - 상세 프로젝트 컨텍스트
