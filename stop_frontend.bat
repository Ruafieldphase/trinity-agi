@echo off
echo ====================================
echo Stopping Frontend Services
echo ====================================

REM Kill Node.js processes (Dashboard)
echo [1/2] Stopping Dashboard (Node.js)...
taskkill /F /IM node.exe 2>nul
if %errorlevel% == 0 (
    echo Dashboard stopped.
) else (
    echo No Dashboard process found.
)

REM Kill Active Trinity Python process (Port 3005)
echo [2/2] Stopping Active Trinity (Port 3005)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3005') do (
    taskkill /F /PID %%a 2>nul
    if %errorlevel% == 0 (
        echo Active Trinity stopped.
    )
)

echo.
echo ====================================
echo Frontend services stopped.
echo ====================================
pause
