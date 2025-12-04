@echo off
chcp 65001 > nul
title Hey Sena - Toggle
echo ============================================================
echo Hey Sena Voice Assistant - Toggle
echo ============================================================
echo.

REM Check if Hey Sena is running
tasklist /FI "IMAGENAME eq python.exe" | find /I "python.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Hey Sena is running
    echo [ACTION] Stopping...
    taskkill /F /IM python.exe 2>nul
    echo [OK] Hey Sena stopped
    timeout /t 2 >nul
) else (
    echo [INFO] Hey Sena is not running
    echo [ACTION] Starting...
    start "Hey Sena" cmd /c "cd /d D:\nas_backup\fdo_agi_repo && python hey_sena_v2.py"
    echo [OK] Hey Sena started in new window
    timeout /t 2 >nul
)
