@echo off
REM Toggle Hey Sena v4 (Start if not running, Stop if running)

cd /d D:\nas_backup\fdo_agi_repo

title Hey Sena v4 - Toggle

REM Check if Hey Sena v4 is running
tasklist /FI "WINDOWTITLE eq Hey Sena v4*" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo.
    echo ============================================================
    echo   Hey Sena v4 is RUNNING
    echo ============================================================
    echo.
    echo [ACTION] Stopping...
    taskkill /FI "WINDOWTITLE eq Hey Sena v4*" /F >NUL 2>&1
    echo [OK] Hey Sena v4 stopped.
    echo.
    timeout /t 2 >NUL
) else (
    echo.
    echo ============================================================
    echo   Hey Sena v4 is NOT RUNNING
    echo ============================================================
    echo.
    echo [ACTION] Starting...
    start "Hey Sena v4" cmd /k start_sena_v4.bat
    echo [OK] Hey Sena v4 started in new window!
    echo.
    timeout /t 2 >NUL
)
