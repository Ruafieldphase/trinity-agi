@echo off
echo ====================================
echo Starting AGI Complete System
echo ====================================
echo.

REM Start Backend Services
echo [1/2] Starting Backend Services...
call start_backend.bat

REM Wait for backend to stabilize
timeout /t 3 /nobreak >nul

REM Start Frontend Services (Silent)
echo [2/2] Starting Frontend Services (Silent)...
cscript //nologo start_frontend_silent.vbs

echo.
echo ====================================
echo AGI System Started!
echo ====================================
echo.
echo Services:
echo   Backend:  http://localhost:8104/unified
echo   Frontend: http://localhost:3000
echo.
echo To stop all services: run stop_all.bat
echo ====================================
