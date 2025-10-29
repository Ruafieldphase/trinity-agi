@echo off
title Hey Sena - Stopping...
echo ============================================================
echo Stopping Hey Sena Voice Assistant
echo ============================================================
echo.

REM Kill all python processes running hey_sena
taskkill /F /FI "WINDOWTITLE eq Hey Sena*" 2>nul
taskkill /F /FI "IMAGENAME eq python.exe" /FI "MEMUSAGE gt 50000" 2>nul

echo.
echo [OK] Hey Sena stopped
echo.
timeout /t 2 >nul
