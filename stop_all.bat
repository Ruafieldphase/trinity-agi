@echo off
echo ====================================
echo Stopping AGI Complete System
echo ====================================
echo.

REM Stop Frontend
echo [1/2] Stopping Frontend...
call stop_frontend.bat

REM Stop Backend
echo [2/2] Stopping Backend...
call stop_backend.bat

echo.
echo ====================================
echo AGI System Stopped
echo ====================================
pause
