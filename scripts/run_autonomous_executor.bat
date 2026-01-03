@echo off
set "WORKSPACE_ROOT=%~dp0.."
cd /d "%WORKSPACE_ROOT%"
"%WORKSPACE_ROOT%\fdo_agi_repo\.venv\Scripts\python.exe" "%WORKSPACE_ROOT%\scripts\autonomous_goal_executor.py" > "%WORKSPACE_ROOT%\outputs\logs\autonomous_executor_%date:~0,10%.log" 2>&1
