@echo off
setlocal
set "WORKSPACE_ROOT=%~dp0.."
cd /d "%WORKSPACE_ROOT%"
set PYTHONIOENCODING=utf-8
echo [%date% %time%] Starting autonomous goal generator...
"%WORKSPACE_ROOT%\fdo_agi_repo\.venv\Scripts\python.exe" "%WORKSPACE_ROOT%\scripts\autonomous_goal_generator.py" --hours 24 2>&1
echo [%date% %time%] Goal generator completed with exit code: %ERRORLEVEL%
exit /b %ERRORLEVEL%
