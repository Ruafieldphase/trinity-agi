@echo off
echo ====================================
echo Starting Frontend Services
echo ====================================

REM Create outputs directory if not exists
if not exist "outputs" mkdir outputs

REM Start Dashboard (Port 3000)
echo [1/2] Starting Dashboard (Port 3000)...
cd dashboard
start /B cmd /c "npm run dev > ..\outputs\dashboard.log 2>&1"
cd ..

REM Wait a moment for dashboard to start
timeout /t 2 /nobreak > nul

REM Start Active Trinity Server (Port 3005)
echo [2/2] Starting Active Trinity (Port 3005)...
start /B python -u active_interface\active_server.py > outputs\active_trinity.log 2>&1

echo.
echo ====================================
echo Frontend services started!
echo ====================================
echo.
echo Dashboard:       http://localhost:3000
echo Active Trinity:  http://localhost:3005
echo.
echo Logs:
echo   - Dashboard:      outputs\dashboard.log
echo   - Active Trinity: outputs\active_trinity.log
echo.
echo To stop: run stop_frontend.bat
echo ====================================
