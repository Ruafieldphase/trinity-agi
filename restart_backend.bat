@echo off
echo Stopping all Python backend services...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Consciousness Service*"
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Unconscious Service*"
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Background Self Service*"
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Unified Aggregator*"
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe

echo Waiting for processes to terminate...
timeout /t 2 /nobreak >nul

echo Starting backend services...
call start_backend.bat
echo Backend services restarted.
