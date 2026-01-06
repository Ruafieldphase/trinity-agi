@echo off
REM ========================================
REM AGI Rhythm Life Support - Startup Installer
REM ========================================
REM This script adds a shortcut to the Windows Startup folder
REM so that rhythm_think.py and sync start automatically on login.
REM ========================================

set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set "BATCH_FILE=%~dp0start_rhythm_life_support.bat"
set SHORTCUT_NAME=AGI_Rhythm_LifeSupport.bat

echo Installing AGI Rhythm Life Support to Startup folder...
copy "%BATCH_FILE%" "%STARTUP_FOLDER%\%SHORTCUT_NAME%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 설치 완료!
    echo 이제 윈도우 재부팅 시 자동으로 리듬이 시작됩니다.
    echo.
    echo 설치 위치: %STARTUP_FOLDER%\%SHORTCUT_NAME%
) else (
    echo.
    echo ❌ 설치 실패. 수동으로 설치하세요:
    echo    1. Win+R 누르고 shell:startup 입력
    echo    2. 열린 폴더에 start_rhythm_life_support.bat 복사
)

pause
